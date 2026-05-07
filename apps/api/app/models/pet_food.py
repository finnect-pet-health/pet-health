import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, Float, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

PetFoodSource = sa.Enum("seed", "fatsecret", "user", name="pet_food_source", create_type=False)


class PetFood(Base):
    __tablename__ = "pet_food"
    __table_args__ = (UniqueConstraint("brand", "name", name="uq_pet_food_brand_name"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    brand: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    kcal_per_100g: Mapped[float] = mapped_column(Float, nullable=False)
    protein: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(
        PetFoodSource, nullable=False, server_default="seed"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
