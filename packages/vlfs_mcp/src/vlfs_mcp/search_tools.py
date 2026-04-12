import os
import subprocess
import shlex
import glob
import yaml
import sqlite3
from vlfs_core import LLMAdapter, EMBEDDING_MODEL, DB_FILENAME
from .config import get_working_root_dir

def search_l0_memory(pattern: str, workspace_subpath: str = ".") -> str:
    """
    Searches only the filenames (using POSIX find and grep).
    Provides a fast way to locate files by their name or extension (e.g. *auth*.py).
    """
    working_root_dir = get_working_root_dir()
    target_path = os.path.abspath(os.path.join(working_root_dir, workspace_subpath))
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

def search_l1_grep(keyword: str, workspace_subpath: str = ".") -> str:
    """
    Searches L1 abstracts by looking for exact keywords within .meta.yaml sidecar files.
    """
    working_root_dir = get_working_root_dir()
    target_path = os.path.abspath(os.path.join(working_root_dir, workspace_subpath))
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

def search_l1_semantic(query: str, limit: int = 3) -> str:
    """
    Semantic vector search over the chunked SQLite-vec index.
    Use explicitly for fuzzy/conceptual questions.
    """
    working_root_dir = get_working_root_dir()
    try:
        import sqlite_vec
    except ImportError:
        return "sqlite-vec is not installed."
        
    db_path = os.path.join(working_root_dir, DB_FILENAME)
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
        abs_path = os.path.join(working_root_dir, rel_filepath)
        output.append(f"File: {abs_path}")
        output.append(f"Distance: {distance:.4f}")
        output.append("-" * 40)
        
    return "\n".join(output)
