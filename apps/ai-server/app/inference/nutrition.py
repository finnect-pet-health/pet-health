"""일일 권장 칼로리(DER) 산출. RER × 활동계수 + 중성화/나이 보정."""
from __future__ import annotations

from app.schemas import NutritionInferIn, NutritionInferOut


def _rer(weight_kg: float) -> float:
    """Resting Energy Requirement = 70 * BW(kg)^0.75."""
    return 70.0 * (weight_kg**0.75)


def _activity_factor(age_year: float, neutered: bool) -> float:
    if age_year < 1:
        return 2.0  # 강아지 (성장기)
    if age_year >= 7:
        return 1.4  # 시니어
    return 1.6 if neutered else 1.8


def infer_nutrition(payload: NutritionInferIn) -> NutritionInferOut:
    rer = _rer(payload.pet_meta.weight)
    factor = _activity_factor(payload.pet_meta.age_year, payload.pet_meta.neutered)
    der = rer * factor
    consumed = sum(m.kcal for m in payload.meals_today)
    deficit = der - consumed

    notes: list[str] = []
    if deficit < -100:
        notes.append("권장량보다 많이 먹었어요. 활동량을 늘려보세요.")
    elif deficit > 100:
        notes.append("권장량보다 적게 먹었어요. 식사를 챙겨주세요.")

    return NutritionInferOut(
        rer_kcal=round(rer, 1),
        der_kcal=round(der, 1),
        consumed_kcal=round(consumed, 1),
        deficit=round(deficit, 1),
        notes=notes,
    )
