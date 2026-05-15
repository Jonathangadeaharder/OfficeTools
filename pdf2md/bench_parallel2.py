"""Quick parallel benchmark — 16 pages, 2 workers."""

import multiprocessing as mp
import time
from pathlib import Path

PDF = Path("/tmp/bench_16.pdf")
N = 16


def worker(pages: tuple[int, int], pdf: Path, q: mp.Queue, wid: int):
    import logging
    import platform
    import warnings

    logging.basicConfig(level=logging.WARNING)
    warnings.filterwarnings("ignore")
    IS_AS = platform.system() == "Darwin" and platform.machine() == "arm64"
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import VlmConvertOptions, VlmPipelineOptions
    from docling.datamodel.settings import settings as docling_settings
    from docling.datamodel.vlm_engine_options import MlxVlmEngineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.pipeline.vlm_pipeline import VlmPipeline

    docling_settings.perf.page_batch_size = 32
    eo = MlxVlmEngineOptions() if IS_AS else None
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
    q.put(
        {
            "wid": wid,
            "md": result.document.export_to_markdown(),
            "pages": pages,
            "t": elapsed,
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
    from docling.datamodel.vlm_engine_options import MlxVlmEngineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.pipeline.vlm_pipeline import VlmPipeline

    docling_settings.perf.page_batch_size = 32
    eo = MlxVlmEngineOptions() if IS_AS else None
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
    return result.document.export_to_markdown(), elapsed


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)

    print("=== Sequential ===")
    md_seq, t_seq = sequential(PDF)
    print(f"  {t_seq:.2f}s ({t_seq / N:.2f}s/page) md_len={len(md_seq)}")

    for nw in [2, 3]:
        pages_per = N // nw
        ranges = []
        start = 1
        for w in range(nw):
            end = start + pages_per - 1
            if w == nw - 1:
                end = N
            ranges.append((start, end))
            start = end + 1

        ctx = mp.get_context("spawn")
        q = ctx.Queue()
        procs = []
        t0 = time.perf_counter()
        for wid, rng in enumerate(ranges):
            p = ctx.Process(target=worker, args=(rng, PDF, q, wid))
            procs.append(p)
            p.start()

        results = [q.get() for _ in procs]
        for p in procs:
            p.join()
        wall = time.perf_counter() - t0

        results.sort(key=lambda r: r["wid"])
        md_par = "\n\n".join(r["md"] for r in results)

        print(f"\n=== Parallel ({nw} workers) ===")
        print(f"  Wall: {wall:.2f}s ({wall / N:.2f}s/page) speedup={t_seq / wall:.2f}x")
        for r in results:
            print(f"    W{r['wid']} p{r['pages']}: {r['t']:.2f}s")
        print(
            f"  md_match: {len(md_par)} == {len(md_seq)}: {len(md_par) == len(md_seq)}"
        )
