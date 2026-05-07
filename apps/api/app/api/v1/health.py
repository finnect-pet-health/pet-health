from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/pets/{pet_id}/health/snapshots")
async def list_snapshots(pet_id: str):
    raise HTTPException(501, "not_implemented")


@router.post("/pets/{pet_id}/health/sync", status_code=202)
async def sync_health(pet_id: str, force: bool = False):
    """케어테일 폴링 강제 트리거. RQ 워커에 enqueue."""
    raise HTTPException(501, "not_implemented")


@router.get("/pets/{pet_id}/diagnoses")
async def list_diagnoses(pet_id: str, limit: int = 20):
    raise HTTPException(501, "not_implemented")
