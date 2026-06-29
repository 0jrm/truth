"""Headless serve: index on startup + file watcher until Ctrl+C."""

from __future__ import annotations

from truth.index.indexer import index_all
from truth.index.watcher import start_watcher
from truth.store.paths import db_path, notes_root


def run_serve() -> None:
    root = notes_root()
    db = db_path()
    print(f"Truth serve — notes={root} db={db}", flush=True)
    indexed = index_all(root)
    print(f"Indexed {indexed} file(s) on startup", flush=True)
    observer = start_watcher(block=False, notes=root)
    print("Watching for changes (Ctrl+C to stop)", flush=True)
    try:
        observer.join()
    except KeyboardInterrupt:
        print("\nStopping...", flush=True)
    finally:
        observer.stop()
        observer.join()
        print("Stopped.", flush=True)


if __name__ == "__main__":
    run_serve()
