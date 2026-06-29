from __future__ import annotations

import os
import tempfile
from pathlib import Path

from truth.index.db import init_schema, open_db
from truth.index.indexer import delete_file_from_index, index_file
from truth.store.paths import notes_root
from truth.tools.write import _safe_note_path, memory_write


def memory_delete(path: str) -> dict:
    """Remove OKF markdown under notes_root. Watcher cleans index; no SQLite writes here."""
    root = notes_root()
    target = _safe_note_path(path, root)
    rel = str(target.resolve().relative_to(root.resolve()))

    if rel == "log.md":
        raise ValueError("cannot delete log.md")

    if not target.exists():
        raise FileNotFoundError(f"note not found: {rel}")

    target.unlink()
    return {"path": rel, "deleted": True}


if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["TRUTH_NOTES_ROOT"] = tmp
        os.environ["TRUTH_DB_PATH"] = str(Path(tmp) / "memory.db")

        written = memory_write("delete-me.md", "ponytail delete selfcheck body")
        root = notes_root()
        conn = open_db()
        init_schema(conn)
        index_file(conn, written, root)

        count = conn.execute(
            "SELECT COUNT(*) FROM chunks WHERE path='delete-me.md'"
        ).fetchone()[0]
        assert count > 0, count

        result = memory_delete("delete-me.md")
        assert result == {"path": "delete-me.md", "deleted": True}
        assert not (root / "delete-me.md").exists()

        delete_file_from_index(conn, root / "delete-me.md", root)
        count = conn.execute(
            "SELECT COUNT(*) FROM chunks WHERE path='delete-me.md'"
        ).fetchone()[0]
        assert count == 0, count

        try:
            memory_delete("log.md")
            raise SystemExit("expected ValueError for log.md")
        except ValueError as exc:
            assert "log.md" in str(exc)

        try:
            memory_delete("../etc/passwd")
            raise SystemExit("expected ValueError for traversal")
        except ValueError:
            pass

    print("ok")
