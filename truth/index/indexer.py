from __future__ import annotations

import warnings
from datetime import datetime, timezone
from pathlib import Path

import sqlite_vec

from truth.store.frontmatter import parse_note_file
from truth.store.links import extract_links
from truth.store.paths import notes_root

from .chunking import chunk_text
from .db import init_schema, open_db
from .embeddings import embed_texts
from .events import record_event
from .hashutil import content_hash

_MAX_FILE_BYTES = 1_000_000


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _relative_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def _rowids_for_path(conn, path: str) -> list[int]:
    rows = conn.execute("SELECT rowid FROM chunks WHERE path = ?", (path,)).fetchall()
    return [int(r["rowid"]) for r in rows]


def _delete_chunks_for_path(conn, path: str) -> None:
    for rowid in _rowids_for_path(conn, path):
        conn.execute("DELETE FROM chunks_fts WHERE rowid = ?", (rowid,))
        conn.execute("DELETE FROM chunks_vec WHERE rowid = ?", (rowid,))
    conn.execute("DELETE FROM chunks WHERE path = ?", (path,))


def _serialize_tags(meta: dict) -> str | None:
    tags = meta.get("tags")
    if isinstance(tags, list):
        return ",".join(sorted(str(t).lower() for t in tags))
    return None


def _should_index_semantic(rel: str, meta: dict) -> bool:
    if rel == "log.md":
        return False
    if meta.get("skip_index") is True:
        return False
    return True


def _sync_graph(
    conn,
    resolved: Path,
    rel: str,
    root: Path,
    note_type: str | None,
    note_title: str | None,
    tags: str | None = None,
) -> None:
    mtime = resolved.stat().st_mtime
    conn.execute(
        """
        INSERT INTO notes (path, type, title, mtime, tags)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
          type = excluded.type,
          title = excluded.title,
          mtime = excluded.mtime,
          tags = excluded.tags
        """,
        (rel, note_type, note_title, mtime, tags),
    )
    conn.execute("DELETE FROM edges WHERE source = ?", (rel,))
    for edge in extract_links(resolved, root):
        try:
            target_rel = _relative_path(edge.target, root)
        except ValueError:
            continue
        if not target_rel.endswith(".md"):
            continue
        conn.execute(
            "INSERT OR IGNORE INTO edges (source, target, label) VALUES (?, ?, ?)",
            (rel, target_rel, edge.label),
        )


def delete_file_from_index(conn, path: Path, notes: Path) -> None:
    rel = _relative_path(path, notes)
    conn.execute("BEGIN")
    try:
        _delete_chunks_for_path(conn, rel)
        conn.execute("DELETE FROM files WHERE path = ?", (rel,))
        conn.execute("DELETE FROM notes WHERE path = ?", (rel,))
        conn.execute("DELETE FROM edges WHERE source = ? OR target = ?", (rel, rel))
        record_event(conn, rel, "delete")
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def index_file(conn, path: Path, notes: Path) -> bool:
    """Index one markdown file. Returns True if content was (re)indexed."""
    root = notes.resolve()
    resolved = path.resolve()
    if not str(resolved).startswith(str(root)):
        return False
    if resolved.suffix.lower() != ".md":
        return False

    rel = _relative_path(resolved, root)
    data = resolved.read_bytes()
    if len(data) > _MAX_FILE_BYTES:
        warnings.warn(f"skip large file ({len(data)} bytes): {rel}")
        return False

    digest = content_hash(data)
    existing = conn.execute(
        "SELECT content_hash FROM files WHERE path = ?", (rel,)
    ).fetchone()
    if existing and existing["content_hash"] == digest:
        return False

    try:
        parsed = parse_note_file(resolved)
    except (ValueError, OSError) as exc:
        warnings.warn(f"skip invalid note {rel}: {exc}")
        return False

    note_type = str(parsed.meta.get("type", "")) or None
    note_title = parsed.meta.get("title")
    if note_title is not None:
        note_title = str(note_title)
    tags = _serialize_tags(parsed.meta)

    is_update = existing is not None

    if not _should_index_semantic(rel, parsed.meta):
        conn.execute("BEGIN")
        try:
            _delete_chunks_for_path(conn, rel)
            conn.execute(
                """
                INSERT INTO files (path, content_hash, indexed_at)
                VALUES (?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                  content_hash = excluded.content_hash,
                  indexed_at = excluded.indexed_at
                """,
                (rel, digest, _utc_now()),
            )
            _sync_graph(conn, resolved, rel, root, note_type, note_title, tags)
            record_event(conn, rel, "update" if is_update else "create")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        return True

    pieces = chunk_text(parsed.body)
    if not pieces:
        pieces = [""]

    vectors = embed_texts(pieces)
    conn.execute("BEGIN")
    try:
        _delete_chunks_for_path(conn, rel)
        for i, (text, vec) in enumerate(zip(pieces, vectors)):
            cur = conn.execute(
                """
                INSERT INTO chunks (path, chunk_index, text, note_type, note_title)
                VALUES (?, ?, ?, ?, ?)
                """,
                (rel, i, text, note_type, note_title),
            )
            rowid = cur.lastrowid
            conn.execute(
                "INSERT INTO chunks_fts (rowid, text) VALUES (?, ?)", (rowid, text)
            )
            conn.execute(
                "INSERT INTO chunks_vec (rowid, embedding) VALUES (?, ?)",
                (rowid, sqlite_vec.serialize_float32(vec)),
            )

        conn.execute(
            """
            INSERT INTO files (path, content_hash, indexed_at)
            VALUES (?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
              content_hash = excluded.content_hash,
              indexed_at = excluded.indexed_at
            """,
            (rel, digest, _utc_now()),
        )
        _sync_graph(conn, resolved, rel, root, note_type, note_title, tags)
        record_event(conn, rel, "update" if is_update else "create")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return True


def index_all(notes: Path | None = None) -> int:
    root = notes or notes_root()
    conn = open_db()
    init_schema(conn)
    indexed = 0
    if not root.exists():
        return 0
    for path in sorted(root.rglob("*.md")):
        if path.name.startswith("."):
            continue
        if index_file(conn, path, root):
            indexed += 1
    return indexed


if __name__ == "__main__":
    import tempfile

    from truth.store.frontmatter import format_note

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        db = root / "memory.db"
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
        conn = open_db(db)
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
        print("skip_semantic=ok")

    count = index_all()
    conn = open_db()
    total = conn.execute("SELECT COUNT(*) AS n FROM chunks").fetchone()["n"]
    notes_n = conn.execute("SELECT COUNT(*) AS n FROM notes").fetchone()["n"]
    assert notes_n >= 3, f"expected >=3 notes rows, got {notes_n}"
    log_chunks = conn.execute(
        "SELECT COUNT(*) AS n FROM chunks WHERE path = 'log.md'"
    ).fetchone()["n"]
    assert log_chunks == 0, f"expected 0 chunks for log.md, got {log_chunks}"
    print(f"indexed_files={count} chunks={total} notes={notes_n}")
