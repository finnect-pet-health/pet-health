from __future__ import annotations

import os

from app.config import settings
from app.integrations.kakao import KakaoOAuthClient


def get_kakao_client() -> KakaoOAuthClient:
    """Return Mock client in dev/test environments, Real client otherwise."""
    use_mock = settings.app_env == "development" or os.getenv("KAKAO_USE_MOCK", "") == "1"
    if use_mock:
        from app.integrations.kakao.mock import MockKakaoOAuthClient

        return MockKakaoOAuthClient()
    from app.integrations.kakao.real import RealKakaoOAuthClient

    return RealKakaoOAuthClient()
