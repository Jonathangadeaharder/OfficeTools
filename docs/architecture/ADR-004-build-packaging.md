# ADR-004: Build, Packaging and Distribution

**Status:** Accepted

**Authors:** Jonathan Gadea Harder
**Reviewers:** Jonathan Gadea Harder
**Context:** Tools need to be distributed as installable Python packages. The build system must support wheel creation for uv tool install, and the process must be automatable in CI.

**Decision:** Use Hatchling as the build backend (configured in each tool's pyproject.toml). Each tool builds independently via `uv build`. The orchestrator wraps uv build + uv tool install. No central package index — tools are installed from local wheels.

**Consequences:**
- Positive: Hatchling is the modern Python build backend with minimal config
- Positive: uv build handles wheel creation, no setuptools needed
- Negative: No version pinning across tools (each has independent version)
- Negative: Local wheel install means no version resolution across tools

**Alternatives:**
- Setuptools: Legacy, more verbose config
- Poetry: Heavier, uv already handles dependency management
- PDM: Additional tool to learn, uv preferred
