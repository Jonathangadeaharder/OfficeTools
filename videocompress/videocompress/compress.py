import platform
import shutil
import subprocess
from pathlib import Path

IS_MACOS = platform.system() == "Darwin"


def _check_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found. Install: brew install ffmpeg")


def _format_size(n_bytes: float) -> str:
    for unit in ("B", "KB", "MB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} GB"


def compress_video(
    input_path: Path,
    output_path: Path | None = None,
    crf: int = 28,
    preset: str = "medium",
    codec: str = "libx264",
    hw: bool = False,
) -> Path:
    _check_ffmpeg()

    if output_path is None:
        output_path = input_path.with_stem(f"{input_path.stem}_compressed")

    # If hardware encoding is requested
    if hw:
        # VideoToolbox has hardware accelerated codecs.
        # It does not support CRF (-crf), so we use -q:v for quality.
        # Map target codec to the hardware accelerated one:
        if codec in ("libx265", "hevc"):
            vcodec = "hevc_videotoolbox"
        else:
            vcodec = "h264_videotoolbox"

        # videotoolbox quality goes from 1 to 100, default is 50-60.
        # CRF goes from 0 (best) to 51 (worst), default is 23/28.
        # Map crf 0-51 to quality 100-1:
        q_val = max(1, min(100, int((51 - crf) / 51 * 100)))

        cmd = [
            "ffmpeg",
            "-i",
            str(input_path),
            "-c:v",
            vcodec,
            "-q:v",
            str(q_val),
            "-c:a",
            "copy",
            "-y",
            str(output_path),
        ]
    else:
        # Software encoding (libx264, libx265/hevc)
        # Note: 'hevc' maps to 'libx265'
        actual_codec = "libx265" if codec in ("libx265", "hevc") else "libx264"
        cmd = [
            "ffmpeg",
            "-i",
            str(input_path),
            "-c:v",
            actual_codec,
            "-crf",
            str(crf),
            "-preset",
            preset,
            "-c:a",
            "copy",
            "-y",
            str(output_path),
        ]

    # Run command and capture output
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
