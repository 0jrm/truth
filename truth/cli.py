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


def _cmd_serve(args: argparse.Namespace) -> int:
    from truth.serve import run_server

    run_server(host=args.host, port=args.port)
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

    p_serve = sub.add_parser("serve", help="Serve JSON API + static inspector HTML")
    p_serve.add_argument("--port", type=int, default=8765)
    p_serve.add_argument("--host", default="127.0.0.1")

    args = parser.parse_args(argv)
    handlers = {
        "tree": _cmd_tree,
        "links": _cmd_links,
        "changes": _cmd_changes,
        "graph": _cmd_graph,
        "serve": _cmd_serve,
    }
    try:
        return handlers[args.command](args)
    except ValueError as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
