import logging
import queue
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from truth.store.paths import notes_root

from .db import init_schema, open_db
from .indexer import delete_file_from_index, index_file

_DEBOUNCE_SEC = 0.5
_QUEUE_MAX = 500
_LOG = logging.getLogger(__name__)


class _DebouncedIndexer(FileSystemEventHandler):
    def __init__(self, notes: Path) -> None:
        self._notes = notes
        self._timers: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()
        self._queue: queue.Queue = queue.Queue(maxsize=_QUEUE_MAX)
        self._writer = threading.Thread(target=self._writer_loop, daemon=True)
        self._writer.start()

    def _enqueue(self, item: tuple[str, Path]) -> None:
        depth = self._queue.qsize()
        if depth >= 100:
            _LOG.warning("watcher queue depth=%s (max=%s)", depth, _QUEUE_MAX)
        self._queue.put(item)

    def _writer_loop(self) -> None:
        conn = open_db()
        init_schema(conn)
        while True:
            kind, path = self._queue.get()
            if kind == "index":
                index_file(conn, path, self._notes)
            elif kind == "delete":
                delete_file_from_index(conn, path, self._notes)
            depth = self._queue.qsize()
            if depth:
                _LOG.info("watcher queue depth=%s", depth)

    def _schedule(self, key: str, fn) -> None:
        with self._lock:
            old = self._timers.pop(key, None)
            if old:
                old.cancel()
            timer = threading.Timer(_DEBOUNCE_SEC, fn)
            self._timers[key] = timer
            timer.start()

    def _rel_md(self, src_path: str) -> Path | None:
        path = Path(src_path)
        if path.suffix.lower() != ".md" or path.name.startswith("."):
            return None
        try:
            path.resolve().relative_to(self._notes.resolve())
        except ValueError:
            return None
        return path

    def on_created(self, event) -> None:
        if event.is_directory:
            return
        path = self._rel_md(event.src_path)
        if path is None:
            return
        key = str(path)

        def _index() -> None:
            self._enqueue(("index", path))

        self._schedule(key, _index)

    def on_modified(self, event) -> None:
        self.on_created(event)

    def on_deleted(self, event) -> None:
        if event.is_directory:
            return
        path = self._rel_md(event.src_path)
        if path is None:
            return
        key = str(path)

        def _delete() -> None:
            self._enqueue(("delete", path))

        self._schedule(key, _delete)


def start_watcher(block: bool = True, notes: Path | None = None) -> Observer:
    root = notes or notes_root()
    handler = _DebouncedIndexer(root)
    observer = Observer()
    observer.schedule(handler, str(root), recursive=True)
    observer.start()
    if block:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    return observer
