"""행정안전부 동물병원 OpenAPI → Postgres 일일 ETL.

실행:
    python -m infra.etl.hospital_sync           # 전체 페이지 fetch + dry-run (DB 미저장)
    python -m infra.etl.hospital_sync --pages 1 # 첫 페이지만
    python -m infra.etl.hospital_sync --upsert  # DB upsert (mgmt_no 기준)
    python -m infra.etl.hospital_sync --seed    # apps/api/seeds/hospitals_seoul.json
                                                #   50건 정적 시드 fallback (R6 대비)

데이터 소스:
- data.go.kr OpenAPI (검증 완료 2026-05-07)
- Endpoint: https://apis.data.go.kr/1741000/animal_hospitals/info
- Dataset: 행정안전부_동물_동물병원 조회서비스 (15154952)
- 갱신: 일일, 전국 약 10,500개

응답 필드 (한국어 매핑):
    BPLC_NM          → name (사업장명, 병원명)
    ROAD_NM_ADDR     → road_addr (도로명주소)
    LOTNO_ADDR       → lot_addr (지번주소)
    ROAD_NM_ZIP      → zip (우편번호)
    TELNO            → tel (전화번호)
    SALS_STTS_NM     → status (영업/정상, 폐업, 휴업)
    DTL_SALS_STTS_NM → status_detail (정상)
    CLSBIZ_YMD       → closed_at (폐업일자, 빈값=영업중)
    LCPMT_YMD        → licensed_at (인허가일자)
    CRD_INFO_X       → tm_x (TM 좌표 X, EPSG:5174 Bessel)
    CRD_INFO_Y       → tm_y (TM 좌표 Y, EPSG:5174)
    LCTN_AREA        → area (면적 ㎡)
    MNG_NO           → mgmt_no (관리번호, 고유 식별자, upsert key)
    OPN_ATMY_GRP_CD  → authority_code (인허가관청 코드)

좌표:
- API 의 EPSG:5174 (Bessel TM 중부원점) 좌표를 pyproj 로 EPSG:4326 (WGS84) 으로 변환.
- 좌표 결측 row (tm_x/tm_y 둘 중 하나라도 비어있음) 는 lat/lng=None 으로 둠.
  PostGIS POINT location 컬럼은 nullable, ST_DWithin 조회 시 자연 제외.

ServiceKey:
- Decoding 키 사용. Encoding 키는 이중 인코딩 오류 발생.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx

ENDPOINT = "https://apis.data.go.kr/1741000/animal_hospitals/info"
DATA_GO_KR_API_KEY = os.environ.get("DATA_GO_KR_API_KEY", "")

_REPO_ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = _REPO_ROOT / "apps" / "api" / "seeds" / "hospitals_seoul.json"

# Lazy pyproj transformer (creation cost ~10ms, reused across rows).
_TRANSFORMER: Any = None


def _get_transformer() -> Any:
    """EPSG:5174 (Bessel TM 중부원점) → EPSG:4326 (WGS84) Transformer.

    pyproj.Transformer 는 thread-safe + 내부 캐시 — 모듈 단위 1회 생성 후 재사용.
    """
    global _TRANSFORMER
    if _TRANSFORMER is None:
        from pyproj import Transformer

        _TRANSFORMER = Transformer.from_crs(5174, 4326, always_xy=True)
    return _TRANSFORMER


def tm_to_wgs84(tm_x: float, tm_y: float) -> tuple[float, float]:
    """EPSG:5174 (x, y) → (lng, lat) WGS84. always_xy=True 이므로 출력도 (lng, lat) 순."""
    transformer = _get_transformer()
    lng, lat = transformer.transform(tm_x, tm_y)
    return lng, lat


async def fetch_page(
    client: httpx.AsyncClient, page: int, num_rows: int = 1000
) -> tuple[list[dict[str, Any]], int]:
    """단일 페이지 fetch. (rows, total_count) 튜플 반환."""
    params = {
        "serviceKey": DATA_GO_KR_API_KEY,
        "pageNo": str(page),
        "numOfRows": str(num_rows),
        "type": "json",
    }
    resp = await client.get(ENDPOINT, params=params)
    resp.raise_for_status()
    data = resp.json()
    body = data.get("response", {}).get("body", {})
    items = body.get("items", {}).get("item", [])
    total = int(body.get("totalCount", 0))
    if isinstance(items, dict):
        items = [items]
    return items, total


def is_active(row: dict[str, Any]) -> bool:
    """영업 중인 병원만 통과. 폐업/휴업/취소 제외."""
    return row.get("SALS_STTS_NM") == "영업/정상" and not row.get("CLSBIZ_YMD")


def transform_row(row: dict[str, Any]) -> dict[str, Any]:
    """raw API row → 내부 Hospital schema (lng/lat 포함, EPSG:4326)."""
    tm_x = float(row["CRD_INFO_X"]) if row.get("CRD_INFO_X") else None
    tm_y = float(row["CRD_INFO_Y"]) if row.get("CRD_INFO_Y") else None
    if tm_x is not None and tm_y is not None:
        lng, lat = tm_to_wgs84(tm_x, tm_y)
    else:
        lng, lat = None, None
    return {
        "mgmt_no": row.get("MNG_NO"),
        "name": row.get("BPLC_NM"),
        "road_addr": row.get("ROAD_NM_ADDR") or "",
        "lot_addr": row.get("LOTNO_ADDR") or "",
        "zip": row.get("ROAD_NM_ZIP") or "",
        "tel": row.get("TELNO") or "",
        "status": row.get("SALS_STTS_NM") or "",
        "licensed_at": row.get("LCPMT_YMD") or None,
        "authority_code": row.get("OPN_ATMY_GRP_CD") or "",
        "tm_x": tm_x,
        "tm_y": tm_y,
        "lat": lat,
        "lng": lng,
    }


async def enrich_with_geocoding(
    rows: list[dict[str, Any]], geocoder: Any
) -> int:
    """좌표 결측 row 를 카카오 로컬 API 지오코딩으로 보정. 채워진 건수 반환.

    `geocoder` 는 `KakaoLocalClient` Protocol 구현체. mock 또는 실 클라이언트.
    `road_addr` 비어있으면 lot_addr 시도. 둘 다 비면 그대로 둠.
    """
    enriched = 0
    for r in rows:
        if r.get("lat") is not None and r.get("lng") is not None:
            continue
        addr = r.get("road_addr") or r.get("lot_addr") or ""
        if not addr:
            continue
        result = await geocoder.geocode_address(addr)
        if result is None:
            continue
        lat, lng = result
        r["lat"] = lat
        r["lng"] = lng
        enriched += 1
    return enriched


def load_static_seed(path: Path | None = None) -> list[dict[str, Any]]:
    """50건 정적 시드를 transform_row 호환 schema 로 로드 (R6 fallback).

    누락 필드는 기본값으로 채움. tm_x/tm_y 는 None 유지 (좌표는 lat/lng 직접 보유).
    """
    seed_path = path or SEED_PATH
    raw = json.loads(seed_path.read_text(encoding="utf-8"))
    out: list[dict[str, Any]] = []
    for r in raw:
        out.append(
            {
                "mgmt_no": r["mgmt_no"],
                "name": r["name"],
                "road_addr": r.get("road_addr", ""),
                "lot_addr": r.get("lot_addr", ""),
                "zip": r.get("zip", ""),
                "tel": r.get("tel", ""),
                "status": r.get("status", "영업/정상"),
                "licensed_at": r.get("licensed_at"),
                "authority_code": r.get("authority_code", ""),
                "tm_x": None,
                "tm_y": None,
                "lat": r["lat"],
                "lng": r["lng"],
            }
        )
    return out


async def upsert_rows(
    rows: list[dict[str, Any]], session: Any = None
) -> int:
    """`hospital` 테이블에 mgmt_no 기준 upsert.

    location = ST_SetSRID(ST_MakePoint(lng, lat), 4326).
    좌표 결측 row 는 location=NULL 로 적재 — 추후 카카오 지오코딩 fallback (W3-v2 D4) 에서 보정.

    `session` 은 테스트에서 주입 (savepoint 격리 보존). 미지정 시 환경 DSN 으로 자체 engine 생성.
    """
    if not rows:
        return 0

    from sqlalchemy import text

    if session is not None:
        return await _upsert_with_session(session, rows, text)

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    dsn = os.environ.get("POSTGRES_DSN") or os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://petfinect:petfinect@localhost:5434/petfinect",
    )
    engine = create_async_engine(dsn, future=True)
    sessionmaker_ = async_sessionmaker(engine, expire_on_commit=False)

    affected = 0
    async with sessionmaker_() as ssn:
        affected = await _upsert_with_session(ssn, rows, text)
        await ssn.commit()
    await engine.dispose()
    return affected


_UPSERT_SQL = """
INSERT INTO hospital (
    id, mgmt_no, name, road_addr, lot_addr, zip, tel, status,
    licensed_at, authority_code, location, updated_at
)
VALUES (
    gen_random_uuid(), :mgmt_no, :name, :road_addr, :lot_addr, :zip, :tel, :status,
    :licensed_at, :authority_code,
    CASE
        WHEN CAST(:lng AS double precision) IS NULL
          OR CAST(:lat AS double precision) IS NULL
        THEN NULL
        ELSE ST_SetSRID(
            ST_MakePoint(
                CAST(:lng AS double precision),
                CAST(:lat AS double precision)
            ),
            4326
        )
    END,
    now()
)
ON CONFLICT (mgmt_no) DO UPDATE SET
    name = EXCLUDED.name,
    road_addr = EXCLUDED.road_addr,
    lot_addr = EXCLUDED.lot_addr,
    zip = EXCLUDED.zip,
    tel = EXCLUDED.tel,
    status = EXCLUDED.status,
    licensed_at = EXCLUDED.licensed_at,
    authority_code = EXCLUDED.authority_code,
    location = EXCLUDED.location,
    updated_at = now()
