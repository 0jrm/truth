import re
from dataclasses import dataclass
from pathlib import Path

from .frontmatter import parse_note_file
from .paths import notes_root as default_notes_root

# ponytail: regex only handles [text](path), not [[wiki]] — upgrade to AST/wiki parser if needed
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")


@dataclass(frozen=True)
class LinkEdge:
    source: Path
    target: Path
    label: str


def _is_graph_target(raw: str) -> bool:
    """MEM-04: internal file links only."""
    return not raw.startswith(("http://", "https://", "mailto:", "#"))


def resolve_link(source: Path, raw_target: str, root: Path) -> Path:
    """Resolve relative to source.parent; normalize via resolve()."""
    source = source.resolve()
    root = root.resolve()
    if raw_target.startswith("/"):
        target = (root / raw_target.lstrip("/")).resolve()
    else:
        target = (source.parent / raw_target).resolve()
    return target


def extract_links_from_body(source: Path, body: str, root: Path) -> list[LinkEdge]:
    """Regex scan body, filter graph targets, resolve paths."""
    source = source.resolve()
    root = root.resolve()
    edges: list[LinkEdge] = []
    for label, raw_target in LINK_RE.findall(body):
        raw_target = raw_target.strip()
        if not _is_graph_target(raw_target):
            continue
        target = resolve_link(source, raw_target, root)
        edges.append(LinkEdge(source=source, target=target, label=label))
    return edges


def extract_links(path: Path, notes_root: Path | None = None) -> list[LinkEdge]:
    """parse_note_file(path) then extract_links_from_body."""
    root = notes_root if notes_root is not None else default_notes_root()
    note = parse_note_file(path)
    return extract_links_from_body(note.path or path, note.body, root)


if __name__ == "__main__":
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as td:
        root = Path(td)
        a = root / "a.md"
        b = root / "sub" / "b.md"
        b.parent.mkdir()
        a.write_text("---\ntype: Note\n---\nSee [b](sub/b.md).\n", encoding="utf-8")
        b.write_text("---\ntype: Note\n---\nNo links.\n", encoding="utf-8")
        edges = extract_links(a, root)
        assert len(edges) == 1 and edges[0].target.name == "b.md"

    repo_notes = Path("notes")
    if (repo_notes / "okf-format.md").exists():
        root = default_notes_root()
        seed_edges: list[LinkEdge] = []
        for md in sorted(root.glob("*.md")):
            seed_edges.extend(extract_links(md, root))
        assert len(seed_edges) >= 2, f"expected >=2 seed edges, got {len(seed_edges)}"

    print("links ok")
