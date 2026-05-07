import uuid
from datetime import date

import sqlalchemy as sa
from sqlalchemy import Boolean, Date, Float, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

PetSpecies = sa.Enum("dog", "cat", "other", name="pet_species")


class Pet(Base):
    __tablename__ = "pet"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    family_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("family.id", ondelete="CASCADE"), nullable=False
    )
    species: Mapped[str] = mapped_column(PetSpecies, nullable=False, server_default="dog")
    breed: Mapped[str | None] = mapped_column(sa.String, nullable=True)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    neutered: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    conditions: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")