"""


async def _upsert_with_session(session: Any, rows: list[dict[str, Any]], text_fn: Any) -> int:
    """주입된 session 으로 upsert. commit 은 호출자 책임 (savepoint 격리 보존)."""
    stmt = text_fn(_UPSERT_SQL)
    affected = 0
    for r in rows:
        if not r.get("mgmt_no") or not r.get("name"):
            continue
        await session.execute(stmt, r)
        affected += 1
    return affected


async def main(
    max_pages: int | None = None,
    do_upsert: bool = False,
    seed_only: bool = False,
    do_geocode: bool = False,
) -> int:
    if seed_only:
        rows = load_static_seed()
        if do_geocode:
            from app.integrations.kakao.local import get_kakao_local_client

            geocoder = get_kakao_local_client()
            await enrich_with_geocoding(rows, geocoder)
        upserted = await upsert_rows(rows) if do_upsert else 0
        print(
            f"✅ seed mode — loaded {len(rows)} rows from {SEED_PATH.name}"
            + (f", upserted {upserted}" if do_upsert else " (dry-run)")
        )
        return 0

    if not DATA_GO_KR_API_KEY:
        print("DATA_GO_KR_API_KEY not set in environment", file=sys.stderr)
        return 1

    geocoder = None
    if do_geocode:
        from app.integrations.kakao.local import get_kakao_local_client

        geocoder = get_kakao_local_client()

    page = 1
    fetched = 0
    active = 0
    geocoded = 0
    upserted = 0
    total = 0
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            rows, total = await fetch_page(client, page, num_rows=1000)
            if not rows:
                break
            transformed = [transform_row(r) for r in rows if is_active(r)]
            if geocoder is not None:
                geocoded += await enrich_with_geocoding(transformed, geocoder)
            fetched += len(rows)
            active += len(transformed)
            if do_upsert:
                upserted += await upsert_rows(transformed)
            print(
                f"page={page:3d} fetched={len(rows):4d} active={len(transformed):4d} "
                f"upserted={upserted if do_upsert else 0:4d} "
                f"geocoded={geocoded:4d} total_so_far={fetched}/{total}"
            )
            if max_pages and page >= max_pages:
                break
            if fetched >= total:
                break
            page += 1
    print(
        f"\n✅ done — fetched {fetched} rows ({active} 영업중) of {total} total"
        + (f", upserted {upserted}" if do_upsert else "")
        + (f", geocoded {geocoded}" if do_geocode else "")
    )
    return 0


def cli() -> int:
    parser = argparse.ArgumentParser(description="동물병원 ETL")
    parser.add_argument("--pages", type=int, default=None, help="최대 페이지 수 (테스트용)")
    parser.add_argument("--upsert", action="store_true", help="DB upsert 활성화")
    parser.add_argument(
        "--seed", action="store_true",
        help="data.go.kr 대신 정적 50건 시드 사용 (R6 fallback)",
    )
    parser.add_argument(
        "--geocode", action="store_true",
        help="좌표 결측 row 를 카카오 로컬 API 지오코딩으로 보정 (mock-first)",
    )
    args = parser.parse_args()
    return asyncio.run(
        main(
            max_pages=args.pages,
            do_upsert=args.upsert,
            seed_only=args.seed,
            do_geocode=args.geocode,
        )
    )


if __name__ == "__main__":
    raise SystemExit(cli())
