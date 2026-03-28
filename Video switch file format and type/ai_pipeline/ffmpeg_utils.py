import subprocess


class FFmpegError(RuntimeError):
    """Raised when an ffmpeg or ffprobe command fails."""


def run_command(command: list[str], failure_message: str) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        binary = command[0] if command else "Required command"
        raise FFmpegError(
            f"{failure_message} Command not found: {binary}. Install FFmpeg and ensure both ffmpeg and ffprobe are available on PATH."
        ) from exc

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "Unknown ffmpeg error."
        raise FFmpegError(f"{failure_message} Command: {' '.join(command)} | Detail: {detail}")
    return result
