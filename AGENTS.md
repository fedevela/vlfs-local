# AGENTS.md

This file serves as the operational memory and structural map of the LLM Council MD Archiver (VLFS System).

## Architecture & Executable Structure

The Virtualized Log-Structured File System (VLFS) is split into two primary workspaces/packages:

### 1. `vlfs_core` (The Foundation)
Responsible for raw data ingestion, chunking, embedding, and semantic persistence.

- **`constants.py`**: Stable definitions (e.g., model names, `DB_FILENAME`).
- **`llm.py` (`LLMAdapter`)**: Adapts and abstracts LLM text generation (L1 summaries) and embeddings, supporting both `LOCAL_DEV_MODE` (via CLI/ollama) and direct `google-genai` SDK.
- **`db.py`**: Initializes the `sqlite-vec` vector database for fast similarity searches.
- **`ignore.py`**: Evaluates `.gitignore` syntax via `pathspec` to skip irrelevant files.
- **`text.py`**: Utilities for segmenting and chunking plain text.
- **`indexer.py` (`process_file`, `sync_memories`)**: The core ingestion engine. Scans directories, extracts raw content, chunk-embeds it into L0 memory, generates an L1 `.meta.yaml` abstract, and persists it.

### 2. `vlfs_mcp` (The Agent Interface)
Wraps the core mechanics into standard MCP Tools (via FastMCP), allowing agents to search and reflect efficiently.

- **`config.py`**: Defines the `WORKING_ROOT_DIR` execution boundary context.
- **`server.py`**: Bootstraps the `FastMCP` server and registers all tool routes.
- **`ingestion_tools.py`**:
  - `sync_all_memories()`: Syncs the workspace.
  - `ingest_memory_file()`: Forces sync on a single artifact.
- **`search_tools.py` (Tiered Retrieval)**:
  - `search_l0_memory()`: POSIX-based filename and extension searches (raw boundaries).
  - `search_l1_grep()`: Rapid keyword/metadata scans against `.meta.yaml` abstracts.
  - `search_l1_semantic()`: Vector-based semantic fallback over L0 chunks.
- **`l2_tools.py` (Reflection)**:
  - `save_l2_memory()`: Commits cross-cutting insights, architectural facts, and agent state as standard markdown within the VLFS, subsequently triggering async ingestion.
  - `read_l2_memory()`: Retrieves explicit long-term reflections.

## Operational Contracts & Workflows

- **Test Contracts**: E2E testing (`src/e2e/test_e2e.py`) asserts the full process flow (Ingestion -> L1 Summary Gen -> L1 Grep -> L0 Search -> L2 Save/Read). The `VLFS_SYNC_ASYNC` env variable allows async ingestion to be deactivated for deterministic assertions.
- **API Hoisting**: Both `vlfs_core` and `vlfs_mcp` employ minimalistic `__init__.py` files containing only explicit `__all__` exports. Internal file structure remains opaque to external consumers.
