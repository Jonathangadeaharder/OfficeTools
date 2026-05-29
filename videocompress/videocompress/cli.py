import argparse
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from .compress import compress_video


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="videocompress",
        description="Compress video files using ffmpeg",
    )
    parser.add_argument("files", nargs="+", type=Path, help="Video file(s) to compress")
    parser.add_argument(
        "-o", "--output", type=Path, help="Output path (single file only)"
    )
    parser.add_argument(
        "-crf",
        "--crf",
        type=int,
        default=28,
        help="Constant Rate Factor for quality, 0-51 (default: 28)",
    )
    parser.add_argument(
        "--preset",
        type=str,
        default="medium",
        choices=[
            "ultrafast",
            "superfast",
            "veryfast",
            "faster",
            "fast",
            "medium",
            "slow",
            "slower",
            "veryslow",
        ],
        help="FFmpeg preset for compression speed/quality (default: medium)",
    )
    parser.add_argument(
        "--codec",
        type=str,
        default="libx264",
        choices=["libx264", "libx265", "hevc"],
        help="Video codec to use (default: libx264)",
    )
    parser.add_argument(
        "--hw",
        action="store_true",
        help="Use hardware-accelerated encoding (macOS VideoToolbox)",
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
                compress_video,
                path,
                output,
                crf=args.crf,
                preset=args.preset,
                codec=args.codec,
                hw=args.hw,
            )
            futures[f] = path

        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                print(f"  ERROR on {futures[f].name}: {e}")
