"""End-to-end integration smoke test."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from truth.index.indexer import index_all
from truth.tools import memory_search, memory_write


def test_smoke_pipeline(isolated_truth):
    root = isolated_truth
    seed = root / "seed.md"
    seed.write_text(
        "---\ntype: Note\ntitle: Seed\n---\nSeed note about quantum storage.\n",
        encoding="utf-8",
    )

    index_all(root)
    memory_write(
        "facts/smoke.md",
        "Smoke test fact: the indexer finds this sentence.",
        title="Smoke fact",
    )
    index_all(root)

    hits = memory_search("smoke test fact indexer", k=3)
    assert any("smoke" in (h.get("path") or "") for h in hits)

    repo = Path(__file__).resolve().parents[1]
    env = {
        **__import__("os").environ,
        "TRUTH_NOTES_ROOT": str(root),
        "TRUTH_DB_PATH": str(root / "memory.db"),
    }
    tree = subprocess.run(
        [sys.executable, "-m", "truth.cli", "tree"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert tree.returncode == 0, tree.stderr
    assert "facts/smoke.md" in tree.stdout

    changes = subprocess.run(
        [sys.executable, "-m", "truth.cli", "changes", "-n", "5"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert changes.returncode == 0, changes.stderr
