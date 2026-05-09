import argparse
from pathlib import Path

from .compress import compress_pdf


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="pdfcompress",
        description="Blazingly fast PDF compression using Ghostscript + pikepdf",
    )
    parser.add_argument(
        "files", nargs="+", type=Path, help="PDF file(s) to compress"
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="Output path (single file only)"
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=85,
        help="JPEG quality 1-100 (default: 85)",
    )
    parser.add_argument(
        "--aggressive",
        action="store_true",
        help="Max compression: 72 DPI images",
    )
    parser.add_argument(
        "--light",
        action="store_true",
        help="Lossless structural compression only (pikepdf, no Ghostscript)",
    )
    args = parser.parse_args()

    if args.output and len(args.files) > 1:
        parser.error("-o/--output can only be used with a single input file")

    for path in args.files:
        if not path.exists():
            print(f"  Skipping: {path} not found")
            continue
        if path.suffix.lower() != ".pdf":
            print(f"  Skipping: {path} not a PDF")
            continue

        output = args.output if args.output and len(args.files) == 1 else None
        compress_pdf(
            path,
            output,
            quality=args.quality,
            aggressive=args.aggressive,
            light=args.light,
        )
