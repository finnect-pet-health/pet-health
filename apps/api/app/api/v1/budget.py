from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/pets/{pet_id}/budget")
async def get_budget(pet_id: str):
    raise HTTPException(501, "not_implemented")


@router.get("/finance/savings")
async def list_savings(monthly: int):
    """월 적금 권장 금액에 맞는 외부 적금 상품 추천."""
    raise HTTPException(501, "not_implemented")


@router.post("/finance/mock-enroll")
async def mock_enroll():
    """PoC 시연용 가짜 적금 가입."""
    raise HTTPException(501, "not_implemented")
