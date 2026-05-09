import shutil
import subprocess
from pathlib import Path


def _check_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg not found. Install: brew install ffmpeg")


def _format_size(n_bytes: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} GB"


def _escape_srt_path(path: Path) -> str:
    escaped = str(path)
    escaped = escaped.replace("\\", "\\\\\\\\")
    escaped = escaped.replace(":", "\\\\:")
    escaped = escaped.replace("'", "\\\\'")
    escaped = escaped.replace("[", "\\\\[")
    escaped = escaped.replace("]", "\\\\]")
    return escaped


def add_subtitles(
    video_path: Path,
    subs_path: Path,
    output_path: Path | None = None,
    force: bool = False,
    language: str = "eng",
    crf: int = 23,
) -> Path:
    _check_ffmpeg()

    if output_path is None:
        output_path = video_path.with_stem(f"{video_path.stem}_subtitled")

    if force:
        escaped_srt = _escape_srt_path(subs_path)
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vf", f"subtitles='{escaped_srt}'",
            "-c:v", "libx264",
            "-crf", str(crf),
            "-preset", "fast",
            "-c:a", "copy",
            "-y",
            str(output_path),
        ]
    else:
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-i", str(subs_path),
            "-c", "copy",
            "-c:s", "mov_text",
            "-metadata:s:s:0", f"language={language}",
            "-y",
            str(output_path),
        ]

    subprocess.run(cmd, check=True, capture_output=True)

    original = video_path.stat().st_size
    result = output_path.stat().st_size
    delta = result - original

    print(
        f"  {output_path.name}: "
        f"{_format_size(original)} -> {_format_size(result)} "
        f"({'+' if delta >= 0 else ''}{(delta / original) * 100:.0f}%)"
    )

    return output_path
