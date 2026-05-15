import argparse
from pathlib import Path

from .convert import pdf_to_markdown


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pdf2md",
        description="Convert PDFs to Markdown using Docling (SOTA AI pipeline).",
    )
    parser.add_argument("files", nargs="+", type=Path, help="PDF file(s) to convert")
    parser.add_argument(
        "-o", "--output", type=Path, help="Output path (single file only)"
    )
    parser.add_argument(
        "--pages",
        help="Page range e.g. '1-5' or '3,7-9'",
    )
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Use OCR/layout pipeline instead of VLM (faster, worse for scanned/image-heavy PDFs)",
    )
    args = parser.parse_args()

    if args.output and len(args.files) > 1:
        parser.error("-o/--output can only be used with a single input file")

    page_range = None
    if args.pages:
        parts = args.pages.split("-")
        if len(parts) == 2:
            try:
                page_range = (int(parts[0]), int(parts[1]))
            except ValueError:
                parser.error(f"Invalid page range: {args.pages}")
        else:
            try:
                p = int(args.pages)
                page_range = (p, p)
            except ValueError:
                parts = args.pages.split(",")[:2]
                if len(parts) == 2:
                    try:
                        page_range = (int(parts[0]), int(parts[1]))
                    except ValueError:
                        parser.error(f"Invalid page range: {args.pages}")
                else:
                    parser.error(f"Invalid page range: {args.pages}. Use '1-5' or '3'.")

    for path in args.files:
        if not path.exists():
            print(f"  Skipping: {path} not found")
            continue
        if path.suffix.lower() != ".pdf":
            print(f"  Skipping: {path} not a PDF")
            continue

        output = args.output if args.output and len(args.files) == 1 else None
        pdf_to_markdown(path, output, page_range=page_range, text_only=args.text_only)
