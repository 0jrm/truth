import sqlite3
from pathlib import Path

import sqlite_vec

from truth.store.paths import db_path

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

CREATE TABLE IF NOT EXISTS notes (
  path TEXT PRIMARY KEY,
  type TEXT,
  title TEXT,
  mtime REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS edges (
  source TEXT NOT NULL,
  target TEXT NOT NULL,
  label TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (source, target, label)
);

CREATE INDEX IF NOT EXISTS edges_target ON edges(target);
"""


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
