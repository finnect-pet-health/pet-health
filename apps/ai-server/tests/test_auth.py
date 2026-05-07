"""AC6 (HMAC 부분): X-AI-HMAC 헤더 검증.

mTLS handshake 는 Cloudflare Tunnel 셋업 + 자체 서명 fixture 가 필요 → W3-v2 D2 본격 작업.
이 케이스는 HMAC 단독 인증만 검증.
"""
from __future__ import annotations

import pytest

from app.security.hmac_auth import compute_hmac


@pytest.mark.asyncio
async def test_vision_missing_hmac_returns_401(client):
    img = b"image-bytes"
    resp = await client.post(
        "/infer/vision",
        files={"file": ("a.jpg", img, "image/jpeg")},
        data={"region": "skin"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_vision_wrong_hmac_returns_403(client):
    img = b"image-bytes"
    resp = await client.post(
        "/infer/vision",
        files={"file": ("a.jpg", img, "image/jpeg")},
        data={"region": "skin"},
        headers={"X-AI-HMAC": "deadbeef" * 8},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_audio_missing_hmac_returns_401(client):
    audio = b"a"
    resp = await client.post(
        "/infer/audio",
        files={"file": ("a.wav", audio, "audio/wav")},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_audio_hmac_must_match_request_body(client):
    audio = b"original-bytes"
    # different content but signed for the original — server should reject.
    sig_for_other = compute_hmac(b"other-bytes")
    resp = await client.post(
        "/infer/audio",
        files={"file": ("a.wav", audio, "audio/wav")},
        headers={"X-AI-HMAC": sig_for_other},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_compute_hmac_changes_with_secret_change(client):
    a = compute_hmac(b"x", secret="secret-1")
    b = compute_hmac(b"x", secret="secret-2")
    assert a != b
