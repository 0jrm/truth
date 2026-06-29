"""Pytest wrapper for 5-note search quality regression gate."""

from truth.index.search_quality import run_search_quality_check


def test_search_quality_rank_one():
    run_search_quality_check()
