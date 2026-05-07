from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/campaigns")
async def list_campaigns():
    raise HTTPException(501, "not_implemented")


@router.post("/redirect")
async def track_and_redirect(campaign_id: str):
    raise HTTPException(501, "not_implemented")
