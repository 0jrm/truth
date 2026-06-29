from pathlib import Path

from truth.store.links import extract_links
from truth.store.paths import notes_root

from ._paths import rel_note_path, resolve_note_path


def _edge_dict(edge, root: Path) -> dict:
    return {
        "source": rel_note_path(edge.source, root),
        "target": rel_note_path(edge.target, root),
        "label": edge.label,
    }


def note_links(rel_path: str, root: Path | None = None) -> dict:
    """Incoming and outgoing link edges for one note (paths relative to root)."""
    base = (root or notes_root()).resolve()
    target = resolve_note_path(rel_path, base)

    outgoing: list[dict] = []
    incoming: list[dict] = []

    all_edges: list = []
    for md in sorted(base.rglob("*.md")):
        if md.is_file():
            all_edges.extend(extract_links(md, base))

    target_rel = rel_note_path(target, base)
    for edge in all_edges:
        d = _edge_dict(edge, base)
        if d["source"] == target_rel:
            outgoing.append(d)
        if d["target"] == target_rel:
            incoming.append(d)

    return {"path": target_rel, "outgoing": outgoing, "incoming": incoming}

