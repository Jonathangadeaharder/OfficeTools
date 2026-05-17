# OfficeTools — Python CLI Tool Monorepo

## Overview

OfficeTools is a monorepo of Python CLI utilities for document and media processing. Each tool is an independent package with its own dependencies, managed under a unified orchestrator CLI.

## Key Decisions

| Decision | Choice |
|----------|--------|
| Package manager | uv (all operations) |
| Build backend | Hatchling |
| Tool isolation | Separate pyproject.toml per tool |
| Orchestrator | officetools CLI (install/update/list) |
| Installation | uv tool install from local wheels |

## Directory Structure

```
OfficeTools/
├── officetools/         # Orchestrator package
│   ├── __init__.py
│   └── cli.py           # install, update, list commands
├── pdf2md/              # PDF to Markdown converter
│   ├── pyproject.toml
│   └── pdf2md/
├── pdfcompress/         # PDF compression tool
│   ├── pyproject.toml
│   └── pdfcompress/
├── pdfconcat/           # PDF concatenation
├── pdfocr/              # PDF OCR processing
├── pdfsplit/            # PDF splitting
├── pdfgui/              # PDF GUI frontend
├── mp4audio/            # MP4 audio extraction
├── mp4subs/             # MP4 subtitle extraction
└── videogui/            # Video processing GUI
```

## Tool Lifecycle

1. **Development**: `cd tool/ && uv add <dep>` (per-tool dependencies)
2. **Build**: `uv build` in tool directory → produces wheel in dist/
3. **Install**: `uv tool install dist/*.whl --force`
4. **Mass install**: `officetools install` (discovers + installs all tools)
5. **Update**: `officetools update` (rebuilds + reinstalls all)

## Discovery Logic

```python
def _find_tools() -> list[Path]:
    tools = []
    for entry in sorted(OFFICE_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        toml = entry / "pyproject.toml"
        if not toml.exists():
            continue
        content = toml.read_text()
        if "[project.scripts]" not in content:
            continue
        if entry.name == "officetools":
            continue
        tools.append(entry)
    return tools
```
