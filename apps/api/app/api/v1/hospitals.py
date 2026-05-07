from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session

router = APIRouter()


class HospitalNearby(BaseModel):
    id: str
    mgmt_no: str
    name: str
    road_addr: str
    tel: str
    lat: float
    lng: float
    distance_m: float


@router.get("/nearby", response_model=list[HospitalNearby])
async def hospitals_nearby(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_m: int = Query(3000, ge=1, le=50000),
    limit: int = Query(3, ge=1, le=50),
    specialty: str | None = Query(None, description="W4-v2 triage 에서 사용, W3-v2 무시"),
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> list[HospitalNearby]:
    """현재 위치 (lat, lng) 기준 PostGIS `ST_DWithin` + 거리 ASC 정렬.

    `specialty` 는 W3-v2 에서 무시 (W4-v2 triage 에서 활용 예정).
    좌표 결측 row (location IS NULL) 는 ST_DWithin 자연 제외.
    """
    _ = specialty  # 라우팅 의도 보존, W4-v2 에서 사용
    stmt = text(
        """
        SELECT
            id::text AS id,
            mgmt_no,
            name,
            road_addr,
            tel,
            ST_Y(location::geometry) AS lat,
            ST_X(location::geometry) AS lng,
            ST_Distance(
                location::geography,
                ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
            ) AS distance_m
        FROM hospital
        WHERE location IS NOT NULL
          AND ST_DWithin(
              location::geography,
              ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
              :radius_m
          )
        ORDER BY distance_m ASC
        LIMIT :limit
        """
    )
    result = await session.execute(
        stmt, {"lat": lat, "lng": lng, "radius_m": radius_m, "limit": limit}
    )
    return [HospitalNearby(**dict(row)) for row in result.mappings()]
