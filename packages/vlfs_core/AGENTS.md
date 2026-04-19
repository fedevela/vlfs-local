# VLFS Core

This module is the **Foundation** of the Virtualized Log-Structured File System (VLFS). It is strictly responsible for raw data ingestion, text processing, embedding, and semantic persistence. It does not expose agent-facing tools directly; it provides the engine that powers them.

## Domain Language

- **L0 Memory**: The raw text content of files stored on disk.
- **L1 Abstract / Summary**: A 1-2 sentence semantic summary generated from the file's raw content.
- **Vector Embedding**: The mathematical representation of the L1 abstract, used for semantic search.
- **Sidecar (`.meta.yaml`)**: A metadata file created alongside the original file, tracking synchronization state, timestamps, and the generated L1 abstract.
- **`viking://` URI**: The unified resource identifier scheme used to map physical file paths to virtual partitions (`resources`, `user/memories`, `skills`).

## Core Objects & Modules

- **`config.py`**: The central configuration loader. It reads `vlfs_config.json` with fallbacks to environment variables to resolve storage paths (`resources`, `memories`, `skills`) and model providers.
- **`db.py`**: Manages the `sqlite-vec` vector database connection (`vlfs_index.db`). It defines the schema for `memories_meta` (storing file URIs) and the virtual table `vec_memories` (storing L1 embeddings).
- **`indexer.py`**: The ingestion engine.
  - `process_file`: Reads a file, generates an L1 abstract via the LLM, embeds the abstract, performs a delete-and-replace sync in the database, and writes the `.meta.yaml` sidecar.
  - `sync_memories`: Recursively scans storage paths for new or modified files (where the file is newer than its sidecar) and triggers `process_file`.
- **`llm.py` (`LLMAdapter`)**: A unified interface for interacting with Language Models. It abstracts away the differences between Google GenAI, OpenAI, and Local Dev Mode (`gemini-cli` / `ollama`).
- **`ignore.py`**: Uses `pathspec` to evaluate `.gitignore` patterns, ensuring irrelevant files are skipped during ingestion.
- **`text.py`**: Provides utilities for chunking plain text.
- **`uri.py`**: Handles bidirectional conversion between absolute physical file paths and `viking://` URIs.

## Behavior & Workflows

1. **Discovery**: The system iterates over configured storage roots, skipping ignored files and metadata sidecars.
2. **Evaluation**: It checks modification times (mtime) between the target file and its `.meta.yaml` sidecar to determine if ingestion is necessary.
3. **Extraction & Embedding**: For a target file, its text is extracted. An LLM prompt generates a short abstract (L1). This abstract is then embedded into a dense vector.
4. **Persistence**: The file's URI is stored in `memories_meta` with a unique ID, and the embedding is stored in `vec_memories` under the same ID. The sidecar is written last to ensure its mtime is newer than the source file.
5. **Isolation**: External consumers (like `vlfs_mcp`) only interact with exports defined in `__init__.py`. The internal file structure and database operations remain opaque.