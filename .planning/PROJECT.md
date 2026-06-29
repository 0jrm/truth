# Truth

## What This Is

Truth is a local-first agent memory system: OKF-compliant markdown files are the source of truth, a SQLite index provides fast hybrid search, and agents maintain the knowledge base via two tools (`memory_search`, `memory_write`). A memory inspector — CLI first, optional static HTML in the browser — lets you see the file tree, link relationships, and changelog. All offline, no cloud, no SDK required to read the data.

## Core Value

Agents can read before they act and write after they learn, with human-readable markdown as the durable record and instant search over that record.

## Requirements

### Validated

- OKF-compliant markdown store with enforced `type` frontmatter — **Validated in Phase 1**
- Cross-links parseable for graph building (MEM-04) — **Validated in Phase 1**
- Configurable `notes/` knowledge root — **Validated in Phase 1**
- SQLite index with local embeddings and content-hash change detection — **Validated in Phase 2**
- Hybrid search (vector + BM25 + RRF merge) — **Validated in Phase 2**
- File watcher re-indexes only changed files; events table tracks create/update/delete — **Validated in Phase 2**
- Agent tools `memory_search` / `memory_write` with function-calling schemas — **Validated in Phase 3**
- OKF `log.md` append on writes — **Validated in Phase 3**
- Agent system prompt contract (search before answer, write after learn) — **Validated in Phase 3**
- Memory inspector: CLI (`tree`, `links`, `changes`, `graph --json`) + optional static HTML — **Validated in Phase 4**

### Active

- [ ] CLI entry point, config, unified `truth serve`, README (Phase 5)

### Out of Scope

- Cloud sync or multi-user auth — local single-user tool
- Ollama/LLM runtime itself — integrate via tools, don't embed a model server
- Graph database — link graph built from markdown links at index time
- Docker deployment — pip install and run
- Custom markdown editor / WYSIWYG — use existing editor (VS Code, Obsidian)
- Full interactive dashboard — force-directed graphs, in-browser markdown viewer, live SSE (v2)
- Mobile app — CLI + optional browser inspector for v1

## Context

Google's Open Knowledge Format (OKF, June 2026) stores knowledge as markdown + YAML frontmatter with `type` as the only required field. Cross-links form a knowledge graph. Optional `index.md` and `log.md` provide navigation and chronological history. This project is ~95% aligned already: markdown folders as truth, SQLite as derived index.

Key architectural insight from vision doc: **never write to SQLite directly** — agents write markdown; the indexer keeps SQLite in sync. Andrej Karpathy's framing: LLMs don't forget cross-references or get bored updating 15 files.

The inspector is observability for humans, not core to the agent loop. CLI commands cover 80% of the value; browser UI is optional polish on the same JSON API.

Reference doc: `VISION.MD` in project root.

## Constraints

- **Tech**: Python 3.11+, sqlite-vec, sentence-transformers, watchdog — matches vision stack
- **Local-only**: All data and embeddings stay on disk; no external API calls for core loop
- **OKF compliance**: Every ingested/written file must have YAML frontmatter with at least `type`
- **Simplicity**: Indexer target ~50–200 lines of core logic; avoid frameworks beyond what's needed
- **Inspector**: CLI-first; optional single static HTML page + JSON API (no React build step for v1)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Markdown as truth, SQLite as index | OKF alignment; human-readable; agents write files not DB rows | ✓ Phase 1 store layer |
| Hybrid search (vector + BM25 + RRF) | Better recall than either alone; standard pattern for local RAG | ✓ Phase 2 |
| Inspector-first, not dashboard | CLI + event log + optional static HTML; full dashboard deferred to v2 | ✓ Accepted 2026-06-28 |
| Events table for changelog | File mtime alone misses deletes and is unreliable; watcher writes events | ✓ Phase 2 |
| OKF `log.md` on write | Human-readable changelog with zero UI; agent-maintained per OKF convention | — Pending Phase 3 |
| Local ONNX embeddings | Offline, no Ollama dependency for search | ✓ Phase 2 (MiniLM via sentence-transformers) |
| `notes/` as default knowledge root | Configurable path; matches vision doc structure | ✓ Phase 1 |
| Watcher thread-safe SQLite | watchdog Timer threads share DB connection | ✓ Phase 2 (check_same_thread=False + lock) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-29 — Phase 4 complete (memory inspector)*
