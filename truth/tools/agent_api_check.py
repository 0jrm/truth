"""Phase 8 agent API regression gate — filters, overwrite, delete."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

# ponytail: global env + singleton reset — acceptable for one regression module; Phase 9 may move to pytest


def run_agent_api_check() -> None:
    import truth.index.db as db_module
    from truth.index.indexer import delete_file_from_index, index_all
    from truth.index.search import memory_search
    from truth.store.frontmatter import format_note
    from truth.tools.delete import memory_delete
    from truth.tools.write import memory_write

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        os.environ["TRUTH_NOTES_ROOT"] = str(tmp_path)
        os.environ["TRUTH_DB_PATH"] = str(tmp_path / "memory.db")
        db_module._CONN = None

        memory_write(
            "filters/decision.md",
            format_note(
                {"type": "Decision", "tags": ["python", "api"], "title": "API choice"},
                "Python API design for the agent memory layer and hybrid search.",
            ),
        )
        memory_write(
            "filters/note.md",
            format_note(
                {"type": "Note", "tags": ["python"], "title": "Python note"},
                "General python programming tips unrelated to API design.",
            ),
        )

        index_all(tmp_path)

        type_hits = memory_search("python", k=5, type="Decision")
        assert type_hits, "expected type=Decision hits"
        assert all(h["path"] == "filters/decision.md" for h in type_hits), type_hits

        tag_hits = memory_search("python", k=5, tags=["python", "api"])
        paths = {h["path"] for h in tag_hits}
        assert "filters/decision.md" in paths, tag_hits
        assert "filters/note.md" not in paths, tag_hits

        created = memory_write("overwrite/test.md", "Original overwrite body for agent api check.")
        assert created["previous"] is None

        overwritten = memory_write("overwrite/test.md", "Updated overwrite body for agent api check.")
        assert overwritten["previous"] is not None
        assert "Original overwrite body" in overwritten["previous"]

        memory_delete("overwrite/test.md")
        from truth.index.db import open_db

        conn = open_db()
        delete_file_from_index(conn, tmp_path / "overwrite/test.md", tmp_path)
        count = conn.execute(
            "SELECT COUNT(*) FROM chunks WHERE path='overwrite/test.md'"
        ).fetchone()[0]
        assert count == 0, count


if __name__ == "__main__":
    run_agent_api_check()
    print("agent_api_check=ok")
