from fastapi import APIRouter

from gamehost_api.api.v1.auth import router as auth_router
from gamehost_api.api.v1.nodes import router as nodes_router
from gamehost_api.api.v1.servers import router as servers_router
from gamehost_api.api.v1.tasks import router as tasks_router
from gamehost_api.api.v1.templates import router as templates_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(templates_router)
router.include_router(nodes_router)
router.include_router(servers_router)
router.include_router(tasks_router)


@router.get("/healthz", tags=["health"])
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz", tags=["health"])
async def readyz() -> dict[str, str]:
    return {"status": "ready"}


api_router = router
