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
) -> Path:
    _check_tesseract()

    if output_path is None:
        output_path = input_path.with_stem(f"{input_path.stem}_ocr")

    kwargs = dict(
        language=language,
        deskew=deskew,
        rotate_pages=rotate,
        optimize=optimize,
        output_type="pdf",
        progress_bar=False,
        quiet=True,
    )

    if force_ocr:
        kwargs["force_ocr"] = True
    else:
        kwargs["skip_text"] = True

    ocrmypdf.ocr(str(input_path), str(output_path), **kwargs)

    original = input_path.stat().st_size
    result = output_path.stat().st_size
    delta = result - original

    print(
        f"  {output_path.name}: "
        f"{_format_size(original)} -> {_format_size(result)} "
        f"({'+' if delta >= 0 else ''}{(delta / original) * 100:.0f}%)"
    )

    return output_path


def _format_size(n_bytes: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} GB"
