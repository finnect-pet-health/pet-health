"""Inference factory — mock/real swap. 실 구현 추가 전까지 항상 mock."""
from __future__ import annotations

import os
import warnings

from app.inference.audio import AudioInference, MockAudio
from app.inference.vision import MockVision, VisionInference


def get_vision_inference() -> VisionInference:
    if os.getenv("VISION_USE_REAL", "") == "1":
        warnings.warn(
            "real Vision (MobileNetV3) not yet implemented (W3-v2 D2) — using mock",
            RuntimeWarning,
            stacklevel=2,
        )
    return MockVision()


def get_audio_inference() -> AudioInference:
    if os.getenv("AUDIO_USE_REAL", "") == "1":
        warnings.warn(
            "real Audio (AnimalCLAP) not yet implemented (W3-v2 D2) — using mock",
            RuntimeWarning,
            stacklevel=2,
        )
    return MockAudio()
