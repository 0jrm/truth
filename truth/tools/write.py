from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from truth.store.frontmatter import format_note, split_frontmatter, validate_frontmatter
from truth.store.paths import notes_root


def _safe_note_path(rel: str, root: Path) -> Path:
    """Resolve relative path under notes root; reject traversal and non-.md."""
    if not rel or rel.startswith("/") or ".." in Path(rel).parts:
        raise ValueError(f"invalid note path: {rel!r}")
    if not rel.lower().endswith(".md"):
        raise ValueError(f"note path must end with .md: {rel!r}")

    root_resolved = root.resolve()
    target = (root_resolved / rel).resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"path escapes notes root: {rel!r}") from exc
    return target


def _relative_note_path(target: Path, root: Path) -> str:
    return str(target.resolve().relative_to(root.resolve()))


def _body_summary(body: str, max_len: int = 120) -> str:
    for line in body.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:max_len]
    return "(empty)"


def _append_log(root: Path, rel_path: str, summary: str) -> None:
    """Append OKF changelog entry to notes/log.md."""
    log_path = root / "log.md"
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    line = f"- {ts} **{rel_path}** — {summary}\n"
    if not log_path.exists():
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            format_note({"type": "Log", "title": "Changelog"}, ""),
            encoding="utf-8",
        )
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line)


def memory_write(
    path: str,
    content: str,
    *,
    type: str = "Note",
    title: str | None = None,
    summary: str | None = None,
) -> dict:
    """Write OKF markdown under notes_root. Watcher indexes; no SQLite writes here."""
    root = notes_root()
    target = _safe_note_path(path, root)

    if content.startswith("---\n"):
        meta, body = split_frontmatter(content)
        meta = validate_frontmatter(meta, auto_type=type)
    else:
        meta = validate_frontmatter({"type": type}, auto_type=type)
        body = content

    if title is not None:
        meta["title"] = title

    text = format_note(meta, body)
    previous = target.read_text(encoding="utf-8") if target.exists() else None
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")

    rel = _relative_note_path(target, root)
    _append_log(root, rel, summary or _body_summary(body))

    return {"path": rel, "previous": previous}

