"""Storage Provider 추상.

W3-v2 — `StorageProvider(Protocol)` + mock/real factory swap.
실 S3 (aiobotocore) 구현은 W3-v2 Day 2 에 추가 예정. 현재는 mock-first 유지.
"""
from __future__ import annotations

from typing import Literal, Protocol

Modality = Literal["image", "audio"]

# AC10: content-type 화이트리스트. 이외는 presign 단계에서 400.
ALLOWED_IMAGE_TYPES: frozenset[str] = frozenset({"image/jpeg", "image/png"})
ALLOWED_AUDIO_TYPES: frozenset[str] = frozenset(
    {"audio/wav", "audio/mpeg", "audio/m4a", "audio/mp4"}
)


def allowed_for(modality: Modality) -> frozenset[str]:
    return ALLOWED_IMAGE_TYPES if modality == "image" else ALLOWED_AUDIO_TYPES


class UnsupportedContentTypeError(ValueError):
    """presign 요청 content-type 이 화이트리스트 외일 때."""


class StorageProvider(Protocol):
    async def presign_put(self, key: str, content_type: str, ttl_s: int = 600) -> str: ...
    async def presign_get(self, key: str, ttl_s: int = 600) -> str: ...
    async def fetch_bytes(self, key: str) -> bytes: ...
    async def put_bytes(self, key: str, data: bytes, content_type: str) -> None: ...
