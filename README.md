# OfficeTools

Collection of CLI and GUI tools for media processing: PDF, audio, video.

## Tools

| Tool | Description |
|------|-------------|
| `pdf2md` | PDF to Markdown conversion |
| `pdfcompress` | PDF compression |
| `pdfconcat` | PDF concatenation |
| `pdfsplit` | PDF splitting |
| `pdfocr` | PDF OCR |
| `pdfgui` | PDF tools GUI |
| `audiocompress` | Audio compression |
| `audioconvert` | Audio format conversion |
| `audiocrop` | Audio cropping |
| `audiogui` | Audio tools GUI |
| `mp4audio` | MP4 audio extraction |
| `mp4subs` | MP4 subtitle extraction |
| `videocrop` | Video cropping |
| `videocompress` | Video compression |
| `videogui` | Video tools GUI |

## Quick Start

```bash
uv sync
uv run <tool-name> --help
```

## Development

```bash
uvx ruff check
uvx ruff format
uvx pyright
uv run pytest
```
