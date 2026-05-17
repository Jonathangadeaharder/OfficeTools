# ADR-001: Python Monorepo with uv

**Status:** Accepted

**Context:** OfficeTools is a collection of CLI utilities for PDF manipulation, video processing, audio extraction, and subtitle management. Each tool has its own dependencies and could be installed independently. The project needs a consistent build and dependency management approach across all tools.

**Decision:** Organize as a Python monorepo using `uv` for package management. Each tool is a separate directory with its own `pyproject.toml`, dependencies, and entry points. The `officetools/` package provides a unified CLI orchestrator that discovers and installs all tools.

**Consequences:**
- Positive: Each tool has isolated dependencies (no version conflicts)
- Positive: Users can install individual tools or all tools via the orchestrator
- Positive: uv provides fast dependency resolution and locking
- Negative: Duplicate dev tooling config across tools
- Negative: Slightly more complex CI than a single-package project

**Alternatives:**
- Single package with optional dependencies: Dependency conflicts over time
- Separate repositories per tool: Higher maintenance overhead, no shared patterns
