"""GET /v1/me — current user + families."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models import User
from app.security.deps import current_user
from app.services.families import list_my_families

router = APIRouter()


class FamilyOut(BaseModel):
    id: str
    name: str
    role: str
    member_count: int


class MeOut(BaseModel):
    id: str
    name: str
    profile_image: str | None
    families: list[FamilyOut]


@router.get("/me", response_model=MeOut, tags=["me"])
async def me(
    user: User = Depends(current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> MeOut:
    families = await list_my_families(session, user)
    return MeOut(
        id=str(user.id),
        name=user.name,
        profile_image=user.profile_image,
        families=[FamilyOut(**f) for f in families],
    )
