import os
import subprocess
import shlex
import glob
import yaml
import sqlite3
import threading
from fastmcp import FastMCP
from vlfs_core import sync_memories, process_file, get_ignore_spec, is_ignored, DB_FILENAME

# Configure the working directory. It can be passed via environment variable VLFS_ROOT_DIR.
# If not provided, it defaults to the directory from which the MCP server was launched.
# We use expanduser to ensure paths like ~/Documents/... are resolved correctly.
WORKING_ROOT_DIR = os.path.abspath(os.path.expanduser(os.environ.get("VLFS_ROOT_DIR", os.getcwd())))

# Initialize FastMCP server
mcp = FastMCP("vlfs-mcp")

@mcp.tool()
def sync_all_memories() -> str:
    """
    Scans the configured working directory for any new or modified memory files
    and synchronizes them into the VLFS state, generating abstracts and vector embeddings.
    """
    try:
        count = sync_memories(WORKING_ROOT_DIR)
        return f"Successfully synchronized {count} memories in {WORKING_ROOT_DIR}."
    except Exception as e:
        return f"Error synchronizing memories: {str(e)}"

@mcp.tool()
def ingest_memory_file(relative_filepath: str) -> str:
    """
    Forces the ingestion and synchronization of a specific memory file.
    The filepath should be relative to the configured working root directory.
    """
    base_name = os.path.basename(relative_filepath)
    if base_name == DB_FILENAME:
        return f"Skipped: {base_name} is the VLFS index database and cannot be ingested."

    absolute_filepath = os.path.join(WORKING_ROOT_DIR, relative_filepath)
    if not os.path.exists(absolute_filepath):
        return f"Error: File not found at {absolute_filepath}"
        
    spec = get_ignore_spec(WORKING_ROOT_DIR)
    if is_ignored(absolute_filepath, WORKING_ROOT_DIR, spec):
        return f"Skipped: {relative_filepath} is ignored by .gitignore."
        
    try:
        process_file(WORKING_ROOT_DIR, absolute_filepath)
        return f"Successfully ingested memory: {relative_filepath}"
    except Exception as e:
        return f"Error ingesting memory: {str(e)}"

@mcp.tool()
def search_l0_memory(pattern: str, workspace_subpath: str = ".") -> str:
    """
    Searches only the filenames (using POSIX find and grep).
    Provides a fast way to locate files by their name or extension (e.g. *auth*.py).
    """
    target_path = os.path.abspath(os.path.join(WORKING_ROOT_DIR, workspace_subpath))
    if not os.path.exists(target_path):
        return f"Path not found: {workspace_subpath}"
        
    try:
        # Use find to list files, then grep on the file paths
        cmd = f"find {shlex.quote(target_path)} -type f | grep -E {shlex.quote(pattern)}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            out = result.stdout
            return out[:4000] + ("\n...[truncated]" if len(out) > 4000 else "")
        elif result.returncode == 1:
            return "No matches found."
        else:
            return f"Error running find/grep: {result.stderr}"
    except Exception as e:
        return f"Error: {e}"

@mcp.tool()
def search_l1_grep(keyword: str, workspace_subpath: str = ".") -> str:
    """
    Searches L1 abstracts by looking for exact keywords within .meta.yaml sidecar files.
    """
    target_path = os.path.abspath(os.path.join(WORKING_ROOT_DIR, workspace_subpath))
    if not os.path.exists(target_path):
        return f"Path not found: {workspace_subpath}"

    matches = []
    # If path is a directory, glob inside it.
    if os.path.isdir(target_path):
        search_pattern = os.path.join(target_path, "**", "*.meta.yaml")
        meta_files = glob.glob(search_pattern, recursive=True)
    else:
        # If it's a specific file
        meta_files = [target_path] if target_path.endswith(".meta.yaml") else []

    keyword_lower = keyword.lower()
    for meta_path in meta_files:
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if not data:
                    continue
                summary = data.get("l1_summary", "")
                if keyword_lower in summary.lower():
                    matches.append((meta_path.replace(".meta.yaml", ""), summary))
        except Exception:
            continue
            
    if not matches:
        return f"No L1 memories found containing '{keyword}' in {workspace_subpath}."
        
    output = [f"Found {len(matches)} L1 Matches:\n"]
    for filepath, summary in matches:
        output.append(f"File: {filepath}")
        output.append(f"Summary: {summary}")
        output.append("-" * 40)
        
    return "\n".join(output)

