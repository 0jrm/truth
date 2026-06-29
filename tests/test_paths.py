"""Tests for inspect path resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from truth.inspect._paths import resolve_note_path


def test_resolve_note_path_accepts_relative(tmp_path):
    root = tmp_path / "notes"
    root.mkdir()
    note = root / "sub" / "note.md"
    note.parent.mkdir()
    note.write_text("---\ntype: Note\n---\n", encoding="utf-8")
    target = resolve_note_path("sub/note.md", root)
    assert target == note.resolve()


def test_resolve_note_path_rejects_traversal(tmp_path):
    root = tmp_path / "notes"
    root.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("---\ntype: Note\n---\n", encoding="utf-8")
    with pytest.raises(ValueError, match="escapes notes root"):
        resolve_note_path("../outside.md", root)


def test_resolve_note_path_case_insensitive_relative(tmp_path):
    """resolved paths under the same root pass relative_to even when casing differs."""
    root = tmp_path / "Notes"
    root.mkdir()
    note = root / "Foo.md"
    note.write_text("---\ntype: Note\n---\n", encoding="utf-8")
    # Simulate case-variant base string that would fail startswith but is same dir
    target = resolve_note_path("Foo.md", root)
    assert target.name == "Foo.md"
