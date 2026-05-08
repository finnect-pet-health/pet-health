import uuid
from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

MealSource = sa.Enum("fatsecret", "custom", "seed", name="meal_source", create_type=False)
# V10: 한글값 → 영문 키. 라벨 i18n 은 클라이언트 책임.
MealFoodKind = sa.Enum(
    "kibble", "treat", "regular", "prescription",
    name="meal_food_kind",
    create_type=False,
)


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
    # V10: Float → Numeric(10, 2) — 영양정보 정밀도.
    qty_g: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    kcal: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    protein_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    carbs_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    fat_g: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    food_kind: Mapped[str | None] = mapped_column(MealFoodKind, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=sa.func.now()
    )
