"""Shared pytest fixtures for Truth regression tests."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

import truth.index.db as db_module


@pytest.fixture
def isolated_truth():
    """Temp notes root + DB path; resets db singleton for function scope."""
    orig_notes = os.environ.get("TRUTH_NOTES_ROOT")
    orig_db = os.environ.get("TRUTH_DB_PATH")
    orig_conn = db_module._CONN

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        os.environ["TRUTH_NOTES_ROOT"] = str(tmp_path)
        os.environ["TRUTH_DB_PATH"] = str(tmp_path / "memory.db")
        db_module._CONN = None
        yield tmp_path

    if orig_notes is None:
        os.environ.pop("TRUTH_NOTES_ROOT", None)
    else:
        os.environ["TRUTH_NOTES_ROOT"] = orig_notes
    if orig_db is None:
        os.environ.pop("TRUTH_DB_PATH", None)
    else:
        os.environ["TRUTH_DB_PATH"] = orig_db
    db_module._CONN = orig_conn
