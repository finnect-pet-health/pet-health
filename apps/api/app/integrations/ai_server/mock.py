"""결정적 mock AI 서버 클라이언트.

테스트 + 시연 용. 입력 bytes 길이 / region 으로 stable 한 결과 생성.
"""
from __future__ import annotations

import hashlib

from app.integrations.ai_server import (
    ActionEnum,
    AudioResult,
    VisionResult,
    VisionTopResult,
)


class MockAIServerClient:
    """입력 해시 기반 결정적 응답."""

    async def infer_vision(self, image_bytes: bytes, region: str) -> VisionResult:
        h = hashlib.sha256(image_bytes + region.encode()).digest()
        labels = self._labels_for_region(region)
        scores = sorted(
            [(b / 255.0) for b in h[:3]], reverse=True
        )
        # 정규화로 합 1 보장 (단순화).
        total = sum(scores) or 1.0
        scores = [s / total for s in scores]
        top1 = scores[0]
        action = self._action_for_score(top1)
        return VisionResult(
            top_results=[
                VisionTopResult(label=lbl, score=round(sc, 4))
                for lbl, sc in zip(labels, scores, strict=False)
            ],
            action=action,
            confidence_top1=round(top1, 4),
        )

    async def infer_audio(self, audio_bytes: bytes) -> AudioResult:
        h = hashlib.sha256(audio_bytes).digest()
        score = h[0] / 255.0
        category = self._audio_category_for_score(score)
        action = self._action_for_score(score)
        return AudioResult(
            category=category,
            score=round(score, 4),
            action=action,
            confidence_top1=round(score, 4),
        )

    @staticmethod
    def _labels_for_region(region: str) -> list[str]:
        catalog = {
            "skin": ["skin_redness", "skin_normal", "skin_alopecia"],
            "eye": ["eye_discharge", "eye_normal", "eye_cataract"],
            "ear": ["ear_inflammation", "ear_normal", "ear_otitis"],
            "gum": ["gum_paleness", "gum_normal", "gum_periodontal"],
        }
        return catalog.get(region, ["unknown_a", "unknown_b", "unknown_c"])

    @staticmethod
    def _action_for_score(score: float) -> ActionEnum:
        if score >= 0.8:
            return "immediate"
        if score >= 0.5:
            return "schedule"
        return "observe"

    @staticmethod
    def _audio_category_for_score(score: float) -> str:
        if score >= 0.8:
            return "이상호흡"
        if score >= 0.6:
            return "기침"
        if score >= 0.3:
            return "꼬르륵"
        return "정상"
