from __future__ import annotations

from pathlib import Path
from typing import Any

from ai_pipeline.ffmpeg_utils import run_command


def _build_output_path(input_path: Path, upload_id: str, tool_id: str, settings: Any) -> Path:
    extension_map = {
        "gif-maker": ".gif",
        "video-to-gif": ".gif",
        "gif-to-mp4": ".mp4",
        "gif-to-webm": ".webm",
        "gif-to-mov": ".mov",
        "webp-to-gif": ".gif",
        "apng-to-gif": ".gif",
        "avif-to-gif": ".gif",
    }
    output_extension = extension_map[tool_id]
    output_name = f"{upload_id}_{tool_id}{output_extension}"
    return settings.outputs_dir / output_name


def _square_filter(size: int) -> str:
    return f"scale={size}:{size}:force_original_aspect_ratio=increase,crop={size}:{size}"


def _landscape_filter(width: int, height: int) -> str:
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x161121"
    )


def _portrait_filter(width: int, height: int) -> str:
    return (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=0x161121"
    )


def _gif_maker_filters(options: dict[str, str]) -> tuple[str, list[str]]:
    pace = options.get("pace", "Steady")
    shape = options.get("shape", "Landscape")

    fps = {
        "Gentle": 8,
        "Steady": 12,
        "Lively": 18,
    }.get(pace, 12)

    if shape == "Square":
        layout = _square_filter(720)
    elif shape == "Portrait":
        layout = _portrait_filter(720, 960)
    else:
        layout = _landscape_filter(960, 540)

    return f"fps={fps},{layout}", []


def _video_to_gif_filters(options: dict[str, str]) -> tuple[str, list[str]]:
    clip_length = options.get("clip", "6 seconds")
    motion = options.get("motion", "Balanced")
    frame = options.get("frame", "Keep full frame")

    duration = {
        "6 seconds": "6",
        "10 seconds": "10",
        "15 seconds": "15",
    }.get(clip_length, "6")

    fps = {
        "Balanced": 12,
        "Sharper": 16,
        "Smaller file": 9,
    }.get(motion, 12)

    if frame == "Square crop":
        layout = _square_filter(720)
    elif frame == "Center crop":
        layout = "scale=960:540:force_original_aspect_ratio=increase,crop=960:540"
    else:
        layout = _landscape_filter(960, 540)

    return f"fps={fps},{layout}", ["-t", duration]


def _web_image_to_gif_filters(tool_id: str, options: dict[str, str]) -> tuple[str, list[str]]:
    if tool_id == "webp-to-gif":
        palette = options.get("palette", "Balanced")
        size = options.get("size", "Original")
        fps = {"Soft gradients": 10, "Balanced": 12, "Punchier contrast": 14}.get(palette, 12)
        width = {"Original": 0, "1080 wide": 1080, "Social ready": 720}.get(size, 0)
    elif tool_id == "apng-to-gif":
        timing = options.get("timing", "Keep timing")
        delivery = options.get("delivery", "Balanced")
        fps = {"Keep timing": 12, "Slightly smoother": 16, "Faster loop": 18}.get(timing, 12)
        width = {"Balanced": 720, "Sharper": 960, "Lighter": 540}.get(delivery, 720)
    else:
        sequence = options.get("sequence", "Preview loop")
        output = options.get("output", "Balanced")
        fps = {"Image set": 8, "Clip strip": 10, "Preview loop": 12}.get(sequence, 12)
        width = {"Balanced": 720, "Smaller": 540, "Showcase": 960}.get(output, 720)

    if width:
        return f"fps={fps},scale={width}:-1:flags=lanczos", []
    return f"fps={fps}", []


def _video_output_filters(tool_id: str, options: dict[str, str]) -> tuple[str, list[str]]:
    if tool_id == "gif-to-mp4":
        delivery = options.get("delivery", "Balanced")
        motion = options.get("motion", "Native loop")

        width = {"Balanced": 720, "Presentation": 1080, "Compact": 540}.get(delivery, 720)
        fps = {"Native loop": 15, "Softer playback": 12, "Sharper cadence": 24}.get(motion, 15)
        crf = {"Balanced": "22", "Presentation": "18", "Compact": "28"}.get(delivery, "22")

        return (
            f"fps={fps},scale={width}:-2:flags=lanczos,format=yuv420p",
            ["-c:v", "libx264", "-crf", crf, "-pix_fmt", "yuv420p", "-movflags", "+faststart"],
        )

    if tool_id == "gif-to-webm":
        quality = options.get("quality", "Balanced")
        width = {"Presentation": 1080, "Balanced": 720, "Smaller": 540}.get(quality, 720)
        crf = {"Presentation": "24", "Balanced": "30", "Smaller": "36"}.get(quality, "30")

        return (
            f"fps=15,scale={width}:-2:flags=lanczos",
            ["-c:v", "libvpx-vp9", "-b:v", "0", "-crf", crf],
        )

    delivery = options.get("delivery", "Editing")
    motion = options.get("motion", "Native")

    width = {"Editing": 960, "Presentation": 1080, "Archival": 1280}.get(delivery, 960)
    fps = {"Native": 15, "Smoothed": 20, "Frame hold": 10}.get(motion, 15)

    return (
        f"fps={fps},scale={width}:-2:flags=lanczos",
        ["-c:v", "png", "-pix_fmt", "rgba"],
    )


def _tool_filters(tool_id: str, options: dict[str, str]) -> tuple[str, list[str], list[str]]:
    if tool_id == "gif-maker":
        filters, extra_inputs = _gif_maker_filters(options)
        return filters, extra_inputs, ["-loop", "0"]

    if tool_id == "video-to-gif":
        filters, extra_inputs = _video_to_gif_filters(options)
        return filters, extra_inputs, ["-loop", "0"]

    if tool_id in {"webp-to-gif", "apng-to-gif", "avif-to-gif"}:
        filters, extra_inputs = _web_image_to_gif_filters(tool_id, options)
        return filters, extra_inputs, ["-loop", "0"]

    filters, output_args = _video_output_filters(tool_id, options)
    return filters, [], output_args


def convert_media(
    input_path: Path,
    upload_id: str,
    tool_id: str,
    options: dict[str, str],
    settings: Any,
) -> dict[str, str]:
    output_path = _build_output_path(input_path, upload_id, tool_id, settings)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    filters, extra_args, output_args = _tool_filters(tool_id, options)

    command = [settings.ffmpeg_binary, "-y"]
    if tool_id == "gif-maker" and input_path.suffix.lower() in {".jpg", ".jpeg", ".png"}:
        command.extend(["-loop", "1", "-t", "3"])

    command.extend(["-i", str(input_path)])
    command.extend(extra_args)
    command.extend(["-vf", filters, *output_args, str(output_path)])

    run_command(command, f"Failed to create {tool_id} output from {input_path}")

    result_name = output_path.name
    result_message = {
        "gif-maker": "Your GIF has been built and is ready to save.",
        "video-to-gif": "Your clip has been turned into a GIF and is ready to save.",
        "gif-to-mp4": "Your MP4 export is ready to download.",
        "gif-to-webm": "Your WebM export is ready to download.",
        "gif-to-mov": "Your MOV export is ready to download.",
        "webp-to-gif": "Your GIF export is ready to download.",
        "apng-to-gif": "Your GIF export is ready to download.",
        "avif-to-gif": "Your GIF export is ready to download.",
    }[tool_id]

    return {
        "result_path": str(output_path),
        "result_filename": result_name,
        "status_headline": "Download ready",
        "status_message": result_message,
    }
