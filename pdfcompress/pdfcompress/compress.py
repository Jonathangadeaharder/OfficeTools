import subprocess
import shutil
import tempfile
from pathlib import Path

# sane defaults for screen viewing (ebook quality, no visible degradation)
GS_CMD = [
    "gs",
    "-sDEVICE=pdfwrite",
    "-dCompatibilityLevel=1.4",
    "-dNOPAUSE",
    "-dQUIET",
    "-dBATCH",
    "-dDetectDuplicateImages=true",
    "-dCompressFonts=true",
    "-dSubsetFonts=true",
    "-dEmbedAllFonts=false",
]

IMAGE_FILTERS = [
    "-dAutoFilterColorImages=false",
    "-dColorImageFilter=/DCTEncode",
    "-dAutoFilterGrayImages=false",
    "-dGrayImageFilter=/DCTEncode",
]


def _check_ghostscript() -> None:
    if not shutil.which("gs"):
        raise SystemExit(
            "ghostscript not found. Install: brew install ghostscript"
        )


def _gs_compress(
    input_path: Path,
    output_path: Path,
    dpi: int,
    jpeg_quality: int,
) -> None:
    grid = str(dpi)
    cmd = GS_CMD + [
        "-dColorImageDownsampleType=/Bicubic",
        f"-dColorImageResolution={grid}",
        "-dGrayImageDownsampleType=/Bicubic",
        f"-dGrayImageResolution={grid}",
        "-dMonoImageDownsampleType=/Bicubic",
        f"-dMonoImageResolution={max(dpi, 150)}",
        *IMAGE_FILTERS,
        f"-dJPEGQ={jpeg_quality}",
        f"-sOutputFile={output_path}",
        str(input_path),
    ]
    subprocess.run(cmd, check=True)


def _pikepdf_lean(input_path: Path, output_path: Path) -> None:
    import pikepdf

    pdf = pikepdf.open(input_path)
    pdf.remove_unreferenced_resources()
    pdf.save(output_path, linearize=True, compress_streams=True)
    pdf.close()


def _format_size(n_bytes: int) -> str:
    for unit in ("B", "KB", "MB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} GB"


def compress_pdf(
    input_path: Path,
    output_path: Path | None = None,
    quality: int = 85,
    aggressive: bool = False,
    light: bool = False,
) -> Path:
    _check_ghostscript()

    if output_path is None:
        output_path = input_path.with_stem(f"{input_path.stem}_compressed")

    if light:
        _pikepdf_lean(input_path, output_path)
    else:
        dpi = 72 if aggressive else 150
        jpeg_q = min(quality, 100)

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            gs_temp = Path(tmp.name)

        try:
            _gs_compress(input_path, gs_temp, dpi, jpeg_q)
            _pikepdf_lean(gs_temp, output_path)
        finally:
            gs_temp.unlink(missing_ok=True)

    original = input_path.stat().st_size
    compressed = output_path.stat().st_size
    reduction = (1 - compressed / original) * 100

    print(
        f"  {output_path.name}: "
        f"{_format_size(original)} -> {_format_size(compressed)} "
        f"({reduction:.0f}% smaller)"
    )

    return output_path
