"""POST /infer/vision — multipart 이미지 + region 폼 + HMAC 검증.

흐름:
1. UploadFile.read() 로 raw bytes 확보 (HMAC 입력)
2. X-AI-HMAC 헤더와 비교 (compute_hmac(file_bytes))
3. MockVision (또는 실 구현) 으로 추론
"""
from __future__ import annotations

from fastapi import APIRouter, File, Form, Header, UploadFile

from app.inference.factory import get_vision_inference
from app.schemas import RegionEnum, VisionInferOut
from app.security.hmac_auth import verify_hmac

router = APIRouter()


@router.post("/infer/vision", response_model=VisionInferOut)
async def infer_vision(
    file: UploadFile = File(...),  # noqa: B008
    region: RegionEnum = Form("skin"),
    x_ai_hmac: str | None = Header(default=None, alias="X-AI-HMAC"),
) -> VisionInferOut:
    image_bytes = await file.read()
    verify_hmac(image_bytes, x_ai_hmac)
    vision = get_vision_inference()
    return await vision.predict(image_bytes, region)
