from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthSnapshotIn(BaseModel):
    ts: datetime
    activity_min: float
    hr_avg: float | None = None
    hr_min: float | None = None
    hr_max: float | None = None
    sleep_state: Literal["awake", "light", "deep"] | None = None
    weight: float | None = None
    quality: float = 1.0


class PetMeta(BaseModel):
    breed: str
    age_year: float
    weight: float
    neutered: bool = False
    conditions: list[str] = Field(default_factory=list)


class DiseaseInferIn(BaseModel):
    pet_id: str
    snapshots: list[HealthSnapshotIn]
    pet_meta: PetMeta


class DiseaseCandidate(BaseModel):
    label: str
    prob: float
    confidence_band: tuple[float, float]


class DiseaseInferOut(BaseModel):
    anomaly_score: float
    feature_contributions: dict[str, float]
    top_diseases: list[DiseaseCandidate]
    action: Literal["immediate", "schedule", "observe"]


class MealIn(BaseModel):
    food: str
    kcal: float
    ts: datetime


class NutritionInferIn(BaseModel):
    pet_meta: PetMeta
    meals_today: list[MealIn]


class NutritionInferOut(BaseModel):
    rer_kcal: float
    der_kcal: float  # 권장 일일 섭취 칼로리
    consumed_kcal: float
    deficit: float
    notes: list[str]
