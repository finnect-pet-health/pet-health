"""W3-v2 head-start: `/v1/diagnose/*` 오케스트레이션 (AC7/8/9).

Mock storage + Mock AI server 경로 happy path.
- AC7 image diagnose
- AC8 audio diagnose
- AC9 list with RBAC (다른 가족 펫 → 404)
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


async def _seed_user_family_pet(
    db_session: AsyncSession, *, user_id: uuid.UUID | None = None
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    uid = user_id or uuid.uuid4()
    fid = uuid.uuid4()
    pid = uuid.uuid4()
    await db_session.execute(
        text(
            """
            INSERT INTO "user" (id, kakao_id, name, email, created_at)
            VALUES (CAST(:uid AS uuid), :kakao_id, :name, :email, now())
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {
            "uid": str(uid),
            "kakao_id": f"k_{uid.hex[:10]}",
            "name": "tester",
            "email": f"{uid.hex[:6]}@test.local",
        },
    )
    await db_session.execute(
        text(
            """
            INSERT INTO family (id, name, owner_id, created_at)
            VALUES (CAST(:fid AS uuid), 'F', CAST(:uid AS uuid), now())
            """
        ),
        {"fid": str(fid), "uid": str(uid)},
    )
    await db_session.execute(
        text(
            """
            INSERT INTO family_member (family_id, user_id, role, joined_at)
            VALUES (CAST(:fid AS uuid), CAST(:uid AS uuid), 'owner', now())
            """
        ),
        {"fid": str(fid), "uid": str(uid)},
    )
    await db_session.execute(
        text(
            """
            INSERT INTO pet (id, family_id, species, breed)
            VALUES (CAST(:pid AS uuid), CAST(:fid AS uuid), 'dog', 'mixed')
            """
        ),
        {"pid": str(pid), "fid": str(fid)},
    )
    await db_session.commit()
    return uid, fid, pid


@pytest.mark.asyncio
async def test_diagnose_image_happy_path(app_client, db_session, auth_headers):
    uid, fid, pid = await _seed_user_family_pet(db_session)

    storage = InMemoryStorage()
    s3_key = "uploads/image/test/sample.jpg"
    await storage.put_bytes(s3_key, b"fake-image-bytes-for-mock-ai", "image/jpeg")

    resp = await app_client.post(
        "/v1/diagnose/image",
        json={"pet_id": str(pid), "image_s3_key": s3_key, "region": "skin"},
        headers=auth_headers(uid, fids=[str(fid)], roles={str(fid): "owner"}),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["modality"] == "image"
    assert body["s3_ref"] == s3_key
    assert body["pet_id"] == str(pid)
    assert body["action"] in {"immediate", "schedule", "observe"}
    assert 0.0 <= body["confidence_top1"] <= 1.0
    assert len(body["top_results"]) == 3
    # skin region 라벨 셋이 mock 카탈로그와 일치
    labels = {r["label"] for r in body["top_results"]}
    assert labels & {"skin_redness", "skin_normal", "skin_alopecia"}


@pytest.mark.asyncio
async def test_diagnose_audio_happy_path(app_client, db_session, auth_headers):
    uid, fid, pid = await _seed_user_family_pet(db_session)

    storage = InMemoryStorage()
    s3_key = "uploads/audio/test/cough.m4a"
    await storage.put_bytes(s3_key, b"\xff\xfb\xfake-audio-bytes", "audio/m4a")

    resp = await app_client.post(
        "/v1/diagnose/audio",
        json={"pet_id": str(pid), "audio_s3_key": s3_key},
        headers=auth_headers(uid, fids=[str(fid)], roles={str(fid): "owner"}),
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["modality"] == "audio"
    assert body["s3_ref"] == s3_key
    assert body["top_results"][0]["category"] in {
        "정상", "기침", "이상호흡", "꼬르륵", "기타"
    }


@pytest.mark.asyncio
async def test_diagnoses_list_orders_desc_with_limit(
    app_client, db_session, auth_headers
):
    uid, fid, pid = await _seed_user_family_pet(db_session)
    storage = InMemoryStorage()

    # 3건 적재 (서로 다른 키 → 결정적이지만 다른 score)
    for i in range(3):
        key = f"uploads/image/test/img-{i}.jpg"
        await storage.put_bytes(key, f"img-bytes-{i}".encode(), "image/jpeg")
        resp = await app_client.post(
            "/v1/diagnose/image",
            json={"pet_id": str(pid), "image_s3_key": key, "region": "eye"},
            headers=auth_headers(uid, fids=[str(fid)], roles={str(fid): "owner"}),
        )
        assert resp.status_code == 200

    resp = await app_client.get(
        f"/v1/pets/{pid}/diagnoses?limit=2",
        headers=auth_headers(uid, fids=[str(fid)], roles={str(fid): "owner"}),
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 2
    assert rows[0]["created_at"] >= rows[1]["created_at"]


@pytest.mark.asyncio
async def test_diagnoses_list_rbac_other_family_returns_404(
    app_client, db_session, auth_headers
):
    # owner 가 진단 생성, 다른 가족 사용자 (B) 가 조회 시도 → 404
    uid_a, fid_a, pid = await _seed_user_family_pet(db_session)
    uid_b = uuid.uuid4()
    fid_b = uuid.uuid4()
    await db_session.execute(
        text(
            """
            INSERT INTO "user" (id, kakao_id, name, email, created_at)
            VALUES (CAST(:uid AS uuid), :kakao_id, 'B', :email, now())
            """
        ),
        {
            "uid": str(uid_b),
            "kakao_id": f"k_{uid_b.hex[:10]}",
            "email": f"{uid_b.hex[:6]}@test.local",
        },
    )
    await db_session.execute(
        text(
            """
            INSERT INTO family (id, name, owner_id, created_at)
            VALUES (CAST(:fid AS uuid), 'B-Fam', CAST(:uid AS uuid), now())
            """
        ),
        {"fid": str(fid_b), "uid": str(uid_b)},
    )
    await db_session.commit()

    resp = await app_client.get(
        f"/v1/pets/{pid}/diagnoses",
        headers=auth_headers(uid_b, fids=[str(fid_b)], roles={str(fid_b): "owner"}),
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"]["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_diagnose_image_unknown_pet_returns_404(
    app_client, db_session, auth_headers
):
    uid, fid, _ = await _seed_user_family_pet(db_session)
    storage = InMemoryStorage()
    await storage.put_bytes("uploads/image/x/y.jpg", b"x", "image/jpeg")

    resp = await app_client.post(
        "/v1/diagnose/image",
        json={
            "pet_id": str(uuid.uuid4()),  # 존재하지 않는 pet
            "image_s3_key": "uploads/image/x/y.jpg",
            "region": "skin",
        },
        headers=auth_headers(uid, fids=[str(fid)], roles={str(fid): "owner"}),
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_diagnose_requires_auth(app_client, db_session):
    _, _, pid = await _seed_user_family_pet(db_session)
    resp = await app_client.post(
        "/v1/diagnose/image",
        json={"pet_id": str(pid), "image_s3_key": "x", "region": "skin"},
    )
    assert resp.status_code == 401
