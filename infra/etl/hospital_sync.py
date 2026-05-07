"""행정안전부 동물병원 OpenAPI → Postgres 일일 ETL.

실행:
    python -m infra.etl.hospital_sync           # 전체 페이지 fetch + dry-run (DB 미저장)
    python -m infra.etl.hospital_sync --pages 1 # 첫 페이지만
    python -m infra.etl.hospital_sync --upsert  # DB upsert (W3-v2 Day 5에 활성화)

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

주의:
- 좌표는 EPSG:5174 (Bessel TM 중부원점) → WGS84 변환 필요. W3-v2 에 pyproj 추가 후 구현.
- ServiceKey 는 Decoding 키 사용 (Encoding 키는 이중 인코딩 오류 발생).
- 폐업/휴업 (SALS_STTS_NM != "영업/정상") 필터링 권장.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Any

import httpx

ENDPOINT = "https://apis.data.go.kr/1741000/animal_hospitals/info"
DATA_GO_KR_API_KEY = os.environ.get("DATA_GO_KR_API_KEY", "")


async def fetch_page(
    client: httpx.AsyncClient, page: int, num_rows: int = 1000
) -> tuple[list[dict[str, Any]], int]:
    """단일 페이지 fetch. (rows, total_count) 튜플 반환.

    >>> rows, total = await fetch_page(client, page=1, num_rows=3)
    >>> total  # 전국 동물병원 수, 약 10,500
    10516
    >>> rows[0]["BPLC_NM"]
    '브라이튼안과치과동물병원'
    """
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
    """raw API row → 내부 Hospital schema. 좌표 변환은 W3-v2 Day 5 에 pyproj 추가 후 구현."""
    return {
        "mgmt_no": row.get("MNG_NO"),
        "name": row.get("BPLC_NM"),
        "road_addr": row.get("ROAD_NM_ADDR") or "",
        "lot_addr": row.get("LOTNO_ADDR") or "",
        "zip": row.get("ROAD_NM_ZIP") or "",
        "tel": row.get("TELNO") or "",
        "status": row.get("SALS_STTS_NM") or "",
        "licensed_at": row.get("LCPMT_YMD") or None,
        "tm_x": float(row["CRD_INFO_X"]) if row.get("CRD_INFO_X") else None,
        "tm_y": float(row["CRD_INFO_Y"]) if row.get("CRD_INFO_Y") else None,
        # TODO(W3-v2 D5): pyproj Transformer EPSG:5174 → EPSG:4326 → lat/lng
        "lat": None,
        "lng": None,
        "authority_code": row.get("OPN_ATMY_GRP_CD") or "",
        "raw": row,  # 디버깅용 원본 보존
    }


async def upsert_rows(rows: list[dict[str, Any]]) -> int:
    """DB upsert. W3-v2 Day 5 에 Hospital 모델 + Alembic 0005 + PostGIS 추가 후 구현."""
    raise NotImplementedError(
        "Hospital 모델·Alembic 0005·PostGIS·pyproj 가 W3-v2 Day 5 에 추가된 후 구현"
    )


async def main(max_pages: int | None = None, do_upsert: bool = False) -> int:
    if not DATA_GO_KR_API_KEY:
        print("DATA_GO_KR_API_KEY not set in environment", file=sys.stderr)
        return 1

    page = 1
    fetched = 0
    active = 0
    total = 0
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            rows, total = await fetch_page(client, page, num_rows=1000)
            if not rows:
                break
            transformed = [transform_row(r) for r in rows if is_active(r)]
            fetched += len(rows)
            active += len(transformed)
            print(
                f"page={page:3d} fetched={len(rows):4d} active={len(transformed):4d} "
                f"total_so_far={fetched}/{total}"
            )
            if do_upsert:
                await upsert_rows(transformed)
            if max_pages and page >= max_pages:
                break
            if fetched >= total:
                break
            page += 1
    print(f"\n✅ done — fetched {fetched} rows ({active} 영업중) of {total} total")
    return 0


def cli() -> int:
    parser = argparse.ArgumentParser(description="동물병원 ETL")
    parser.add_argument("--pages", type=int, default=None, help="최대 페이지 수 (테스트용)")
    parser.add_argument("--upsert", action="store_true", help="DB upsert 활성화 (W3-v2 D5+)")
    args = parser.parse_args()
    return asyncio.run(main(max_pages=args.pages, do_upsert=args.upsert))


if __name__ == "__main__":
    raise SystemExit(cli())
