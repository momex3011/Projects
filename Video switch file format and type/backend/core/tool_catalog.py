from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ToolKind = Literal["restoration", "converter"]


@dataclass(frozen=True)
class ToolSpec:
    id: str
    label: str
    kind: ToolKind
    accepted_extensions: tuple[str, ...]
    output_extension: str
    download_label: str


TOOL_SPECS: dict[str, ToolSpec] = {
    "video-upscaler": ToolSpec(
        id="video-upscaler",
        label="Video Upscaler",
        kind="restoration",
        accepted_extensions=(".mp4",),
        output_extension=".mp4",
        download_label="Download uploaded clip",
    ),
    "gif-maker": ToolSpec(
        id="gif-maker",
        label="GIF maker",
        kind="converter",
        accepted_extensions=(".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov", ".webm"),
        output_extension=".gif",
        download_label="Download GIF",
    ),
    "video-to-gif": ToolSpec(
        id="video-to-gif",
        label="Video to GIF",
        kind="converter",
        accepted_extensions=(".mp4", ".mov", ".webm"),
        output_extension=".gif",
        download_label="Download GIF",
    ),
    "gif-to-mp4": ToolSpec(
        id="gif-to-mp4",
        label="GIF to MP4",
        kind="converter",
        accepted_extensions=(".gif",),
        output_extension=".mp4",
        download_label="Download MP4",
    ),
    "gif-to-webm": ToolSpec(
        id="gif-to-webm",
        label="GIF to WebM",
        kind="converter",
        accepted_extensions=(".gif",),
        output_extension=".webm",
        download_label="Download WebM",
    ),
    "gif-to-mov": ToolSpec(
        id="gif-to-mov",
        label="GIF to MOV",
        kind="converter",
        accepted_extensions=(".gif",),
        output_extension=".mov",
        download_label="Download MOV",
    ),
    "webp-to-gif": ToolSpec(
        id="webp-to-gif",
        label="WebP to GIF",
        kind="converter",
        accepted_extensions=(".webp",),
        output_extension=".gif",
        download_label="Download GIF",
    ),
    "apng-to-gif": ToolSpec(
        id="apng-to-gif",
        label="APNG to GIF",
        kind="converter",
        accepted_extensions=(".apng", ".png"),
        output_extension=".gif",
        download_label="Download GIF",
    ),
    "avif-to-gif": ToolSpec(
        id="avif-to-gif",
        label="AVIF to GIF",
        kind="converter",
        accepted_extensions=(".avif",),
        output_extension=".gif",
        download_label="Download GIF",
    ),
}


def get_tool_spec(tool_id: str) -> ToolSpec:
    try:
        return TOOL_SPECS[tool_id]
    except KeyError as exc:
        raise ValueError(f"Unsupported tool: {tool_id}") from exc
