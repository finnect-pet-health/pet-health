from __future__ import annotations

import httpx

from app.config import settings
from app.integrations.kakao import KakaoExchangeError, KakaoUser

_TOKEN_URL = "https://kauth.kakao.com/oauth/token"  # noqa: S105
_USERINFO_URL = "https://kapi.kakao.com/v2/user/me"


class RealKakaoOAuthClient:
    """Production Kakao OAuth client. Full implementation deferred to W2."""

    async def exchange_code(self, code: str, redirect_uri: str) -> KakaoUser:
        async with httpx.AsyncClient() as client:
            # Step 1: exchange auth code for kakao access_token
            token_resp = await client.post(
                _TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.kakao_rest_api_key,
                    "client_secret": settings.kakao_client_secret,
                    "redirect_uri": redirect_uri,
                    "code": code,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if token_resp.status_code != 200:
                raise KakaoExchangeError(f"token_exchange_failed: {token_resp.status_code}")

            # Step 2: fetch user info with kakao access_token
            kakao_access_token = token_resp.json().get("access_token")
            _user_resp = await client.get(
                _USERINFO_URL,
                headers={"Authorization": f"Bearer {kakao_access_token}"},
            )

        # W2: parse user_resp JSON into KakaoUser
        raise NotImplementedError("W2")
