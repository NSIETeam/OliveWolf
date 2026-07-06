from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="OliveWolf Studio API",
        version="0.1.0",
        description="Production control plane for OliveWolf digital human workspaces.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api/v1")

    web_dir = Path(__file__).resolve().parent / "web"
    app.mount("/studio", StaticFiles(directory=web_dir, html=True), name="studio")

    @app.get("/", include_in_schema=False)
    def studio_index():
        return FileResponse(web_dir / "index.html")

    return app


app = create_app()
