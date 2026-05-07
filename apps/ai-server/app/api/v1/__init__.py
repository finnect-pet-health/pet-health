from fastapi import APIRouter

from app.api.v1 import audio as audio_route
from app.api.v1 import vision as vision_route

router = APIRouter()
router.include_router(vision_route.router, tags=["infer"])
router.include_router(audio_route.router, tags=["infer"])
