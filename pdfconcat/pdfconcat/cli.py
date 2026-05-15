import argparse
from pathlib import Path

import pikepdf
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)


def concat_pdfs(input_paths: list[Path], output_path: Path, progress: Progress) -> Path:
    task = progress.add_task("[cyan]merging", total=len(input_paths))
    merged = pikepdf.Pdf.new()
    try:
        for path in input_paths:
            src = pikepdf.open(path)
            merged.pages.extend(src.pages)
            src.close()
            progress.update(task, advance=1)
        merged.save(output_path)
        return output_path
    finally:
        merged.close()
        progress.update(task, visible=False)


def _format_size(n_bytes: float) -> str:
    for unit in ("B", "KB", "MB"):
        if n_bytes < 1024:
            return f"{n_bytes:.1f} {unit}"
        n_bytes /= 1024
    return f"{n_bytes:.1f} GB"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pdfconcat",
        description="Merge multiple PDFs into one.",
    )
    parser.add_argument(
        "files", nargs="+", type=Path, help="PDF files to merge (in order)"
    )
    parser.add_argument(
        "-o", "--output", type=Path, required=True, help="Output PDF path"
    )
    args = parser.parse_args()

    for path in args.files:
        if not path.exists():
            print(f"  Skipping: {path} not found")
            return
        if path.suffix.lower() != ".pdf":
            print(f"  Skipping: {path} not a PDF")
            return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        concat_pdfs(args.files, args.output, progress)

    result_size = args.output.stat().st_size
    total_size = sum(p.stat().st_size for p in args.files)
    print(
        f"  {args.output.name}: "
        f"{_format_size(total_size)} -> {_format_size(result_size)} "
        f"({len(args.files)} files merged)"
    )
