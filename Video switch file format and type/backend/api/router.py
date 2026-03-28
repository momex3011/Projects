from fastapi import APIRouter

from backend.api.endpoints import ai_process, converters, upload


api_router = APIRouter()
api_router.include_router(upload.router)
api_router.include_router(ai_process.router)
api_router.include_router(converters.router)
