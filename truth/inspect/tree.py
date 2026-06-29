from pathlib import Path

from truth.store.frontmatter import parse_note_file
from truth.store.paths import notes_root

from ._paths import rel_note_path


def build_tree(root: Path | None = None) -> list[dict]:
    """Flat list of notes with rel_path, type, title (sorted by path)."""
    base = (root or notes_root()).resolve()
    if not base.is_dir():
        return []

    items: list[dict] = []
    for path in sorted(base.rglob("*.md")):
        if not path.is_file():
            continue
        rel = rel_note_path(path, base)
        try:
            note = parse_note_file(path)
            note_type = str(note.meta.get("type", ""))
            title = str(note.meta.get("title", "") or path.stem)
        except (ValueError, OSError):
            note_type = "?"
            title = path.stem
        depth = len(Path(rel).parts) - 1
        items.append(
            {
                "path": rel,
                "type": note_type,
                "title": title,
                "depth": depth,
            }
        )
    return items


def format_tree(root: Path | None = None) -> str:
    lines: list[str] = []
    base = (root or notes_root()).resolve()
    lines.append(f"{base.name}/")
    for item in build_tree(base):
        indent = "  " * (item["depth"] + 1)
        lines.append(f"{indent}{item['path']}  [{item['type']}]  {item['title']}")
    return "\n".join(lines) + "\n"

