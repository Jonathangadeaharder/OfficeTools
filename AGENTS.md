# AGENTS.md — OfficeTools

## Build & Test Commands

```bash
# Per-tool (run from tool directory, e.g. cd pdfcompress)
uv sync
uv run pytest
uvx ruff check
uvx ruff format
uvx pyright
```

## PR Instructions

- Branch: feature/*, fix/*, chore/*
- Title: `<type>(<scope>): <description>`
- Types: feat, fix, docs, style, refactor, perf, test, build, ci, chore
- Run `uvx ruff check` before committing
- One logical change per commit
