"""Auth service layer — Kakao user upsert, access claim assembly, token pair issue."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.kakao import KakaoUser
from app.models import FamilyMember, User
from app.security.jwt import encode_access, issue_refresh


async def upsert_kakao_user(session: AsyncSession, kakao: KakaoUser) -> User:
    """Insert-or-update a User keyed by ``kakao_id`` (D2).

    Idempotent: subsequent calls update name / email / profile_image / last_login_at.
    """
    now = datetime.now(UTC)
    stmt = (
        pg_insert(User)
        .values(
            id=uuid.uuid4(),
            kakao_id=kakao.kakao_id,
            email=kakao.email,
            name=kakao.name,
            profile_image=kakao.profile_image,
            created_at=now,
            last_login_at=now,
        )
        .on_conflict_do_update(
            index_elements=[User.kakao_id],
            set_={
                "name": kakao.name,
                "email": kakao.email,
                "profile_image": kakao.profile_image,
                "last_login_at": now,
            },
        )
        .returning(User.id)
    )
    result = await session.execute(stmt)
    user_id = result.scalar_one()
    await session.commit()

    # ON CONFLICT DO UPDATE bypasses ORM identity map — expire so we re-read.
    session.expire_all()
    user = await session.get(User, user_id)
    assert user is not None  # row was just upserted
    return user


async def build_access_for(session: AsyncSession, user: User) -> str:
    """Encode an access JWT with the user's current family membership claims."""
    stmt = select(FamilyMember.family_id, FamilyMember.role).where(
        FamilyMember.user_id == user.id
    )
    rows = (await session.execute(stmt)).all()
    fids = [str(fid) for fid, _ in rows]
    roles = {str(fid): role for fid, role in rows}
    return encode_access(str(user.id), fids, roles)


async def issue_token_pair(
    session: AsyncSession, redis: Redis, user: User
) -> tuple[str, str]:
    """Return (access, refresh) for the given user."""
    access = await build_access_for(session, user)
    refresh, _jti = await issue_refresh(str(user.id), redis)
    return access, refresh
