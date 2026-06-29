import os
from pathlib import Path


def notes_root(base: Path | None = None) -> Path:
    """MEM-01: configurable root, default notes/."""
    raw = os.environ.get("TRUTH_NOTES_ROOT", "notes")
    root = Path(raw) if base is None else base / raw
    return root.resolve()
