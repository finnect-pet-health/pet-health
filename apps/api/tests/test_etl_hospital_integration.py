"""W3-v2 AC11: 정적 시드 → DB upsert → ST_DWithin count(location IS NOT NULL) ≥ 50.

infra/etl/hospital_sync.py 의 load_static_seed + upsert_rows 를 db_session
fixture (savepoint 격리) 위에서 실행해 회귀 검출.
"""
from __future__ import annotations

import sys
from pathlib import Path

# infra/ 모듈을 apps/api pytest 컨텍스트에서 import 가능하도록 repo root 추가.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pytest  # noqa: E402
from infra.etl.hospital_sync import (  # noqa: E402
    enrich_with_geocoding,
    load_static_seed,
    upsert_rows,
)
from sqlalchemy import text  # noqa: E402


@pytest.mark.asyncio
async def test_seed_upsert_yields_50_rows_with_location(db_session):
    rows = load_static_seed()
    affected = await upsert_rows(rows, session=db_session)
    assert affected == 50

    located = (
        await db_session.execute(
            text("SELECT count(*) FROM hospital WHERE location IS NOT NULL")
        )
    ).scalar()
    assert located >= 50


@pytest.mark.asyncio
async def test_seed_upsert_supports_st_dwithin_seoul_city_hall(db_session):
    rows = load_static_seed()
    await upsert_rows(rows, session=db_session)

    # Seoul City Hall (37.5665, 126.9780). 25개 자치구 시드가 박스 안 → 5km 내 다수 hit.
    nearby = (
        await db_session.execute(
            text(
                """
                SELECT count(*) FROM hospital
                WHERE location IS NOT NULL
                  AND ST_DWithin(
                      location::geography,
                      ST_SetSRID(ST_MakePoint(126.9780, 37.5665), 4326)::geography,
                      5000
                  )
                """
            )
        )
    ).scalar()
    assert nearby >= 5  # 종로/중구/마포/용산/서대문 등 cluster


@pytest.mark.asyncio
async def test_geocoding_fallback_after_seed_with_missing_rows(db_session):
    """좌표 결측 row 가 섞인 시나리오: enrich_with_geocoding → upsert 시 location 채워짐."""
    rows = load_static_seed()
    # 인공적으로 첫 row 좌표 제거 + lot_addr 없는 채로 road_addr 만 둠 → mock 카카오로 보정.
    rows[0]["lat"] = None
    rows[0]["lng"] = None

    from app.integrations.kakao.local import MockKakaoLocalClient

    geocoder = MockKakaoLocalClient()
    enriched = await enrich_with_geocoding(rows, geocoder)
    assert enriched == 1
    assert rows[0]["lat"] is not None and rows[0]["lng"] is not None

    affected = await upsert_rows(rows, session=db_session)
    assert affected == 50

    located = (
        await db_session.execute(
            text("SELECT count(*) FROM hospital WHERE location IS NOT NULL")
        )
    ).scalar()
    assert located == 50  # 모든 row 위치 적재


@pytest.mark.asyncio
async def test_etl_with_geocode_fallback(db_session):
    """AC11 검증 핸들 (W3-v2 plan §2 AC11 검증 명령과 동일 의도).

    seed → 일부 좌표 결측 → kakao mock 지오코딩 → upsert →
    `count(*) FROM hospital WHERE location IS NOT NULL` ≥ 50.
    """
    rows = load_static_seed()
    # 마지막 5건 좌표 의도적 결측.
    for r in rows[-5:]:
        r["lat"] = None
        r["lng"] = None

    from app.integrations.kakao.local import MockKakaoLocalClient

    enriched = await enrich_with_geocoding(rows, MockKakaoLocalClient())
    assert enriched == 5

    affected = await upsert_rows(rows, session=db_session)
    assert affected == 50

    located = (
        await db_session.execute(
            text("SELECT count(*) FROM hospital WHERE location IS NOT NULL")
        )
    ).scalar()
    assert located >= 50
