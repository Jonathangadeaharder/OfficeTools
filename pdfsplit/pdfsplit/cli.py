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


def split_pdf(
    input_path: Path,
    output_dir: Path | None = None,
    progress: Progress | None = None,
) -> list[Path]:
    if output_dir is None:
        output_dir = input_path.parent

    src = pikepdf.open(input_path)
    n_pages = len(src.pages)
    base = input_path.stem

    task = None
    if progress:
        task = progress.add_task("[cyan]splitting", total=n_pages)

    outputs: list[Path] = []
    try:
        for i in range(n_pages):
            out = pikepdf.Pdf.new()
            out.pages.append(src.pages[i])
            out_path = output_dir / f"{base}_{i + 1:03d}.pdf"
            out.save(out_path)
            out.close()
            outputs.append(out_path)
            if task and progress:
                progress.update(task, advance=1)
    finally:
        src.close()
        if task and progress:
            progress.update(task, visible=False)

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pdfsplit",
        description="Split a PDF into individual pages.",
    )
    parser.add_argument("file", type=Path, help="PDF file to split")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="Output directory (default: same as input)",
    )
    args = parser.parse_args()

    if not args.file.exists():
        print(f"  Error: {args.file} not found")
        return
    if args.file.suffix.lower() != ".pdf":
        print(f"  Error: {args.file} not a PDF")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        transient=True,
    ) as progress:
        outputs = split_pdf(args.file, args.output_dir, progress)

    print(f"  {args.file.name} -> {len(outputs)} pages")
