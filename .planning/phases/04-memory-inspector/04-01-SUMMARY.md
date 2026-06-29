---
phase: 04-memory-inspector
plan: "01"
subsystem: cli
tags: [python, inspector, argparse, links, events]

requires:
  - phase: 02-hybrid-index
    provides: events table, list_events
  - phase: 01-okf-memory-store
    provides: extract_links, frontmatter parser
provides:
  - truth CLI with tree, links, changes, graph --json
  - truth.inspect package (read-only over notes + SQLite)
affects: [04-02, phase-5-integration]

tech-stack:
  added: []
  patterns:
    - "Read-only inspector; no SQLite writes"
    - "Paths relative to notes_root; accepts notes/ prefix alias"

key-files:
  created:
    - truth/cli.py
    - truth/inspect/__init__.py
    - truth/inspect/_paths.py
    - truth/inspect/tree.py
    - truth/inspect/links.py
    - truth/inspect/changes.py
    - truth/inspect/graph.py
  modified:
    - pyproject.toml

key-decisions:
  - "Graph/link ids are paths relative to notes root (not project root)"
  - "CLI path arg accepts notes/foo.md or foo.md"

patterns-established:
  - "resolve_note_path rejects traversal outside notes root"

requirements-completed: [INSPECT-01, INSPECT-02, INSPECT-03, INSPECT-04]

duration: 15min
completed: 2026-06-29
---

# 04-01 Summary: CLI Inspector Commands

**CLI-first memory inspector** — `truth tree`, `links`, `changes`, and `graph --json` over OKF notes and the events index.

## What was built

- `truth/inspect/` package reusing `extract_links`, `parse_note_file`, and `list_events`
- `truth/cli.py` argparse entry with four subcommands
- `truth` console script registered in `pyproject.toml`

## Verification

- `truth tree` — shows 3 sample notes with type/title
- `truth links notes/hybrid-search.md` — outgoing edge to sqlite-vectors.md
- `truth changes -n 3` — lists events from memory.db
- `truth graph --json` — valid JSON with 3 nodes, 2 edges

## Self-Check: PASSED
