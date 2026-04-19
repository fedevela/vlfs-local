# AGENTS.md

This file serves as the top-level operational memory and structural map of the LLM Council MD Archiver (VLFS System).

## Architecture & Executable Structure

The Virtualized Log-Structured File System (VLFS) is a dual-package architecture. Detailed operational behavior, domain language, and module breakdowns are delegated to the `AGENTS.md` files within each package:

### 1. `vlfs_core` (The Foundation)
**Documentation:** `packages/vlfs_core/AGENTS.md`

Responsible for raw data ingestion, text processing, embedding, and semantic persistence.

*Key correction from legacy architecture: The system extracts raw content (L0 memory), generates a 1-2 sentence abstract (L1 summary), and creates vector embeddings of the **L1 abstract only** for semantic search. The raw L0 text is not chunk-embedded.*

### 2. `vlfs_mcp` (The Agent Interface)
**Documentation:** `packages/vlfs_mcp/AGENTS.md`

Wraps the core mechanics into standard MCP Tools (via FastMCP) adhering to the OpenViking standard. This allows agents to search, reflect, and navigate efficiently using the `viking://` URI scheme.

## Operational Contracts & Workflows

- **Test Contracts**: E2E testing (`src/e2e/test_e2e.py`) asserts the full OpenViking process flow (Pre-sync -> FS LS -> Memory Store -> Memory Recall -> Memory Forget). The `VLFS_SYNC_ASYNC` env variable allows async ingestion to be deactivated for deterministic assertions.
- **Configuration**: Uses a structured JSON format (`vlfs_config.json`) alongside `.env` fallbacks for model and storage setup as the primary source of truth. By default, `viking://skills/` and `viking://user/memories/` map to hidden folders inside the workspace (`.viking/skills` and `.viking/user/memories`), but they are fully configurable as independent partitions in `vlfs_config.json`.
- **API Hoisting**: Both `vlfs_core` and `vlfs_mcp` employ minimalistic `__init__.py` files containing only explicit `__all__` exports. Internal file structure remains opaque to external consumers.
