# Truth

## What This Is

Truth is a local-first agent memory system: OKF-compliant markdown files are the source of truth, a SQLite index provides fast hybrid search, and agents maintain the knowledge base via two tools (`memory_search`, `memory_write`). An HTML dashboard lets you browse the knowledge graph, read notes, and see what changed — all offline, no cloud, no SDK required to read the data.

## Core Value

Agents can read before they act and write after they learn, with human-readable markdown as the durable record and instant search over that record.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] OKF-compliant markdown store with enforced `type` frontmatter
- [ ] SQLite index with local embeddings and content-hash change detection
- [ ] Hybrid search (vector + BM25 + RRF merge)
- [ ] File watcher re-indexes only changed files
- [ ] `memory_search` and `memory_write` agent tools
- [ ] HTML dashboard to browse, navigate links, and view recent changes
- [ ] Agent system prompt contract (search before answer, write after learn)

### Out of Scope

- Cloud sync or multi-user auth — local single-user tool
- Ollama/LLM runtime itself — integrate via tools, don't embed a model server
- Graph database — link graph built from markdown links at index time
- Docker deployment — pip install and run
- Mobile app — browser dashboard only for v1

## Context

Google's Open Knowledge Format (OKF, June 2026) stores knowledge as markdown + YAML frontmatter with `type` as the only required field. Cross-links form a knowledge graph. This project is ~95% aligned already: markdown folders as truth, SQLite as derived index.

Key architectural insight from vision doc: **never write to SQLite directly** — agents write markdown; the indexer keeps SQLite in sync. Andrej Karpathy's framing: LLMs don't forget cross-references or get bored updating 15 files.

Embedding: local ONNX model (~80MB, CPU-only) via sentence-transformers — no Ollama needed for search. Examples: `all-MiniLM-L6-v2`, `nomic-embed-text-v1.5`.

Reference doc: `VISION.MD` in project root.

## Constraints

- **Tech**: Python 3.11+, sqlite-vec, sentence-transformers, watchdog — matches vision stack
- **Local-only**: All data and embeddings stay on disk; no external API calls for core loop
- **OKF compliance**: Every ingested/written file must have YAML frontmatter with at least `type`
- **Simplicity**: Indexer target ~50–200 lines of core logic; avoid frameworks beyond what's needed
- **Dashboard**: Static HTML + lightweight Python HTTP server (no React build step for v1)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Markdown as truth, SQLite as index | OKF alignment; human-readable; agents write files not DB rows | — Pending |
| Hybrid search (vector + BM25 + RRF) | Better recall than either alone; standard pattern for local RAG | — Pending |
| HTML dashboard in v1 | User requested visualize/navigate memory and changes | — Pending |
| Local ONNX embeddings | Offline, no Ollama dependency for search | — Pending |
| `notes/` as default knowledge root | Configurable path; matches vision doc structure | — Pending |

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
*Last updated: 2026-06-28 after initialization*
