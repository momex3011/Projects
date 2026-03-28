from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.router import api_router
from backend.core.config import ensure_storage_dirs, get_settings


def create_fastapi_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="FastAPI backend for RetroScale AI video ingestion and processing.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup_event() -> None:
        ensure_storage_dirs(settings)

    @app.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {
            "name": "RetroScale AI API",
            "docs": "/docs",
            "health": "/health",
            "upload_init": f"{settings.api_prefix}/upload/init",
        }

    @app.get("/health", tags=["system"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router, prefix=settings.api_prefix)
    return app
