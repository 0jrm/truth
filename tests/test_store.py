"""Unit tests for OKF store layer (frontmatter, links, path safety)."""

from __future__ import annotations

from pathlib import Path

import pytest

from truth.store.frontmatter import format_note, parse_note, split_frontmatter
from truth.store.links import extract_links, extract_links_from_body
from truth.tools.write import _safe_note_path


def test_format_note_round_trip():
    meta = {"type": "Note", "title": "Título", "tags": ["a", "b"]}
    body = "Body with unicode: café\n"
    text = format_note(meta, body)
    parsed = parse_note(text)
    assert parsed.meta["type"] == "Note"
    assert parsed.meta["title"] == "Título"
    assert parsed.body == body


def test_split_frontmatter_no_block():
    meta, body = split_frontmatter("plain text\n")
    assert meta == {}
    assert body == "plain text\n"


def test_safe_note_path_rejects_traversal(tmp_path):
    root = tmp_path / "notes"
    root.mkdir()
    with pytest.raises(ValueError, match="invalid note path"):
        _safe_note_path("../etc/passwd", root)
    with pytest.raises(ValueError, match="invalid note path"):
        _safe_note_path("/abs/path.md", root)
    with pytest.raises(ValueError, match="must end with .md"):
        _safe_note_path("notes.txt", root)


def test_safe_note_path_accepts_relative(tmp_path):
    root = tmp_path / "notes"
    root.mkdir()
    target = _safe_note_path("sub/note.md", root)
    assert target == (root / "sub" / "note.md").resolve()


def test_extract_links_filters_external(tmp_path):
    root = tmp_path
    source = root / "a.md"
    source.write_text("---\ntype: Note\n---\n", encoding="utf-8")
    body = (
        "See [local](sub/b.md) and [web](https://example.com) "
        "and [mail](mailto:x@y.com).\n"
    )
    edges = extract_links_from_body(source, body, root)
    assert len(edges) == 1
    assert edges[0].target.name == "b.md"
    assert edges[0].label == "local"


def test_extract_links_relative_resolution(tmp_path):
    root = tmp_path
    sub = root / "sub"
    sub.mkdir()
    a = root / "a.md"
    b = sub / "b.md"
    a.write_text("---\ntype: Note\n---\nLink [b](sub/b.md).\n", encoding="utf-8")
    b.write_text("---\ntype: Note\n---\n\n", encoding="utf-8")
    edges = extract_links(a, root)
    assert len(edges) == 1
    assert edges[0].target.resolve() == b.resolve()
