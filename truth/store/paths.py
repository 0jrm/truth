import os
from pathlib import Path


def notes_root(base: Path | None = None) -> Path:
    """MEM-01: configurable root, default notes/."""
    raw = os.environ.get("TRUTH_NOTES_ROOT", "notes")
    root = Path(raw) if base is None else base / raw
    return root.resolve()


def db_path() -> Path:
    """CLI-02: TRUTH_DB_PATH override; default colocated in notes root (Phase 5)."""
    raw = os.environ.get("TRUTH_DB_PATH")
    if raw:
        return Path(raw).resolve()
    return (notes_root() / "memory.db").resolve()
