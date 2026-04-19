import os
import glob
import yaml
import sqlite_vec
from datetime import datetime

from .constants import DB_FILENAME, SUMMARY_MODEL, EMBEDDING_MODEL
from .llm import LLMAdapter
from .db import init_db
from .text import chunk_text
from .ignore import get_ignore_spec, is_ignored
from .config import get_storage_paths
from .uri import uri_from_path

def process_file(working_root_dir: str, filepath: str):
    base_filename = os.path.basename(filepath)
    meta_filepath = filepath + ".meta.yaml"
    
    print(f"DEBUG: Attempting to read and process {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError as e:
        print(f"ERROR: Cannot read {filepath} as UTF-8 text. It might be a binary file. Skipping. Details: {e}")
        return

    # Initialize Adapter
    local_dev_mode = os.environ.get("LOCAL_DEV_MODE", "false").lower() == "true"
    adapter = LLMAdapter(local_dev_mode=local_dev_mode)
    embedding_dim = 768 if local_dev_mode else 3072

    # 1. L1 Generation
    summary_prompt = f"Provide a 1-2 sentence abstract of the following text:\n\n{content[:2000]}"
    abstract = adapter.generate_summary(model=SUMMARY_MODEL, prompt=summary_prompt)

    # 2. Vector Sync (Delete-and-Replace)
    db = init_db(working_root_dir, embedding_dim=embedding_dim)
    viking_uri = uri_from_path(filepath)
    
    try:
        db.execute("DELETE FROM vec_memories WHERE rowid IN (SELECT rowid FROM memories_meta WHERE filepath = ?)", (viking_uri,))
        db.execute("DELETE FROM memories_meta WHERE filepath = ?", (viking_uri,))
        
        if abstract:
            embeddings = adapter.embed_content(model=EMBEDDING_MODEL, contents=[abstract])
            if embeddings:
                import uuid
                # Generate a random positive 63-bit integer to serve as unified rowid across tables
                new_rowid = uuid.uuid4().int & ((1<<63)-1)
                
                db.execute("INSERT INTO memories_meta (rowid, filepath) VALUES (?, ?)", (new_rowid, viking_uri))
                db.execute(
                    "INSERT INTO vec_memories(rowid, embedding) VALUES (?, ?)",
                    (new_rowid, sqlite_vec.serialize_float32(embeddings[0]))
                )
        db.commit()
    finally:
        db.close()

    # 3. Sidecar Creation (Writing this last ensures its mtime > md's mtime)
    meta_data = {
        "id": base_filename,
        "timestamp": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat(),
        "l1_summary": abstract,
        "vector_indexed": True
    }
    with open(meta_filepath, 'w', encoding='utf-8') as f:
        yaml.dump(meta_data, f, default_flow_style=False)

    print(f"Synchronized: {base_filename}")

def sync_memories(working_root_dir: str, target_dir: str = None):
    """Finds files that are newer than their .meta.yaml sidecars, or lack one."""
    paths = get_storage_paths()
    if target_dir:
        search_dirs = [target_dir]
    else:
        search_dirs = [paths["resources"], paths["memories"], paths["skills"]]
        
    spec = get_ignore_spec(working_root_dir)
    processed_count = 0
    
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
        all_files = glob.glob(os.path.join(search_dir, "**", "*"), recursive=True)
        
        for file_path in all_files:
            # Prevent scanning .viking metadata directory when indexing the base workspace
            if search_dir == paths["resources"] and ".viking" in os.path.relpath(file_path, paths["resources"]).split(os.sep):
                continue
                
            base_name = os.path.basename(file_path)
            if base_name == DB_FILENAME:
                continue
            if not os.path.isfile(file_path):
                continue
            if file_path.endswith(".meta.yaml"):
                continue
            if is_ignored(file_path, working_root_dir, spec):
                continue
                
            meta_path = file_path + ".meta.yaml"
            if not os.path.exists(meta_path) or os.path.getmtime(file_path) > os.path.getmtime(meta_path):
                print(f"Processing: {file_path}")
                try:
                    process_file(working_root_dir, file_path)
                    processed_count += 1
                except Exception as e:
                    print(f"ERROR: Failed to process {file_path}. Skipping. Details: {e}")
            
    if processed_count == 0:
        print("No new or modified memories to sync.")
    return processed_count
