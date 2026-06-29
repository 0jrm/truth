"""Copy static inspector assets into notes root beside memory.db."""

from __future__ import annotations

import shutil
from pathlib import Path

from truth.store.paths import notes_root

_STATIC_DIR = Path(__file__).resolve().parent / "static"
_ASSETS = (
    "inspector.html",
    "vendor/sql-wasm.js",
    "vendor/sql-wasm.wasm",
)


def export_inspector(dest: Path | None = None) -> Path:
    out = (dest or notes_root()).resolve()
    out.mkdir(parents=True, exist_ok=True)
    for rel in _ASSETS:
        src = _STATIC_DIR / rel
        if not src.is_file():
            raise FileNotFoundError(f"missing static asset: {src}")
        if rel == "inspector.html":
            target = out / "inspector.html"
        else:
            target = out / "vendor" / Path(rel).name
            target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    return out


if __name__ == "__main__":
    path = export_inspector()
    print(f"exported to {path}")
