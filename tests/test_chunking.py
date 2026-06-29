"""Pytest wrapper for chunker boundary regression."""

from truth.index.chunking import assert_overlap_preserves_paragraph_boundary


def test_overlap_preserves_paragraph_boundary():
    assert_overlap_preserves_paragraph_boundary()
