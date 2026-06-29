# Requirements: Truth

**Defined:** 2026-06-28
**Core Value:** Agents can read before they act and write after they learn, with human-readable markdown as the durable record and instant search over that record.

## v1 Requirements

### Memory Store (MEM)

- [ ] **MEM-01**: System stores knowledge as markdown files in a configurable root directory (default `notes/`)
- [ ] **MEM-02**: Every memory file has YAML frontmatter with at least a `type` field (OKF compliance)
- [ ] **MEM-03**: `memory_write` rejects or auto-adds missing required frontmatter before saving
- [ ] **MEM-04**: Cross-links between concepts use standard markdown links and are parseable for graph building

### Indexing (IDX)

- [ ] **IDX-01**: Indexer walks the knowledge folder, chunks each `.md` file, and stores text + metadata in SQLite
- [ ] **IDX-02**: Chunks are embedded with a local in-process model (no external API)
- [ ] **IDX-03**: Content-hash change detection skips unchanged files on re-index
- [ ] **IDX-04**: File watcher detects create/update/delete and re-indexes only affected files
- [ ] **IDX-05**: Failed index operations do not leave partial/corrupt rows (transactional safety)

### Search (SRCH)

- [ ] **SRCH-01**: `memory_search(query, k)` returns top-k relevant chunks
- [ ] **SRCH-02**: Search combines vector similarity and BM25 keyword search
- [ ] **SRCH-03**: Results are merged via reciprocal rank fusion (RRF)
- [ ] **SRCH-04**: Search results include source path, chunk text, and relevance score

### Agent Tools (TOOL)

- [ ] **TOOL-01**: `memory_write(path, content)` writes markdown to the knowledge root
- [ ] **TOOL-02**: Tools are importable Python functions suitable for Ollama/function-calling integration
- [ ] **TOOL-03**: System prompt template documents search-before-answer and write-after-learn rules

### Dashboard (DASH)

- [ ] **DASH-01**: User can open an HTML dashboard served locally (browser)
- [ ] **DASH-02**: Dashboard lists all memory files with title, type, and tags from frontmatter
- [ ] **DASH-03**: User can click a note to read rendered markdown content
- [ ] **DASH-04**: Dashboard shows link graph — which notes link to which (navigate by clicking links)
- [ ] **DASH-05**: Dashboard shows recent changes (files modified/created/deleted with timestamps)
- [ ] **DASH-06**: Dashboard includes search box that queries the same hybrid search backend

### CLI & Config (CLI)

- [ ] **CLI-01**: Single entry point to start indexer + watcher + dashboard server
- [ ] **CLI-02**: Knowledge root path and database path are configurable (env or config file)

## v2 Requirements

### Dashboard

- **DASH-07**: Interactive force-directed graph visualization (canvas/SVG)
- **DASH-08**: Diff view showing what changed in a file between versions

### Agent Integration

- **AGNT-01**: Pre-built Ollama modelfile or OpenAI-compatible tool schema export
- **AGNT-02**: Optional `log.md` chronological history auto-maintained by agent writes

### OKF Bundle

- **OKF-01**: Export/import full OKF bundle with `index.md` navigation file generation

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-user / auth | Local single-user tool for v1 |
| Cloud sync | Contradicts local-first core value |
| Embedded LLM runtime | Integrate with Ollama externally; don't ship a model server |
| Graph DB (Neo4j etc.) | Link graph derived from markdown at index time |
| React/SPA build pipeline | Static HTML + vanilla JS keeps v1 simple |
| Real-time collaborative editing | Single writer (agent or human) per session |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| MEM-01 | Phase 1 | Pending |
| MEM-02 | Phase 1 | Pending |
| MEM-03 | Phase 1 | Pending |
| MEM-04 | Phase 1 | Pending |
| IDX-01 | Phase 2 | Pending |
| IDX-02 | Phase 2 | Pending |
| IDX-03 | Phase 2 | Pending |
| IDX-04 | Phase 2 | Pending |
| IDX-05 | Phase 2 | Pending |
| SRCH-01 | Phase 2 | Pending |
| SRCH-02 | Phase 2 | Pending |
| SRCH-03 | Phase 2 | Pending |
| SRCH-04 | Phase 2 | Pending |
| TOOL-01 | Phase 3 | Pending |
| TOOL-02 | Phase 3 | Pending |
| TOOL-03 | Phase 3 | Pending |
| DASH-01 | Phase 4 | Pending |
| DASH-02 | Phase 4 | Pending |
| DASH-03 | Phase 4 | Pending |
| DASH-04 | Phase 4 | Pending |
| DASH-05 | Phase 4 | Pending |
| DASH-06 | Phase 4 | Pending |
| CLI-01 | Phase 5 | Pending |
| CLI-02 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0 ✓

---
*Requirements defined: 2026-06-28*
*Last updated: 2026-06-28 after roadmap creation*
