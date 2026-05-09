import shutil
import subprocess
from pathlib import Path


def _check_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found. Install: brew install ffmpeg")


def _format_size(n_bytes: float) -> str:
    for unit in ("B", "KB", "MB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} GB"


def extract_audio(
    input_path: Path,
    output_path: Path | None = None,
    reencode: bool = False,
    bitrate: int = 128,
) -> Path:
    _check_ffmpeg()

    if output_path is None:
        output_path = input_path.with_suffix(".m4a")

    if reencode:
        cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-vn",
            "-c:a", "aac",
            "-b:a", f"{bitrate}k",
            "-y",
            str(output_path),
        ]
    else:
        cmd = [
            "ffmpeg",
            "-i", str(input_path),
            "-vn",
            "-c:a", "copy",
            "-y",
            str(output_path),
        ]

    subprocess.run(cmd, check=True, capture_output=True)

    original = input_path.stat().st_size
    result = output_path.stat().st_size
    reduction = (1 - result / original) * 100

    print(
        f"  {output_path.name}: "
        f"{_format_size(original)} -> {_format_size(result)} "
        f"({reduction:.0f}% smaller)"
    )

    return output_path
