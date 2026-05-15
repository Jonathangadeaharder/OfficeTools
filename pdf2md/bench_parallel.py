"""Benchmark parallel pdf2md — tests 4pg and 16pg PDFs."""

import multiprocessing as mp
import time
from pathlib import Path

TESTS = [
    (Path("/tmp/bench_test.pdf"), 4),
    (Path("/tmp/bench_16.pdf"), 16),
]


def worker(pages: tuple[int, int], pdf: Path, result_queue: mp.Queue, worker_id: int):
    import logging
    import platform
    import warnings

    logging.basicConfig(level=logging.WARNING)
    warnings.filterwarnings("ignore")
    IS_AS = platform.system() == "Darwin" and platform.machine() == "arm64"
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import VlmConvertOptions, VlmPipelineOptions
    from docling.datamodel.settings import settings as docling_settings
    from docling.datamodel.vlm_engine_options import (
        MlxVlmEngineOptions,
        TransformersVlmEngineOptions,
    )
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.pipeline.vlm_pipeline import VlmPipeline

    docling_settings.perf.page_batch_size = 32
    eo = MlxVlmEngineOptions() if IS_AS else TransformersVlmEngineOptions()
    vlm_opts = VlmConvertOptions.from_preset(
        "granite_docling", engine_options=eo, scale=1.0
    )
    vlm_opts.model_spec.max_new_tokens = 2048
    po = VlmPipelineOptions(vlm_options=vlm_opts)
    conv = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=VlmPipeline, pipeline_options=po
            )
        }
    )
    t0 = time.perf_counter()
    result = conv.convert(pdf, page_range=pages)
    elapsed = time.perf_counter() - t0
    result_queue.put(
        {
            "worker": worker_id,
            "md": result.document.export_to_markdown(),
            "time": elapsed,
        }
    )


def sequential(pdf: Path):
    import logging
    import platform
    import warnings

    logging.basicConfig(level=logging.WARNING)
    warnings.filterwarnings("ignore")
    IS_AS = platform.system() == "Darwin" and platform.machine() == "arm64"
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import VlmConvertOptions, VlmPipelineOptions
    from docling.datamodel.settings import settings as docling_settings
    from docling.datamodel.vlm_engine_options import (
        MlxVlmEngineOptions,
        TransformersVlmEngineOptions,
    )
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.pipeline.vlm_pipeline import VlmPipeline

    docling_settings.perf.page_batch_size = 32
    eo = MlxVlmEngineOptions() if IS_AS else TransformersVlmEngineOptions()
    vlm_opts = VlmConvertOptions.from_preset(
        "granite_docling", engine_options=eo, scale=1.0
    )
    vlm_opts.model_spec.max_new_tokens = 2048
    po = VlmPipelineOptions(vlm_options=vlm_opts)
    conv = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=VlmPipeline, pipeline_options=po
            )
        }
    )
    t0 = time.perf_counter()
    result = conv.convert(pdf)
    elapsed = time.perf_counter() - t0
    return result.document.export_to_markdown(), elapsed, len(result.pages)


def run_parallel(pdf: Path, n_pages: int, n_workers: int):
    pages_per = n_pages // n_workers
    ranges = []
    start = 1
    for w in range(n_workers):
        end = start + pages_per - 1
        if w == n_workers - 1:
            end = n_pages
        ranges.append((start, end))
        start = end + 1

    ctx = mp.get_context("spawn")
    q = ctx.Queue()
    procs = []
    t0 = time.perf_counter()
    for wid, rng in enumerate(ranges):
        p = ctx.Process(target=worker, args=(rng, pdf, q, wid))
        procs.append(p)
        p.start()

    results = [q.get() for _ in procs]
    for p in procs:
        p.join()
    wall = time.perf_counter() - t0

    results.sort(key=lambda r: r["worker"])
    md = "\n\n".join(r["md"] for r in results)
    max_wt = max(r["time"] for r in results)
    return md, wall, max_wt, results


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    print(
        f"{'PDF pages':>10} {'workers':>8} {'wall(s)':>9} {'s/pg':>7} {'speedup':>8} {'max_wkr':>9}"
    )
    print("-" * 55)

    for pdf, npages in TESTS:
        md_seq, t_seq, _ = sequential(pdf)
        print(
            f"{npages:>10} {'1 (seq)':>8} {t_seq:>9.2f} {t_seq / npages:>7.2f} {'1.00x':>8} {'-':>9}"
        )

        for nw in [2, 4]:
            md_par, wall, max_wt, _ = run_parallel(pdf, npages, nw)
            speedup = t_seq / wall
            print(
                f"{npages:>10} {nw:>8} {wall:>9.2f} {wall / npages:>7.2f} {speedup:>7.2f}x {'-':>9}"
            )
