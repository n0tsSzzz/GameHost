from fastapi import FastAPI

from gamehost_node.api.router import router


def create_app() -> FastAPI:
    app = FastAPI(title="GameHost Node Agent", version="0.1.0")
    app.include_router(router)
    return app


app = create_app()
