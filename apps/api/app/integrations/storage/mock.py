"""In-memory storage mock.

테스트 + dev 용. 모듈 단위 dict 로 bytes 보관, presign URL 은 결정적 fake.
"""
from __future__ import annotations

import time

from app.config import settings
from app.integrations.storage import StorageProvider

_OBJECTS: dict[str, tuple[bytes, str]] = {}


class InMemoryStorage(StorageProvider):
    """프로세스 메모리 dict 에 객체 저장. presign URL 은 fake `mock-s3://` 스킴."""

    def __init__(self, bucket: str | None = None) -> None:
        self.bucket = bucket or settings.s3_bucket

    async def presign_put(self, key: str, content_type: str, ttl_s: int = 600) -> str:
        return self._build_url(key, content_type, ttl_s, op="put")

    async def presign_get(self, key: str, ttl_s: int = 600) -> str:
        return self._build_url(key, "", ttl_s, op="get")

    async def fetch_bytes(self, key: str) -> bytes:
        if key not in _OBJECTS:
            raise KeyError(f"object not found: {key}")
        data, _ = _OBJECTS[key]
        return data

    async def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        _OBJECTS[key] = (data, content_type)

    def _build_url(self, key: str, content_type: str, ttl_s: int, *, op: str) -> str:
        expires = int(time.time()) + ttl_s
        ct_part = f"&ct={content_type}" if content_type else ""
        return (
            f"mock-s3://{self.bucket}/{key}"
            f"?op={op}&expires={expires}{ct_part}&sig=mock-deterministic"
        )


def reset() -> None:
    """테스트 fixture cleanup 용."""
    _OBJECTS.clear()
