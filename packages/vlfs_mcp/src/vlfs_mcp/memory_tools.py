import os
import sqlite3
import threading
import uuid
import shlex
import subprocess
from vlfs_core import LLMAdapter, EMBEDDING_MODEL, DB_FILENAME, process_file, sync_memories
from vlfs_core import get_working_root_dir, get_storage_paths
from .utils import resolve_viking_uri, uri_from_path

def memory_recall(query: str, limit: int = 3, targetUri: str = None, scoreThreshold: float = 0.0) -> str:
    """
    Searches the long-term viking:// memory partitions and injects the L1/L2 results into the context window.
    """
    working_root_dir = get_working_root_dir()
    try:
        import sqlite_vec
    except ImportError:
        return "sqlite-vec is not installed."
        
    db_path = os.path.join(working_root_dir, DB_FILENAME)
    if not os.path.exists(db_path):
        return "Database not found. Please wait for memories to sync."

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
    
    distance_threshold = 1.0 - scoreThreshold
    params = [sqlite_vec.serialize_float32(query_embedding), distance_threshold]
    
    if targetUri:
        query_sql = """
        SELECT (SELECT filepath FROM memories_meta WHERE rowid = v.rowid), v.distance
        FROM vec_memories v
        WHERE v.rowid IN (SELECT rowid FROM memories_meta WHERE filepath LIKE ?)
          AND v.embedding MATCH ? 
          AND v.distance <= ?
        ORDER BY v.distance
        LIMIT ?
        """
        # Note: LIKE param comes first in the string
        params.insert(0, f"{targetUri}%")
    else:
        query_sql = """
        SELECT (SELECT filepath FROM memories_meta WHERE rowid = v.rowid), v.distance
        FROM vec_memories v
        WHERE v.embedding MATCH ? 
          AND v.distance <= ?
        ORDER BY v.distance
        LIMIT ?
        """
        
    params.append(limit)

    cursor.execute(query_sql, tuple(params))
    results = cursor.fetchall()
    db.close()
    
    if not results:
        return "No relevant memories found."
        
    output = [f"Recall Results (Limit: {limit}):\n"]
    for viking_uri, distance in results:
        abs_path = resolve_viking_uri(viking_uri)
        
        # Inject full content for L2/Markdown, or just summary for other files
        content_preview = ""
        try:
            if os.path.exists(abs_path):
                with open(abs_path, 'r', encoding='utf-8') as f:
                    content_preview = f.read(1000) + ("..." if os.path.getsize(abs_path) > 1000 else "")
        except Exception:
            content_preview = "<unreadable>"
            
        output.append(f"Memory URI: {viking_uri}")
        output.append(f"Relevance: {1.0 - distance:.4f}")
        output.append(f"Content:\n{content_preview}")
        output.append("-" * 40)
        
    return "\n".join(output)


def memory_store(text: str, targetUri: str) -> str:
    """
    Manually writes raw text to an OpenViking session or target partition, triggering background extraction loop.
    """
    if not targetUri:
        return "Error: targetUri is required."
        
    valid_prefixes = ("viking://resources/", "viking://skills/", "viking://user/memories/")
    if not any(targetUri.startswith(prefix) for prefix in valid_prefixes):
        return "Error: targetUri must begin with a valid partition prefix."
        
    if targetUri.endswith("/"):
        return "Error: targetUri must specify a complete filename, not a directory."
        
    working_root_dir = get_working_root_dir()
    filepath = resolve_viking_uri(targetUri)
    
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(text)
            
        # Trigger async ingestion
        def ingest():
            try:
                process_file(working_root_dir, filepath)
            except Exception as e:
                print(f"Async ingestion failed for {filepath}: {e}")
                
        if os.environ.get("VLFS_SYNC_ASYNC", "true").lower() == "false":
            ingest()
        else:
            threading.Thread(target=ingest, daemon=True).start()
            
        return f"Successfully stored memory to {targetUri}. Background extraction triggered."
    except Exception as e:
        return f"Failed to store memory: {e}"


def memory_forget(query: str = None, uri: str = None, targetUri: str = None, limit: int = 1) -> str:
    """
    Prunes or deletes specific conversational memories to maintain context hygiene.
    Requires either a specific uri or a query to find memories to delete.
    """
    paths = get_storage_paths()
    
    deleted_count = 0
    to_delete = []
    
    if uri:
        abs_path = resolve_viking_uri(uri)
        if os.path.exists(abs_path):
            to_delete.append(abs_path)
    elif query:
        try:
            search_paths = []
            if targetUri:
                search_paths.append(resolve_viking_uri(targetUri))
            else:
                search_paths = [paths["workspace"], paths["memories"], paths["skills"]]
            
            for search_path in search_paths:
                if not os.path.exists(search_path):
                    continue
                cmd = f"grep -rl {shlex.quote(query)} {shlex.quote(search_path)} | head -n {limit}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    matched_files = result.stdout.strip().split('\n')
                    for p in matched_files:
                        if p and os.path.exists(p):
                            to_delete.append(p)
                
                # Stop if we reached the limit across paths
                if len(to_delete) >= limit:
                    to_delete = to_delete[:limit]
                    break
        except Exception as e:
            return f"Failed to search for memory to forget: {e}"
            
    if not to_delete:
        return "No matching memories found to forget."
        
    for abs_path in to_delete:
        try:
            os.remove(abs_path)
            deleted_count += 1
        except Exception:
            pass
            
    return f"Successfully forgot {deleted_count} memories."


def memory_sync(targetUri: str = "viking://resources/") -> str:
    """
    Bulk Ingestion (Add local folders).
    Synchronizes the specified OpenViking URI, generating abstracts and vector embeddings for new or modified files.
    """
    working_root_dir = get_working_root_dir()
    target_abs_path = resolve_viking_uri(targetUri)
        
    if not os.path.exists(target_abs_path):
        return f"Path not found: {targetUri}"
        
    try:
        count = sync_memories(working_root_dir, target_dir=target_abs_path)
        return f"Successfully synchronized {count} memories in {targetUri}."
    except Exception as e:
        return f"Error synchronizing memories: {str(e)}"
