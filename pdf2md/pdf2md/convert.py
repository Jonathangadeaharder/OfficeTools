import logging
import platform
import re
import warnings
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import VlmConvertOptions, VlmPipelineOptions
from docling.datamodel.vlm_engine_options import (
    MlxVlmEngineOptions,
    TransformersVlmEngineOptions,
)
from docling.datamodel.settings import settings as docling_settings
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
from docling.pipeline.vlm_pipeline import VlmPipeline

docling_settings.perf.page_batch_size = 32

warnings.filterwarnings("ignore", message="The `use_fast` parameter is deprecated")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

IS_APPLE_SILICON = platform.system() == "Darwin" and platform.machine() == "arm64"


def _emit_progress(pct: int) -> None:
    print(f"  PROGRESS: {pct}", flush=True)


class _DoclingProgressHandler(logging.Handler):
    _PATTERN = re.compile(r"Finished converting pages (\d+)/(\d+) time=")

    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self._total_pages = 0

    def emit(self, record: logging.LogRecord) -> None:
        if record.name != "docling.pipeline.base_pipeline":
            return
        m = self._PATTERN.search(record.getMessage())
        if not m:
            return
        current = int(m.group(1))
        if self._total_pages == 0:
            self._total_pages = int(m.group(2))
        if self._total_pages <= 0:
            return
        pct = 10 + int((current / self._total_pages) * 80)
        _emit_progress(pct)


def pdf_to_markdown(
    input_path: Path,
    output_path: Path | None = None,
    page_range: tuple[int, int] | None = None,
    text_only: bool = False,
) -> Path:
    label = "Standard" if text_only else "VLM"
    print(f"\n  [DOCLING] {label} conversion: {input_path.name}...", flush=True)
    _emit_progress(0)

    if output_path is None:
        output_path = input_path.with_suffix(".md")

    if text_only:
        conv = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_cls=StandardPdfPipeline),
            }
        )
    else:
        engine_options = (
            MlxVlmEngineOptions()
            if IS_APPLE_SILICON
            else TransformersVlmEngineOptions()
        )

        vlm_options = VlmConvertOptions.from_preset(
            "granite_docling",
            engine_options=engine_options,
            scale=1.0,
        )
        vlm_options.model_spec.max_new_tokens = 1024
        vlm_options.batch_size = 2

        pipeline_options = VlmPipelineOptions(vlm_options=vlm_options)
        conv = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_cls=VlmPipeline,
                    pipeline_options=pipeline_options,
                ),
            }
        )

    _emit_progress(10)

    handler = _DoclingProgressHandler()
    pipeline_logger = logging.getLogger("docling.pipeline.base_pipeline")
    original_level = pipeline_logger.level
    pipeline_logger.addHandler(handler)
    pipeline_logger.setLevel(logging.DEBUG)

    try:
        if page_range is not None:
            result = conv.convert(input_path, page_range=page_range)
        else:
            result = conv.convert(input_path)
    finally:
        pipeline_logger.removeHandler(handler)
        pipeline_logger.setLevel(original_level)

    print("  [DOCLING] Exporting to markdown...", flush=True)
    _emit_progress(90)
    md = result.document.export_to_markdown()

    output_path.write_text(md, encoding="utf-8")

    md_kb = len(md.encode("utf-8")) / 1024
    print(
        f"  ✓ {input_path.name} -> {output_path.name} ({md_kb:.1f} KB markdown)",
        flush=True,
    )
    _emit_progress(100)

    return output_path
