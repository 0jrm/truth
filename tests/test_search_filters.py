"""Search filter over-fetch: type/tags filters must still return k results."""

from __future__ import annotations

from truth.index.indexer import index_all
from truth.index.search import memory_search
from truth.store.frontmatter import format_note, split_frontmatter
from truth.tools.write import memory_write


def test_filtered_search_returns_k_results(isolated_truth):
    root = isolated_truth
    for i in range(15):
        memory_write(
            f"batch/noise-{i}.md",
            f"Generic filler content number {i} without special tokens.",
            title=f"Noise {i}",
        )
    for i in range(5):
        memory_write(
            f"batch/tagged-{i}.md",
            f"Rare zebra keyword phrase unique token {i} for filter test.",
            title=f"Tagged {i}",
        )
        path = root / f"batch/tagged-{i}.md"
        meta, body = split_frontmatter(path.read_text(encoding="utf-8"))
        meta["tags"] = ["zebra", "filtertest"]
        path.write_text(format_note(meta, body), encoding="utf-8")

    index_all(root)

    hits = memory_search("zebra keyword phrase", k=5, tags=["zebra", "filtertest"])
    paths = {h["path"] for h in hits}
    assert len(hits) == 5, f"expected 5 filtered hits, got {len(hits)}: {paths}"
    assert all(p.startswith("batch/tagged-") for p in paths)
