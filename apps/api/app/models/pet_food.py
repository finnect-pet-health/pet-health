import uuid
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import DateTime, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

PetFoodSource = sa.Enum("seed", "fatsecret", "user", name="pet_food_source", create_type=False)


class PetFood(Base):
    __tablename__ = "pet_food"
    __table_args__ = (UniqueConstraint("brand", "name", name="uq_pet_food_brand_name"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    brand: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    # V10: Float → Numeric(10, 2). protein/carbs/fat 컬럼명에 단위(per 100g) 명시.
    kcal_per_100g: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    protein_per_100g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    carbs_per_100g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    fat_per_100g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    source: Mapped[str] = mapped_column(
        PetFoodSource, nullable=False, server_default="seed"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
