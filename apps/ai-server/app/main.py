from fastapi import Depends, FastAPI, Header, HTTPException

from app.config import settings
from app.inference.disease import infer_disease
from app.inference.nutrition import infer_nutrition
from app.schemas import DiseaseInferIn, DiseaseInferOut, NutritionInferIn, NutritionInferOut

app = FastAPI(title="PetFinect Local AI Server", version="0.1.0")


def verify_secret(x_internal_secret: str = Header(...)) -> None:
    if x_internal_secret != settings.shared_secret:
        raise HTTPException(401, "invalid_internal_secret")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.post("/infer/disease", response_model=DiseaseInferOut, dependencies=[Depends(verify_secret)])
async def disease(payload: DiseaseInferIn) -> DiseaseInferOut:
    return infer_disease(payload)


@app.post(
    "/infer/nutrition", response_model=NutritionInferOut, dependencies=[Depends(verify_secret)]
)
async def nutrition(payload: NutritionInferIn) -> NutritionInferOut:
    return infer_nutrition(payload)
