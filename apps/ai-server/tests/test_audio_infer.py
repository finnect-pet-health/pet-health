"""AC4: POST /infer/audio mock smoke."""
from __future__ import annotations

import pytest

from app.security.hmac_auth import compute_hmac


@pytest.mark.asyncio
async def test_audio_smoke_mock(client):
    audio_bytes = b"\xff\xfb\xfake-audio-mock-bytes" * 20  # ~5초 시뮬레이션
    sig = compute_hmac(audio_bytes)

    resp = await client.post(
        "/infer/audio",
        files={"file": ("cough.m4a", audio_bytes, "audio/m4a")},
        headers={"X-AI-HMAC": sig},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["category"] in {"정상", "기침", "이상호흡", "꼬르륵", "기타"}
    assert 0.0 <= body["score"] <= 1.0
    assert body["action"] in {"immediate", "schedule", "observe"}


@pytest.mark.asyncio
async def test_audio_deterministic_for_same_input(client):
    audio = b"deterministic-input"
    sig = compute_hmac(audio)

    r1 = await client.post(
        "/infer/audio",
        files={"file": ("a.wav", audio, "audio/wav")},
        headers={"X-AI-HMAC": sig},
    )
    r2 = await client.post(
        "/infer/audio",
        files={"file": ("a.wav", audio, "audio/wav")},
        headers={"X-AI-HMAC": sig},
    )
    assert r1.json() == r2.json()
