from fastapi import APIRouter

from gamehost_api.api.v1.auth import router as auth_router

router = APIRouter()
router.include_router(auth_router)


@router.get("/healthz", tags=["health"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz", tags=["health"])
async def readyz() -> dict[str, str]:
    return {"status": "ready"}


api_router = router
