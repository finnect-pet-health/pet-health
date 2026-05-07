"""Diagnose service — storage fetch → AI 추론 → DiagnosisEvent 적재."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1._errors import http_error
from app.integrations.ai_server import AIServerClient
from app.integrations.storage import StorageProvider
from app.models import DiagnosisEvent, Pet, User
from app.services.pets import get_pet_for_user


async def _ensure_pet_access(
    session: AsyncSession, pet_id_str: str, user: User
) -> Pet:
    try:
        pid = uuid.UUID(pet_id_str)
    except (ValueError, TypeError) as exc:
        raise http_error(404, "NOT_FOUND", "pet not found") from exc
    return await get_pet_for_user(session, pid, user)


async def diagnose_image(
    session: AsyncSession,
    *,
    storage: StorageProvider,
    ai: AIServerClient,
    user: User,
    pet_id: str,
    s3_key: str,
    region: str,
) -> DiagnosisEvent:
    pet = await _ensure_pet_access(session, pet_id, user)
    image_bytes = await storage.fetch_bytes(s3_key)
    result = await ai.infer_vision(image_bytes, region)
    return await _persist(
        session,
        pet_id=pet.id,
        modality="image",
        s3_ref=s3_key,
        top_results=[r.model_dump() for r in result.top_results],
        action=result.action,
        confidence_top1=result.confidence_top1,
    )


async def diagnose_audio(
    session: AsyncSession,
    *,
    storage: StorageProvider,
    ai: AIServerClient,
    user: User,
    pet_id: str,
    s3_key: str,
) -> DiagnosisEvent:
    pet = await _ensure_pet_access(session, pet_id, user)
    audio_bytes = await storage.fetch_bytes(s3_key)
    result = await ai.infer_audio(audio_bytes)
    return await _persist(
        session,
        pet_id=pet.id,
        modality="audio",
        s3_ref=s3_key,
        top_results=[
            {"category": result.category, "score": result.score},
        ],
        action=result.action,
        confidence_top1=result.confidence_top1,
    )


async def list_pet_diagnoses(
    session: AsyncSession, *, user: User, pet_id: str, limit: int
) -> list[DiagnosisEvent]:
    pet = await _ensure_pet_access(session, pet_id, user)
    stmt = (
        select(DiagnosisEvent)
        .where(DiagnosisEvent.pet_id == pet.id)
        .order_by(DiagnosisEvent.created_at.desc())
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


async def _persist(
    session: AsyncSession,
    *,
    pet_id: uuid.UUID,
    modality: str,
    s3_ref: str,
    top_results: list[dict[str, Any]],
    action: str,
    confidence_top1: float,
) -> DiagnosisEvent:
    evt = DiagnosisEvent(
        pet_id=pet_id,
        modality=modality,
        s3_ref=s3_ref,
        top_results=top_results,
        action=action,
        confidence_top1=confidence_top1,
    )
    session.add(evt)
    await session.commit()
    await session.refresh(evt)
    return evt
