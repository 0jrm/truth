"""Watcher concurrency + log.md skip regression gate — isolated temp notes + DB."""

from __future__ import annotations

import os
import tempfile
import threading
import time
from pathlib import Path

# ponytail: global env + singleton reset — acceptable for one regression module; Phase 9 may move to pytest

_PATHS = ("concurrent-a.md", "concurrent-b.md")
_POLL_TIMEOUT_SEC = 60


def _wait_for_chunks(conn, paths: tuple[str, ...], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if all(
            conn.execute("SELECT COUNT(*) FROM chunks WHERE path=?", (p,)).fetchone()[0] >= 1
            for p in paths
        ):
            return
        time.sleep(0.25)
    counts = {
        p: conn.execute("SELECT COUNT(*) FROM chunks WHERE path=?", (p,)).fetchone()[0]
        for p in paths
    }
    raise AssertionError(f"chunks not indexed within {timeout}s: {counts}")


def run_watcher_correctness_check() -> None:
    import truth.index.db as db_module
    from truth.index.db import open_db
    from truth.index.watcher import start_watcher
    from truth.tools.write import memory_write

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        os.environ["TRUTH_NOTES_ROOT"] = str(tmp_path)
        os.environ["TRUTH_DB_PATH"] = str(tmp_path / "memory.db")
        db_module._CONN = None

        observer = start_watcher(block=False, notes=tmp_path)

        def _writer(path: str, prefix: str) -> None:
            for i in range(5):
                memory_write(
                    path,
                    f"{prefix} body revision {i} for watcher concurrency check.",
                    title=f"{prefix} note",
                )

        threads = [
            threading.Thread(target=_writer, args=("concurrent-a.md", "alpha")),
            threading.Thread(target=_writer, args=("concurrent-b.md", "beta")),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        conn = open_db()
        _wait_for_chunks(conn, _PATHS, _POLL_TIMEOUT_SEC)

        log_chunks = conn.execute(
            "SELECT COUNT(*) FROM chunks WHERE path='log.md'"
        ).fetchone()[0]
        assert log_chunks == 0, f"log.md must have zero chunks, got {log_chunks}"

        observer.stop()
        observer.join()


if __name__ == "__main__":
    run_watcher_correctness_check()
    print("watcher_correctness=ok")
