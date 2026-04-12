import os
import sqlite3
import sqlite_vec

from .constants import DB_FILENAME

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
