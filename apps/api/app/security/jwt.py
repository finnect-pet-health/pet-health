from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from redis.asyncio import Redis

from app.config import settings

ALGORITHM = "HS256"
_REFRESH_TTL_SECONDS = settings.refresh_token_ttl_days * 24 * 3600


class TokenError(Exception):
    """Raised on JWT decode failure or refresh token validation failure."""


@dataclass(frozen=True)
class AccessClaims:
    sub: str                          # user_id (UUID as str)
    fids: list[str] = field(default_factory=list)   # family UUIDs
    roles: dict[str, str] = field(default_factory=dict)  # {fid: role}
    exp: int = 0                      # unix timestamp


def encode_access(
    user_id: str,
    fids: list[str],
    roles: dict[str, str],
    ttl_min: int = 15,
) -> str:
    """Issue a signed HS256 access JWT."""
    expire = datetime.now(UTC) + timedelta(minutes=ttl_min)
    payload = {
        "sub": str(user_id),
        "fids": [str(f) for f in fids],
        "roles": {str(k): v for k, v in roles.items()},
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access(token: str) -> AccessClaims:
    """Decode and validate an access JWT. Raises TokenError on failure."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise TokenError(str(exc)) from exc

    return AccessClaims(
        sub=payload["sub"],
        fids=payload.get("fids", []),
        roles=payload.get("roles", {}),
        exp=payload.get("exp", 0),
    )


async def issue_refresh(user_id: str, redis: Redis) -> tuple[str, str]:
    """Create an opaque refresh token and store it in Redis.

    Returns (token, jti). Redis key: refresh:{user_id}:{jti}
    """
    jti = str(uuid.uuid4())
    token = str(uuid.uuid4())
    key = f"refresh:{user_id}:{jti}"
    # Store token value so we can verify it on rotation
    await redis.setex(key, _REFRESH_TTL_SECONDS, token)
    # Store reverse mapping: token -> "{user_id}:{jti}" for lookup
    rev_key = f"refresh_rev:{token}"
    await redis.setex(rev_key, _REFRESH_TTL_SECONDS, f"{user_id}:{jti}")
    return token, jti


async def rotate_refresh(token: str, redis: Redis) -> tuple[str, str]:
    """Validate existing refresh token, revoke it, and issue a new one.

    Returns (new_token, user_id). Raises TokenError if token is not found/expired.
    """
    rev_key = f"refresh_rev:{token}"
    mapping = await redis.get(rev_key)
    if not mapping:
        raise TokenError("refresh token not found or expired")

    mapping_str = mapping.decode() if isinstance(mapping, bytes) else mapping
    user_id, jti = mapping_str.split(":", 1)

    # Delete old keys atomically-ish (pipeline)
    pipe = redis.pipeline()
    pipe.delete(f"refresh:{user_id}:{jti}")
    pipe.delete(rev_key)
    await pipe.execute()

    new_token, _new_jti = await issue_refresh(user_id, redis)
    return new_token, user_id


async def revoke_refresh(token: str, redis: Redis) -> None:
    """Revoke a refresh token. Raises TokenError if not found."""
    rev_key = f"refresh_rev:{token}"
    mapping = await redis.get(rev_key)
    if not mapping:
        raise TokenError("refresh token not found or already revoked")

    mapping_str = mapping.decode() if isinstance(mapping, bytes) else mapping
    user_id, jti = mapping_str.split(":", 1)

    pipe = redis.pipeline()
    pipe.delete(f"refresh:{user_id}:{jti}")
    pipe.delete(rev_key)
    await pipe.execute()
