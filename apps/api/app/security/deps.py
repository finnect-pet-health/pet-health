"""FastAPI dependency providers for auth, redis, and family RBAC."""
from __future__ import annotations

import uuid

from fastapi import Depends, Header, Request
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1._errors import http_error
from app.database import get_session
from app.models import FamilyMember, User
from app.security.jwt import AccessClaims, TokenError, decode_access


async def get_redis(request: Request) -> Redis:
    """Return the application Redis client from app.state."""
    return request.app.state.redis


def _parse_bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise http_error(401, "UNAUTHORIZED", "missing bearer token")
    return authorization.split(" ", 1)[1].strip()


async def current_claims(
    authorization: str | None = Header(default=None),
) -> AccessClaims:
    token = _parse_bearer(authorization)
    try:
        return decode_access(token)
    except TokenError as exc:
        raise http_error(401, "UNAUTHORIZED", str(exc)) from exc


async def current_user(
    claims: AccessClaims = Depends(current_claims),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> User:
    try:
        user_id = uuid.UUID(claims.sub)
    except (ValueError, TypeError) as exc:
        raise http_error(401, "UNAUTHORIZED", "invalid sub claim") from exc

    user = await session.get(User, user_id)
    if user is None:
        raise http_error(401, "UNAUTHORIZED", "user not found")
    return user


def require_family(role: str = "member"):
    """RBAC dep — ensure current user has at least the requested role on the
    `family_id` path parameter. ``owner`` implies ``member``.
    """

    async def _dep(
        family_id: str,
        claims: AccessClaims = Depends(current_claims),  # noqa: B008
        user: User = Depends(current_user),  # noqa: B008
        session: AsyncSession = Depends(get_session),  # noqa: B008
    ) -> FamilyMember:
        try:
            fid = uuid.UUID(family_id)
        except (ValueError, TypeError) as exc:
            raise http_error(404, "NOT_FOUND", "family not found") from exc

        # Token fast-path: roles dict has authoritative role for fids in token.
        token_role = claims.roles.get(str(fid))

        # DB fallback (covers freshly joined families that are not yet in the token).
        stmt = select(FamilyMember).where(
            FamilyMember.family_id == fid,
            FamilyMember.user_id == user.id,
        )
        member = (await session.execute(stmt)).scalar_one_or_none()
        if member is None:
            if token_role:
                raise http_error(403, "FORBIDDEN", "not a member of this family")
            raise http_error(404, "NOT_FOUND", "family not found")

        effective_role = member.role
        if role == "owner" and effective_role != "owner":
            raise http_error(403, "FORBIDDEN", "owner role required")
        return member

    return _dep
