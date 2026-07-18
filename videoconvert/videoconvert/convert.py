import shutil
import subprocess
from pathlib import Path

FORMAT_CODECS: dict[str, dict[str, str]] = {
    "mp4": {"vcodec": "libx264", "acodec": "aac", "ext": ".mp4"},
    "mkv": {"vcodec": "libx264", "acodec": "aac", "ext": ".mkv"},
    "mov": {"vcodec": "libx264", "acodec": "aac", "ext": ".mov"},
    "avi": {"vcodec": "mpeg4", "acodec": "libmp3lame", "ext": ".avi"},
    "webm": {"vcodec": "libvpx-vp9", "acodec": "libopus", "ext": ".webm"},
    "wmv": {"vcodec": "wmv2", "acodec": "wmav2", "ext": ".wmv"},
    "flv": {"vcodec": "flv", "acodec": "libmp3lame", "ext": ".flv"},
}

SUPPORTED_FORMATS = list(FORMAT_CODECS.keys())


def _check_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        raise FileNotFoundError("ffmpeg not found. Install: brew install ffmpeg")


def _format_size(n_bytes: float) -> str:
    for unit in ("B", "KB", "MB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} GB"


def convert_video(
    input_path: Path,
    fmt: str,
    output_path: Path | None = None,
    copy_streams: bool = False,
) -> Path:
    _check_ffmpeg()

    fmt = fmt.lower().lstrip(".")
    if fmt not in FORMAT_CODECS:
        raise ValueError(
            f"Unsupported format: {fmt}. Supported: {', '.join(SUPPORTED_FORMATS)}"
        )

    codecs = FORMAT_CODECS[fmt]
    if output_path is None:
        output_path = input_path.with_suffix(codecs["ext"])
    if output_path == input_path:
        output_path = input_path.with_stem(f"{input_path.stem}_converted")

    if copy_streams:
        cmd = [
            "ffmpeg",
            "-i",
            str(input_path),
            "-c",
            "copy",
            "-y",
            str(output_path),
        ]
    else:
        cmd = [
            "ffmpeg",
            "-i",
            str(input_path),
            "-c:v",
            codecs["vcodec"],
            "-c:a",
            codecs["acodec"],
            "-y",
            str(output_path),
        ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"ffmpeg failed on {input_path.name}: "
            f"{e.stderr.strip() if e.stderr else e}"
        ) from e

    original = input_path.stat().st_size
    result = output_path.stat().st_size
    delta = ((result / original - 1) * 100) if original > 0 else 0.0

    print(
        f"  {input_path.name} -> {output_path.name}: "
        f"{_format_size(original)} -> {_format_size(result)} "
        f"({delta:+.0f}%)"
    )

    return output_path
