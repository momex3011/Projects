import json
from fractions import Fraction
from pathlib import Path
from typing import Any
from uuid import uuid4

from ai_pipeline.audio_processor import extract_audio_track
from ai_pipeline.ffmpeg_utils import FFmpegError, run_command


def _parse_fps(raw_value: str | None) -> float | None:
    if not raw_value or raw_value == "0/0":
        return None
    return float(Fraction(raw_value))


def probe_video(video_path: Path, settings: Any) -> dict[str, Any]:
    command = [
        settings.ffprobe_binary,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,avg_frame_rate,r_frame_rate,nb_frames",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(video_path),
    ]
    result = run_command(command, f"Failed to inspect video: {video_path}")
    payload = json.loads(result.stdout)

    streams = payload.get("streams", [])
    if not streams:
        raise FFmpegError(f"No video stream found in {video_path}")

    stream = streams[0]
    duration = payload.get("format", {}).get("duration")
    fps = _parse_fps(stream.get("avg_frame_rate")) or _parse_fps(stream.get("r_frame_rate"))

    return {
        "width": stream.get("width"),
        "height": stream.get("height"),
        "fps": fps,
        "duration_seconds": float(duration) if duration else None,
        "frame_count": int(stream["nb_frames"]) if stream.get("nb_frames") not in {None, "N/A"} else None,
    }


def extract_frames(video_path: Path, frames_dir: Path, settings: Any) -> Path:
    frames_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = frames_dir / "frame_%08d.png"
    command = [
        settings.ffmpeg_binary,
        "-y",
        "-i",
        str(video_path),
        "-map",
        "0:v:0",
        "-vsync",
        "0",
        "-start_number",
        "0",
        str(output_pattern),
    ]
    run_command(command, f"Failed to extract frames from {video_path}")
    return frames_dir


def initialize_processing_job(
    video_path: Path,
    settings: Any,
    should_extract_frames: bool = True,
    extract_audio: bool = True,
) -> dict[str, Any]:
    task_id = f"task_{uuid4().hex}"
    task_dir = settings.processing_dir / task_id
    input_frames_dir = task_dir / "input_frames"
    output_frames_dir = task_dir / "output_frames"
    task_dir.mkdir(parents=True, exist_ok=True)
    input_frames_dir.mkdir(parents=True, exist_ok=True)
    output_frames_dir.mkdir(parents=True, exist_ok=True)

    video_metadata = probe_video(video_path, settings)
    if should_extract_frames:
        extract_frames(video_path, input_frames_dir, settings)

    audio_path = None
    if extract_audio:
        audio_target = task_dir / "audio.wav"
        extracted_audio = extract_audio_track(video_path, audio_target, settings)
        audio_path = str(extracted_audio) if extracted_audio else None

    job_manifest = {
        "task_id": task_id,
        "source_video": str(video_path),
        "task_dir": str(task_dir),
        "input_frames_dir": str(input_frames_dir),
        "output_frames_dir": str(output_frames_dir),
        "audio_path": audio_path,
        "video_metadata": video_metadata,
        "status": "ready_for_inference",
    }
    (task_dir / "job.json").write_text(json.dumps(job_manifest, indent=2), encoding="utf-8")
    return job_manifest
