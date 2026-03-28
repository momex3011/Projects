from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel


router = APIRouter(prefix="/process", tags=["ai-process"])


class ProcessRequest(BaseModel):
    task_id: str


@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
async def start_process(request: ProcessRequest) -> dict[str, str]:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "AI orchestration is the next step. "
            "Wire this endpoint to your upscaler, colorizer, interpolator, and merger modules."
        ),
    )
