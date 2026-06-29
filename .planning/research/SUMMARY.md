# Project Research Summary

**Project:** Truth
**Domain:** Local-first agent memory / personal knowledge base
**Researched:** 2026-06-28 (synthesized from VISION.MD — inline, no subagent research)
**Confidence:** HIGH (vision doc is prescriptive; stack choices validated by existing projects)

## Executive Summary

Truth builds on the OKF pattern: curated markdown concepts with cross-links, not chunk-and-retrieve RAG. The SQLite MVP approach (markdown truth + derived index) is already 95% OKF-compliant. Adding enforced `type` frontmatter closes the gap.

Local hybrid search (vector + BM25 + RRF) is the standard pattern for small-to-medium personal knowledge bases. A watchdog-driven incremental indexer with content-hash skipping avoids re-embedding unchanged files.

For observability, a CLI-first memory inspector (`tree`, `links`, `changes`, `graph --json`) covers most needs. Optional static HTML + JSON API for browser viewing — no SPA, no in-browser markdown editor for v1.

## Key Findings

### Recommended Stack

- **Python 3.11+** with `sqlite-vec`, `sentence-transformers`, `watchdog`
- **Embeddings**: `all-MiniLM-L6-v2` (fast, small) or `nomic-embed-text-v1.5` (768-dim, better quality)
- **Dashboard**: stdlib `http.server` or `starlette`/`fastapi` if API grows — start minimal
- **Frontmatter**: `python-frontmatter` or manual YAML parse (stdlib `yaml` if PyYAML already a dep)

**Avoid for v1:** Neo4j, Docker, cloud embeddings, React build chain, writing to SQLite from agents

### Table Stakes Features

- Markdown source of truth with metadata
- Full-text + semantic search
- File change detection / auto re-index
- Browse and read notes
- Agent write/search API

### Watch Out For

- **Dual-write drift**: Agents must never write SQLite directly — only markdown
- **Frontmatter corruption**: Validate on write, not just on read
- **Embedding model first-run**: ~80MB download; document this in README
- **Changelog reliability**: Use events table from watcher, not file mtime alone; also append OKF `log.md` on writes
- **Link resolution**: Handle relative paths, missing targets, and `[[wiki]]` style if supported

## Roadmap Implications

1. **Phase 1 before Phase 2** — graph extraction and frontmatter validation are prerequisites for index metadata
2. **Phase 2 before Phase 4** — dashboard search depends on hybrid search API
3. **Inspector after index** — needs events table (Phase 2) and link graph (Phase 1)
4. **CLI `serve` last** — integrates watcher + optional static HTML inspector
5. **Full dashboard deferred** — force graph, note viewer, live refresh are v2

---
*Research synthesized: 2026-06-28*
