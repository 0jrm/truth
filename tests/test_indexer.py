"""Indexer skip semantics for log.md and skip_index frontmatter."""

from __future__ import annotations

from truth.index.db import init_schema, open_db
from truth.index.indexer import index_file
from truth.store.frontmatter import format_note


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
