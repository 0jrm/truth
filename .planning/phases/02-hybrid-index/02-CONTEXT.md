# Phase 2: Hybrid Index - Context

**Gathered:** 2026-06-28
**Status:** Ready for planning
**Mode:** Auto-selected decisions (pipeline advance)

<domain>
## Phase Boundary

Fast local hybrid search over the OKF markdown store: SQLite index with chunked embeddings, FTS5 BM25, vector similarity, RRF merge, content-hash incremental indexing, watchdog-driven re-index, and an events table for change tracking. Markdown in `notes/` remains truth; agents never write SQLite directly.

</domain>

<decisions>
## Implementation Decisions

### Embedding model
- **D-01:** Use `sentence-transformers` with `all-MiniLM-L6-v2` (384-dim, CPU ONNX). First run downloads ~80MB; document in plan/README notes.
- **D-02:** Lazy-load the model singleton on first embed; reuse across indexer and search.

### Chunking
- **D-03:** Paragraph-based chunking on body text (after frontmatter strip). Target ~512 characters per chunk with ~64-character overlap between consecutive chunks.
- **D-04:** Store chunk index, source path, content hash, and frontmatter `type`/`title` as metadata columns.

### Database placement & schema
- **D-05:** Default DB path `memory.db` at project root; override via `TRUTH_DB_PATH` env var (prep for CLI-02 in Phase 5).
- **D-06:** Schema: `files` (path, content_hash, mtime), `chunks` (rowid PK), `chunks_fts` (FTS5 virtual, trigram tokenizer), `chunks_vec` (vec0 float[384]), `events` (id, path, op, ts). Shared `rowid` links FTS + vec rows to `chunks`.

### Invalid / skipped notes
- **D-07:** Notes missing valid frontmatter or failing `parse_note()` are skipped with a logged warning; indexer continues (no quarantine folder in v1).

### Watcher behavior
- **D-08:** `watchdog` observer on `notes/` with 500ms debounce before re-indexing a changed path.
- **D-09:** On delete, remove all chunks for that path and write a `delete` event.

### Search API
- **D-10:** Phase 2 delivers `memory_search(query, k=5)` in `truth.index.search` (callable for smoke tests). Phase 3 re-exports via `truth.tools`.
- **D-11:** Hybrid merge via RRF with `k=60`; retrieve top-50 per channel before fusion; return path, chunk text, score, rank metadata (SRCH-04).

### Transactional safety
- **D-12:** Per-file index updates run in a SQLite transaction: delete old chunks for path, insert new chunks + FTS + vec rows atomically. Failed file leaves prior index intact.

### the agent's Discretion
- Exact SQL for RRF CTE vs Python-side fusion (prefer SQL where readable).
- Chunk overlap implementation (character vs sentence boundary).
- Whether `truth index` CLI subcommand ships in Phase 2 or waits for Phase 5 (minimal `python -m truth.index` self-check is enough).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project requirements & architecture
- `.planning/PROJECT.md` — core value, key decisions (hybrid search, events table, local ONNX)
- `.planning/REQUIREMENTS.md` — IDX-01..06, SRCH-01..04
- `.planning/ROADMAP.md` — Phase 2 goal, success criteria, plan breakdown
- `VISION.MD` — indexer loop, never write SQLite from agents, hybrid search sketch
- `AGENTS.md` — stack, conventions, ponytail comments

### Phase 1 store layer (import, do not duplicate)
- `truth/store/frontmatter.py` — `parse_note`, `parse_note_file`
- `truth/store/links.py` — `extract_links` (metadata for future inspector; optional index in Phase 2)
- `truth/store/paths.py` — `notes_root()`, `TRUTH_NOTES_ROOT`

### Seed notes (indexer fixtures)
- `notes/okf-format.md`, `notes/sqlite-vectors.md`, `notes/hybrid-search.md`

### External patterns
- sqlite-vec hybrid search with FTS5 + RRF (Alex Garcia blog / issue #48 on asg017/sqlite-vec)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `truth.store.parse_note_file` — single parse path for indexer (no duplicate frontmatter logic)
- `truth.store.notes_root` — configurable knowledge root already works
- `truth.store.extract_links` — optional: store link edges later; not required for search MVP

### Established Patterns
- PyYAML + stdlib only in Phase 1; Phase 2 adds `sqlite-vec`, `sentence-transformers`, `watchdog`
- `ponytail:` comments for intentional shortcuts (global embed lock, naive chunker)
- Self-check via `python -m truth.<module>` pattern from Phase 1

### Integration Points
- New package `truth/index/` sits beside `truth/store/`; indexer imports store, never the reverse
- `pyproject.toml` gains new dependencies; no CLI entry point until Phase 5

</code_context>

<specifics>
## Specific Ideas

- Follow VISION.MD "~50 lines of core indexer" spirit — keep orchestration thin; schema + search in focused modules
- Sample notes already describe hybrid search and sqlite-vectors — indexer should index them successfully on first run

</specifics>

<deferred>
## Deferred Ideas

- `[[wiki]]` link indexing — standard markdown links only (Phase 1 decision)
- Link graph table in SQLite — Phase 4 inspector can use `extract_links` at read time
- `memory_write` and OKF `log.md` append — Phase 3
- CLI `truth serve` / unified config file — Phase 5
- nomic-embed-text-v1.5 upgrade path — note in RESEARCH as future swap if recall insufficient

</deferred>

---

*Phase: 02-hybrid-index*
*Context gathered: 2026-06-28*
