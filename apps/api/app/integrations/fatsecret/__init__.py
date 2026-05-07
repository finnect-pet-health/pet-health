"""FatSecret food data integration.

Provides a swap-ready food search API. Mock for dev/test, Real for staging/prod.
"""
from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel


class FoodItem(BaseModel):
    food_id: str
    name: str
    brand: str | None = None
    kcal_per_100g: float
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    locale: str = "ko_KR"


class FoodProvider(Protocol):
    async def search(self, q: str, locale: str = "ko_KR") -> list[FoodItem]: ...
    async def get(self, food_id: str) -> FoodItem | None: ...
