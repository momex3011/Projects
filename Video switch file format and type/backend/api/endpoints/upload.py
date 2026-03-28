import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ai_pipeline.converter_engine import convert_media
from ai_pipeline.frame_extractor import FFmpegError, initialize_processing_job
from backend.core.config import get_settings
from backend.core.tool_catalog import TOOL_SPECS, get_tool_spec


router = APIRouter(prefix="/upload", tags=["upload"])
settings = get_settings()


class UploadInitRequest(BaseModel):
    tool_id: str = "video-upscaler"
    filename: str
    total_size: int = Field(gt=0)
    total_chunks: int = Field(gt=0)
    content_type: str | None = None


class UploadInitResponse(BaseModel):
    upload_id: str
    filename: str
    total_chunks: int
    recommended_chunk_size: int
    accepted_extensions: list[str]


class UploadCompleteRequest(BaseModel):
    upload_id: str
    tool_id: str = "video-upscaler"
    extract_frames: bool = True
    extract_audio: bool = True
    resolution: str = "1080p"
    colorize: bool = False
    interpolate_60fps: bool = False
    audio_restore: bool = False
    film_restore: bool = False
    tool_options: dict[str, str] = Field(default_factory=dict)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_tool(tool_id: str) -> str:
    if tool_id not in TOOL_SPECS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported tool: {tool_id}",
        )
    return tool_id


def _normalize_filename(filename: str, tool_id: str) -> str:
    candidate = Path(filename).name
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A valid filename is required.",
        )

    suffix = Path(candidate).suffix.lower()
    spec = get_tool_spec(tool_id)
    if suffix not in spec.accepted_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {', '.join(spec.accepted_extensions)}",
        )

    return candidate


def _upload_workspace(upload_id: str) -> Path:
    return settings.temp_chunks_dir / upload_id


def _manifest_path(upload_id: str) -> Path:
    return _upload_workspace(upload_id) / "manifest.json"


def _chunk_path(upload_id: str, chunk_index: int) -> Path:
    return _upload_workspace(upload_id) / f"chunk_{chunk_index:08d}.part"


def _read_manifest(upload_id: str) -> dict[str, Any]:
    manifest_path = _manifest_path(upload_id)
    if not manifest_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Upload session not found.",
        )

    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _write_manifest(upload_id: str, payload: dict[str, Any]) -> None:
    manifest_path = _manifest_path(upload_id)
    manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _all_chunks_exist(upload_id: str, total_chunks: int) -> bool:
    return all(_chunk_path(upload_id, index).exists() for index in range(total_chunks))


def _assemble_chunks(upload_id: str, safe_filename: str) -> Path:
    manifest = _read_manifest(upload_id)
    final_filename = f"{upload_id}_{safe_filename}"
    final_path = settings.uploads_dir / final_filename

    with final_path.open("wb") as target:
        for chunk_index in range(manifest["total_chunks"]):
            chunk_file = _chunk_path(upload_id, chunk_index)
            if not chunk_file.exists():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing chunk {chunk_index}.",
                )
            with chunk_file.open("rb") as source:
                shutil.copyfileobj(source, target)

    manifest["status"] = "assembled"
    manifest["assembled_path"] = str(final_path)
    manifest["assembled_at"] = _timestamp()
    _write_manifest(upload_id, manifest)
    return final_path


@router.post("/init", response_model=UploadInitResponse, status_code=status.HTTP_201_CREATED)
async def init_upload(request: UploadInitRequest) -> UploadInitResponse:
    tool_id = _validate_tool(request.tool_id)
    safe_filename = _normalize_filename(request.filename, tool_id)
    max_upload_bytes = settings.max_upload_size_mb * 1024 * 1024
    if request.total_size > max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Upload exceeds configured size limit of {settings.max_upload_size_mb} MB.",
        )

    upload_id = uuid4().hex
    workspace = _upload_workspace(upload_id)
    workspace.mkdir(parents=True, exist_ok=True)

    manifest = {
        "upload_id": upload_id,
        "tool_id": tool_id,
        "filename": request.filename,
        "safe_filename": safe_filename,
        "total_size": request.total_size,
        "total_chunks": request.total_chunks,
        "content_type": request.content_type,
        "uploaded_chunks": [],
        "status": "initialized",
        "created_at": _timestamp(),
    }
    _write_manifest(upload_id, manifest)

    return UploadInitResponse(
        upload_id=upload_id,
        filename=safe_filename,
        total_chunks=request.total_chunks,
        recommended_chunk_size=settings.chunk_size_mb * 1024 * 1024,
        accepted_extensions=list(get_tool_spec(tool_id).accepted_extensions),
    )


