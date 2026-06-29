# Roadmap: Truth

## Overview

Build a local OKF-compliant agent memory system in five coarse phases: establish the markdown store, add the SQLite hybrid index, expose agent tools, ship an HTML dashboard for browsing and change tracking, then wire everything together with a CLI. Each phase delivers something runnable.

## Phases

- [ ] **Phase 1: OKF Memory Store** — Markdown truth layer with frontmatter enforcement
- [ ] **Phase 2: Hybrid Index** — SQLite + local embeddings + watcher + search
- [ ] **Phase 3: Agent Tools** — `memory_search` and `memory_write` for LLM integration
- [ ] **Phase 4: HTML Dashboard** — Browse, navigate links, search, view changes
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
- [ ] 01-01: Project scaffold, `notes/` layout, frontmatter parser/validator
- [ ] 01-02: Link graph extractor + sample seed notes

### Phase 2: Hybrid Index
**Goal**: Fast local search over the markdown store with automatic re-indexing on file changes.
**Depends on**: Phase 1
**Requirements**: IDX-01, IDX-02, IDX-03, IDX-04, IDX-05, SRCH-01, SRCH-02, SRCH-03, SRCH-04
**UI hint**: no
**Success Criteria** (what must be TRUE):
  1. Running the indexer populates `memory.db` with chunked, embedded content from all notes
  2. Editing a note triggers re-index of only that file (watcher)
  3. Deleting a note removes its chunks from the index
  4. `memory_search("query")` returns relevant results using hybrid vector+BM25+RRF
  5. Re-running indexer on unchanged files completes without re-embedding (hash skip)
**Plans**: 3 plans

Plans:
- [ ] 02-01: SQLite schema, chunking, local embedding model integration
- [ ] 02-02: BM25 + vector search + RRF merge
- [ ] 02-03: Watchdog watcher with content-hash incremental updates

### Phase 3: Agent Tools
**Goal**: Clean Python API for agents to search and write memory, plus system prompt contract.
**Depends on**: Phase 2
**Requirements**: TOOL-01, TOOL-02, TOOL-03
**UI hint**: no
**Success Criteria** (what must be TRUE):
  1. `from truth.tools import memory_search, memory_write` works in a Python REPL
  2. `memory_write` creates a file that appears in search results within one watcher cycle
  3. Tool functions have docstrings/schemas suitable for function-calling
  4. `prompts/system.md` documents the search-before-answer / write-after-learn loop
**Plans**: 2 plans

Plans:
- [ ] 03-01: `memory_search` and `memory_write` implementations
- [ ] 03-02: Tool schemas + system prompt template

### Phase 4: HTML Dashboard
**Goal**: Browser UI to explore the knowledge base, navigate links, search, and see what changed.
**Depends on**: Phase 2 (search API), Phase 1 (notes + graph)
**Requirements**: DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, DASH-06
**UI hint**: yes
**Success Criteria** (what must be TRUE):
  1. Opening `http://localhost:<port>` shows a list of all memory files with type/tags
  2. Clicking a note renders its markdown content in the browser
  3. Outgoing links on a note are clickable and navigate to linked notes
  4. A "Recent changes" panel shows files modified in the last N hours/days
  5. Search box returns same results as `memory_search` API
  6. Dashboard updates when files change (polling or SSE — keep simple for v1)
**Plans**: 3 plans

Plans:
- [ ] 04-01: HTTP API routes (list, read, search, graph, changes)
- [ ] 04-02: HTML/CSS layout — file list, note viewer, changes panel
- [ ] 04-03: Link navigation + search UI wired to API

### Phase 5: Integration
**Goal**: One command to run the full system; configurable paths; ready for agent hookup.
**Depends on**: Phases 1–4
**Requirements**: CLI-01, CLI-02
**UI hint**: no
**Success Criteria** (what must be TRUE):
  1. `truth serve` (or equivalent) starts watcher, indexer, and dashboard together
  2. Knowledge root and DB path configurable via env vars or `truth.toml`
  3. README documents install, first-run, and Ollama tool hookup
  4. End-to-end demo: write note → appears in dashboard → searchable → linked
**Plans**: 2 plans

Plans:
- [ ] 05-01: CLI entry point, config loading, unified serve command
- [ ] 05-02: README, sample brain, end-to-end smoke test

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. OKF Memory Store | 0/2 | Not started | - |
| 2. Hybrid Index | 0/3 | Not started | - |
| 3. Agent Tools | 0/2 | Not started | - |
| 4. HTML Dashboard | 0/3 | Not started | - |
| 5. Integration | 0/2 | Not started | - |
