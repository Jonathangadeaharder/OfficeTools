import argparse
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
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
    parser.add_argument(
        "--sw",
        action="store_true",
        dest="sw_encode",
        help="Force software AAC encoding even on macOS",
    )
    args = parser.parse_args()

    if args.output and len(args.files) > 1:
        parser.error("-o/--output can only be used with a single input file")

    valid = []
    for path in args.files:
        if not path.exists():
            print(f"  Skipping: {path} not found")
            continue
        if path.suffix.lower() != ".mp4":
            print(f"  Skipping: {path} not an MP4")
            continue
        valid.append(path)

    if not valid:
        return

    cpu = os.cpu_count() or 1
    max_workers = max(1, min(int(cpu**0.5), len(valid)))

    with ProcessPoolExecutor(max_workers=max_workers) as pool:
        futures = {}
        for path in valid:
            output = args.output if args.output and len(valid) == 1 else None
            f = pool.submit(
                extract_audio,
                path,
                output,
                reencode=args.reencode,
                bitrate=args.bitrate,
                sw_encode=args.sw_encode,
            )
            futures[f] = path

        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f"  ERROR on {futures[f].name}: {e}")
