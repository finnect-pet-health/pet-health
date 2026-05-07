import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

MealSource = sa.Enum("fatsecret", "custom", "seed", name="meal_source", create_type=False)
MealFoodKind = sa.Enum("사료", "간식", "일반식", "처방식", name="meal_food_kind", create_type=False)


class Meal(Base):
    __tablename__ = "meal"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    pet_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pet.id", ondelete="CASCADE"), nullable=False
    )
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    source: Mapped[str] = mapped_column(MealSource, nullable=False)
    food_id: Mapped[str | None] = mapped_column(String, nullable=True)
    food_name: Mapped[str] = mapped_column(String, nullable=False)
    qty_g: Mapped[float] = mapped_column(Float, nullable=False)
    kcal: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    food_kind: Mapped[str | None] = mapped_column(MealFoodKind, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
