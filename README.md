# OfficeTools

Collection of CLI and GUI tools for PDF, audio, video, and ebook processing. Each tool is an independent Python package with its own `pyproject.toml`.

## Tools

| Tool | Description |
|------|-------------|
| `pdf2md` | PDF to Markdown conversion |
| `pdfcompress` | PDF compression |
| `pdfconcat` | PDF concatenation |
| `pdfsplit` | PDF splitting |
| `pdfocr` | PDF OCR |
| `docgui` | PDF tools GUI |
| `ebooktool` | Ebook conversion/processing |
| `mp4audio` | MP4 audio extraction |
| `mp4subs` | MP4 subtitle extraction |
| `videocompress` | Video compression |
| `videogui` | Video tools GUI |

## Quick Start

Each tool is standalone. Run individually:

```bash
cd <tool-name>
uv sync
uv run <tool-name> --help
```

The `officetools/` package is a shared utility library used by multiple tools.

## Development

```bash
uvx ruff check
uvx ruff format
uvx pyright
uv run pytest
```
