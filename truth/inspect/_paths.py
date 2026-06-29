from pathlib import Path

from truth.store.paths import notes_root


def resolve_note_path(rel: str, root: Path | None = None) -> Path:
    """Resolve rel path under notes root; reject traversal."""
    base = (root or notes_root()).resolve()
    rel = rel.strip().lstrip("/")
    # ponytail: accept `notes/foo.md` from CLI examples as alias for `foo.md`
    base_name = base.name
    if rel.startswith(f"{base_name}/"):
        rel = rel[len(base_name) + 1 :]
    target = (base / rel).resolve()
    if not str(target).startswith(str(base)):
        raise ValueError(f"path escapes notes root: {rel}")
    if target.suffix != ".md":
        raise ValueError(f"not a markdown note: {rel}")
    return target


def rel_note_path(path: Path, root: Path | None = None) -> str:
    base = (root or notes_root()).resolve()
    return path.resolve().relative_to(base).as_posix()
