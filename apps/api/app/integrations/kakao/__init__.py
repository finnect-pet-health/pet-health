from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class KakaoExchangeError(Exception):
    """Raised when an auth-code exchange fails."""


@dataclass(frozen=True)
class KakaoUser:
    kakao_id: str
    name: str
    email: str | None
    profile_image: str | None


class KakaoOAuthClient(Protocol):
    async def exchange_code(self, code: str, redirect_uri: str) -> KakaoUser:
        ...
