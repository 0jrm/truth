"""Integration tests for Truth Phase 5."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_smoke_script_exits_zero():
    repo = Path(__file__).resolve().parents[1]
    proc = subprocess.run(
        [sys.executable, "-m", "truth.smoke"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert "smoke ok" in proc.stdout
