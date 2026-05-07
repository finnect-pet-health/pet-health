"""W3-v2 head-start: DiagnosisEvent ORM smoke (Alembic 0004).

라우터 (`/v1/diagnose/*`) 는 W3-v2 D3 에 추가 — 본 테스트는 모델 + enum 적용 확인만.
"""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DiagnosisEvent


async def _seed_pet(db_session: AsyncSession) -> uuid.UUID:
    fid = uuid.uuid4()
    pid = uuid.uuid4()
    uid = uuid.uuid4()
    await db_session.execute(
        text(
            """
            INSERT INTO "user" (id, kakao_id, name, email, created_at)
            VALUES (CAST(:uid AS uuid), :kakao_id, :name, :email, now())
            """
        ),
        {
            "uid": str(uid),
            "kakao_id": f"k_{uid.hex[:10]}",
            "name": "owner",
            "email": f"{uid.hex[:6]}@test.local",
        },
    )
    await db_session.execute(
        text(
            """
            INSERT INTO family (id, name, owner_id, created_at)
            VALUES (CAST(:fid AS uuid), :name, CAST(:uid AS uuid), now())
            """
        ),
        {"fid": str(fid), "name": "F", "uid": str(uid)},
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
    return pid


@pytest.mark.asyncio
async def test_diagnosis_event_insert_image(db_session: AsyncSession):
    pid = await _seed_pet(db_session)
    evt = DiagnosisEvent(
        pet_id=pid,
        modality="image",
        s3_ref="uploads/image/u/x.jpg",
        top_results=[{"label": "skin_redness", "score": 0.82}],
        action="schedule",
        confidence_top1=0.82,
    )
    db_session.add(evt)
    await db_session.commit()

    fetched = (
        await db_session.execute(
            select(DiagnosisEvent).where(DiagnosisEvent.pet_id == pid)
        )
    ).scalar_one()
    assert fetched.modality == "image"
    assert fetched.action == "schedule"
    assert fetched.top_results[0]["label"] == "skin_redness"
    assert fetched.confidence_top1 == pytest.approx(0.82)
    assert fetched.created_at is not None


@pytest.mark.asyncio
async def test_diagnosis_event_modality_audio(db_session: AsyncSession):
    pid = await _seed_pet(db_session)
    evt = DiagnosisEvent(
        pet_id=pid,
        modality="audio",
        s3_ref="uploads/audio/u/y.m4a",
        top_results=[{"category": "기침", "score": 0.71}],
        action="observe",
        confidence_top1=0.71,
    )
    db_session.add(evt)
    await db_session.commit()
    assert evt.id is not None
