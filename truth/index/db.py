import os
import sqlite3
from pathlib import Path

import sqlite_vec

_SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
  path TEXT PRIMARY KEY,
  content_hash TEXT NOT NULL,
  indexed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS chunks (
  rowid INTEGER PRIMARY KEY,
  path TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  text TEXT NOT NULL,
  note_type TEXT,
  note_title TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
  text,
  tokenize='trigram'
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec USING vec0(
  embedding float[384]
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY,
  path TEXT NOT NULL,
  op TEXT NOT NULL CHECK(op IN ('create', 'update', 'delete')),
  ts TEXT NOT NULL
);
"""


def db_path() -> Path:
    raw = os.environ.get("TRUTH_DB_PATH", "memory.db")
    return Path(raw).resolve()


def open_db(path: Path | None = None) -> sqlite3.Connection:
    # ponytail: check_same_thread=False — watchdog Timer threads share this conn; serialize via watcher lock
    conn = sqlite3.connect(path or db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(_SCHEMA)
    conn.commit()
