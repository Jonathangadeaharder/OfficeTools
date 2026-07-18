import argparse
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from .convert import SUPPORTED_FORMATS, convert_video


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="videoconvert",
        description="Convert video files between common formats using ffmpeg",
    )
    parser.add_argument("files", nargs="+", type=Path, help="Video file(s) to convert")
    parser.add_argument(
        "-f",
        "--format",
        required=True,
        choices=SUPPORTED_FORMATS,
        help="Target video format",
    )
    parser.add_argument(
        "-o", "--output", type=Path, help="Output path (single file only)"
    )
    parser.add_argument(
        "-c",
        "--copy",
        action="store_true",
        help="Stream copy (fast remux, no re-encode). "
        "Fails if codecs are incompatible with the target container.",
    )
    args = parser.parse_args()

    if args.output and len(args.files) > 1:
        parser.error("-o/--output can only be used with a single input file")

    valid = []
    for path in args.files:
        if not path.exists():
            print(f"  Skipping: {path} not found")
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
                convert_video,
                path,
                args.format,
                output,
                copy_streams=args.copy,
            )
            futures[f] = path

        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f"  ERROR on {futures[f].name}: {e}")
