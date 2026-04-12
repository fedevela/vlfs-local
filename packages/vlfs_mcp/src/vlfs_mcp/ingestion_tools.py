import os
from vlfs_core import sync_memories, process_file, get_ignore_spec, is_ignored, DB_FILENAME
from .config import get_working_root_dir

def sync_all_memories() -> str:
    """
    Scans the configured working directory for any new or modified memory files
    and synchronizes them into the VLFS state, generating abstracts and vector embeddings.
    """
    working_root_dir = get_working_root_dir()
    try:
        count = sync_memories(working_root_dir)
        return f"Successfully synchronized {count} memories in {working_root_dir}."
    except Exception as e:
        return f"Error synchronizing memories: {str(e)}"

def ingest_memory_file(relative_filepath: str) -> str:
    """
    Forces the ingestion and synchronization of a specific memory file.
    The filepath should be relative to the configured working root directory.
    """
    working_root_dir = get_working_root_dir()
    base_name = os.path.basename(relative_filepath)
    if base_name == DB_FILENAME:
        return f"Skipped: {base_name} is the VLFS index database and cannot be ingested."

    absolute_filepath = os.path.join(working_root_dir, relative_filepath)
    if not os.path.exists(absolute_filepath):
        return f"Error: File not found at {absolute_filepath}"
        
    spec = get_ignore_spec(working_root_dir)
    if is_ignored(absolute_filepath, working_root_dir, spec):
        return f"Skipped: {relative_filepath} is ignored by .gitignore."
        
    try:
        process_file(working_root_dir, absolute_filepath)
        return f"Successfully ingested memory: {relative_filepath}"
    except Exception as e:
        return f"Error ingesting memory: {str(e)}"
