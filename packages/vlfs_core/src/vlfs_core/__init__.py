import os
import glob
import time
import subprocess
import yaml
import sqlite3
import sqlite_vec
import pathspec
from datetime import datetime
from google import genai

SUMMARY_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "text-embedding-004"

def init_db(working_root_dir: str) -> sqlite3.Connection:
    db_path = os.path.join(working_root_dir, "index.db")
    db = sqlite3.connect(db_path)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_memories USING vec0(
            filepath TEXT,
            embedding float[768]
        );
    """)
    db.commit()
    return db

def chunk_text(text: str, chunk_size: int = 1000) -> list[str]:
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def get_ignore_spec(working_root_dir: str):
    gitignore_path = os.path.join(working_root_dir, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, f)
    return None

def is_ignored(filepath: str, working_root_dir: str, spec: pathspec.PathSpec) -> bool:
    if not spec:
        return False
    rel_path = os.path.relpath(filepath, working_root_dir)
    return spec.match_file(rel_path)

def process_file(working_root_dir: str, filepath: str):
    base_filename = os.path.basename(filepath)
    meta_filepath = filepath[:-3] + ".meta.yaml"
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. L1 Generation
    client = genai.Client()
    summary_prompt = f"Provide a 1-2 sentence abstract of the following text:\n\n{content[:2000]}"
    response = client.models.generate_content(model=SUMMARY_MODEL, contents=summary_prompt)
    abstract = response.text.strip() if response.text else "Summary unavailable."

    # 2. Vector Sync (Delete-and-Replace)
    db = init_db(working_root_dir)
    rel_filepath = os.path.relpath(filepath, working_root_dir)
    db.execute("DELETE FROM vec_memories WHERE filepath = ?", (rel_filepath,))
    
    chunks = chunk_text(content)
    if chunks:
        embed_response = client.models.embed_content(model=EMBEDDING_MODEL, contents=chunks)
        embeddings = embed_response.embeddings
        
        for i, chunk_embedding in enumerate(embeddings):
            db.execute(
                "INSERT INTO vec_memories(filepath, embedding) VALUES (?, ?)",
                (rel_filepath, chunk_embedding.values)
            )
    db.commit()
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

    # 4. State Snapshot
    try:
        subprocess.run(["git", "add", filepath, meta_filepath], cwd=working_root_dir, check=True)
        subprocess.run(["git", "commit", "-m", f"VLFS Auto-index sync: {base_filename}"], cwd=working_root_dir, check=True)
        print(f"Synchronized and committed: {base_filename}")
    except subprocess.CalledProcessError as e:
        print(f"Git commit failed (maybe no changes?): {e}")

def sync_memories(working_root_dir: str):
    """Finds .md files that are newer than their .meta.yaml sidecars, or lack one."""
    md_files = glob.glob(os.path.join(working_root_dir, "**", "*.md"), recursive=True)
    spec = get_ignore_spec(working_root_dir)
    
    processed_count = 0
    for md_path in md_files:
        if is_ignored(md_path, working_root_dir, spec):
            continue
            
        meta_path = md_path[:-3] + ".meta.yaml"
        if not os.path.exists(meta_path) or os.path.getmtime(md_path) > os.path.getmtime(meta_path):
            print(f"Processing: {md_path}")
            process_file(working_root_dir, md_path)
            processed_count += 1
            
    if processed_count == 0:
        print("No new or modified memories to sync.")
    return processed_count