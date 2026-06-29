"""Agent API regression — filters, overwrite, delete."""

from __future__ import annotations

from truth.index.db import open_db, reset_db_singleton
from truth.index.indexer import index_all
from truth.index.search import memory_search
from truth.store.frontmatter import format_note
from truth.tools.delete import memory_delete
from truth.tools.write import memory_write


def test_agent_api_filters_overwrite_delete(isolated_truth):
    root = isolated_truth
    reset_db_singleton()

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

    index_all(root)

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
    conn = open_db()
    count = conn.execute(
        "SELECT COUNT(*) FROM chunks WHERE path='overwrite/test.md'"
    ).fetchone()[0]
    assert count == 0, count
