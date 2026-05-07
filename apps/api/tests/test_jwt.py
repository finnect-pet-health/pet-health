"""Tests for JWT encode/decode and refresh token lifecycle."""
from __future__ import annotations

import time
import uuid

import pytest
import pytest_asyncio
import redis.asyncio as aioredis

from app.security.jwt import (
    AccessClaims,
    TokenError,
    decode_access,
    encode_access,
    issue_refresh,
    revoke_refresh,
    rotate_refresh,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def redis_client():
    client = aioredis.from_url("redis://localhost:6382/15", decode_responses=False)
    yield client
    await client.flushdb()
    await client.aclose()


# ---------------------------------------------------------------------------
# Access token tests
# ---------------------------------------------------------------------------

def test_encode_decode_roundtrip():
    user_id = str(uuid.uuid4())
    fid = str(uuid.uuid4())
    roles = {fid: "owner"}
    token = encode_access(user_id, [fid], roles)
    claims = decode_access(token)
    assert isinstance(claims, AccessClaims)
    assert claims.sub == user_id
    assert fid in claims.fids
    assert claims.roles[fid] == "owner"


def test_decode_expired_token_raises():
    user_id = str(uuid.uuid4())
    # Issue token with TTL of 0 minutes — expires immediately
    token = encode_access(user_id, [], {}, ttl_min=0)
    # Give jose a moment to consider it expired (exp is in the past by now)
    time.sleep(1)
    with pytest.raises(TokenError):
        decode_access(token)


def test_decode_forged_token_raises():
    with pytest.raises(TokenError):
        decode_access("this.is.not.a.valid.jwt")


def test_decode_wrong_secret_raises():
    """Token signed with wrong secret must fail."""
    from jose import jwt as jose_jwt

    payload = {"sub": str(uuid.uuid4()), "fids": [], "roles": {}, "exp": 9999999999}
    bad_token = jose_jwt.encode(payload, "wrong-secret", algorithm="HS256")
    with pytest.raises(TokenError):
        decode_access(bad_token)


# ---------------------------------------------------------------------------
# Refresh token tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_issue_refresh_stores_in_redis(redis_client):
    user_id = str(uuid.uuid4())
    token, jti = await issue_refresh(user_id, redis_client)
    assert token
    assert jti
    # Both forward and reverse keys must exist
    fwd = await redis_client.get(f"refresh:{user_id}:{jti}")
    rev = await redis_client.get(f"refresh_rev:{token}")
    assert fwd is not None
    assert rev is not None


@pytest.mark.asyncio
async def test_rotate_refresh_invalidates_old_token(redis_client):
    user_id = str(uuid.uuid4())
    old_token, old_jti = await issue_refresh(user_id, redis_client)
    new_token, returned_uid = await rotate_refresh(old_token, redis_client)
    assert new_token != old_token
    assert returned_uid == user_id

    # Old token must be gone
    old_rev = await redis_client.get(f"refresh_rev:{old_token}")
    assert old_rev is None

    # Old forward key must be gone
    old_fwd = await redis_client.get(f"refresh:{user_id}:{old_jti}")
    assert old_fwd is None

    # New token must work (rotate again)
    another_token, another_uid = await rotate_refresh(new_token, redis_client)
    assert another_token != new_token
    assert another_uid == user_id


@pytest.mark.asyncio
async def test_rotate_nonexistent_token_raises(redis_client):
    with pytest.raises(TokenError):
        await rotate_refresh("nonexistent-token", redis_client)


@pytest.mark.asyncio
async def test_revoke_refresh(redis_client):
    user_id = str(uuid.uuid4())
    token, jti = await issue_refresh(user_id, redis_client)
    await revoke_refresh(token, redis_client)

    # Token must be gone after revoke
    rev = await redis_client.get(f"refresh_rev:{token}")
    assert rev is None


@pytest.mark.asyncio
async def test_revoke_then_rotate_raises(redis_client):
    user_id = str(uuid.uuid4())
    token, _ = await issue_refresh(user_id, redis_client)
    await revoke_refresh(token, redis_client)
    with pytest.raises(TokenError):
        await rotate_refresh(token, redis_client)


@pytest.mark.asyncio
async def test_revoke_nonexistent_raises(redis_client):
    with pytest.raises(TokenError):
        await revoke_refresh("ghost-token", redis_client)
