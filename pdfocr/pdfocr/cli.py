import argparse
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from .ocr import ocr_pdf


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pdfocr",
        description="OCR PDFs using Tesseract via ocrmypdf",
    )
    parser.add_argument("files", nargs="+", type=Path, help="PDF file(s) to OCR")
    parser.add_argument(
        "-o", "--output", type=Path, help="Output path (single file only)"
    )
    parser.add_argument(
        "-l",
        "--language",
        default="eng",
        help="OCR language(s) e.g. 'eng' or 'deu+eng' (default: eng)",
    )
    parser.add_argument(
        "--force-ocr",
        action="store_true",
        help="Re-OCR even if text layer already exists",
    )
    parser.add_argument(
        "--no-deskew",
        action="store_false",
        dest="deskew",
        help="Disable auto-deskew",
    )
    parser.add_argument(
        "--no-rotate",
        action="store_false",
        dest="rotate",
        help="Disable auto-rotate",
    )
    parser.add_argument(
        "--no-optimize",
        action="store_false",
        dest="optimize",
        help="Disable output optimization",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=None,
        help="Parallel page workers per file (default: sqrt(cpu_count))",
    )
    args = parser.parse_args()

    if args.output and len(args.files) > 1:
        parser.error("-o/--output can only be used with a single input file")

    valid = []
    for path in args.files:
        if not path.exists():
            print(f"  Skipping: {path} not found")
            continue
        if path.suffix.lower() != ".pdf":
            print(f"  Skipping: {path} not a PDF")
            continue
        valid.append(path)

    if not valid:
        return

    cpu = os.cpu_count() or 1
    max_workers = max(1, int(cpu**0.5))

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = {}
        for path in valid:
            output = args.output if args.output and len(valid) == 1 else None
            f = pool.submit(
                ocr_pdf,
                path,
                output,
                language=args.language,
                force_ocr=args.force_ocr,
                deskew=args.deskew,
                rotate=args.rotate,
                optimize=1 if args.optimize else 0,
                jobs=args.jobs,
            )
            futures[f] = path

        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f"  ERROR on {futures[f].name}: {e}")
