import os
import threading
from vlfs_core import process_file
from .config import get_working_root_dir

def save_l2_memory(memory_id: str, content: str, workspace_subpath: str = ".") -> str:
    """
    Saves a high-level L2 memory into a specific path within the VLFS root, triggering async ingestion.
    """
    working_root_dir = get_working_root_dir()
    target_dir = os.path.join(working_root_dir, workspace_subpath)
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
                process_file(working_root_dir, filepath)
            except Exception as e:
                print(f"Async ingestion failed for {filepath}: {e}")
                
        if os.environ.get("VLFS_SYNC_ASYNC", "true").lower() == "false":
            ingest()
        else:
            threading.Thread(target=ingest, daemon=True).start()
            
        return f"Successfully saved L2 memory to {filepath}. Ingestion has been scheduled."
    except Exception as e:
        return f"Failed to save L2 memory: {e}"

def read_l2_memory(memory_id: str, workspace_subpath: str = ".") -> str:
    """
    Retrieves the contents of an L2 memory by its ID and relative path.
    """
    working_root_dir = get_working_root_dir()
    if not memory_id.endswith(".md"):
        memory_id += ".md"
        
    filepath = os.path.join(working_root_dir, workspace_subpath, memory_id)
    if not os.path.exists(filepath):
        return f"L2 Memory '{memory_id}' not found at {filepath}."
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Failed to read L2 memory: {e}"
