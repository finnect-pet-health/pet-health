"""W2 자산 (Stage 1 disease + nutrition) smoke — 80% coverage 가드 통과용.

W3-v2 에선 deprecated 경로 (Phase 2 부활 검토 대상). 입출력 schema 와 룰 기반 동작
검증만.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.inference.disease import infer_disease
from app.inference.nutrition import infer_nutrition
from app.schemas import (
    DiseaseInferIn,
    HealthSnapshotIn,
    MealIn,
    NutritionInferIn,
    PetMeta,
)

_PET = PetMeta(breed="mixed", age_year=4.0, weight=8.0, neutered=True, conditions=[])


def _snap(days_ago: int, activity: float, hr: float = 100.0) -> HealthSnapshotIn:
    ts = datetime.now(UTC) - timedelta(days=days_ago)
    return HealthSnapshotIn(
        ts=ts,
        activity_min=activity,
        hr_avg=hr,
        sleep_state="deep",
        weight=8.0,
    )


def test_disease_observe_when_baseline_normal():
    payload = DiseaseInferIn(
        pet_id="p-1",
        snapshots=[_snap(d, 60.0) for d in range(14, 0, -1)],
        pet_meta=_PET,
    )
    out = infer_disease(payload)
    assert out.action == "observe"
    assert out.anomaly_score < 0.4


def test_disease_immediate_when_severe_anomaly():
    # 11일 baseline 60 활동 → 마지막 3일 5분 활동 (-90%) → high anomaly score.
    snaps = [_snap(d, 60.0) for d in range(14, 3, -1)] + [
        _snap(d, 5.0, hr=180.0) for d in range(3, 0, -1)
    ]
    payload = DiseaseInferIn(pet_id="p-2", snapshots=snaps, pet_meta=_PET)
    out = infer_disease(payload)
    assert out.action in {"immediate", "schedule"}
    assert out.anomaly_score > 0.4


def test_disease_handles_empty_snapshots():
    payload = DiseaseInferIn(pet_id="p-3", snapshots=[], pet_meta=_PET)
    out = infer_disease(payload)
    assert out.anomaly_score == 0.0
    assert out.action == "observe"


def test_nutrition_der_for_neutered_adult():
    payload = NutritionInferIn(
        pet_meta=_PET,
        meals_today=[
            MealIn(food="사료", kcal=200.0, ts=datetime.now(UTC)),
            MealIn(food="간식", kcal=50.0, ts=datetime.now(UTC)),
        ],
    )
    out = infer_nutrition(payload)
    # RER = 70 * 8^0.75 ≈ 333, neutered adult factor 1.6 → DER ≈ 533
    assert 500 < out.der_kcal < 600
    assert out.consumed_kcal == 250.0
    assert out.deficit > 200  # 권장 미달


def test_nutrition_growth_phase_factor_higher():
    puppy = PetMeta(breed="m", age_year=0.5, weight=4.0, neutered=False)
    senior = PetMeta(breed="m", age_year=10.0, weight=4.0, neutered=False)
    common: list[MealIn] = []
    p_out = infer_nutrition(NutritionInferIn(pet_meta=puppy, meals_today=common))
    s_out = infer_nutrition(NutritionInferIn(pet_meta=senior, meals_today=common))
    # 강아지(2.0) > 시니어(1.4) → 동일 weight 에서 DER 더 큼.
    assert p_out.der_kcal > s_out.der_kcal


def test_nutrition_overeating_note():
    payload = NutritionInferIn(
        pet_meta=_PET,
        meals_today=[MealIn(food="사료", kcal=2000.0, ts=datetime.now(UTC))],
    )
    out = infer_nutrition(payload)
    assert out.deficit < -100
    assert any("많이 먹었" in n for n in out.notes)


@pytest.mark.asyncio
async def test_legacy_disease_route_with_internal_secret(client):
    payload = {
        "pet_id": "p-x",
        "snapshots": [
            {
                "ts": (datetime.now(UTC) - timedelta(days=d)).isoformat(),
                "activity_min": 60.0,
                "hr_avg": 100.0,
                "sleep_state": "deep",
                "weight": 8.0,
            }
            for d in range(14, 0, -1)
        ],
        "pet_meta": _PET.model_dump(),
    }
    resp = await client.post(
        "/infer/disease",
        json=payload,
        headers={"X-Internal-Secret": "dev-shared-secret"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["action"] in {"immediate", "schedule", "observe"}


@pytest.mark.asyncio
async def test_legacy_disease_route_rejects_bad_secret(client):
    resp = await client.post(
        "/infer/disease",
        json={"pet_id": "x", "snapshots": [], "pet_meta": _PET.model_dump()},
        headers={"X-Internal-Secret": "wrong"},
    )
    assert resp.status_code == 401
