from pathlib import Path
from typing import Any

from ai_pipeline.ffmpeg_utils import FFmpegError, run_command


def extract_audio_track(video_path: Path, output_path: Path, settings: Any) -> Path | None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        settings.ffmpeg_binary,
        "-y",
        "-i",
        str(video_path),
        "-map",
        "0:a:0?",
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "48000",
        "-ac",
        "2",
        str(output_path),
    ]
    try:
        run_command(command, f"Failed to extract audio from {video_path}.")
    except FFmpegError as exc:
        detail = str(exc)
        if "matches no streams" in detail or "does not contain any stream" in detail:
            return None
        raise
    return output_path
