"""AC2: POST /infer/vision mock smoke (multipart + region + HMAC)."""
from __future__ import annotations

import pytest

from app.security.hmac_auth import compute_hmac


@pytest.mark.asyncio
async def test_vision_smoke_mock(client):
    image_bytes = b"fake-jpeg-bytes-for-mock-test"
    sig = compute_hmac(image_bytes)

    resp = await client.post(
        "/infer/vision",
        files={"file": ("sample.jpg", image_bytes, "image/jpeg")},
        data={"region": "skin"},
        headers={"X-AI-HMAC": sig},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert len(body["top_results"]) == 3
    assert body["action"] in {"immediate", "schedule", "observe"}
    assert 0.0 <= body["confidence_top1"] <= 1.0
    labels = {r["label"] for r in body["top_results"]}
    assert labels & {"skin_redness", "skin_normal", "skin_alopecia"}


@pytest.mark.asyncio
async def test_vision_default_region_is_skin(client):
    img = b"x"
    resp = await client.post(
        "/infer/vision",
        files={"file": ("a.jpg", img, "image/jpeg")},
        headers={"X-AI-HMAC": compute_hmac(img)},
    )
    assert resp.status_code == 200
    labels = {r["label"] for r in resp.json()["top_results"]}
    assert labels & {"skin_redness", "skin_normal", "skin_alopecia"}


@pytest.mark.asyncio
@pytest.mark.parametrize("region", ["eye", "ear", "gum"])
async def test_vision_each_region_uses_its_label_catalog(client, region):
    img = b"region-test"
    resp = await client.post(
        "/infer/vision",
        files={"file": ("a.jpg", img, "image/jpeg")},
        data={"region": region},
        headers={"X-AI-HMAC": compute_hmac(img)},
    )
    assert resp.status_code == 200
    labels = [r["label"] for r in resp.json()["top_results"]]
    assert any(region in lbl for lbl in labels)
