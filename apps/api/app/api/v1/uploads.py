"""POST /v1/uploads/presign — modality 별 presigned PUT URL 발급.

AC10: content-type 화이트리스트, TTL 10분, key 는 `uploads/{modality}/{user_id}/{uuid}.{ext}`.
"""
from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.v1._errors import http_error
from app.integrations.storage import (
    Modality,
    UnsupportedContentTypeError,
    allowed_for,
)
from app.integrations.storage.factory import get_storage
from app.models import User
from app.security.deps import current_user

router = APIRouter()

_PRESIGN_TTL_S = 600

_EXT_BY_TYPE: dict[str, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "audio/wav": "wav",
    "audio/mpeg": "mp3",
    "audio/m4a": "m4a",
    "audio/mp4": "m4a",
}


class PresignRequest(BaseModel):
    modality: Literal["image", "audio"]
    content_type: str


class PresignResponse(BaseModel):
    key: str
    url: str
    ttl_s: int


def _validate_content_type(modality: Modality, content_type: str) -> None:
    if content_type not in allowed_for(modality):
        raise UnsupportedContentTypeError(
            f"content_type '{content_type}' not allowed for modality '{modality}'"
        )


def _build_key(modality: Modality, user_id: uuid.UUID, content_type: str) -> str:
    ext = _EXT_BY_TYPE[content_type]
    return f"uploads/{modality}/{user_id}/{uuid.uuid4()}.{ext}"


@router.post("/presign", response_model=PresignResponse)
async def presign_upload(
    payload: PresignRequest,
    user: User = Depends(current_user),  # noqa: B008
) -> PresignResponse:
    try:
        _validate_content_type(payload.modality, payload.content_type)
    except UnsupportedContentTypeError as exc:
        raise http_error(400, "INVALID_CONTENT_TYPE", str(exc)) from exc

    key = _build_key(payload.modality, user.id, payload.content_type)
    storage = get_storage()
    url = await storage.presign_put(key, payload.content_type, ttl_s=_PRESIGN_TTL_S)
    return PresignResponse(key=key, url=url, ttl_s=_PRESIGN_TTL_S)
