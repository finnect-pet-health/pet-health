from __future__ import annotations

import re

from app.integrations.kakao import KakaoExchangeError, KakaoUser

_PATTERN = re.compile(r"^mock-user-(\d+)$")


class MockKakaoOAuthClient:
    """Deterministic mock: 'mock-user-{n}' -> KakaoUser."""

    async def exchange_code(self, code: str, redirect_uri: str) -> KakaoUser:
        m = _PATTERN.match(code)
        if not m:
            raise KakaoExchangeError("invalid_code")
        n = m.group(1)
        return KakaoUser(
            kakao_id=f"mock_{n}",
            name=f"테스트유저{n}",
            email=f"mock{n}@example.test",
            profile_image=None,
        )
