from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from gamehost_shared.schemas import ProblemDetail
from prometheus_fastapi_instrumentator import Instrumentator

from gamehost_api.api.v1.router import api_router
from gamehost_api.core.config import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    get_settings()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="GameHost API",
        version="0.1.0",
        lifespan=lifespan,
        openapi_url="/api/v1/openapi.json",
    )
    app.include_router(api_router, prefix="/api/v1")

    @app.exception_handler(HTTPException)
    async def problem_detail_handler(_request: object, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else None
        body = ProblemDetail(
            title=exc.detail or "HTTP error",
            status=exc.status_code,
            detail=detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=body.model_dump(by_alias=True),
            media_type="application/problem+json",
            headers=exc.headers,
        )

    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
    return app


app = create_app()
