"""Seed 200 Korean dog food items into pet_food table.

Usage:
    cd apps/api
    python -m app.seeds.pet_foods            # idempotent upsert by (brand, name)
    python -m app.seeds.pet_foods --reset    # delete all source='seed' rows first

Sources: Brand official sites + Korean pet food retailers (가정 — 표기 정확도는 Day 2 lead 검수).
"""
from __future__ import annotations

import argparse
import asyncio
import logging
from typing import TypedDict
from uuid import uuid4

from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import SessionLocal
from app.models.pet_food import PetFood

logger = logging.getLogger(__name__)


class FoodEntry(TypedDict):
    brand: str
    name: str
    kcal_per_100g: float
    protein: float | None
    carbs: float | None
    fat: float | None


SEED_DATA: list[FoodEntry] = [
    # ── 로얄캐닌 (50 SKUs) ─────────────────────────────────────────────────────
    # 라이프스테이지 - 중형견
    {"brand": "로얄캐닌", "name": "어덜트 미디엄 (4kg)", "kcal_per_100g": 360.0, "protein": 25.0, "fat": 14.0, "carbs": 43.0},
    {"brand": "로얄캐닌", "name": "어덜트 미디엄 (10kg)", "kcal_per_100g": 360.0, "protein": 25.0, "fat": 14.0, "carbs": 43.0},
    {"brand": "로얄캐닌", "name": "어덜트 미디엄 (15kg)", "kcal_per_100g": 360.0, "protein": 25.0, "fat": 14.0, "carbs": 43.0},
    # 라이프스테이지 - 소형견
    {"brand": "로얄캐닌", "name": "미니 어덜트 (2kg)", "kcal_per_100g": 374.0, "protein": 26.0, "fat": 15.0, "carbs": 41.0},
    {"brand": "로얄캐닌", "name": "미니 어덜트 (4kg)", "kcal_per_100g": 374.0, "protein": 26.0, "fat": 15.0, "carbs": 41.0},
    {"brand": "로얄캐닌", "name": "미니 어덜트 (8kg)", "kcal_per_100g": 374.0, "protein": 26.0, "fat": 15.0, "carbs": 41.0},
    # 라이프스테이지 - 대형견
    {"brand": "로얄캐닌", "name": "맥시 어덜트 (4kg)", "kcal_per_100g": 355.0, "protein": 24.0, "fat": 13.0, "carbs": 44.0},
    {"brand": "로얄캐닌", "name": "맥시 어덜트 (10kg)", "kcal_per_100g": 355.0, "protein": 24.0, "fat": 13.0, "carbs": 44.0},
    {"brand": "로얄캐닌", "name": "맥시 어덜트 (15kg)", "kcal_per_100g": 355.0, "protein": 24.0, "fat": 13.0, "carbs": 44.0},
    # 시니어
    {"brand": "로얄캐닌", "name": "미니 시니어 8+ (1.5kg)", "kcal_per_100g": 349.0, "protein": 28.0, "fat": 12.0, "carbs": 40.0},
    {"brand": "로얄캐닌", "name": "미니 시니어 8+ (4kg)", "kcal_per_100g": 349.0, "protein": 28.0, "fat": 12.0, "carbs": 40.0},
    {"brand": "로얄캐닌", "name": "미디엄 시니어 7+ (3kg)", "kcal_per_100g": 340.0, "protein": 27.0, "fat": 11.0, "carbs": 41.0},
    {"brand": "로얄캐닌", "name": "미디엄 시니어 7+ (10kg)", "kcal_per_100g": 340.0, "protein": 27.0, "fat": 11.0, "carbs": 41.0},
    {"brand": "로얄캐닌", "name": "맥시 시니어 8+ (3kg)", "kcal_per_100g": 335.0, "protein": 25.0, "fat": 10.0, "carbs": 43.0},
    # 퍼피
    {"brand": "로얄캐닌", "name": "미니 퍼피 (2kg)", "kcal_per_100g": 392.0, "protein": 29.0, "fat": 17.0, "carbs": 38.0},
    {"brand": "로얄캐닌", "name": "미니 퍼피 (4kg)", "kcal_per_100g": 392.0, "protein": 29.0, "fat": 17.0, "carbs": 38.0},
    {"brand": "로얄캐닌", "name": "미디엄 퍼피 (4kg)", "kcal_per_100g": 385.0, "protein": 28.0, "fat": 16.0, "carbs": 39.0},
    {"brand": "로얄캐닌", "name": "맥시 퍼피 (4kg)", "kcal_per_100g": 378.0, "protein": 27.0, "fat": 15.0, "carbs": 40.0},
    {"brand": "로얄캐닌", "name": "맥시 퍼피 (10kg)", "kcal_per_100g": 378.0, "protein": 27.0, "fat": 15.0, "carbs": 40.0},
    # 처방식
    {"brand": "로얄캐닌", "name": "처방식 Renal (신장) (2kg)", "kcal_per_100g": 310.0, "protein": 14.0, "fat": 10.0, "carbs": 46.0},
    {"brand": "로얄캐닌", "name": "처방식 Renal (신장) (7kg)", "kcal_per_100g": 310.0, "protein": 14.0, "fat": 10.0, "carbs": 46.0},
    {"brand": "로얄캐닌", "name": "처방식 Hepatic (간) (1.5kg)", "kcal_per_100g": 320.0, "protein": 16.0, "fat": 11.0, "carbs": 47.0},
    {"brand": "로얄캐닌", "name": "처방식 Hepatic (간) (6kg)", "kcal_per_100g": 320.0, "protein": 16.0, "fat": 11.0, "carbs": 47.0},
    {"brand": "로얄캐닌", "name": "처방식 Gastrointestinal (소화기) (2kg)", "kcal_per_100g": 335.0, "protein": 22.0, "fat": 13.0, "carbs": 44.0},
    {"brand": "로얄캐닌", "name": "처방식 Gastrointestinal (소화기) (7.5kg)", "kcal_per_100g": 335.0, "protein": 22.0, "fat": 13.0, "carbs": 44.0},
    {"brand": "로얄캐닌", "name": "처방식 Urinary SO (비뇨기) (2kg)", "kcal_per_100g": 345.0, "protein": 20.0, "fat": 12.0, "carbs": 45.0},
    {"brand": "로얄캐닌", "name": "처방식 Urinary SO (비뇨기) (7.5kg)", "kcal_per_100g": 345.0, "protein": 20.0, "fat": 12.0, "carbs": 45.0},
    {"brand": "로얄캐닌", "name": "처방식 Satiety Weight Management (1.5kg)", "kcal_per_100g": 295.0, "protein": 24.0, "fat": 9.0, "carbs": 38.0},
    {"brand": "로얄캐닌", "name": "처방식 Satiety Weight Management (6kg)", "kcal_per_100g": 295.0, "protein": 24.0, "fat": 9.0, "carbs": 38.0},
    {"brand": "로얄캐닌", "name": "처방식 Dental (치아) (2kg)", "kcal_per_100g": 350.0, "protein": 23.0, "fat": 13.0, "carbs": 42.0},
    {"brand": "로얄캐닌", "name": "처방식 Dental (치아) (6kg)", "kcal_per_100g": 350.0, "protein": 23.0, "fat": 13.0, "carbs": 42.0},
    {"brand": "로얄캐닌", "name": "처방식 Hypoallergenic (저알러지) (2kg)", "kcal_per_100g": 330.0, "protein": 20.0, "fat": 12.0, "carbs": 45.0},
    {"brand": "로얄캐닌", "name": "처방식 Hypoallergenic (저알러지) (7kg)", "kcal_per_100g": 330.0, "protein": 20.0, "fat": 12.0, "carbs": 45.0},
    {"brand": "로얄캐닌", "name": "처방식 Skin Support (피부) (2kg)", "kcal_per_100g": 325.0, "protein": 22.0, "fat": 12.0, "carbs": 43.0},
    {"brand": "로얄캐닌", "name": "처방식 Skin Support (피부) (7kg)", "kcal_per_100g": 325.0, "protein": 22.0, "fat": 12.0, "carbs": 43.0},
    {"brand": "로얄캐닌", "name": "처방식 Anallergenic (면역) (3kg)", "kcal_per_100g": 318.0, "protein": 19.0, "fat": 11.0, "carbs": 46.0},
    {"brand": "로얄캐닌", "name": "처방식 Mobility C2P+ (관절) (2kg)", "kcal_per_100g": 328.0, "protein": 21.0, "fat": 12.0, "carbs": 44.0},
    {"brand": "로얄캐닌", "name": "처방식 Mobility C2P+ (관절) (7kg)", "kcal_per_100g": 328.0, "protein": 21.0, "fat": 12.0, "carbs": 44.0},
    {"brand": "로얄캐닌", "name": "처방식 Cardiac (심장) (2kg)", "kcal_per_100g": 315.0, "protein": 18.0, "fat": 10.0, "carbs": 47.0},
    {"brand": "로얄캐닌", "name": "처방식 Cardiac (심장) (7kg)", "kcal_per_100g": 315.0, "protein": 18.0, "fat": 10.0, "carbs": 47.0},
    {"brand": "로얄캐닌", "name": "처방식 Neurology (신경) (3kg)", "kcal_per_100g": 322.0, "protein": 20.0, "fat": 12.0, "carbs": 45.0},
    {"brand": "로얄캐닌", "name": "처방식 Recovery (회복식) (400g)", "kcal_per_100g": 100.0, "protein": 8.0, "fat": 6.0, "carbs": 8.0},
    {"brand": "로얄캐닌", "name": "라이트 웨이트케어 미니 (3kg)", "kcal_per_100g": 310.0, "protein": 26.0, "fat": 9.0, "carbs": 38.0},
    {"brand": "로얄캐닌", "name": "라이트 웨이트케어 미디엄 (3kg)", "kcal_per_100g": 308.0, "protein": 25.0, "fat": 9.0, "carbs": 39.0},
    {"brand": "로얄캐닌", "name": "스테릴라이즈드 (불임견) (3kg)", "kcal_per_100g": 318.0, "protein": 27.0, "fat": 10.0, "carbs": 39.0},
    {"brand": "로얄캐닌", "name": "스테릴라이즈드 (불임견) (6kg)", "kcal_per_100g": 318.0, "protein": 27.0, "fat": 10.0, "carbs": 39.0},
    {"brand": "로얄캐닌", "name": "재팬 (일본스피츠 전용) (2kg)", "kcal_per_100g": 365.0, "protein": 26.0, "fat": 14.0, "carbs": 42.0},
    {"brand": "로얄캐닌", "name": "요크셔테리어 (견종전용) (1.5kg)", "kcal_per_100g": 368.0, "protein": 27.0, "fat": 15.0, "carbs": 41.0},
    {"brand": "로얄캐닌", "name": "푸들 어덜트 (견종전용) (3kg)", "kcal_per_100g": 362.0, "protein": 26.0, "fat": 14.0, "carbs": 42.0},
    {"brand": "로얄캐닌", "name": "시츄 어덜트 (견종전용) (3kg)", "kcal_per_100g": 366.0, "protein": 25.0, "fat": 15.0, "carbs": 42.0},

    # ── 힐스 사이언스 다이어트 (40 SKUs) ──────────────────────────────────────
    # 어덜트
    {"brand": "힐스 사이언스 다이어트", "name": "어덜트 1-6 소형견 (1.8kg)", "kcal_per_100g": 368.0, "protein": 22.0, "fat": 14.0, "carbs": 44.0},
    {"brand": "힐스 사이언스 다이어트", "name": "어덜트 1-6 소형견 (5.4kg)", "kcal_per_100g": 368.0, "protein": 22.0, "fat": 14.0, "carbs": 44.0},
    {"brand": "힐스 사이언스 다이어트", "name": "어덜트 1-6 중형견 (7.5kg)", "kcal_per_100g": 362.0, "protein": 22.0, "fat": 13.5, "carbs": 44.5},
    {"brand": "힐스 사이언스 다이어트", "name": "어덜트 1-6 중형견 (15kg)", "kcal_per_100g": 362.0, "protein": 22.0, "fat": 13.5, "carbs": 44.5},
    {"brand": "힐스 사이언스 다이어트", "name": "어덜트 1-6 대형견 (12kg)", "kcal_per_100g": 358.0, "protein": 21.5, "fat": 13.0, "carbs": 45.5},
    # 어덜트 7+
    {"brand": "힐스 사이언스 다이어트", "name": "어덜트 7+ 소형견 (1.8kg)", "kcal_per_100g": 340.0, "protein": 23.0, "fat": 11.0, "carbs": 43.0},
    {"brand": "힐스 사이언스 다이어트", "name": "어덜트 7+ 소형견 (5.4kg)", "kcal_per_100g": 340.0, "protein": 23.0, "fat": 11.0, "carbs": 43.0},
    {"brand": "힐스 사이언스 다이어트", "name": "어덜트 7+ 중형견 (7.5kg)", "kcal_per_100g": 335.0, "protein": 22.5, "fat": 10.5, "carbs": 44.0},
    {"brand": "힐스 사이언스 다이어트", "name": "어덜트 7+ 대형견 (12kg)", "kcal_per_100g": 330.0, "protein": 22.0, "fat": 10.0, "carbs": 45.0},
    # 어덜트 라이트
    {"brand": "힐스 사이언스 다이어트", "name": "어덜트 라이트 소형견 (1.8kg)", "kcal_per_100g": 305.0, "protein": 24.0, "fat": 8.5, "carbs": 43.5},
    {"brand": "힐스 사이언스 다이어트", "name": "어덜트 라이트 소형견 (5.4kg)", "kcal_per_100g": 305.0, "protein": 24.0, "fat": 8.5, "carbs": 43.5},
    {"brand": "힐스 사이언스 다이어트", "name": "어덜트 라이트 중형견 (7.5kg)", "kcal_per_100g": 299.0, "protein": 23.5, "fat": 8.0, "carbs": 44.5},
    {"brand": "힐스 사이언스 다이어트", "name": "어덜트 라이트 대형견 (12kg)", "kcal_per_100g": 295.0, "protein": 23.0, "fat": 7.5, "carbs": 45.5},
    # 퍼피
    {"brand": "힐스 사이언스 다이어트", "name": "퍼피 소형견 (1.8kg)", "kcal_per_100g": 390.0, "protein": 28.0, "fat": 17.0, "carbs": 37.0},
    {"brand": "힐스 사이언스 다이어트", "name": "퍼피 소형견 (5.4kg)", "kcal_per_100g": 390.0, "protein": 28.0, "fat": 17.0, "carbs": 37.0},
    {"brand": "힐스 사이언스 다이어트", "name": "퍼피 중형견 (7.5kg)", "kcal_per_100g": 382.0, "protein": 27.5, "fat": 16.5, "carbs": 38.0},
    {"brand": "힐스 사이언스 다이어트", "name": "퍼피 대형견 (12kg)", "kcal_per_100g": 375.0, "protein": 27.0, "fat": 16.0, "carbs": 39.0},
    # 처방식
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 i/d (소화기) (1.5kg)", "kcal_per_100g": 345.0, "protein": 20.0, "fat": 13.0, "carbs": 44.0},
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 i/d (소화기) (5kg)", "kcal_per_100g": 345.0, "protein": 20.0, "fat": 13.0, "carbs": 44.0},
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 i/d Low Fat (저지방 소화기) (1.5kg)", "kcal_per_100g": 298.0, "protein": 19.0, "fat": 6.5, "carbs": 49.5},
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 k/d (신장) (1.5kg)", "kcal_per_100g": 317.0, "protein": 14.0, "fat": 12.0, "carbs": 50.0},
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 k/d (신장) (5kg)", "kcal_per_100g": 317.0, "protein": 14.0, "fat": 12.0, "carbs": 50.0},
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 c/d (비뇨기) (1.5kg)", "kcal_per_100g": 343.0, "protein": 20.5, "fat": 13.5, "carbs": 44.0},
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 c/d (비뇨기) (5kg)", "kcal_per_100g": 343.0, "protein": 20.5, "fat": 13.5, "carbs": 44.0},
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 t/d (치아) (2.3kg)", "kcal_per_100g": 320.0, "protein": 22.0, "fat": 10.5, "carbs": 44.5},
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 t/d (치아) (8.5kg)", "kcal_per_100g": 320.0, "protein": 22.0, "fat": 10.5, "carbs": 44.5},
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 w/d (당뇨/비만) (1.5kg)", "kcal_per_100g": 285.0, "protein": 21.0, "fat": 8.0, "carbs": 47.0},
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 w/d (당뇨/비만) (5kg)", "kcal_per_100g": 285.0, "protein": 21.0, "fat": 8.0, "carbs": 47.0},
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 j/d (관절) (1.5kg)", "kcal_per_100g": 355.0, "protein": 20.0, "fat": 14.0, "carbs": 43.0},
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 j/d (관절) (5kg)", "kcal_per_100g": 355.0, "protein": 20.0, "fat": 14.0, "carbs": 43.0},
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 h/d (심장) (1.5kg)", "kcal_per_100g": 338.0, "protein": 17.0, "fat": 12.5, "carbs": 47.5},
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 l/d (간) (1.5kg)", "kcal_per_100g": 322.0, "protein": 15.5, "fat": 11.5, "carbs": 50.0},
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 z/d (알러지) (1.5kg)", "kcal_per_100g": 314.0, "protein": 17.0, "fat": 10.5, "carbs": 48.5},
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 z/d (알러지) (5kg)", "kcal_per_100g": 314.0, "protein": 17.0, "fat": 10.5, "carbs": 48.5},
    {"brand": "힐스 사이언스 다이어트", "name": "퍼펙트 다이제스티온 어덜트 소형 (1.8kg)", "kcal_per_100g": 358.0, "protein": 22.5, "fat": 13.5, "carbs": 44.0},
    {"brand": "힐스 사이언스 다이어트", "name": "퍼펙트 다이제스티온 어덜트 중형 (7.5kg)", "kcal_per_100g": 354.0, "protein": 22.0, "fat": 13.0, "carbs": 45.0},
    {"brand": "힐스 사이언스 다이어트", "name": "어덜트 7+ 라이트 소형견 (1.8kg)", "kcal_per_100g": 296.0, "protein": 24.0, "fat": 7.5, "carbs": 45.5},
    {"brand": "힐스 사이언스 다이어트", "name": "센시티브 스토마크&스킨 (2.7kg)", "kcal_per_100g": 350.0, "protein": 21.0, "fat": 13.0, "carbs": 45.0},
    {"brand": "힐스 사이언스 다이어트", "name": "센시티브 스토마크&스킨 (7.5kg)", "kcal_per_100g": 350.0, "protein": 21.0, "fat": 13.0, "carbs": 45.0},
    {"brand": "힐스 사이언스 다이어트", "name": "처방식 r/d (비만관리) (1.5kg)", "kcal_per_100g": 281.0, "protein": 21.5, "fat": 7.5, "carbs": 47.0},

    # ── 오리젠 (25 SKUs) ──────────────────────────────────────────────────────
    {"brand": "오리젠", "name": "오리지널 (2kg)", "kcal_per_100g": 392.0, "protein": 38.0, "fat": 18.0, "carbs": 20.0},
    {"brand": "오리젠", "name": "오리지널 (6kg)", "kcal_per_100g": 392.0, "protein": 38.0, "fat": 18.0, "carbs": 20.0},
    {"brand": "오리젠", "name": "오리지널 (11.4kg)", "kcal_per_100g": 392.0, "protein": 38.0, "fat": 18.0, "carbs": 20.0},
    {"brand": "오리젠", "name": "시니어 (2kg)", "kcal_per_100g": 366.0, "protein": 36.0, "fat": 14.0, "carbs": 22.0},
    {"brand": "오리젠", "name": "시니어 (6kg)", "kcal_per_100g": 366.0, "protein": 36.0, "fat": 14.0, "carbs": 22.0},
    {"brand": "오리젠", "name": "시니어 (11.4kg)", "kcal_per_100g": 366.0, "protein": 36.0, "fat": 14.0, "carbs": 22.0},
    {"brand": "오리젠", "name": "6 피쉬 (2kg)", "kcal_per_100g": 385.0, "protein": 37.0, "fat": 17.0, "carbs": 21.0},
    {"brand": "오리젠", "name": "6 피쉬 (6kg)", "kcal_per_100g": 385.0, "protein": 37.0, "fat": 17.0, "carbs": 21.0},
    {"brand": "오리젠", "name": "6 피쉬 (11.4kg)", "kcal_per_100g": 385.0, "protein": 37.0, "fat": 17.0, "carbs": 21.0},
    {"brand": "오리젠", "name": "리저널 레드 (2kg)", "kcal_per_100g": 398.0, "protein": 39.0, "fat": 19.0, "carbs": 18.0},
    {"brand": "오리젠", "name": "리저널 레드 (6kg)", "kcal_per_100g": 398.0, "protein": 39.0, "fat": 19.0, "carbs": 18.0},
    {"brand": "오리젠", "name": "리저널 레드 (11.4kg)", "kcal_per_100g": 398.0, "protein": 39.0, "fat": 19.0, "carbs": 18.0},
    {"brand": "오리젠", "name": "어드벤처 (2kg)", "kcal_per_100g": 400.0, "protein": 38.0, "fat": 20.0, "carbs": 18.0},
    {"brand": "오리젠", "name": "어드벤처 (6kg)", "kcal_per_100g": 400.0, "protein": 38.0, "fat": 20.0, "carbs": 18.0},
    {"brand": "오리젠", "name": "로얄 (Royal) (2kg)", "kcal_per_100g": 410.0, "protein": 40.0, "fat": 21.0, "carbs": 17.0},
    {"brand": "오리젠", "name": "로얄 (Royal) (6kg)", "kcal_per_100g": 410.0, "protein": 40.0, "fat": 21.0, "carbs": 17.0},
    {"brand": "오리젠", "name": "로얄 (Royal) (11.4kg)", "kcal_per_100g": 410.0, "protein": 40.0, "fat": 21.0, "carbs": 17.0},
    {"brand": "오리젠", "name": "퍼피 라지 (2kg)", "kcal_per_100g": 402.0, "protein": 39.0, "fat": 19.0, "carbs": 19.0},
    {"brand": "오리젠", "name": "퍼피 라지 (6kg)", "kcal_per_100g": 402.0, "protein": 39.0, "fat": 19.0, "carbs": 19.0},
    {"brand": "오리젠", "name": "퍼피 라지 (11.4kg)", "kcal_per_100g": 402.0, "protein": 39.0, "fat": 19.0, "carbs": 19.0},
    {"brand": "오리젠", "name": "퍼피 (2kg)", "kcal_per_100g": 406.0, "protein": 40.0, "fat": 20.0, "carbs": 18.0},
    {"brand": "오리젠", "name": "퍼피 (6kg)", "kcal_per_100g": 406.0, "protein": 40.0, "fat": 20.0, "carbs": 18.0},
    {"brand": "오리젠", "name": "트라우트&살몬 미쉬 (2kg)", "kcal_per_100g": 388.0, "protein": 37.5, "fat": 18.0, "carbs": 21.0},
    {"brand": "오리젠", "name": "글레인 프리 오리지널 (2kg)", "kcal_per_100g": 395.0, "protein": 38.5, "fat": 18.5, "carbs": 20.5},
    {"brand": "오리젠", "name": "글레인 프리 오리지널 (6kg)", "kcal_per_100g": 395.0, "protein": 38.5, "fat": 18.5, "carbs": 20.5},

    # ── 아카나 (25 SKUs) ──────────────────────────────────────────────────────
    {"brand": "아카나", "name": "어덜트 스몰브리드 (2kg)", "kcal_per_100g": 378.0, "protein": 31.0, "fat": 17.0, "carbs": 28.0},
    {"brand": "아카나", "name": "어덜트 스몰브리드 (6kg)", "kcal_per_100g": 378.0, "protein": 31.0, "fat": 17.0, "carbs": 28.0},
    {"brand": "아카나", "name": "어덜트 스몰브리드 (11.4kg)", "kcal_per_100g": 378.0, "protein": 31.0, "fat": 17.0, "carbs": 28.0},
    {"brand": "아카나", "name": "어덜트 라지브리드 (2kg)", "kcal_per_100g": 372.0, "protein": 30.0, "fat": 16.5, "carbs": 29.0},
    {"brand": "아카나", "name": "어덜트 라지브리드 (6kg)", "kcal_per_100g": 372.0, "protein": 30.0, "fat": 16.5, "carbs": 29.0},
    {"brand": "아카나", "name": "어덜트 라지브리드 (11.4kg)", "kcal_per_100g": 372.0, "protein": 30.0, "fat": 16.5, "carbs": 29.0},
    {"brand": "아카나", "name": "시니어 (2kg)", "kcal_per_100g": 358.0, "protein": 30.0, "fat": 13.0, "carbs": 28.0},
    {"brand": "아카나", "name": "시니어 (6kg)", "kcal_per_100g": 358.0, "protein": 30.0, "fat": 13.0, "carbs": 28.0},
    {"brand": "아카나", "name": "시니어 (11.4kg)", "kcal_per_100g": 358.0, "protein": 30.0, "fat": 13.0, "carbs": 28.0},
    {"brand": "아카나", "name": "와일드프레리 (2kg)", "kcal_per_100g": 386.0, "protein": 33.0, "fat": 17.0, "carbs": 25.0},
    {"brand": "아카나", "name": "와일드프레리 (6kg)", "kcal_per_100g": 386.0, "protein": 33.0, "fat": 17.0, "carbs": 25.0},
    {"brand": "아카나", "name": "와일드프레리 (11.4kg)", "kcal_per_100g": 386.0, "protein": 33.0, "fat": 17.0, "carbs": 25.0},
    {"brand": "아카나", "name": "그래시랜드 (2kg)", "kcal_per_100g": 382.0, "protein": 32.0, "fat": 16.5, "carbs": 26.0},
    {"brand": "아카나", "name": "그래시랜드 (6kg)", "kcal_per_100g": 382.0, "protein": 32.0, "fat": 16.5, "carbs": 26.0},
    {"brand": "아카나", "name": "그래시랜드 (11.4kg)", "kcal_per_100g": 382.0, "protein": 32.0, "fat": 16.5, "carbs": 26.0},
    {"brand": "아카나", "name": "라이트&피트 (2kg)", "kcal_per_100g": 325.0, "protein": 33.0, "fat": 11.0, "carbs": 25.0},
    {"brand": "아카나", "name": "라이트&피트 (6kg)", "kcal_per_100g": 325.0, "protein": 33.0, "fat": 11.0, "carbs": 25.0},
    {"brand": "아카나", "name": "듀오 슈리 (2kg)", "kcal_per_100g": 370.0, "protein": 30.5, "fat": 15.0, "carbs": 30.0},
    {"brand": "아카나", "name": "듀오 슈리 (6kg)", "kcal_per_100g": 370.0, "protein": 30.5, "fat": 15.0, "carbs": 30.0},
    {"brand": "아카나", "name": "퍼스트 하비스트 포크 (2kg)", "kcal_per_100g": 384.0, "protein": 32.0, "fat": 17.0, "carbs": 26.0},
    {"brand": "아카나", "name": "퍼스트 하비스트 포크 (6kg)", "kcal_per_100g": 384.0, "protein": 32.0, "fat": 17.0, "carbs": 26.0},
    {"brand": "아카나", "name": "헤리티지 미트 (2kg)", "kcal_per_100g": 376.0, "protein": 31.0, "fat": 16.0, "carbs": 27.0},
    {"brand": "아카나", "name": "헤리티지 미트 (6kg)", "kcal_per_100g": 376.0, "protein": 31.0, "fat": 16.0, "carbs": 27.0},
    {"brand": "아카나", "name": "퍼피 스몰브리드 (2kg)", "kcal_per_100g": 390.0, "protein": 33.0, "fat": 18.0, "carbs": 26.0},
    {"brand": "아카나", "name": "퍼피 스몰브리드 (6kg)", "kcal_per_100g": 390.0, "protein": 33.0, "fat": 18.0, "carbs": 26.0},

    # ── 내추럴발란스 (15 SKUs) ────────────────────────────────────────────────
    {"brand": "내추럴발란스", "name": "LID 양고기&브라운라이스 (2.3kg)", "kcal_per_100g": 352.0, "protein": 21.0, "fat": 11.0, "carbs": 47.0},
    {"brand": "내추럴발란스", "name": "LID 양고기&브라운라이스 (5.4kg)", "kcal_per_100g": 352.0, "protein": 21.0, "fat": 11.0, "carbs": 47.0},
    {"brand": "내추럴발란스", "name": "LID 연어&브라운라이스 (2.3kg)", "kcal_per_100g": 348.0, "protein": 20.5, "fat": 10.5, "carbs": 48.0},
    {"brand": "내추럴발란스", "name": "LID 연어&브라운라이스 (5.4kg)", "kcal_per_100g": 348.0, "protein": 20.5, "fat": 10.5, "carbs": 48.0},
    {"brand": "내추럴발란스", "name": "LID 오리&감자 (2.3kg)", "kcal_per_100g": 345.0, "protein": 20.0, "fat": 10.0, "carbs": 49.0},
    {"brand": "내추럴발란스", "name": "LID 오리&감자 (5.4kg)", "kcal_per_100g": 345.0, "protein": 20.0, "fat": 10.0, "carbs": 49.0},
    {"brand": "내추럴발란스", "name": "LID 사슴&감자 (2.3kg)", "kcal_per_100g": 342.0, "protein": 20.5, "fat": 9.5, "carbs": 49.0},
    {"brand": "내추럴발란스", "name": "LID 사슴&감자 (5.4kg)", "kcal_per_100g": 342.0, "protein": 20.5, "fat": 9.5, "carbs": 49.0},
    {"brand": "내추럴발란스", "name": "LID 생선&고구마 (2.3kg)", "kcal_per_100g": 340.0, "protein": 20.0, "fat": 9.0, "carbs": 50.0},
    {"brand": "내추럴발란스", "name": "LID 생선&고구마 (5.4kg)", "kcal_per_100g": 340.0, "protein": 20.0, "fat": 9.0, "carbs": 50.0},
    {"brand": "내추럴발란스", "name": "어덜트 올 내추럴 (5.4kg)", "kcal_per_100g": 360.0, "protein": 22.0, "fat": 12.0, "carbs": 46.0},
    {"brand": "내추럴발란스", "name": "어덜트 올 내추럴 (11.3kg)", "kcal_per_100g": 360.0, "protein": 22.0, "fat": 12.0, "carbs": 46.0},
    {"brand": "내추럴발란스", "name": "시니어 (5.4kg)", "kcal_per_100g": 332.0, "protein": 23.0, "fat": 9.0, "carbs": 46.0},
    {"brand": "내추럴발란스", "name": "LID 닭고기&브라운라이스 (2.3kg)", "kcal_per_100g": 355.0, "protein": 21.5, "fat": 11.5, "carbs": 47.0},
    {"brand": "내추럴발란스", "name": "LID 닭고기&브라운라이스 (5.4kg)", "kcal_per_100g": 355.0, "protein": 21.5, "fat": 11.5, "carbs": 47.0},

    # ── 간식 브랜드 (25 SKUs) ─────────────────────────────────────────────────
    # 시저
    {"brand": "시저", "name": "시저 클래식 루프 쇠고기 (100g)", "kcal_per_100g": 80.0, "protein": 8.0, "fat": 5.0, "carbs": 2.0},
    {"brand": "시저", "name": "시저 클래식 루프 닭고기 (100g)", "kcal_per_100g": 82.0, "protein": 8.5, "fat": 5.0, "carbs": 2.0},
    {"brand": "시저", "name": "시저 셀렉션 연어&참치 (100g)", "kcal_per_100g": 78.0, "protein": 9.0, "fat": 4.5, "carbs": 1.5},
    {"brand": "시저", "name": "시저 그릴드 버라이어티 팩 (100g×7)", "kcal_per_100g": 85.0, "protein": 8.5, "fat": 5.5, "carbs": 2.5},
    {"brand": "시저", "name": "시저 홈 딜라이트 칠면조&야채 (100g)", "kcal_per_100g": 77.0, "protein": 8.0, "fat": 4.5, "carbs": 2.0},
    {"brand": "시저", "name": "시저 고메 퀴진 치킨 (100g)", "kcal_per_100g": 83.0, "protein": 8.5, "fat": 5.0, "carbs": 2.5},
    # 덴탈프레쉬
    {"brand": "덴탈프레쉬", "name": "덴탈 스틱 소형견 (440g)", "kcal_per_100g": 310.0, "protein": 15.0, "fat": 8.0, "carbs": 49.0},
    {"brand": "덴탈프레쉬", "name": "덴탈 스틱 중형견 (720g)", "kcal_per_100g": 310.0, "protein": 15.0, "fat": 8.0, "carbs": 49.0},
    {"brand": "덴탈프레쉬", "name": "덴탈 스틱 대형견 (1kg)", "kcal_per_100g": 310.0, "protein": 15.0, "fat": 8.0, "carbs": 49.0},
    {"brand": "덴탈프레쉬", "name": "치킨 덴탈 츄 (180g)", "kcal_per_100g": 295.0, "protein": 17.0, "fat": 7.5, "carbs": 46.0},
    {"brand": "덴탈프레쉬", "name": "소프트 치킨 스트립 (100g)", "kcal_per_100g": 280.0, "protein": 40.0, "fat": 5.0, "carbs": 15.0},
    # 펫썸레터
    {"brand": "펫썸레터", "name": "동결건조 닭가슴살 트릿 (50g)", "kcal_per_100g": 345.0, "protein": 70.0, "fat": 5.0, "carbs": 5.0},
    {"brand": "펫썸레터", "name": "동결건조 연어 트릿 (50g)", "kcal_per_100g": 330.0, "protein": 65.0, "fat": 8.0, "carbs": 3.0},
    {"brand": "펫썸레터", "name": "소고기 저키 (80g)", "kcal_per_100g": 320.0, "protein": 55.0, "fat": 6.0, "carbs": 10.0},
    {"brand": "펫썸레터", "name": "오리고기 저키 (80g)", "kcal_per_100g": 315.0, "protein": 53.0, "fat": 7.0, "carbs": 10.0},
    {"brand": "펫썸레터", "name": "고구마 간식 (100g)", "kcal_per_100g": 200.0, "protein": 3.0, "fat": 0.5, "carbs": 48.0},
    # 꼬빠
    {"brand": "꼬빠", "name": "꼬빠 오리지널 닭 (90g)", "kcal_per_100g": 285.0, "protein": 42.0, "fat": 6.0, "carbs": 18.0},
    {"brand": "꼬빠", "name": "꼬빠 연어 트릿 (90g)", "kcal_per_100g": 278.0, "protein": 40.0, "fat": 7.0, "carbs": 17.0},
    {"brand": "꼬빠", "name": "꼬빠 소고기 (90g)", "kcal_per_100g": 290.0, "protein": 43.0, "fat": 6.5, "carbs": 17.5},
    {"brand": "꼬빠", "name": "꼬빠 치즈 트릿 (100g)", "kcal_per_100g": 350.0, "protein": 25.0, "fat": 20.0, "carbs": 22.0},
    {"brand": "꼬빠", "name": "꼬빠 당근 비스킷 (120g)", "kcal_per_100g": 310.0, "protein": 8.0, "fat": 5.0, "carbs": 58.0},
    {"brand": "꼬빠", "name": "꼬빠 블루베리 쿠키 (100g)", "kcal_per_100g": 325.0, "protein": 7.0, "fat": 6.0, "carbs": 62.0},
    {"brand": "꼬빠", "name": "꼬빠 캥거루 저키 (70g)", "kcal_per_100g": 300.0, "protein": 48.0, "fat": 5.0, "carbs": 18.0},
    {"brand": "꼬빠", "name": "꼬빠 오리 &사과 (90g)", "kcal_per_100g": 272.0, "protein": 38.0, "fat": 6.0, "carbs": 20.0},
    {"brand": "꼬빠", "name": "꼬빠 양고기 (90g)", "kcal_per_100g": 282.0, "protein": 40.0, "fat": 7.0, "carbs": 17.0},

    # ── 일반식 / 자연식 (20 SKUs) ────────────────────────────────────────────
    {"brand": "일반식", "name": "삶은 닭가슴살 (100g)", "kcal_per_100g": 110.0, "protein": 24.0, "fat": 1.5, "carbs": 0.0},
    {"brand": "일반식", "name": "삶은 연어 (100g)", "kcal_per_100g": 130.0, "protein": 20.0, "fat": 6.0, "carbs": 0.0},
    {"brand": "일반식", "name": "두부 (100g)", "kcal_per_100g": 76.0, "protein": 8.0, "fat": 4.0, "carbs": 2.0},
    {"brand": "일반식", "name": "삶은 브로콜리 (100g)", "kcal_per_100g": 35.0, "protein": 2.5, "fat": 0.3, "carbs": 6.5},
    {"brand": "일반식", "name": "삶은 호박 (100g)", "kcal_per_100g": 30.0, "protein": 1.0, "fat": 0.1, "carbs": 7.0},
    {"brand": "일반식", "name": "삶은 당근 (100g)", "kcal_per_100g": 41.0, "protein": 0.9, "fat": 0.2, "carbs": 9.6},
    {"brand": "일반식", "name": "쪄서 익힌 고구마 (100g)", "kcal_per_100g": 86.0, "protein": 1.6, "fat": 0.1, "carbs": 20.1},
    {"brand": "일반식", "name": "사과 (씨 제거, 100g)", "kcal_per_100g": 52.0, "protein": 0.3, "fat": 0.2, "carbs": 13.8},
    {"brand": "일반식", "name": "바나나 (100g)", "kcal_per_100g": 89.0, "protein": 1.1, "fat": 0.3, "carbs": 23.0},
    {"brand": "일반식", "name": "삶은 쇠고기 (100g)", "kcal_per_100g": 143.0, "protein": 26.0, "fat": 4.0, "carbs": 0.0},
    {"brand": "일반식", "name": "삶은 계란 (흰자, 100g)", "kcal_per_100g": 52.0, "protein": 11.0, "fat": 0.2, "carbs": 0.7},
    {"brand": "일반식", "name": "플레인 요거트 무지방 (100g)", "kcal_per_100g": 59.0, "protein": 10.0, "fat": 0.4, "carbs": 3.6},
    {"brand": "일반식", "name": "삶은 감자 (100g)", "kcal_per_100g": 77.0, "protein": 2.0, "fat": 0.1, "carbs": 17.5},
    {"brand": "일반식", "name": "삶은 오리 가슴살 (100g)", "kcal_per_100g": 140.0, "protein": 23.0, "fat": 5.0, "carbs": 0.0},
    {"brand": "일반식", "name": "삶은 소간 (100g)", "kcal_per_100g": 135.0, "protein": 20.0, "fat": 4.5, "carbs": 3.5},
    {"brand": "일반식", "name": "오트밀 (조리 후, 100g)", "kcal_per_100g": 71.0, "protein": 2.5, "fat": 1.5, "carbs": 12.0},
    {"brand": "일반식", "name": "삶은 현미 (100g)", "kcal_per_100g": 112.0, "protein": 2.6, "fat": 0.9, "carbs": 23.5},
    {"brand": "일반식", "name": "블루베리 (100g)", "kcal_per_100g": 57.0, "protein": 0.7, "fat": 0.3, "carbs": 14.5},
    {"brand": "일반식", "name": "수박 (씨 제거, 100g)", "kcal_per_100g": 30.0, "protein": 0.6, "fat": 0.2, "carbs": 7.6},
    {"brand": "일반식", "name": "삶은 참치 (100g)", "kcal_per_100g": 116.0, "protein": 26.0, "fat": 1.0, "carbs": 0.0},
]


async def seed(reset: bool = False) -> int:
    async with SessionLocal() as session:
        if reset:
            await session.execute(delete(PetFood).where(PetFood.source == "seed"))
            await session.commit()
        for entry in SEED_DATA:
            stmt = (
                pg_insert(PetFood)
                .values(
                    id=uuid4(),
                    source="seed",
                    **entry,
                )
                .on_conflict_do_nothing(index_elements=["brand", "name"])
            )
            await session.execute(stmt)
        await session.commit()
    return len(SEED_DATA)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed pet food data into DB")
    parser.add_argument("--reset", action="store_true", help="Delete existing seed rows first")
    args = parser.parse_args()
    n = asyncio.run(seed(reset=args.reset))
    print(f"Seeded {n} pet foods (reset={args.reset})")


if __name__ == "__main__":
    main()
