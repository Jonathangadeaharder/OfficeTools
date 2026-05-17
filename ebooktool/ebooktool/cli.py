import argparse
from pathlib import Path

from .convert import convert


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ebooktool",
        description="Convert ebook formats (epub, mobi) to/from md, txt, pdf.",
    )
    parser.add_argument("input", type=Path, help="Input file")
    parser.add_argument("-o", "--output", type=Path, help="Output path (detected from extension if omitted)")
    parser.add_argument("--to", choices=["md", "txt", "pdf", "epub", "mobi"], help="Target format (auto-detected from --output or input basename)")
    args = parser.parse_args()

    input_path = args.input
    if not input_path.exists():
        print(f"  Skipping: {input_path} not found")
        return

    ext = args.to
    if args.output:
        ext = args.output.suffix.lstrip(".")
    elif not ext:
        ext = "md"

    if ext not in ("md", "txt", "pdf", "epub", "mobi"):
        print(f"  Unsupported output format: {ext}")
        return

    output_path = args.output or input_path.with_suffix(f".{ext}")
    convert(input_path, output_path)
