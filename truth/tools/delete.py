from __future__ import annotations

from truth.index.db import init_schema, open_db
from truth.index.indexer import delete_file_from_index
from truth.store.paths import notes_root
from truth.tools.write import _safe_note_path


def memory_delete(path: str) -> dict:
    """Remove OKF markdown under notes_root and eagerly drop index rows."""
    root = notes_root()
    target = _safe_note_path(path, root)
    rel = str(target.resolve().relative_to(root.resolve()))

    if rel == "log.md":
        raise ValueError("cannot delete log.md")

    if not target.exists():
        raise FileNotFoundError(f"note not found: {rel}")

    conn = open_db()
    init_schema(conn)
    delete_file_from_index(conn, target, root)
    target.unlink()
    return {"path": rel, "deleted": True}
