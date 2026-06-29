"""Verify wheel includes static and bundled agent assets."""

from __future__ import annotations

from pathlib import Path


def test_static_and_bundled_files_on_disk():
    pkg = Path(__file__).resolve().parents[1] / "truth"
    assert (pkg / "static" / "inspector.html").is_file()
    assert (pkg / "static" / "vendor" / "sql-wasm.wasm").is_file()
    assert (pkg / "bundled" / "truth-memory" / "SKILL.md").is_file()
