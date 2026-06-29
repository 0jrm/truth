#!/usr/bin/env python3
"""End-to-end smoke test for Truth integration."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

# ponytail: running as truth/smoke.py puts truth/ on sys.path and shadows stdlib inspect
_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
_script_dir = str(Path(__file__).resolve().parent)
sys.path[:] = [p for p in sys.path if p != _script_dir]


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory() as td:
        notes = Path(td) / "notes"
        notes.mkdir()
        db = notes / "memory.db"
        os.environ["TRUTH_NOTES_ROOT"] = str(notes)
        os.environ["TRUTH_DB_PATH"] = str(db)

        seed = notes / "seed.md"
        seed.write_text(
            "---\ntype: Note\ntitle: Seed\n---\nSeed note about quantum storage.\n",
            encoding="utf-8",
        )

        from truth.index.indexer import index_all
        from truth.tools import memory_search, memory_write

        index_all(notes)
        memory_write(
            "facts/smoke.md",
            "Smoke test fact: the indexer finds this sentence.",
            title="Smoke fact",
        )
        index_all(notes)

        hits = memory_search("smoke test fact indexer", k=3)
        if not any("smoke" in (h.get("path") or "") for h in hits):
            print("FAIL: memory_search did not find written note", file=sys.stderr)
            return 1

        env = os.environ.copy()
        tree = subprocess.run(
            [sys.executable, "-m", "truth.cli", "tree"],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if tree.returncode != 0:
            print(tree.stderr, file=sys.stderr)
            return 1
        if "facts/smoke.md" not in tree.stdout:
            print("FAIL: truth tree missing written note", file=sys.stderr)
            return 1

        changes = subprocess.run(
            [sys.executable, "-m", "truth.cli", "changes", "-n", "5"],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if changes.returncode != 0:
            print(changes.stderr, file=sys.stderr)
            return 1

    print("smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
