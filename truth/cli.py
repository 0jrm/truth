"""Truth CLI — memory inspector commands."""

import argparse
import json
import sys

from truth.inspect.changes import recent_changes
from truth.inspect.graph import build_graph
from truth.inspect.links import note_links
from truth.inspect.tree import format_tree


def _cmd_tree(_args: argparse.Namespace) -> int:
    sys.stdout.write(format_tree())
    return 0


def _cmd_links(args: argparse.Namespace) -> int:
    data = note_links(args.path)
    sys.stdout.write(f"Note: {data['path']}\n\n")
    sys.stdout.write("Outgoing:\n")
    if data["outgoing"]:
        for e in data["outgoing"]:
            label = f' "{e["label"]}"' if e["label"] else ""
            sys.stdout.write(f"  → {e['target']}{label}\n")
    else:
        sys.stdout.write("  (none)\n")
    sys.stdout.write("\nIncoming:\n")
    if data["incoming"]:
        for e in data["incoming"]:
            label = f' "{e["label"]}"' if e["label"] else ""
            sys.stdout.write(f"  ← {e['source']}{label}\n")
    else:
        sys.stdout.write("  (none)\n")
    return 0


def _cmd_changes(args: argparse.Namespace) -> int:
    for ev in recent_changes(args.n):
        sys.stdout.write(f"{ev['ts']}  {ev['op']:6}  {ev['path']}\n")
    return 0


def _cmd_graph(args: argparse.Namespace) -> int:
    data = build_graph()
    if args.json:
        sys.stdout.write(json.dumps(data, indent=2) + "\n")
    else:
        sys.stdout.write(f"nodes: {len(data['nodes'])}, edges: {len(data['edges'])}\n")
    return 0


def _cmd_serve(_args: argparse.Namespace) -> int:
    from truth.serve import run_serve

    run_serve()
    return 0


def _cmd_mcp(_args: argparse.Namespace) -> int:
    from truth.mcp_server import main as mcp_main

    mcp_main()
    return 0


def _cmd_index(_args: argparse.Namespace) -> int:
    from truth.index.indexer import index_all

    count = index_all()
    print(f"indexed_files={count}")
    return 0


def _cmd_export(_args: argparse.Namespace) -> int:
    from truth.export import export_inspector

    path = export_inspector()
    print(f"exported inspector to {path}")
    return 0


def _cmd_skill_install(args: argparse.Namespace) -> int:
    from truth.skill_install import install_skill

    written = install_skill(
        target=Path(args.directory) if args.directory else None,
        personal=args.personal,
        force=args.force,
        mcp=not args.no_mcp,
    )
    if not written:
        print("nothing to install (files exist; use --force to overwrite)")
        return 0
    for path in written:
        print(f"installed {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="truth", description="Truth memory inspector")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("tree", help="Show notes folder hierarchy with type/title")

    p_links = sub.add_parser("links", help="Show incoming/outgoing links for a note")
    p_links.add_argument("path", help="Note path relative to notes root (e.g. notes/foo.md)")

    p_changes = sub.add_parser("changes", help="Recent file ops from events table")
    p_changes.add_argument("-n", type=int, default=20, help="Number of events (default 20)")

    p_graph = sub.add_parser("graph", help="Export link graph")
    p_graph.add_argument("--json", action="store_true", help="Output JSON nodes/edges")

    sub.add_parser("mcp", help="Run stdio MCP server for agent tools")
    sub.add_parser("serve", help="Index notes and watch for changes (Ctrl+C to stop)")
    sub.add_parser("index", help="One-shot full reindex")
    sub.add_parser("export", help="Copy static browser inspector into notes root")

    p_skill = sub.add_parser("skill", help="Install truth-memory agent skill for Cursor")
    skill_sub = p_skill.add_subparsers(dest="skill_command", required=True)
    p_install = skill_sub.add_parser("install", help="Copy skill, rule, prompt, and MCP config")
    p_install.add_argument(
        "--directory",
        help="Project root (default: current directory)",
    )
    p_install.add_argument(
        "--personal",
        action="store_true",
        help="Install skill to ~/.cursor/skills/ only (no rule or mcp.json)",
    )
    p_install.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing skill/rule/prompt files",
    )
    p_install.add_argument(
        "--no-mcp",
        action="store_true",
        help="Do not create .cursor/mcp.json",
    )

    args = parser.parse_args(argv)
    handlers = {
        "tree": _cmd_tree,
        "links": _cmd_links,
        "changes": _cmd_changes,
        "graph": _cmd_graph,
        "mcp": _cmd_mcp,
        "serve": _cmd_serve,
        "index": _cmd_index,
        "export": _cmd_export,
    }
    if args.command == "skill":
        return _cmd_skill_install(args)
    try:
        return handlers[args.command](args)
    except ValueError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
