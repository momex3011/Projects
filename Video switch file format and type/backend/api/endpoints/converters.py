from fastapi import APIRouter


router = APIRouter(prefix="/converters", tags=["converters"])


@router.get("/health", status_code=200)
async def converters_health() -> dict[str, str]:
    return {"status": "converter endpoints will be added after the upload pipeline"}
