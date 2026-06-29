import json
from pathlib import Path

from truth.store.frontmatter import parse_note_file
from truth.store.links import extract_links
from truth.store.paths import notes_root

from ._paths import rel_note_path


def build_graph(root: Path | None = None) -> dict:
    """Nodes and edges for external tools (Obsidian, etc.)."""
    base = (root or notes_root()).resolve()
    nodes: list[dict] = []
    edges: list[dict] = []
    seen_nodes: set[str] = set()

    if not base.is_dir():
        return {"nodes": nodes, "edges": edges}

    for path in sorted(base.rglob("*.md")):
        if not path.is_file():
            continue
        rel = rel_note_path(path, base)
        try:
            note = parse_note_file(path)
            node = {
                "id": rel,
                "type": str(note.meta.get("type", "")),
                "title": str(note.meta.get("title", "") or path.stem),
            }
        except (ValueError, OSError):
            node = {"id": rel, "type": "?", "title": path.stem}
        nodes.append(node)
        seen_nodes.add(rel)

    for md in sorted(base.rglob("*.md")):
        if not md.is_file():
            continue
        for edge in extract_links(md, base):
            src = rel_note_path(edge.source, base)
            tgt = rel_note_path(edge.target, base)
            if tgt not in seen_nodes:
                nodes.append({"id": tgt, "type": "?", "title": Path(tgt).stem})
                seen_nodes.add(tgt)
            edges.append({"source": src, "target": tgt, "label": edge.label})

    return {"nodes": nodes, "edges": edges}


def graph_json(root: Path | None = None) -> str:
    return json.dumps(build_graph(root), indent=2)


if __name__ == "__main__":
    g = build_graph()
    assert "nodes" in g and "edges" in g
    parsed = json.loads(graph_json())
    assert isinstance(parsed["nodes"], list)
    print("graph ok")
