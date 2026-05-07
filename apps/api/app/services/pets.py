"""Pet service layer — create, list, fetch by id."""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1._errors import http_error
from app.models import FamilyMember, Pet, User


async def create_pet(
    session: AsyncSession,
    family_id: uuid.UUID,
    *,
    breed: str | None,
    dob: date | None,
    weight: float | None,
    neutered: bool,
    conditions: list[str],
) -> Pet:
    pet = Pet(
        id=uuid.uuid4(),
        family_id=family_id,
        species="dog",
        breed=breed,
        dob=dob,
        weight=weight,
        neutered=neutered,
        conditions=conditions,
    )
    session.add(pet)
    await session.commit()
    await session.refresh(pet)
    return pet


async def list_family_pets(
    session: AsyncSession, family_id: uuid.UUID
) -> list[Pet]:
    stmt = select(Pet).where(Pet.family_id == family_id).order_by(Pet.id)
    return list((await session.execute(stmt)).scalars().all())


async def get_pet_for_user(
    session: AsyncSession, pet_id: uuid.UUID, user: User
) -> Pet:
    """Return the pet only if the user is a member of its family.

    Raises 404 NOT_FOUND when pet missing OR user lacks access (policy: do not
    leak existence of pets in other families).
    """
    pet = await session.get(Pet, pet_id)
    if pet is None:
        raise http_error(404, "NOT_FOUND", "pet not found")

    membership = (
        await session.execute(
            select(FamilyMember).where(
                FamilyMember.family_id == pet.family_id,
                FamilyMember.user_id == user.id,
            )
        )
    ).scalar_one_or_none()
    if membership is None:
        raise http_error(404, "NOT_FOUND", "pet not found")
    return pet
