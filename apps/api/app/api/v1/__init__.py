from fastapi import APIRouter

from app.api.v1 import (
    auth,
    budget,
    diagnose,
    donations,
    families,
    health,
    hospitals,
    me,
    pets,
    uploads,
)

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(me.router, tags=["me"])
router.include_router(families.router, prefix="/families", tags=["families"])
router.include_router(pets.family_pets_router, prefix="/families", tags=["pets"])
router.include_router(pets.router, prefix="/pets", tags=["pets"])
router.include_router(diagnose.pet_diagnoses_router, prefix="/pets", tags=["diagnose"])
router.include_router(health.router, tags=["health"])
router.include_router(hospitals.router, prefix="/hospitals", tags=["hospitals"])
router.include_router(budget.router, tags=["budget"])
router.include_router(donations.router, prefix="/donations", tags=["donations"])
router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])
router.include_router(diagnose.diagnose_router, prefix="/diagnose", tags=["diagnose"])
