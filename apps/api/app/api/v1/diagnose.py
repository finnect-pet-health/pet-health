"""POST /v1/diagnose/image, /v1/diagnose/audio + GET /v1/pets/{pet_id}/diagnoses."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.integrations.ai_server.factory import get_ai_client
from app.integrations.storage.factory import get_storage
from app.models import DiagnosisEvent, User
from app.security.deps import current_user
from app.services.diagnose import (
    diagnose_audio,
    diagnose_image,
    list_pet_diagnoses,
)

diagnose_router = APIRouter()
pet_diagnoses_router = APIRouter()


class DiagnoseImageIn(BaseModel):
    pet_id: str
    image_s3_key: str
    region: Literal["skin", "eye", "ear", "gum"] = "skin"


class DiagnoseAudioIn(BaseModel):
    pet_id: str
    audio_s3_key: str


class DiagnosisOut(BaseModel):
    id: str
    pet_id: str
    modality: str
    s3_ref: str
    top_results: list[dict]
    action: str
    confidence_top1: float
    created_at: datetime


def _serialize(evt: DiagnosisEvent) -> DiagnosisOut:
    return DiagnosisOut(
        id=str(evt.id),
        pet_id=str(evt.pet_id),
        modality=evt.modality,
        s3_ref=evt.s3_ref,
        top_results=list(evt.top_results or []),
        action=evt.action,
        confidence_top1=evt.confidence_top1,
        created_at=evt.created_at,
    )


@diagnose_router.post("/image", response_model=DiagnosisOut)
async def diagnose_image_route(
    payload: DiagnoseImageIn,
    user: User = Depends(current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> DiagnosisOut:
    storage = get_storage()
    ai = get_ai_client()
    evt = await diagnose_image(
        session,
        storage=storage,
        ai=ai,
        user=user,
        pet_id=payload.pet_id,
        s3_key=payload.image_s3_key,
        region=payload.region,
    )
    return _serialize(evt)


@diagnose_router.post("/audio", response_model=DiagnosisOut)
async def diagnose_audio_route(
    payload: DiagnoseAudioIn,
    user: User = Depends(current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> DiagnosisOut:
    storage = get_storage()
    ai = get_ai_client()
    evt = await diagnose_audio(
        session,
        storage=storage,
        ai=ai,
        user=user,
        pet_id=payload.pet_id,
        s3_key=payload.audio_s3_key,
    )
    return _serialize(evt)


@pet_diagnoses_router.get("/{pet_id}/diagnoses", response_model=list[DiagnosisOut])
async def list_diagnoses_route(
    pet_id: str,
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[DiagnosisOut]:
    rows = await list_pet_diagnoses(session, user=user, pet_id=pet_id, limit=limit)
    return [_serialize(r) for r in rows]
