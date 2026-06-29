"""Chunker boundary regression."""

from truth.index.chunking import chunk_text


def test_overlap_preserves_paragraph_boundary():
    p1 = "A" * 40
    p2 = "B" * 40
    body = f"{p1}\n\n{p2}"
    chunks = chunk_text(body, target=50, overlap=20)
    assert len(chunks) >= 2, chunks
    assert any("\n\n" in c and "A" in c and "B" in c for c in chunks[1:]), chunks
