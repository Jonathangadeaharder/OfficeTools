# ADR-005: Tool Discovery and Installation Mechanism

**Status:** Accepted

**Authors:** Jonathan Gadea Harder
**Reviewers:** Jonathan Gadea Harder
**Context:** The orchestrator must reliably discover all tool packages and install them. The discovery mechanism should not require manual registration of new tools.

**Decision:** The orchestrator discovers tools by iterating sibling directories of the officetools package root, looking for directories containing a `pyproject.toml` with `[project.scripts]`. The `OFFICE_ROOT` environment variable (defaulting to `~/projects/OfficeTools`) allows overriding the search path.

**Consequences:**
- Positive: Adding a new tool = creating a directory with pyproject.toml
- Positive: No central registry file to update
- Negative: Nested or renamed directories break discovery
- Negative: Tools outside the sibling structure require OFFICE_ROOT override

**Alternatives:**
- Manifest file listing all tools: Requires updates when adding tools
- Python package discovery (pkg_resources): Complex, slow
