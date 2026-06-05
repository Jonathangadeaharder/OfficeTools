# ADR-002: Individual Tool Isolation

**Status:** Accepted

**Authors:** Jonathan Gadea Harder
**Reviewers:** Jonathan Gadea Harder
**Context:** PDF tools (pdf2md, pdfcompress, pdfconcat, pdfocr, pdfsplit) and video tools (mp4audio, mp4subs, videogui, videocompress) have different dependencies. Pdf2md needs docling[vlm], fpdf2, and mlx-vlm, while video tools rely on system ffmpeg. Mixing all dependencies in one package causes bloat.

**Decision:** Each tool is a standalone Python package with its own `pyproject.toml`, dependency declarations, and `[project.scripts]` entry points. Tools share no runtime code between them — each is independently installable via `uv tool install`.

**Consequences:**
- Positive: Users only install what they need
- Positive: Dependency conflicts cannot propagate between tools
- Positive: Each tool can use its own Python version constraint
- Negative: Shared utilities (e.g., PDF helpers) must be duplicated or extracted as a library
- Negative: More pyproject.toml files to maintain

**Alternatives:**
- Monolithic package: Dependency bloat, conflicts
- Namespace packages: Complex setup, unclear boundaries
