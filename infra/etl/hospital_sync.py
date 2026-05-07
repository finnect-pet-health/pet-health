"""농림축산식품부 동물병원 공공데이터 → Postgres 일일 ETL.

실행: `python -m infra.etl.hospital_sync` (cron 또는 GitHub Actions schedule).

데이터 소스 (예시):
- 공공데이터포털 동물병원 정보 API (data.go.kr)
- 또는 행정안전부 LOCALDATA 인허가 자료 (수의사업)
"""
from __future__ import annotations

import asyncio
import os
import sys

import httpx


DATA_GO_KR_API_KEY = os.environ.get("DATA_GO_KR_API_KEY", "")


async def fetch_page(client: httpx.AsyncClient, page: int) -> list[dict]:
    # TODO(W1): 실제 endpoint 와 파라미터로 교체.
    # 예: https://api.odcloud.kr/api/15098893/v1/uddi:...?page=1&perPage=1000&serviceKey=...
    return []


async def main() -> int:
    if not DATA_GO_KR_API_KEY:
        print("DATA_GO_KR_API_KEY not set", file=sys.stderr)
        return 1

    async with httpx.AsyncClient(timeout=30) as client:
        page = 1
        total = 0
        while True:
            rows = await fetch_page(client, page)
            if not rows:
                break
            # TODO: upsert into hospitals table (PostGIS POINT)
            total += len(rows)
            page += 1
        print(f"synced {total} hospital rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
