"""Shared test fixtures.

- ``_alembic_upgrade`` (session scope): one-time schema upgrade against the test DB.
- ``db_session``: SAVEPOINT-based rollback per test for isolation.
- ``redis_client``: dedicated DB index 15, ``flushdb`` between tests.
- ``app_client``: httpx.AsyncClient over ASGITransport, lifespan bypassed.
- ``auth_headers``: tiny helper for generating Bearer tokens with full claims.
"""
from __future__ import annotations

import asyncio
import os
import uuid

import pytest
import pytest_asyncio
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure DSN/redis URL are set BEFORE app imports load Settings.
_DEFAULT_DSN = "postgresql+asyncpg://petfinect:petfinect@localhost:5434/petfinect_test"
_DEFAULT_REDIS = "redis://localhost:6382/15"
os.environ.setdefault("PYTEST_DSN", _DEFAULT_DSN)
os.environ["POSTGRES_DSN"] = os.environ["PYTEST_DSN"]
os.environ["REDIS_URL"] = _DEFAULT_REDIS

from app.database import Base  # noqa: E402
from app.main import app  # noqa: E402
from app.security.deps import get_redis  # noqa: E402
from app.security.jwt import encode_access  # noqa: E402

TEST_DSN = os.environ["PYTEST_DSN"]
TEST_REDIS_URL = os.environ["REDIS_URL"]


@pytest.fixture(scope="session")
def _alembic_upgrade():
    """Drop + recreate the test schema using SQLAlchemy metadata (asyncpg only)."""
    import app.models  # noqa: F401  populate Base.metadata

    async def _bootstrap() -> None:
        engine = create_async_engine(TEST_DSN, future=True)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            for enum_name in ("member_role", "pet_species"):
                await conn.execute(text(f"DROP TYPE IF EXISTS {enum_name} CASCADE"))
            await conn.run_sync(Base.metadata.create_all)
        await engine.dispose()

    asyncio.run(_bootstrap())
    yield


@pytest_asyncio.fixture
async def db_session(_alembic_upgrade) -> AsyncSession:
    """Per-test AsyncSession with SAVEPOINT-based rollback isolation.

    Uses the documented "nested transaction with auto-restart" pattern so that
    code under test can call ``session.commit()`` (only the inner SAVEPOINT is
    released; the outer transaction we own is rolled back at teardown).
    """
    engine = create_async_engine(TEST_DSN, future=True)
    connection = await engine.connect()
    trans = await connection.begin()

    sessionmaker_ = async_sessionmaker(
        bind=connection,
        expire_on_commit=False,
        class_=AsyncSession,
        join_transaction_mode="create_savepoint",
    )
    session = sessionmaker_()

    try:
        yield session
    finally:
        await session.close()
        if trans.is_active:
            await trans.rollback()
        await connection.close()
        await engine.dispose()


@pytest_asyncio.fixture
async def redis_client():
    client = aioredis.from_url(TEST_REDIS_URL, decode_responses=False)
    await client.flushdb()
    try:
        yield client
    finally:
        await client.flushdb()
        await client.aclose()


@pytest_asyncio.fixture
async def app_client(db_session: AsyncSession, redis_client):
    """Provide an httpx.AsyncClient that talks to the FastAPI app in-process.

    Lifespan is bypassed (D7); ``app.state.redis`` and ``get_session`` are stubbed
    via ``dependency_overrides`` so the request shares the test session.
    """
    from app.database import get_session

    async def _override_session():
        yield db_session

    async def _override_redis():
        return redis_client

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_redis] = _override_redis
    app.state.redis = redis_client

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """Return a callable producing Bearer headers for a given user/family map."""

    def _make(
        user_id: str | uuid.UUID,
        fids: list[str] | None = None,
        roles: dict[str, str] | None = None,
    ) -> dict[str, str]:
        token = encode_access(str(user_id), fids or [], roles or {})
        return {"Authorization": f"Bearer {token}"}

    return _make
