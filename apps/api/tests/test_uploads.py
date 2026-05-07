"""W3-v2 head-start: `/v1/uploads/presign` content-type 화이트리스트 + key 포맷 검증.

Mock storage 경로(InMemoryStorage)만 다룸. AC10 의 LocalStack/S3 PUT 라운드트립은
real provider 가 W3-v2 D2 에 추가된 뒤 별도 케이스로 보강.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.storage.mock import InMemoryStorage, reset


@pytest.fixture(autouse=True)
def _reset_inmemory_storage():
    reset()
    yield
    reset()


async def _make_user(db_session: AsyncSession) -> uuid.UUID:
    uid = uuid.uuid4()
    await db_session.execute(
        text(
            """
            INSERT INTO "user" (id, kakao_id, name, email, created_at)
            VALUES (CAST(:id AS uuid), :kakao_id, :name, :email, now())
            """
        ),
        {
            "id": str(uid),
            "kakao_id": f"k_{uid.hex[:10]}",
            "name": "tester",
            "email": f"{uid.hex[:6]}@test.local",
        },
    )
    await db_session.commit()
    return uid


@pytest.mark.asyncio
async def test_presign_image_returns_key_url_ttl(app_client, db_session, auth_headers):
    uid = await _make_user(db_session)
    resp = await app_client.post(
        "/v1/uploads/presign",
        json={"modality": "image", "content_type": "image/jpeg"},
        headers=auth_headers(uid),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ttl_s"] == 600
    assert body["key"].startswith(f"uploads/image/{uid}/")
    assert body["key"].endswith(".jpg")
    assert body["url"].startswith("mock-s3://")
    assert "ct=image/jpeg" in body["url"]


@pytest.mark.asyncio
async def test_presign_audio_m4a(app_client, db_session, auth_headers):
    uid = await _make_user(db_session)
    resp = await app_client.post(
        "/v1/uploads/presign",
        json={"modality": "audio", "content_type": "audio/m4a"},
        headers=auth_headers(uid),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["key"].startswith(f"uploads/audio/{uid}/")
    assert body["key"].endswith(".m4a")


@pytest.mark.asyncio
async def test_presign_rejects_disallowed_content_type(app_client, db_session, auth_headers):
    uid = await _make_user(db_session)
    # PDF for image modality — block.
    resp = await app_client.post(
        "/v1/uploads/presign",
        json={"modality": "image", "content_type": "application/pdf"},
        headers=auth_headers(uid),
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["error"]["code"] == "INVALID_CONTENT_TYPE"

    # WAV for image modality (cross-modality) — block.
    resp = await app_client.post(
        "/v1/uploads/presign",
        json={"modality": "image", "content_type": "audio/wav"},
        headers=auth_headers(uid),
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_presign_requires_auth(app_client):
    resp = await app_client.post(
        "/v1/uploads/presign",
        json={"modality": "image", "content_type": "image/jpeg"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_inmemory_storage_put_get_roundtrip():
    storage = InMemoryStorage()
    key = "uploads/image/test/abc.jpg"
    await storage.put_bytes(key, b"\x89PNG\x00fake", "image/png")
    data = await storage.fetch_bytes(key)
    assert data == b"\x89PNG\x00fake"


@pytest.mark.asyncio
async def test_inmemory_storage_fetch_missing_raises():
    storage = InMemoryStorage()
    with pytest.raises(KeyError):
        await storage.fetch_bytes("does/not/exist")
