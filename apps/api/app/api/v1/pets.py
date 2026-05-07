"""POST /v1/families/{family_id}/pets, GET /v1/families/{family_id}/pets, GET /v1/pets/{pet_id}."""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1._errors import http_error
from app.database import get_session
from app.models import FamilyMember, Pet, User
from app.security.deps import current_user, require_family
from app.services.pets import create_pet, get_pet_for_user, list_family_pets

# Two routers: one nested under /families (for family-scoped routes), one
# mounted at /pets (for direct pet lookup). Both are exported via __init__.
family_pets_router = APIRouter()
router = APIRouter()


class PetCreateIn(BaseModel):
    breed: str | None = Field(default=None, max_length=50)
    dob: date | None = None
    weight: float | None = Field(default=None, gt=0)
    neutered: bool = False
    conditions: list[str] = Field(default_factory=list)

    @field_validator("conditions")
    @classmethod
    def _conditions_are_strings(cls, v: list[str]) -> list[str]:
        if not all(isinstance(item, str) for item in v):
            raise ValueError("conditions must be a list of strings")
        return v


class PetOut(BaseModel):
    id: str
    family_id: str
    species: str
    breed: str | None
    dob: date | None
    weight: float | None
    neutered: bool
    conditions: list[str]


def _serialize(pet: Pet) -> PetOut:
    return PetOut(
        id=str(pet.id),
        family_id=str(pet.family_id),
        species=pet.species,
        breed=pet.breed,
        dob=pet.dob,
        weight=pet.weight,
        neutered=pet.neutered,
        conditions=list(pet.conditions or []),
    )


@family_pets_router.post("/{family_id}/pets", response_model=PetOut)
async def create_family_pet(
    family_id: str,
    payload: PetCreateIn,
    member: FamilyMember = Depends(require_family("owner")),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> PetOut:
    pet = await create_pet(
        session,
        member.family_id,
        breed=payload.breed,
        dob=payload.dob,
        weight=payload.weight,
        neutered=payload.neutered,
        conditions=payload.conditions,
    )
    return _serialize(pet)


@family_pets_router.get("/{family_id}/pets", response_model=list[PetOut])
async def list_family_pets_route(
    family_id: str,
    member: FamilyMember = Depends(require_family("member")),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[PetOut]:
    pets = await list_family_pets(session, member.family_id)
    return [_serialize(p) for p in pets]


@router.get("/{pet_id}", response_model=PetOut)
async def get_pet(
    pet_id: str,
    user: User = Depends(current_user),  # noqa: B008
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> PetOut:
    try:
        pid = uuid.UUID(pet_id)
    except (ValueError, TypeError) as exc:
        raise http_error(404, "NOT_FOUND", "pet not found") from exc
    pet = await get_pet_for_user(session, pid, user)
    return _serialize(pet)
