# ADR-003: officetools Orchestrator CLI

**Status:** Accepted

**Authors:** Jonathan Gadea Harder
**Reviewers:** Jonathan Gadea Harder
**Context:** Users need a unified way to discover, install, and update all OfficeTools utilities. Without an orchestrator, each tool must be installed manually from its directory.

**Decision:** The `officetools` package provides a CLI with `install`, `update`, and `list` commands. It discovers all tool directories by scanning sibling directories for those with `[project.scripts]` in their `pyproject.toml`. The install command builds each tool with uv and installs it as a uv tool.

**Consequences:**
- Positive: Single command to install all tools: `officetools install`
- Positive: Tool discovery is automatic (no manual registry)
- Negative: Assumes flat directory structure (siblings of officetools/)
- Negative: uv tool install requires wheel builds — adds latency

**Alternatives:**
- Manual installation per tool: Tedious, error-prone
- Makefile: Platform-specific, less discoverable
