import os
import shutil
from pathlib import Path

import ocrmypdf


def _check_tesseract() -> None:
    if not shutil.which("tesseract"):
        raise SystemExit("tesseract not found. Install: brew install tesseract")


def ocr_pdf(
    input_path: Path,
    output_path: Path | None = None,
    language: str = "eng",
    force_ocr: bool = False,
    deskew: bool = True,
    rotate: bool = True,
    optimize: int = 1,
    jobs: int | None = None,
) -> Path:
    _check_tesseract()

    if output_path is None:
        output_path = input_path.with_stem(f"{input_path.stem}_ocr")

    if jobs is None:
        cpu = os.cpu_count() or 1
        jobs = max(1, int(cpu**0.5))

    ocrmypdf.ocr(
        str(input_path),
        str(output_path),
        language=language,
        deskew=deskew,
        rotate_pages=rotate,
        optimize=optimize,
        output_type="pdf",
        progress_bar=False,
        quiet=True,
        jobs=jobs,
        force_ocr=force_ocr,
        skip_text=not force_ocr,
    )

    original = input_path.stat().st_size
    result = output_path.stat().st_size
    delta = result - original

    print(
        f"  {output_path.name}: "
        f"{_format_size(original)} -> {_format_size(result)} "
        f"({'+' if delta >= 0 else ''}{(delta / original) * 100:.0f}%)"
    )

    return output_path


def _format_size(n_bytes: float) -> str:
    for unit in ("B", "KB", "MB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} GB"
