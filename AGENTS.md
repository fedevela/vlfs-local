# AGENTS.md

This file serves as the operational memory and structural map of the LLM Council MD Archiver (VLFS System).

## Architecture & Executable Structure

The Virtualized Log-Structured File System (VLFS) is split into two primary workspaces/packages:

### 1. `vlfs_core` (The Foundation)
Responsible for raw data ingestion, chunking, embedding, and semantic persistence.

- **`constants.py`**: Stable definitions (e.g., model names, `DB_FILENAME`).
- **`config.py`**: Loads configuration from `vlfs_config.json` with fallback to environment variables.
- **`llm.py` (`LLMAdapter`)**: Adapts and abstracts LLM text generation (L1 summaries) and embeddings, supporting `LOCAL_DEV_MODE` (via CLI/ollama), Google GenAI, and OpenAI providers based on config.
- **`db.py`**: Initializes the `sqlite-vec` vector database for fast similarity searches.
- **`ignore.py`**: Evaluates `.gitignore` syntax via `pathspec` to skip irrelevant files.
- **`text.py`**: Utilities for segmenting and chunking plain text.
- **`indexer.py` (`process_file`, `sync_memories`)**: The core ingestion engine. Scans directories, extracts raw content, chunk-embeds it into L0 memory, generates an L1 `.meta.yaml` abstract, and persists it.

### 2. `vlfs_mcp` (The Agent Interface)
Wraps the core mechanics into standard MCP Tools (via FastMCP) adhering to the OpenViking standard, allowing agents to search and reflect efficiently using the `viking://` URI scheme.

- **`config.py`**: Proxies the execution boundary context configuration from `vlfs_core`.
- **`utils.py`**: Resolves `viking://` URIs to absolute local paths, mapping `viking://resources/` to the workspace root and isolating `viking://user/memories/` and `viking://skills/` within a hidden `.viking/` directory.
- **`server.py`**: Bootstraps the `FastMCP` server, registers all tool routes, and maps native OpenViking resources.
- **`resources.py` (Native Resources)**:
  - `viking://resources/{domain}`: External, static knowledge (maps to workspace root).
  - `viking://user/memories/{session_id}`: Agent cognition layer (maps to `.viking/user/memories/`).
  - `viking://skills/{tool_name}`: Callable capabilities or instructions (maps to `.viking/skills/`).
- **`memory_tools.py` (Cognition & Retrieval)**:
  - `memory_recall()`: Semantic searches over long-term `viking://` memory partitions, injecting L1/L2 results.
  - `memory_store()`: Manually writes raw text to an OpenViking session, triggering background extraction loop.
  - `memory_sync()`: Bulk ingestion for specific OpenViking URIs (maps to `ov ingest`).
  - `memory_forget()`: Prunes or deletes specific conversational memories to maintain context hygiene.
- **`fs_tools.py` (Filesystem Navigation & Search)**:
  - `fs_ls()`: Navigates the OpenViking virtual filesystem directory tree using standard POSIX tools to discover available context.
  - `fs_grep()`: Exact Text Search (Keyword matching) across the virtual filesystem using `grep`, mapping to `ov grep`.

## Operational Contracts & Workflows

- **Test Contracts**: E2E testing (`src/e2e/test_e2e.py`) asserts the full OpenViking process flow (Pre-sync -> FS LS -> Memory Store -> Memory Recall -> Memory Forget). The `VLFS_SYNC_ASYNC` env variable allows async ingestion to be deactivated for deterministic assertions.
- **Configuration**: Uses a structured JSON format (`vlfs_config.json`) alongside `.env` fallbacks for model and storage setup as the primary source of truth. By default, `viking://skills/` and `viking://user/memories/` map to hidden folders inside the workspace (`.viking/skills` and `.viking/user/memories`), but they are fully configurable as independent partitions in `vlfs_config.json`.
- **API Hoisting**: Both `vlfs_core` and `vlfs_mcp` employ minimalistic `__init__.py` files containing only explicit `__all__` exports. Internal file structure remains opaque to external consumers.
