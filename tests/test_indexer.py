"""Indexer skip semantics for log.md and skip_index frontmatter."""

from __future__ import annotations

import sqlite3

import sqlite_vec

from truth.index.db import _schema_stale, init_schema, open_db
from truth.index.indexer import index_file
from truth.store.frontmatter import format_note


def test_stale_v10_schema_drops_and_recreates_index_tables(tmp_path):
    """v1.0 used 384-dim vectors and trigram FTS; init_schema must drop, not crash."""
    db = tmp_path / "memory.db"
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    conn.executescript(
        """
        CREATE TABLE files (path TEXT PRIMARY KEY, content_hash TEXT, indexed_at TEXT);
        CREATE TABLE chunks (
          rowid INTEGER PRIMARY KEY, path TEXT, chunk_index INTEGER, text TEXT,
          note_type TEXT, note_title TEXT
        );
        CREATE VIRTUAL TABLE chunks_fts USING fts5(text, tokenize='trigram');
        CREATE VIRTUAL TABLE chunks_vec USING vec0(embedding float[384]);
        CREATE TABLE notes (path TEXT PRIMARY KEY, type TEXT, title TEXT, mtime REAL);
        CREATE TABLE events (id INTEGER PRIMARY KEY, path TEXT, op TEXT, ts TEXT);
        INSERT INTO chunks (path, chunk_index, text) VALUES ('old.md', 0, 'stale');
        """
    )
    conn.commit()
    assert _schema_stale(conn)
    init_schema(conn)
    vec_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE name='chunks_vec'"
    ).fetchone()["sql"]
    fts_sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE name='chunks_fts'"
    ).fetchone()["sql"]
    assert "float[768]" in vec_sql
    assert "trigram" not in fts_sql
    assert conn.execute("SELECT COUNT(*) AS n FROM chunks").fetchone()["n"] == 0


def test_log_and_skip_index_excluded_from_chunks(isolated_truth):
    root = isolated_truth
    log_path = root / "log.md"
    skip_path = root / "skip.md"
    log_path.write_text(
        format_note({"type": "Log", "title": "Changelog"}, "changelog entry\n"),
        encoding="utf-8",
    )
    skip_path.write_text(
        format_note({"type": "Note", "skip_index": True}, "skip me\n"),
        encoding="utf-8",
    )
    conn = open_db()
    init_schema(conn)
    index_file(conn, log_path, root)
    index_file(conn, skip_path, root)

    skipped_chunks = conn.execute(
        "SELECT COUNT(*) AS n FROM chunks WHERE path IN ('log.md', 'skip.md')"
    ).fetchone()["n"]
    assert skipped_chunks == 0, f"expected 0 chunks for skipped files, got {skipped_chunks}"

    for rel in ("log.md", "skip.md"):
        row = conn.execute("SELECT 1 FROM files WHERE path = ?", (rel,)).fetchone()
        assert row is not None, f"missing files row for {rel}"
