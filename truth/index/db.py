import sqlite3
import threading
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
  tokenize='porter unicode61'
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_vec USING vec0(
  embedding float[768]
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

_CONN: sqlite3.Connection | None = None
_CONN_LOCK = threading.Lock()


def open_db(path: Path | None = None) -> sqlite3.Connection:
    # ponytail: check_same_thread=False — watchdog Timer threads share this conn; serialize via watcher lock
    conn = sqlite3.connect(path or db_path(), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def _schema_stale(conn: sqlite3.Connection) -> bool:
    rows = conn.execute(
        "SELECT sql FROM sqlite_master WHERE name IN ('chunks_vec', 'chunks_fts')"
    ).fetchall()
    for row in rows:
        sql = row["sql"] or ""
        if "float[384]" in sql or "trigram" in sql:
            return True
    return False


def _drop_index_tables(conn: sqlite3.Connection) -> None:
    # ponytail: drops index tables only; user must run `truth index` to rebuild chunks/vec/fts
    conn.executescript(
        """
        DROP TABLE IF EXISTS chunks_fts;
        DROP TABLE IF EXISTS chunks_vec;
        DROP TABLE IF EXISTS chunks;
        DROP TABLE IF EXISTS files;
        """
    )
    conn.commit()


def init_schema(conn: sqlite3.Connection) -> None:
    if _schema_stale(conn):
        _drop_index_tables(conn)
    conn.executescript(_SCHEMA)
    conn.commit()


def get_db() -> sqlite3.Connection:
    global _CONN
    if _CONN is None:
        with _CONN_LOCK:
            if _CONN is None:
                _CONN = open_db()
                init_schema(_CONN)
    return _CONN
