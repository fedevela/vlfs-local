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
import json

SUMMARY_MODEL = "gemini-2.5-flash"
EMBEDDING_MODEL = "gemini-embedding-001"

DB_FILENAME = "vlfs_index.db"

class LLMAdapter:
    """A simple adapter to toggle between the google-genai SDK and the local dev tools."""
    
    def __init__(self, local_dev_mode: bool = False):
        self.local_dev_mode = local_dev_mode
        if not self.local_dev_mode:
            self.client = genai.Client()

    def generate_summary(self, model: str, prompt: str) -> str:
        if self.local_dev_mode:
            # We call the gemini-cli headless
            cmd = ["gemini", "-m", model, "-p", prompt, "-o", "json"]
            try:
                # Capture stdout independently to avoid pollution from stderr logs
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                # Find the first '{' to parse the json, since there might be preamble logs
                stdout = result.stdout
                json_start = stdout.find('{')
                if json_start != -1:
                    data = json.loads(stdout[json_start:])
                    return data.get("response", "Summary unavailable.").strip()
                return "Summary unavailable."
            except Exception as e:
                print(f"gemini-cli generation failed: {e}")
                return "Summary unavailable."
        else:
            response = self.client.models.generate_content(model=model, contents=prompt)
            return response.text.strip() if response.text else "Summary unavailable."

    def embed_content(self, model: str, contents: list[str]) -> list[list[float]]:
        """Returns a unified list of float arrays."""
        if self.local_dev_mode:
            import ollama
            response = ollama.embed(model='nomic-embed-text', input=contents)
            return response['embeddings']
        else:
            response = self.client.models.embed_content(model=model, contents=contents)
            return [emb.values for emb in response.embeddings]

def init_db(working_root_dir: str, embedding_dim: int = 3072) -> sqlite3.Connection:
    db_path = os.path.join(working_root_dir, DB_FILENAME)
    db = sqlite3.connect(db_path)
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.execute(f"""
        CREATE VIRTUAL TABLE IF NOT EXISTS vec_memories USING vec0(
            filepath TEXT,
            embedding float[{embedding_dim}]
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
    meta_filepath = filepath + ".meta.yaml"
    
    print(f"DEBUG: Attempting to read and process {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError as e:
        print(f"ERROR: Cannot read {filepath} as UTF-8 text. It might be a binary file. Skipping. Details: {e}")
        raise RuntimeError(f"Failed to read {filepath}: {e}")

    # Initialize Adapter
    local_dev_mode = os.environ.get("LOCAL_DEV_MODE", "false").lower() == "true"
    adapter = LLMAdapter(local_dev_mode=local_dev_mode)
    embedding_dim = 768 if local_dev_mode else 3072

    # 1. L1 Generation
    summary_prompt = f"Provide a 1-2 sentence abstract of the following text:\n\n{content[:2000]}"
    abstract = adapter.generate_summary(model=SUMMARY_MODEL, prompt=summary_prompt)

    # 2. Vector Sync (Delete-and-Replace)
    db = init_db(working_root_dir, embedding_dim=embedding_dim)
    rel_filepath = os.path.relpath(filepath, working_root_dir)
    db.execute("DELETE FROM vec_memories WHERE filepath = ?", (rel_filepath,))
    
    chunks = chunk_text(content)
    if chunks:
        embeddings = adapter.embed_content(model=EMBEDDING_MODEL, contents=chunks)
        
        for i, chunk_embedding in enumerate(embeddings):
            db.execute(
                "INSERT INTO vec_memories(filepath, embedding) VALUES (?, ?)",
                (rel_filepath, sqlite_vec.serialize_float32(chunk_embedding))
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
        subprocess.run(
            ["git", "add", filepath, meta_filepath], 
            cwd=working_root_dir, 
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        subprocess.run(
            ["git", "commit", "-m", f"VLFS Auto-index sync: {base_filename}"], 
            cwd=working_root_dir, 
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print(f"Synchronized and committed: {base_filename}")
    except subprocess.CalledProcessError as e:
        print(f"Git commit failed (maybe no changes?): {e}")

def sync_memories(working_root_dir: str):
    """Finds files that are newer than their .meta.yaml sidecars, or lack one."""
    all_files = glob.glob(os.path.join(working_root_dir, "**", "*"), recursive=True)
    spec = get_ignore_spec(working_root_dir)
    
    processed_count = 0
    for file_path in all_files:
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
            process_file(working_root_dir, file_path)
            processed_count += 1
            
    if processed_count == 0:
        print("No new or modified memories to sync.")
    return processed_count