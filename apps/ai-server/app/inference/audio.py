"""Audio 추론 모듈 — Protocol + Mock + (실 구현은 W3-v2 D2 AnimalCLAP).

실 구현 후보:
- AnimalCLAP encoder (HTS-AT, MIT, frozen) + MLP head 512→128→5 (1차 채택)
- YAMNet + MLP head fallback (AC5 미달 또는 호환성 이슈 시)

참조: `scripts/spike_animalclap.py` (2026-05-07 검증 통과 — `[1, 512]` 임베딩).
"""
from __future__ import annotations

import hashlib
from typing import Protocol

from app.schemas import ActionEnum, AudioCategory, AudioInferOut


class AudioInference(Protocol):
    async def predict(self, audio_bytes: bytes) -> AudioInferOut: ...


def _action_for(score: float) -> ActionEnum:
    if score >= 0.8:
        return "immediate"
    if score >= 0.5:
        return "schedule"
    return "observe"


def _category_for(score: float) -> AudioCategory:
    if score >= 0.8:
        return "이상호흡"
    if score >= 0.6:
        return "기침"
    if score >= 0.3:
        return "꼬르륵"
    return "정상"


class MockAudio:
    """결정적 mock — sha256(audio_bytes) 첫 바이트로 score → category/action 매핑."""

    async def predict(self, audio_bytes: bytes) -> AudioInferOut:
        h = hashlib.sha256(audio_bytes).digest()
        score = h[0] / 255.0
        return AudioInferOut(
            category=_category_for(score),
            score=round(score, 4),
            action=_action_for(score),
            confidence_top1=round(score, 4),
        )
