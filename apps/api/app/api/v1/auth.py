"""POST /v1/auth/kakao | /refresh | /logout."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1._errors import http_error
from app.database import get_session
from app.integrations.kakao import KakaoExchangeError
from app.integrations.kakao.factory import get_kakao_client
from app.models import User
from app.security.deps import get_redis
from app.security.jwt import (
    TokenError,
    revoke_refresh,
    rotate_refresh,
)
from app.services.auth import build_access_for, issue_token_pair, upsert_kakao_user

router = APIRouter()


class KakaoLoginIn(BaseModel):
    auth_code: str
    redirect_uri: str


class UserOut(BaseModel):
    id: str
    name: str
    profile_image: str | None


class KakaoLoginOut(BaseModel):
    access: str
    refresh: str
    user: UserOut


class TokenPair(BaseModel):
    access: str
    refresh: str


class RefreshIn(BaseModel):
    refresh: str


@router.post("/kakao", response_model=KakaoLoginOut)
async def kakao_login(
    payload: KakaoLoginIn,
    session: AsyncSession = Depends(get_session),  # noqa: B008
    redis: Redis = Depends(get_redis),  # noqa: B008
) -> KakaoLoginOut:
    client = get_kakao_client()
    try:
        kakao_user = await client.exchange_code(payload.auth_code, payload.redirect_uri)
    except KakaoExchangeError as exc:
        raise http_error(400, "INVALID_CODE", str(exc)) from exc
    except Exception as exc:  # network failures from real client
        raise http_error(502, "KAKAO_UNREACHABLE", "kakao api unreachable") from exc

    user = await upsert_kakao_user(session, kakao_user)
    access, refresh = await issue_token_pair(session, redis, user)
    return KakaoLoginOut(
        access=access,
        refresh=refresh,
        user=UserOut(
            id=str(user.id), name=user.name, profile_image=user.profile_image
        ),
    )


@router.post("/refresh", response_model=TokenPair)
async def refresh_token(
    payload: RefreshIn,
    session: AsyncSession = Depends(get_session),  # noqa: B008
    redis: Redis = Depends(get_redis),  # noqa: B008
) -> TokenPair:
    try:
        new_refresh, user_id = await rotate_refresh(payload.refresh, redis)
    except TokenError as exc:
        raise http_error(401, "UNAUTHORIZED", str(exc)) from exc

    import uuid as _uuid

    user = await session.get(User, _uuid.UUID(user_id))
    if user is None:
        raise http_error(401, "UNAUTHORIZED", "user not found")
    access = await build_access_for(session, user)
    return TokenPair(access=access, refresh=new_refresh)


@router.post("/logout", status_code=204)
async def logout(
    payload: RefreshIn,
    redis: Redis = Depends(get_redis),  # noqa: B008
) -> None:
    """Idempotent logout — revoke refresh token if it exists; otherwise no-op."""
    try:
        await revoke_refresh(payload.refresh, redis)
    except TokenError:
        pass
    return None
