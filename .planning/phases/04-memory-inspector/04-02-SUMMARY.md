---
phase: 04-memory-inspector
plan: "02"
subsystem: ui
tags: [python, http-server, static-html, inspector]

requires:
  - phase: 04-memory-inspector
    provides: truth.inspect data functions from 04-01
provides:
  - truth serve JSON API + inspector.html
affects: [phase-5-integration]

tech-stack:
  added: []
  patterns:
    - "stdlib ThreadingHTTPServer on 127.0.0.1"
    - "Single static HTML, no build step"

key-files:
  created:
    - truth/serve.py
    - truth/static/inspector.html
  modified:
    - truth/cli.py

key-decisions:
  - "Default port 8765; bind localhost only"
  - "No in-browser markdown viewer (v2 deferred)"

patterns-established:
  - "API routes: /api/tree, /api/links, /api/changes, /api/graph"

requirements-completed: [INSPECT-05]

duration: 10min
completed: 2026-06-29
---

# 04-02 Summary: Static Inspector + JSON API

**Optional browser UI** — `truth serve` exposes the same inspector data via JSON and a minimal three-panel HTML page.

## What was built

- `truth/serve.py` — stdlib HTTP server with JSON API routes
- `truth/static/inspector.html` — tree, links, changes panels via fetch
- `serve` subcommand on `truth` CLI

## Verification

- In-process smoke: `/api/tree` returns 3 notes; `/inspector.html` references `/api/tree`
- Server binds `127.0.0.1` only

## Self-Check: PASSED
