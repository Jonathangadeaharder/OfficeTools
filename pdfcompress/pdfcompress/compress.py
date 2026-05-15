import re
import subprocess
import shutil
import tempfile
from pathlib import Path

import pikepdf
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
)


GS_CMD = [
    "gs",
    "-sDEVICE=pdfwrite",
    "-dCompatibilityLevel=1.4",
    "-dNOPAUSE",
    "-dBATCH",
    "-dDetectDuplicateImages=true",
    "-dCompressFonts=true",
    "-dSubsetFonts=true",
    "-dEmbedAllFonts=false",
    "-dAutoFilterColorImages=false",
    "-dColorImageFilter=/DCTEncode",
    "-dAutoFilterGrayImages=false",
    "-dGrayImageFilter=/DCTEncode",
    "-dDownsampleColorImages=true",
    "-dDownsampleGrayImages=true",
    "-dDownsampleMonoImages=true",
    "-dPassThroughJPEGImages=true",
    "-dWriteObjStms=true",
]


def _qpdf_normalize(input_path: Path, output_path: Path, progress: Progress) -> None:
    """Repair broken xref / structural issues before optimization."""
    task = progress.add_task("[cyan]qpdf repair", total=100)
    process = subprocess.Popen(
        ["qpdf", "--progress", str(input_path), str(output_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    assert process.stdout is not None
    for line in process.stdout:
        m = re.search(r"write progress: (\d+)%", line)
        if m:
            progress.update(task, completed=int(m.group(1)))
    process.wait()
    progress.update(task, visible=False)
    if not output_path.exists() or output_path.stat().st_size == 0:
        raise RuntimeError("qpdf normalize produced no output")


def _qpdf_optimize(
    input_path: Path, output_path: Path, jpeg_q: int, progress: Progress
) -> None:
    fixed = input_path.with_suffix(".fixed.pdf")
    try:
        _qpdf_normalize(input_path, fixed, progress)
    except (subprocess.CalledProcessError, RuntimeError):
        fixed = input_path

    source = str(fixed)
    task_id = None
    try:
        # Tier 1: full optimization including images
        task_id = progress.add_task("[cyan]qpdf optimize", total=100)
        process = subprocess.Popen(
            [
                "qpdf",
                "--progress",
                "--object-streams=generate",
                "--recompress-flate",
                "--compression-level=9",
                "--optimize-images",
                f"--jpeg-quality={jpeg_q}",
                "--oi-min-width=0",
                "--oi-min-height=0",
                "--remove-unreferenced-resources=auto",
                "--externalize-inline-images",
                source,
                str(output_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        assert process.stdout is not None
        for line in process.stdout:
            m = re.search(r"write progress: (\d+)%", line)
            if m:
                progress.update(task_id, completed=int(m.group(1)))
        process.wait()
        progress.update(task_id, completed=100, visible=False)
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, process.args)
    except subprocess.CalledProcessError:
        if task_id is not None:
            progress.update(task_id, visible=False)
        try:
            # Tier 2: structural only, skip image optimization
            task_id = progress.add_task("[cyan]qpdf optimize (structural)", total=100)
            process = subprocess.Popen(
                [
                    "qpdf",
                    "--progress",
                    "--object-streams=generate",
                    "--recompress-flate",
                    "--compression-level=9",
                    "--remove-unreferenced-resources=auto",
                    source,
                    str(output_path),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            assert process.stdout is not None
            for line in process.stdout:
                m = re.search(r"write progress: (\d+)%", line)
                if m:
                    progress.update(task_id, completed=int(m.group(1)))
            process.wait()
            progress.update(task_id, completed=100, visible=False)
            if process.returncode != 0:
                raise subprocess.CalledProcessError(process.returncode, process.args)
        except subprocess.CalledProcessError:
            if task_id is not None:
                progress.update(task_id, visible=False)
            # Tier 3: fallback copy
            shutil.copy2(source, output_path)
    finally:
        if fixed is not input_path:
            fixed.unlink(missing_ok=True)


def _gs_compress(
    input_path: Path,
    output_path: Path,
    dpi: int,
    jpeg_q: int,
    n_pages: int,
    progress: Progress,
) -> None:
    grid = str(dpi)

    task = progress.add_task("[green]ghostscript", total=n_pages)

    cmd = GS_CMD + [
        "-dColorImageDownsampleType=/Bicubic",
        f"-dColorImageResolution={grid}",
        "-dGrayImageDownsampleType=/Bicubic",
        f"-dGrayImageResolution={grid}",
        "-dMonoImageDownsampleType=/Bicubic",
        f"-dMonoImageResolution={max(dpi, 150)}",
        f"-dJPEGQ={jpeg_q}",
        f"-sOutputFile={output_path}",
        str(input_path),
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )

    assert process.stdout is not None
    for line in process.stdout:
        m = re.search(r"^Page (\d+)", line)
        if m and n_pages:
            progress.update(task, completed=int(m.group(1)))

    process.wait()
    progress.update(task, visible=False)

    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, cmd)


def _pick_smallest(*paths: Path) -> Path:
    return min(paths, key=lambda p: p.stat().st_size)


def _format_size(n_bytes: float) -> str:
    for unit in ("B", "KB", "MB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} GB"


def _analyze_pdf(input_path: Path) -> dict:
    """Estimate image content ratio and page count. Returns {image_ratio, total_bytes, image_bytes, page_count}."""
    total_bytes = input_path.stat().st_size
    if total_bytes == 0:
        return {"image_ratio": 0.0, "total_bytes": 0, "image_bytes": 0, "page_count": 0}

    img_bytes = 0
    page_count = 0
    try:
        pdf = pikepdf.open(input_path)
        page_count = len(pdf.pages)
        for page in pdf.pages:
            for _name, img in page.images.items():
                try:
                    raw = img.read_raw_bytes()
                    img_bytes += len(raw)
                except Exception:
                    pass
        pdf.close()
    except Exception:
        return {
            "image_ratio": 0.0,
            "total_bytes": total_bytes,
            "image_bytes": 0,
            "page_count": 0,
        }

    return {
        "image_ratio": img_bytes / total_bytes,
        "total_bytes": total_bytes,
        "image_bytes": img_bytes,
        "page_count": page_count,
    }


AUTO_STRATEGIES = {
    "light": {"dpi": None, "label": "text-only → light"},
    "normal": {"dpi": 150, "label": "mixed → normal (150 DPI)"},
    "aggressive": {"dpi": 72, "label": "image-heavy → aggressive (72 DPI)"},
}


def _pick_auto_strategy(image_ratio: float) -> str:
    if image_ratio < 0.15:
        return "light"
    if image_ratio > 0.50:
        return "aggressive"
    return "normal"


def compress_pdf(
    input_path: Path,
    output_path: Path | None = None,
    quality: int = 75,
    aggressive: bool = False,
    light: bool = False,
    dpi: int | None = None,
) -> Path:
    _check_deps()
    jpeg_q = min(max(quality, 1), 100)

    if output_path is None:
        output_path = input_path.with_stem(f"{input_path.stem}_compressed")

    # Determine strategy — explicit flags disable auto-detection
    use_light = light
    use_dpi = dpi
    auto_label = ""
    analysis = None

    if aggressive:
        use_dpi = 72
        use_light = False
        auto_label = "aggressive (72 DPI)"
    elif light:
        auto_label = "light"
    elif dpi is not None:
        use_light = False
        auto_label = f"user DPI ({dpi})"
    else:
        analysis = _analyze_pdf(input_path)
        auto_key = _pick_auto_strategy(analysis["image_ratio"])
        strat = AUTO_STRATEGIES[auto_key]
        use_light = auto_key == "light"
        use_dpi = strat["dpi"]
        auto_label = strat["label"]

    with (
        tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as t1,
        tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as t2,
    ):
        qpdf_tmp = Path(t1.name)
        gs_tmp = Path(t2.name)

    temps = [qpdf_tmp, gs_tmp]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        try:
            _qpdf_optimize(
                input_path, qpdf_tmp, jpeg_q if not use_light else 90, progress
            )

            if use_light:
                best = _pick_smallest(input_path, qpdf_tmp)
            else:
                assert use_dpi is not None
                n_pages = analysis["page_count"] if analysis else 0
                _gs_compress(qpdf_tmp, gs_tmp, use_dpi, jpeg_q, n_pages, progress)
                best = _pick_smallest(input_path, qpdf_tmp, gs_tmp)

            original = input_path.stat().st_size
            shutil.copy2(best, output_path)
            result_size = output_path.stat().st_size
        finally:
            for t in temps:
                t.unlink(missing_ok=True)

    reduction = (1 - result_size / original) * 100
    tag = " (optimal)" if result_size >= original else ""

    print(
        f"  {output_path.name}: "
        f"{_format_size(original)} -> {_format_size(result_size)} "
        f"({reduction:.0f}% smaller){tag}  [{auto_label}]"
    )

    return output_path


def _check_deps() -> None:
    missing = []
    if not shutil.which("qpdf"):
        missing.append("qpdf")
    if not shutil.which("gs"):
        missing.append("ghostscript")
    if missing:
        raise SystemExit(
            "Missing system dependencies: "
            + ", ".join(missing)
            + ". Install with: brew install "
            + " ".join(missing)
        )
