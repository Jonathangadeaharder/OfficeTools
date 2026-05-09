import argparse
from pathlib import Path

from .extract import extract_audio


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mp4audio",
        description="Extract m4a audio from mp4 files (stream copy by default)",
    )
    parser.add_argument(
        "files", nargs="+", type=Path, help="MP4 file(s) to extract audio from"
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="Output path (single file only)"
    )
    parser.add_argument(
        "--reencode",
        action="store_true",
        help="Re-encode audio to AAC instead of stream copy",
    )
    parser.add_argument(
        "--bitrate",
        type=int,
        default=128,
        help="AAC bitrate in kbps (default: 128, only with --reencode)",
    )
    args = parser.parse_args()

    if args.output and len(args.files) > 1:
        parser.error("-o/--output can only be used with a single input file")

    for path in args.files:
        if not path.exists():
            print(f"  Skipping: {path} not found")
            continue
        if path.suffix.lower() != ".mp4":
            print(f"  Skipping: {path} not an MP4")
            continue

        output = args.output if args.output and len(args.files) == 1 else None
        extract_audio(
            path,
            output,
            reencode=args.reencode,
            bitrate=args.bitrate,
        )