@mcp.tool()
def search_l1_semantic(query: str, limit: int = 3) -> str:
    """
    Semantic vector search over the chunked SQLite-vec index.
    Use explicitly for fuzzy/conceptual questions.
    """
    try:
        import sqlite_vec
    except ImportError:
        return "sqlite-vec is not installed."
        
    from vlfs_core import LLMAdapter, EMBEDDING_MODEL

    db_path = os.path.join(WORKING_ROOT_DIR, DB_FILENAME)
    if not os.path.exists(db_path):
        return "Database not found. Please sync memories first."

    local_dev_mode = os.environ.get("LOCAL_DEV_MODE", "false").lower() == "true"
    adapter = LLMAdapter(local_dev_mode=local_dev_mode)
    
    try:
        query_embedding = adapter.embed_content(model=EMBEDDING_MODEL, contents=[query])[0]
    except Exception as e:
        return f"Failed to embed query: {e}"

    db = sqlite3.connect(db_path)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    
    cursor = db.cursor()
    cursor.execute(
        """
        SELECT filepath, distance
        FROM vec_memories
        WHERE embedding MATCH ?
        ORDER BY distance
        LIMIT ?
        """,
        (sqlite_vec.serialize_float32(query_embedding), limit)
    )
    
    results = cursor.fetchall()
    db.close()
    
    if not results:
        return "No relevant memories found."
        
    output = [f"Top {len(results)} Semantic Matches:\n"]
    for rel_filepath, distance in results:
        abs_path = os.path.join(WORKING_ROOT_DIR, rel_filepath)
        output.append(f"File: {abs_path}")
        output.append(f"Distance: {distance:.4f}")
        output.append("-" * 40)
        
    return "\n".join(output)

@mcp.tool()
def save_l2_memory(memory_id: str, content: str, workspace_subpath: str = ".") -> str:
    """
    Saves a high-level L2 memory into a specific path within the VLFS root, triggering async ingestion.
    """
    target_dir = os.path.join(WORKING_ROOT_DIR, workspace_subpath)
    os.makedirs(target_dir, exist_ok=True)
    
    if not memory_id.endswith(".md"):
        memory_id += ".md"
        
    filepath = os.path.join(target_dir, memory_id)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Trigger async ingestion (can be disabled for testing)
        def ingest():
            try:
                process_file(WORKING_ROOT_DIR, filepath)
            except Exception as e:
                print(f"Async ingestion failed for {filepath}: {e}")
                
        if os.environ.get("VLFS_SYNC_ASYNC", "true").lower() == "false":
            ingest()
        else:
            threading.Thread(target=ingest, daemon=True).start()
            
        return f"Successfully saved L2 memory to {filepath}. Ingestion has been scheduled."
    except Exception as e:
        return f"Failed to save L2 memory: {e}"

@mcp.tool()
def read_l2_memory(memory_id: str, workspace_subpath: str = ".") -> str:
    """
    Retrieves the contents of an L2 memory by its ID and relative path.
    """
    if not memory_id.endswith(".md"):
        memory_id += ".md"
        
    filepath = os.path.join(WORKING_ROOT_DIR, workspace_subpath, memory_id)
    if not os.path.exists(filepath):
        return f"L2 Memory '{memory_id}' not found at {filepath}."
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Failed to read L2 memory: {e}"

def run():
    print(f"Starting VLFS MCP Server. Working root directory: {WORKING_ROOT_DIR}")
    mcp.run()

if __name__ == "__main__":
    run()