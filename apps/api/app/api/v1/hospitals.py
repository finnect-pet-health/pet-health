from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("")
async def search_hospitals(lat: float, lng: float, radius_m: int = 3000):
    """위치 기반 동물병원 검색 (PostGIS ST_DWithin)."""
    raise HTTPException(501, "not_implemented")
