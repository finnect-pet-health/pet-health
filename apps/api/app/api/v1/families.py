"""POST/GET /v1/families, invite, join, members."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1._errors import http_error
from app.database import get_session
from app.models import Family, FamilyMember, User
from app.security.deps import current_user, require_family
from app.services.families import (
    create_family_with_owner,
    issue_invite,
    join_by_code,
    list_members,
    list_my_families,
)

router = APIRouter()


class FamilyCreateIn(BaseModel):
    name: str


class FamilyDetailOut(BaseModel):
    id: str
    name: str


class CreateFamilyOut(BaseModel):
    family: FamilyDetailOut
    member: dict


class FamilyListItemOut(BaseModel):
    id: str
    name: str
    role: str
    member_count: int


class InviteIn(BaseModel):
    ttl_hours: int = Field(default=72, ge=1, le=24 * 30)


class InviteOut(BaseModel):
    invite_code: str
    expires_at: datetime


class JoinIn(BaseModel):
    invite_code: str


class JoinOut(BaseModel):
    family: FamilyDetailOut
    role: str


class MemberOut(BaseModel):
    user_id: str
    name: str
    role: str
    joined_at: str


@router.post("", response_model=CreateFamilyOut)
async def create_family(
    payload: FamilyCreateIn,
    user: User = Depends(current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> CreateFamilyOut:
    fam = await create_family_with_owner(session, user, payload.name)
    return CreateFamilyOut(
        family=FamilyDetailOut(id=str(fam.id), name=fam.name),
        member={"role": "owner"},
    )


@router.get("", response_model=list[FamilyListItemOut])
async def list_families(
    user: User = Depends(current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[FamilyListItemOut]:
    rows = await list_my_families(session, user)
    return [FamilyListItemOut(**r) for r in rows]


@router.post("/{family_id}/invite", response_model=InviteOut)
async def issue_family_invite(
    family_id: str,
    payload: InviteIn | None = None,
    member: FamilyMember = Depends(require_family("owner")),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> InviteOut:
    fam = await session.get(Family, member.family_id)
    if fam is None:
        raise http_error(404, "NOT_FOUND", "family not found")
    ttl_hours = (payload.ttl_hours if payload else 72)
    code, expires_at = await issue_invite(session, fam, ttl_hours)
    return InviteOut(invite_code=code, expires_at=expires_at)


@router.post("/join", response_model=JoinOut)
async def join_family(
    payload: JoinIn,
    user: User = Depends(current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> JoinOut:
    fam = await join_by_code(session, user, payload.invite_code)
    return JoinOut(family=FamilyDetailOut(id=str(fam.id), name=fam.name), role="member")


@router.get("/{family_id}/members", response_model=list[MemberOut])
async def get_members(
    family_id: str,
    member: FamilyMember = Depends(require_family("member")),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[MemberOut]:
    fam = await session.get(Family, member.family_id)
    if fam is None:
        raise http_error(404, "NOT_FOUND", "family not found")
    rows = await list_members(session, fam)
    return [MemberOut(**r) for r in rows]
