"""Storage factory — env 기반 mock/real swap.

W3-v2 head-start: 실 S3 (aiobotocore) 구현 추가 전까지 항상 mock 반환.
AWS keys 가 명시적으로 셋되어도 RuntimeWarning + mock fallback (계획 §3.1 참조).
"""
from __future__ import annotations

import os
import warnings

from app.config import settings
from app.integrations.storage import StorageProvider


def get_storage() -> StorageProvider:
    use_mock = (
        settings.app_env != "production"
        or os.getenv("STORAGE_USE_MOCK", "") == "1"
    )
    if not use_mock:
        warnings.warn(
            "real S3 provider not yet implemented (W3-v2 D2 deliverable) — "
            "falling back to in-memory mock",
            RuntimeWarning,
            stacklevel=2,
        )
    from app.integrations.storage.mock import InMemoryStorage

    return InMemoryStorage()
