"""Standard error envelope helper (spec auth-and-family.md § 4.3)."""
from __future__ import annotations

from fastapi import HTTPException


def http_error(status: int, code: str, message: str) -> HTTPException:
    """Return an HTTPException whose body is ``{"error": {"code", "message"}}``."""
    return HTTPException(status_code=status, detail={"error": {"code": code, "message": message}})
