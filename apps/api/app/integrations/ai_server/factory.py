"""AI 서버 클라이언트 factory — mock/real swap.

W3-v2 D2 의 mTLS+HMAC httpx 실 구현 추가 전까지 mock 강제.
`AI_SERVER_USE_MOCK=1` 또는 app_env != production → mock.
"""
from __future__ import annotations

import os
import warnings

from app.config import settings
from app.integrations.ai_server import AIServerClient


def get_ai_client() -> AIServerClient:
    use_mock = (
        settings.app_env != "production"
        or os.getenv("AI_SERVER_USE_MOCK", "") == "1"
    )
    if not use_mock:
        warnings.warn(
            "real AIServerClient (mTLS+HMAC) not yet implemented (W3-v2 D2 deliverable) — "
            "falling back to mock",
            RuntimeWarning,
            stacklevel=2,
        )
    from app.integrations.ai_server.mock import MockAIServerClient

    return MockAIServerClient()
