import logging
import warnings
from pathlib import Path

import pymupdf
import pymupdf4llm

# pymupdf4llm's OCR feature computation can hit empty slices on
# image-only regions; the noise is harmless.
warnings.filterwarnings("ignore", category=RuntimeWarning)

logging.getLogger("pymupdf4llm").setLevel(logging.WARNING)


def _emit_progress(pct: int) -> None:
    print(f"  PROGRESS: {pct}", flush=True)


def pdf_to_markdown(
    input_path: Path,
    output_path: Path | None = None,
    page_range: tuple[int, int] | None = None,
) -> Path:
    print(f"\n  [PDF2MD] Conversion: {input_path.name}...", flush=True)
    _emit_progress(0)

    if output_path is None:
        output_path = input_path.with_suffix(".md")

    with pymupdf.open(input_path) as doc:
        doc_pages = doc.page_count

    pages: list[int] | None = None
    if page_range is not None:
        start, end = page_range
        # User-facing ranges are 1-based and inclusive.
        first = max(start - 1, 0)
        last = min(end - 1, doc_pages - 1)
        if first > last or first >= doc_pages:
            raise ValueError(
                f"Page range {start}-{end} out of bounds "
                f"({input_path.name} has {doc_pages} pages)"
            )
        pages = list(range(first, last + 1))

    _emit_progress(10)

    md = pymupdf4llm.to_markdown(str(input_path), pages=pages, write_images=False)
    # Return type is str | list[dict] union in the lib; without page_chunks
    # it is always a str, but the annotation is not precise.
    assert isinstance(md, str), f"unexpected to_markdown result: {type(md)}"

    _emit_progress(90)
    print("  [PDF2MD] Exporting markdown...", flush=True)

    output_path.write_text(md, encoding="utf-8")

    md_kb = len(md.encode("utf-8")) / 1024
    print(
        f"  ✓ {input_path.name} -> {output_path.name} ({md_kb:.1f} KB markdown)",
        flush=True,
    )
    _emit_progress(100)

    return output_path
