# VLFS Local (OpenViking MCP)

A local, lightweight, and powerful implementation of the **Virtualized Log-Structured File System (VLFS)** principles, adhering to the [**OpenViking** standard](https://github.com/volcengine/OpenViking). 

This project automatically turns your local workspace into a contextual **Model Context Protocol (MCP)** server. By simply running the server within your project, you empower any connected LLM agent with semantic memory, intelligent structural discovery, and isolated cognition layers.

## Why VLFS Local?

When working with LLM agents on large codebases or projects, context window exhaustion is a constant threat. Standard approaches involve either dumping massive files into the prompt or relying on black-box external RAG systems.

VLFS Local provides a transparent, local-first alternative:
1. **Naive but Powerful:** It uses standard POSIX-like verbs and simple SQLite vector indexing (`sqlite-vec`). No complex infrastructure required.
2. **Context Preservation:** It gives your agent a dedicated, persistent memory layer that survives across sessions.
3. **The Discovery Funnel:** It strictly enforces a hierarchical search strategy (L0 -> L1 -> L2) to minimize token usage while maximizing context retrieval.

## The OpenViking Virtual Filesystem (`viking://`)

The MCP server exposes a unified virtual filesystem to the agent under the `viking://` URI scheme. This root behaves like a real directory containing three isolated partitions:

- `viking://resources/`: Your actual workspace/project files. This is where your code, documents, and assets live. The server respects your `.gitignore`.
- `viking://skills/`: Executable instructions and procedural guidance for the agent. Physically stored in `.viking/skills/`.
- `viking://user/memories/`: The agent's episodic cognition layer. A place for the agent to write reflections, session summaries, and long-term context. Physically stored in `.viking/user/memories/`.

*Note: By adding `.viking/` to your project's `.gitignore`, your agent's memory and skills are kept cleanly isolated from your actual source code repository.*

## The L0/L1/L2 Discovery Hierarchy

To prevent token exhaustion, the MCP tools enforce a strict discovery funnel, teaching the connected LLM how to efficiently navigate the project:

### L0 Layer: Discovery & Metadata
*Tools: `fs_ls`, `fs_tree`*
* Provides the structural map of the workspace.
* Uses minimal tokens to show directory trees and file names without loading any raw content.
* Agents use this to understand the shape of the project and locate potential areas of interest.

### L1 Layer: Scanning & Routing
*Tools: `memory_find` / `memory_recall`*
* Semantic vector search across the workspace.
* Instead of searching raw text, VLFS automatically generates a 1-2 sentence abstract (L1 Summary) for every file and stores its embedding in a local `sqlite-vec` database.
* Agents use this to "fuzzy search" for concepts (e.g., "authentication logic") without committing to a deep, token-heavy read.

### L2 Layer: Deep Reading & Exact Matching
*Tools: `fs_cat`, `fs_grep`*
* Retrieves the raw, unadulterated file contents (L2 Memory).
* `fs_cat` loads the full file into the context window.
* `fs_grep` performs an exact literal string match across the raw text.
* Agents are instructed to only use L2 tools once they have narrowed down their target via L0 or L1.

## Registration & Synchronization (Indexing)

Creating or saving a file in your project directory does *not* automatically place it into the agent's semantic memory. Just like `git add`, files must be ingested and registered with the vector index to be discoverable via `memory_find`.

VLFS Local handles indexing in two ways:
1. **Single File Registration (`memory_store`)**: When an agent explicitly writes a memory or updates a file using the `memory_store` tool, the core engine saves the raw file and immediately triggers a background extraction loop to index it.
2. **Bulk Synchronization (`memory_sync`)**: Because VLFS Local does *not* run a background daemon watching your filesystem, any file created or modified out-of-band is "unregistered" or "stale". This includes you (the human) modifying files in your IDE or pulling a PR, *as well as* the agent itself modifying code via standard CLI tools (e.g., `sed`, `echo`, or `replace`). To make these files discoverable in the semantic index, you or the agent must manually call `memory_sync` (e.g., `ov ingest`). This tool recursively scans the specified `viking://` partition, identifies files that are newer than their `.meta.yaml` sidecar (or lack one entirely), and bulk-processes them.

For each unregistered or stale file, the engine uses a local or cloud LLM (configurable) to generate an L1 abstract, embeds it, and updates the SQLite vector database. A `.meta.yaml` sidecar file is dropped next to the original file to act as the synchronization receipt.

## Architecture

The system is split into two primary python packages:
- **`vlfs_core` (The Foundation):** Handles raw data ingestion, abstract generation, chunking, embedding, and semantic database persistence.
- **`vlfs_mcp` (The Agent Interface):** Wraps the core engine into standard FastMCP tools, enforcing the OpenViking `viking://` routing and exposing the L0/L1/L2 verbs to the LLM.

## Setup & Configuration

*Detailed setup instructions coming soon...*
* Uses `vlfs_config.json` for overriding storage paths and model providers (supports Local Dev Mode via Ollama/CLI, Google GenAI, OpenAI).
