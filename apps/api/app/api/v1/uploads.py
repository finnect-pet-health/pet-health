"""POST /v1/uploads/presign — modality 별 presigned PUT URL 발급.

AC10: content-type 화이트리스트, TTL 10분, key 는 `uploads/{modality}/{user_id}/{uuid}.{ext}`.
또한 dev/mock 환경 (`mock-s3://` URL) 흐름을 위한 `POST /v1/uploads/raw?key=...` 라우트를 제공.
"""
from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Header, Query, Request
from pydantic import BaseModel

from app.api.v1._errors import http_error
from app.config import settings
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


class RawUploadOk(BaseModel):
    key: str
    bytes: int


@router.post("/raw", response_model=RawUploadOk)
async def raw_upload(
    request: Request,
    key: str = Query(..., min_length=1, max_length=512),
    content_type: str = Header(..., alias="Content-Type"),
    _user: User = Depends(current_user),  # noqa: B008
) -> RawUploadOk:
    """Dev-only mock storage 직업로드 — `mock-s3://` URL 으로부터의 forward 대상.

    실 운영(`app_env=='production'`)에서는 404 — presigned URL 흐름만 사용.
    content-type 화이트리스트 적용 (image/audio 양쪽 통합).
    """
    if settings.app_env == "production":
        raise http_error(404, "NOT_FOUND", "raw upload disabled in production")

    if content_type not in (allowed_for("image") | allowed_for("audio")):
        raise http_error(400, "INVALID_CONTENT_TYPE", f"'{content_type}' not allowed")

    body = await request.body()
    if not body:
        raise http_error(400, "EMPTY_BODY", "empty upload body")

    storage = get_storage()
    await storage.put_bytes(key, body, content_type)
    return RawUploadOk(key=key, bytes=len(body))
