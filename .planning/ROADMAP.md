# Roadmap: Truth

## Overview

Build a local OKF-compliant agent memory system in five coarse phases: establish the markdown store, add the SQLite hybrid index with event tracking, expose agent tools (including OKF `log.md`), ship a CLI-first memory inspector with optional static HTML, then wire everything together. Each phase delivers something runnable.

## Phases

- [x] **Phase 1: OKF Memory Store** — Markdown truth layer with frontmatter enforcement (completed 2026-06-29)
- [x] **Phase 2: Hybrid Index** — SQLite + embeddings + watcher + search + events table (completed 2026-06-29)
- [x] **Phase 3: Agent Tools** — `memory_search`, `memory_write`, OKF `log.md` append (completed 2026-06-29)
- [x] **Phase 4: Memory Inspector** — CLI tree/links/changes/graph + optional static HTML (completed 2026-06-29)
- [ ] **Phase 5: Integration** — CLI entry point, config, sample data, docs

## Phase Details

### Phase 1: OKF Memory Store
**Goal**: Knowledge lives as OKF-compliant markdown files with validated frontmatter and parseable link graph.
**Depends on**: Nothing (first phase)
**Requirements**: MEM-01, MEM-02, MEM-03, MEM-04
**UI hint**: no
**Success Criteria** (what must be TRUE):
  1. Creating a note via the write path produces a `.md` file with valid YAML frontmatter including `type`
  2. Files missing `type` are rejected or auto-corrected before save
  3. Markdown links between files are extractable as a list of (source, target) pairs
  4. Sample `notes/` directory exists with 2–3 linked example concepts
**Plans**: 2 plans

Plans:

**Wave 1**
- [x] 01-01: Project scaffold, `notes/` layout, frontmatter parser/validator

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 01-02: Link graph extractor + sample seed notes

**Cross-cutting constraints:**
- Every memory file must have YAML frontmatter with at least `type` (OKF compliance)
- Markdown files in `notes/` are source of truth — store layer never touches SQLite

### Phase 2: Hybrid Index
**Goal**: Fast local search over the markdown store with automatic re-indexing and reliable change tracking.
**Depends on**: Phase 1
**Requirements**: IDX-01, IDX-02, IDX-03, IDX-04, IDX-05, IDX-06, SRCH-01, SRCH-02, SRCH-03, SRCH-04
**UI hint**: no
**Success Criteria** (what must be TRUE):
  1. Running the indexer populates `memory.db` with chunked, embedded content from all notes
  2. Editing a note triggers re-index of only that file (watcher)
  3. Deleting a note removes its chunks from the index
  4. `memory_search("query")` returns relevant results using hybrid vector+BM25+RRF
  5. Re-running indexer on unchanged files completes without re-embedding (hash skip)
  6. Each create/update/delete writes a row to the `events` table queryable by `truth changes`
**Plans**: 4 plans

Plans:
- [x] 02-01: SQLite schema, chunking, local embedding model integration
- [x] 02-02: BM25 + vector search + RRF merge
- [x] 02-03: Watchdog watcher with content-hash incremental updates
- [x] 02-04: Events table + change tracking on file ops

### Phase 3: Agent Tools
**Goal**: Clean Python API for agents to search and write memory, OKF log append, plus system prompt contract.
**Depends on**: Phase 2
**Requirements**: TOOL-01, TOOL-02, TOOL-03, TOOL-04
**UI hint**: no
**Success Criteria** (what must be TRUE):
  1. `from truth.tools import memory_search, memory_write` works in a Python REPL
  2. `memory_write` creates a file that appears in search results within one watcher cycle
  3. `memory_write` appends a timestamped entry to `log.md`
  4. Tool functions have docstrings/schemas suitable for function-calling
  5. `prompts/system.md` documents the search-before-answer / write-after-learn loop
**Plans**: 2 plans

Plans:
- [x] 03-01: `memory_search` and `memory_write` implementations
- [x] 03-02: OKF `log.md` append, tool schemas + system prompt template

### Phase 4: Memory Inspector
**Goal**: Observe file tree, link relationships, and changelog — CLI first, optional browser UI.
**Depends on**: Phase 2 (events + graph), Phase 1 (notes + links)
**Requirements**: INSPECT-01, INSPECT-02, INSPECT-03, INSPECT-04, INSPECT-05
**UI hint**: yes
**Success Criteria** (what must be TRUE):
  1. `truth tree` prints folder hierarchy with type/title from frontmatter
  2. `truth links notes/foo.md` shows incoming and outgoing edges
  3. `truth changes -n 20` lists recent ops from events table with timestamps
  4. `truth graph --json` outputs valid nodes/edges JSON
  5. `truth serve` serves JSON API + static `inspector.html` with tree, links, and changes panels (no in-browser markdown viewer)
**Plans**: 2 plans

Plans:
- [x] 04-01: CLI commands (`tree`, `links`, `changes`, `graph --json`)
- [x] 04-02: Static `inspector.html` + JSON API (tree, links, changes)

### Phase 5: Integration
**Goal**: One command to run the full system; configurable paths; ready for agent hookup.
**Depends on**: Phases 1–4
**Requirements**: CLI-01, CLI-02
**UI hint**: no
**Success Criteria** (what must be TRUE):
  1. `truth serve` starts watcher, indexer, and optional inspector server together
  2. Knowledge root and DB path configurable via env vars or `truth.toml`
  3. README documents install, first-run, CLI inspector workflow, and Ollama tool hookup
  4. End-to-end demo: write note → in `truth changes` → searchable → visible in `truth tree` and links
**Plans**: 2 plans

Plans:
- [ ] 05-01: CLI entry point, config loading, unified serve command
- [ ] 05-02: README, sample brain, end-to-end smoke test

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. OKF Memory Store | 2/2 | Complete   | 2026-06-29 |
| 2. Hybrid Index | 4/4 | Complete    | 2026-06-29 |
| 3. Agent Tools | 2/2 | Complete   | 2026-06-29 |
| 4. Memory Inspector | 2/2 | Complete    | 2026-06-29 |
| 5. Integration | 0/2 | Not started | - |