@router.post("/chunk", status_code=status.HTTP_202_ACCEPTED)
async def upload_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(..., ge=0),
    total_chunks: int = Form(..., gt=0),
    chunk: UploadFile = File(...),
) -> dict[str, Any]:
    manifest = _read_manifest(upload_id)
    if total_chunks != manifest["total_chunks"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chunk metadata does not match the initialized upload session.",
        )

    if chunk_index >= manifest["total_chunks"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chunk index is outside the declared upload range.",
        )

    max_chunk_bytes = settings.chunk_size_mb * 1024 * 1024
    chunk_path = _chunk_path(upload_id, chunk_index)
    received_bytes = 0
    with chunk_path.open("wb") as target:
        while True:
            block = await chunk.read(1024 * 1024)
            if not block:
                break

            received_bytes += len(block)
            if received_bytes > max_chunk_bytes:
                target.close()
                chunk_path.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"Chunk exceeds configured size limit of {settings.chunk_size_mb} MB.",
                )
            target.write(block)

    if received_bytes == 0:
        chunk_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Received an empty chunk payload.",
        )

    uploaded_chunks = set(manifest["uploaded_chunks"])
    uploaded_chunks.add(chunk_index)
    manifest["uploaded_chunks"] = sorted(uploaded_chunks)
    manifest["status"] = "uploading"
    manifest["last_chunk_at"] = _timestamp()
    _write_manifest(upload_id, manifest)

    return {
        "upload_id": upload_id,
        "chunk_index": chunk_index,
        "received_chunks": len(manifest["uploaded_chunks"]),
        "total_chunks": manifest["total_chunks"],
        "is_complete": len(manifest["uploaded_chunks"]) == manifest["total_chunks"],
    }


@router.post("/complete", status_code=status.HTTP_202_ACCEPTED)
async def complete_upload(request: UploadCompleteRequest) -> dict[str, Any]:
    manifest = _read_manifest(request.upload_id)
    tool_id = _validate_tool(request.tool_id or manifest.get("tool_id", "video-upscaler"))
    if manifest.get("tool_id") and manifest["tool_id"] != tool_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected tool does not match the active upload session.",
        )
    if not _all_chunks_exist(request.upload_id, manifest["total_chunks"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Upload is incomplete. One or more chunks are missing.",
        )

    assembled_path = _assemble_chunks(request.upload_id, manifest["safe_filename"])
    spec = get_tool_spec(tool_id)
    manifest["tool_id"] = tool_id
    manifest["requested_pipeline"] = {
        "resolution": request.resolution,
        "colorize": request.colorize,
        "interpolate_60fps": request.interpolate_60fps,
        "audio_restore": request.audio_restore,
        "film_restore": request.film_restore,
    }
    manifest["tool_options"] = request.tool_options
    manifest["download_target"] = str(assembled_path)

    if spec.kind == "converter":
        try:
            result = convert_media(
                input_path=assembled_path,
                upload_id=request.upload_id,
                tool_id=tool_id,
                options=request.tool_options,
                settings=settings,
            )
        except FFmpegError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc

        manifest["status"] = "converted"
        manifest["result_path"] = result["result_path"]
        manifest["result_filename"] = result["result_filename"]
        manifest["download_target"] = result["result_path"]
        manifest["completed_at"] = _timestamp()
        _write_manifest(request.upload_id, manifest)

        for chunk_index in range(manifest["total_chunks"]):
            _chunk_path(request.upload_id, chunk_index).unlink(missing_ok=True)

        return {
            "mode": spec.kind,
            "upload_id": request.upload_id,
            "task_id": None,
            "upload_path": str(assembled_path),
            "processing_dir": None,
            "frames_dir": None,
            "audio_path": None,
            "video_metadata": None,
            "requested_pipeline": manifest["requested_pipeline"],
            "result_path": result["result_path"],
            "result_filename": result["result_filename"],
            "download_url": f"{settings.api_prefix}/upload/{request.upload_id}/download",
            "download_label": spec.download_label,
            "status_headline": result["status_headline"],
            "status_message": result["status_message"],
            "next_step": "Download your converted file or choose another source to create a new export.",
        }

    try:
        job = initialize_processing_job(
            video_path=assembled_path,
            settings=settings,
            should_extract_frames=request.extract_frames,
            extract_audio=request.extract_audio,
        )
    except FFmpegError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    manifest["status"] = "processing_ready"
    manifest["task_id"] = job["task_id"]
    manifest["processing_dir"] = job["task_dir"]
    manifest["video_metadata"] = job["video_metadata"]
    manifest["result_filename"] = Path(assembled_path).name
    _write_manifest(request.upload_id, manifest)

    for chunk_index in range(manifest["total_chunks"]):
        _chunk_path(request.upload_id, chunk_index).unlink(missing_ok=True)

    return {
        "mode": spec.kind,
        "upload_id": request.upload_id,
        "task_id": job["task_id"],
        "upload_path": str(assembled_path),
        "processing_dir": job["task_dir"],
        "frames_dir": job["input_frames_dir"],
        "audio_path": job["audio_path"],
        "video_metadata": job["video_metadata"],
        "requested_pipeline": manifest["requested_pipeline"],
        "result_path": str(assembled_path),
        "result_filename": Path(assembled_path).name,
        "download_url": f"{settings.api_prefix}/upload/{request.upload_id}/download",
        "download_label": spec.download_label,
        "status_headline": "Source ready",
        "status_message": "Your clip is uploaded, prepared, and available to download while the restoration stages continue to grow.",
        "next_step": "Choose another clip or keep this prepared source on hand while the restoration pipeline is expanded.",
    }


@router.get("/{upload_id}", status_code=status.HTTP_200_OK)
async def get_upload_status(upload_id: str) -> dict[str, Any]:
    manifest = _read_manifest(upload_id)
    return manifest


@router.get("/{upload_id}/download", status_code=status.HTTP_200_OK)
async def download_upload_result(upload_id: str) -> FileResponse:
    manifest = _read_manifest(upload_id)
    download_target = manifest.get("download_target") or manifest.get("assembled_path")
    if not download_target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No downloadable file is available for this upload yet.",
        )

    target_path = Path(download_target)
    if not target_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The downloadable file could not be found on disk.",
        )

    return FileResponse(target_path, filename=target_path.name)
