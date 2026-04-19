# VLFS MCP

This module is the **Agent Interface** of the Virtualized Log-Structured File System (VLFS). It wraps the foundational capabilities of `vlfs_core` into standard Model Context Protocol (MCP) Tools and Resources via `FastMCP`. It adheres strictly to the OpenViking standard, allowing autonomous agents to search, reflect, and navigate efficiently.

## Domain Language

- **MCP (Model Context Protocol)**: The standardized communication layer for exposing tools and resources to LLM agents.
- **OpenViking Standard**: The architectural paradigm dictating the use of the `viking://` URI scheme to virtualize access to workspace context, memories, and skills.
- **Cognition Layer**: The `viking://user/memories/` partition where agents store long-term reflections and episodic context.
- **L1/L2 Injection**: The process of returning summarized (L1) and detailed (L2/Markdown) content into the agent's context window during retrieval.

### The Discovery Hierarchy
To prevent context window exhaustion, the OpenViking standard enforces a strict discovery funnel:
- **L0 Layer (Discovery & Metadata)**: Verbs `ov ls`, `ov tree`. Returns only the structural map. Uses minimal tokens to see file names and directory trees without loading any actual context.
- **L1 Layer (Scanning & Routing)**: Verb `ov find`. Semantic vector search. It does not scan raw text; it queries the vector database for L1 Summaries. Used to "fuzzy search" concepts without committing to a deep read.
- **L2 Layer (Deep Reading & Exact Matching)**: Verbs `ov cat`, `ov grep`. Forces the system to access the raw, unadulterated Markdown files. Use only when you have identified a specific file via L0/L1.

## Core Objects & Modules

- **`server.py`**: Bootstraps the `FastMCP` server, registers all tools and native resources, and acts as the entry point for the MCP host.
- **`resources.py`**: Maps native OpenViking URIs to read-only MCP resources:
  - `viking://resources/{domain}`: Exposes external, static knowledge from the workspace root.
  - `viking://user/memories/{session_id}`: Aggregates and exposes the cognition layer for a specific session.
  - `viking://skills/{tool_name}`: Exposes callable capabilities and static instructions.
- **`memory_tools.py`**: Provides the cognition and retrieval toolset:
  - `memory_recall`: Executes a semantic similarity search against the `sqlite-vec` database (matching the query embedding against L1 abstract embeddings) and returns relevant file paths and previews. Supports path prefix filtering via `targetUri`.
  - `memory_store`: Manually writes raw text to a specified `viking://` URI and triggers the `vlfs_core` ingestion loop (synchronously or asynchronously based on `VLFS_SYNC_ASYNC`).
  - `memory_forget`: Prunes conversational memories by deleting files based on exact URI or a keyword search.
  - `memory_sync`: Triggers bulk ingestion for a specified directory.
- **`fs_tools.py`**: Provides standard filesystem navigation:
  - `fs_ls`: Uses POSIX `ls` or `find` to navigate the virtual filesystem directory tree and map results back to `viking://` URIs.
  - `fs_grep`: Uses POSIX `grep` for exact text (keyword) matching across the virtual filesystem.
- **`utils.py` & `config.py`**: Proxies execution boundary context configuration from `vlfs_core` and ensures proper bidirectional translation of `viking://` URIs.

## Behavior & Workflows

1. **Tool Execution**: When an agent invokes an MCP tool, the module translates the requested `viking://` URIs to absolute paths, executes the underlying command (database query, filesystem POSIX command, or `vlfs_core` function), and maps the outputs back to virtual URIs before returning.
2. **Semantic Retrieval (`memory_recall`)**: Translates the user's query into an embedding vector, performs a threshold-based distance search in `sqlite-vec`, and injects the resulting file URIs alongside content previews back to the agent.
3. **Resource Provisioning**: Exposes specific directories as structured, read-only text resources, allowing agents to ingest entire sessions or skill definitions seamlessly.