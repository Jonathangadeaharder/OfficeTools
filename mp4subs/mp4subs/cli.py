import argparse
from pathlib import Path

from .subs import add_subtitles


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mp4subs",
        description="Add SRT subtitles to MP4 (soft sub by default, --force to hard-burn)",
    )
    parser.add_argument("video", type=Path, help="MP4 video file")
    parser.add_argument("subs", type=Path, help="SRT subtitle file")
    parser.add_argument("-o", "--output", type=Path, help="Output path")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Hard-burn subtitles into video frames",
    )
    parser.add_argument(
        "--language",
        default="eng",
        help="Subtitle track language tag (default: eng)",
    )
    parser.add_argument(
        "--crf",
        type=int,
        default=23,
        help="H.264 CRF value for hard burn (default: 23, ignored with hardware encode)",
    )
    parser.add_argument(
        "--sw",
        action="store_true",
        dest="sw_encode",
        help="Force software encoding (libx264) even on Apple Silicon",
    )
    args = parser.parse_args()

    if not args.video.exists():
        parser.error(f"Video file not found: {args.video}")
    if not args.subs.exists():
        parser.error(f"Subtitle file not found: {args.subs}")
    if args.video.suffix.lower() != ".mp4":
        parser.error(f"Video must be an MP4 file, got: {args.video.suffix}")
    if args.subs.suffix.lower() != ".srt":
        parser.error(f"Subtitle must be an SRT file, got: {args.subs.suffix}")

    add_subtitles(
        args.video,
        args.subs,
        args.output,
        force=args.force,
        language=args.language,
        crf=args.crf,
        sw_encode=args.sw_encode,
    )
