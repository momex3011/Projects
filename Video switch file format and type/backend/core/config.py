import os
import shutil
from functools import lru_cache
from glob import glob
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STORAGE_DIR = PROJECT_ROOT / "storage"


class Settings(BaseSettings):
    app_name: str = "RetroScale AI API"
    api_prefix: str = "/api"
    max_upload_size_mb: int = 20480
    chunk_size_mb: int = 5
    ffmpeg_binary: str = "ffmpeg"
    ffprobe_binary: str = "ffprobe"
    uploads_dir: Path = DEFAULT_STORAGE_DIR / "uploads"
    processing_dir: Path = DEFAULT_STORAGE_DIR / "processing"
    outputs_dir: Path = DEFAULT_STORAGE_DIR / "outputs"
    temp_chunks_dir: Path = DEFAULT_STORAGE_DIR / ".chunks"
    models_dir: Path = PROJECT_ROOT / "models"
    allowed_video_extensions: tuple[str, ...] = (".mp4",)
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / "backend" / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


def ensure_storage_dirs(settings: Settings) -> None:
    for path in (
        settings.uploads_dir,
        settings.processing_dir,
        settings.outputs_dir,
        settings.temp_chunks_dir,
        settings.models_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)


def _resolve_binary_path(configured_value: str, binary_name: str) -> str:
    configured_path = Path(configured_value)
    if configured_path.exists():
        return str(configured_path)

    discovered_on_path = shutil.which(configured_value)
    if discovered_on_path:
        return discovered_on_path

    if os.name != "nt":
        return configured_value

    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return configured_value

    binary_filename = f"{binary_name}.exe"
    candidate_patterns = [
        Path(local_app_data)
        / "Microsoft"
        / "WinGet"
        / "Packages"
        / "Gyan.FFmpeg_*"
        / "*"
        / "bin"
        / binary_filename,
        Path(local_app_data)
        / "Microsoft"
        / "WinGet"
        / "Packages"
        / "BtbN.FFmpeg*"
        / "*"
        / "bin"
        / binary_filename,
        Path(local_app_data)
        / "Microsoft"
        / "WinGet"
        / "Packages"
        / "yt-dlp.FFmpeg*"
        / "*"
        / "bin"
        / binary_filename,
    ]

    for pattern in candidate_patterns:
        matches = glob(str(pattern))
        if matches:
            return matches[0]

    return configured_value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ffmpeg_binary = _resolve_binary_path(settings.ffmpeg_binary, "ffmpeg")
    settings.ffprobe_binary = _resolve_binary_path(settings.ffprobe_binary, "ffprobe")
    ensure_storage_dirs(settings)
    return settings
