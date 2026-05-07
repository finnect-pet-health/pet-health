"""로컬 AI 서버 (RTX 5090) 클라이언트 추상.

실 구현은 mTLS + HMAC + httpx (W3-v2 D2). 현재는 mock-first 유지.
"""
from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel, Field

ActionEnum = Literal["immediate", "schedule", "observe"]


class VisionTopResult(BaseModel):
    label: str
    score: float = Field(ge=0.0, le=1.0)


class VisionResult(BaseModel):
    top_results: list[VisionTopResult]
    action: ActionEnum
    confidence_top1: float = Field(ge=0.0, le=1.0)


class AudioResult(BaseModel):
    category: str
    score: float = Field(ge=0.0, le=1.0)
    action: ActionEnum
    confidence_top1: float = Field(ge=0.0, le=1.0)


class AIServerError(Exception):
    """AI 서버 호출 실패 (timeout/HMAC/mTLS). 라우터는 룰 기반 fallback 후 200 유지."""


class AIServerClient(Protocol):
    async def infer_vision(self, image_bytes: bytes, region: str) -> VisionResult: ...
    async def infer_audio(self, audio_bytes: bytes) -> AudioResult: ...
