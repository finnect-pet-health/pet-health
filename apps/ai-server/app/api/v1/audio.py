"""POST /infer/audio — multipart 오디오 + HMAC 검증."""
from __future__ import annotations

from fastapi import APIRouter, File, Header, UploadFile

from app.inference.factory import get_audio_inference
from app.schemas import AudioInferOut
from app.security.hmac_auth import verify_hmac

router = APIRouter()


@router.post("/infer/audio", response_model=AudioInferOut)
async def infer_audio(
    file: UploadFile = File(...),  # noqa: B008
    x_ai_hmac: str | None = Header(default=None, alias="X-AI-HMAC"),
) -> AudioInferOut:
    audio_bytes = await file.read()
    verify_hmac(audio_bytes, x_ai_hmac)
    audio = get_audio_inference()
    return await audio.predict(audio_bytes)
