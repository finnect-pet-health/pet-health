"""Vision 추론 모듈 — Protocol + Mock + (실 구현은 W3-v2 D2).

실 구현 후보:
- MobileNetV3-Small (torchvision pretrained → Kaggle dog skin diseases fine-tune)
- ConvNeXt-Tiny (timm `convnext_tiny.fb_in1k`) fallback if AC3 < 70%
"""
from __future__ import annotations

import hashlib
from typing import Protocol

from app.schemas import ActionEnum, RegionEnum, VisionInferOut, VisionTopResult


class VisionInference(Protocol):
    async def predict(self, image_bytes: bytes, region: RegionEnum) -> VisionInferOut: ...


_REGION_LABELS: dict[str, list[str]] = {
    "skin": ["skin_redness", "skin_normal", "skin_alopecia"],
    "eye": ["eye_discharge", "eye_normal", "eye_cataract"],
    "ear": ["ear_inflammation", "ear_normal", "ear_otitis"],
    "gum": ["gum_paleness", "gum_normal", "gum_periodontal"],
}


def _action_for(score: float) -> ActionEnum:
    if score >= 0.8:
        return "immediate"
    if score >= 0.5:
        return "schedule"
    return "observe"


class MockVision:
    """결정적 mock — 입력 bytes + region 으로 stable 한 top-3 + action 생성."""

    async def predict(
        self, image_bytes: bytes, region: RegionEnum
    ) -> VisionInferOut:
        h = hashlib.sha256(image_bytes + region.encode()).digest()
        labels = _REGION_LABELS.get(region, ["unknown_a", "unknown_b", "unknown_c"])
        raw = sorted([(b / 255.0) for b in h[:3]], reverse=True)
        total = sum(raw) or 1.0
        scores = [s / total for s in raw]
        top1 = scores[0]
        return VisionInferOut(
            top_results=[
                VisionTopResult(label=lbl, score=round(sc, 4))
                for lbl, sc in zip(labels, scores, strict=False)
            ],
            action=_action_for(top1),
            confidence_top1=round(top1, 4),
        )
