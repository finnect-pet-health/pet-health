"""X-AI-HMAC 헤더 검증.

스킴: HMAC-SHA256(shared_secret, file_bytes) → hex digest. 클라이언트(클라우드 백엔드)는
업로드 파일 raw bytes 에 대해 HMAC 을 계산하여 헤더로 전송. 서버는 동일 secret 으로
재계산 후 `hmac.compare_digest` 비교.

상태 코드:
- 헤더 누락 → 401 UNAUTHORIZED
- 서명 불일치 → 403 FORBIDDEN
"""
from __future__ import annotations

import hashlib
import hmac

from fastapi import Header, HTTPException

from app.config import settings


def compute_hmac(body: bytes, secret: str | None = None) -> str:
    key = (secret or settings.shared_secret).encode("utf-8")
    return hmac.new(key, body, hashlib.sha256).hexdigest()


def verify_hmac(body: bytes, header_value: str | None) -> None:
    if not header_value:
        raise HTTPException(401, "missing_x_ai_hmac")
    expected = compute_hmac(body)
    if not hmac.compare_digest(expected, header_value):
        raise HTTPException(403, "invalid_x_ai_hmac")


async def require_hmac_header(
    x_ai_hmac: str | None = Header(default=None, alias="X-AI-HMAC"),
) -> str:
    """헤더 존재 확인만 — 실제 본문 비교는 라우터 안에서 수행 (multipart 본문 접근 필요)."""
    if not x_ai_hmac:
        raise HTTPException(401, "missing_x_ai_hmac")
    return x_ai_hmac
