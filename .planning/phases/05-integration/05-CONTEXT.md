# Phase 5: Integration - Context

**Gathered:** 2026-06-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire the full Truth system into a single runnable workflow: unified `truth serve` (index + watcher), env-based config with DB colocated in notes root, `truth index` for manual reindex, static browser inspector via sql.js reading `memory.db` directly (no HTTP server), indexer extensions for graph metadata in SQLite, README updates from user baseline, expanded sample notes, and end-to-end verification (README + smoke script + pytest).

Phase 4 CLI inspector commands (`truth tree`, `links`, `changes`, `graph`) remain the primary human observability path. Browser inspector is optional static HTML — open `file://` after `truth export`, refresh to see current DB state.

</domain>

<decisions>
## Implementation Decisions

### Unified `truth serve`
- **D-01:** `truth serve` runs `index_all()` on startup, then starts the file watcher on a **daemon background thread**, then **blocks on the main thread** until Ctrl+C.
- **D-02:** Ctrl+C performs **clean shutdown** — stop watcher observer, join threads, no orphans.
- **D-03:** `truth serve` does **not** start an HTTP server. Phase 4's `ThreadingHTTPServer` inspector path is **removed/replaced** — serve is headless indexer + watcher only.
- **D-04:** `truth index` is a separate subcommand that runs `index_all()` once and exits. `truth serve` also calls `index_all()` on startup (both ship in v1).

### Static browser inspector (sql.js)
- **D-05:** Browser inspector uses **sql.js** (SQLite WASM) vendored offline in `truth/static/` — no CDN dependency.
- **D-06:** `truth export` copies `inspector.html` + sql.js/wasm assets from `truth/static/` into the **notes root** beside `memory.db`. User opens via `file://`; browser `fetch()`es `memory.db` directly.
- **D-07:** No `inspector.json` export step. No auto-export on watcher cycles. **Refresh in browser** reads current `memory.db` — staleness solved by DB being live on disk, not by a sync/export pipeline.
- **D-08:** `memory.db` default path moves **inside notes root** (e.g. `{TRUTH_NOTES_ROOT}/memory.db` when env unset). Inspector HTML and DB must be colocated for `file://` fetch to work.

### Indexer graph extension (for browser + future reuse)
- **D-09:** Extend indexer to populate two new tables at index time:
  - `notes` — `path`, `type`, `title`, `mtime` (file metadata for tree view)
  - `edges` — `source`, `target`, `label` (markdown link graph)
- **D-10:** Populate/replace rows per file on index; delete related rows on file delete. CLI inspector may continue reading filesystem for v1 or switch to DB — planner picks smallest diff; browser **must** use DB tables via sql.js.

### Configuration
- **D-11:** **Env-only config for v1** — no `truth.toml`. Satisfies CLI-02 via `TRUTH_NOTES_ROOT` and `TRUTH_DB_PATH` (ROADMAP mention of `truth.toml` deferred).
- **D-12:** Only two env vars: `TRUTH_NOTES_ROOT` (default `notes/`) and `TRUTH_DB_PATH` (default `{notes_root}/memory.db` after D-08). No extra inspector path vars.

### CLI surface (deferred subcommands from Phases 2–3)
- **D-13:** Ship `truth index` — one-shot full reindex (Phase 2 deferral resolved).
- **D-14:** **Do not** ship `truth write` CLI — agents use `memory_write` Python API; humans edit markdown directly (Phase 3 deferral: declined).

### README & docs
- **D-15:** User-authored `README.md` at repo root is the **baseline** — Phase 5 updates it (do not rewrite from scratch). Key updates: `truth serve` / `truth index` quickstart replaces `python -m` incantations; DB default inside notes root; sql.js static inspector workflow; mark Phase 4 complete; remove `truth.toml` from roadmap checkbox until v2.
- **D-16:** Ollama hookup section in README is sufficient — `tool_schemas()` + dispatch loop example stays; no modelfile export (v2 AGNT-01).

### Sample data & verification
- **D-17:** Expand `notes/` with **2–3 additional linked concepts** (e.g. agent workflow, log convention) for richer demo/inspector.
- **D-18:** End-to-end verification uses **all three**: README quickstart documents the flow, a standalone smoke script automates write → index → search → tree/changes, and a pytest integration test guards regressions.

### Carried forward from skipped prior-phase discussions
- **D-19:** Phase 4 discuss-phase was skipped — inspector HTTP API shipped in 04-02; Phase 5 **supersedes** serve semantics per D-03/D-05–D-07. CLI commands from user's Phase 4 spec are already implemented and verified.
- **D-20:** Phase 1/2/3 used auto-context — `truth index` deferral resolved (D-04/D-13); `truth write` deferral declined (D-14); wiki-links remain out of scope.

### Claude's Discretion
- Exact default for `TRUTH_DB_PATH` when unset (`notes/memory.db` vs `notes/.truth/memory.db`)
- Whether CLI `tree`/`links` switch to DB tables or keep filesystem reads (browser requires DB)
- sql.js query shapes in inspector.html; minimal dark UI polish
- Smoke script location (`truth/smoke.py` vs `scripts/e2e.py`)
- Graceful migration if existing `memory.db` at project root — document one-time move or support both briefly

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & architecture
- `.planning/PROJECT.md` — core value, markdown-as-truth, inspector-first
- `.planning/REQUIREMENTS.md` — CLI-01, CLI-02 (env vars satisfy CLI-02)
- `.planning/ROADMAP.md` — Phase 5 success criteria (update serve/inspector semantics during planning)
- `VISION.MD` — indexer loop, never write SQLite from agents
- `AGENTS.md` — conventions, ponytail comments
- `README.md` — user baseline docs (update, don't replace)

### Phase 4 inspector (existing — reuse/refactor)
- `truth/cli.py` — argparse entry; extend with `index`, refactor `serve`
- `truth/serve.py` — **refactor or replace** — HTTP server removed per D-03
- `truth/static/inspector.html` — refactor for sql.js + DB queries
- `truth/inspect/` — tree, links, changes, graph (CLI data layer)

### Index & store (extend)
- `truth/index/indexer.py` — `index_all`, `index_file`; add notes/edges table writes
- `truth/index/watcher.py` — `start_watcher(block=False)` for daemon thread
- `truth/index/db.py` — schema migration for `notes` + `edges` tables
- `truth/store/links.py` — `extract_links` for edge population
- `truth/store/paths.py` — `notes_root()`, update default `db_path()` resolution
- `truth/tools/` — agent API unchanged

### Agent integration
- `prompts/system.md` — update watcher/serve references

### External
- [sql.js](https://github.com/sql-js/sql.js) — SQLite WASM for static browser inspector (vendored, offline)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `truth.cli:main` — entry point registered in `pyproject.toml`; add `index`, refactor `serve`
- `index_all()` / `start_watcher()` — orchestration building blocks already exist
- `truth/static/inspector.html` — starting point for sql.js refactor (currently fetch API)
- Phase 4 inspector modules — same data shapes for tree/links/changes/graph JSON

### Established Patterns
- stdlib argparse, no click — keep for CLI
- `ponytail:` comments for intentional shortcuts (threading, sql.js asset bundling)
- Self-check via `python -m truth.<module>` and module `__main__` blocks
- Env vars via `os.environ` in `paths.py` / `db.py` — centralize in one config module if helpful

### Integration Points
- `db.py` schema + `indexer.py` — add notes/edges writes on every `index_file`
- `paths.py` + `db.py` — align default DB path inside notes root (breaking change from current project-root default)
- `truth export` new subcommand — copy static assets to notes root
- Remove or gut HTTP routes in `serve.py`; serve becomes watcher loop only
- README quickstart section — replace `python -m` with `truth serve` / `truth index`

</code_context>

<specifics>
## Specific Ideas

- User pasted Phase 4 inspector spec during discussion — confirms tree/links/changes/graph output shapes already match implementation; main gap was serve unification, now redefined as headless + static sql.js inspector.
- User created `README.md` before discuss-phase — treat as authoritative tone/structure; adjust facts only.
- Browser inspector philosophy: "HTML reads memory.db directly — refresh is the sync mechanism." No server process for viewing.
- sql.js constraint drove decision to index graph metadata into SQLite (tree/links can't read `notes/` from `file://`).

</specifics>

<deferred>
## Deferred Ideas

- `truth.toml` config file — deferred beyond v1 (env-only per D-11); revisit if multi-project setups need it
- `truth write` CLI subcommand — declined for v1 (D-14)
- HTTP inspector server (`truth serve --port`) — replaced by static sql.js inspector; no optional HTTP keepalive
- Ollama modelfile export — v2 (AGNT-01)
- In-browser markdown note viewer — v2 (UI-02)
- `[[wiki]]` link syntax — out of scope since Phase 1

</deferred>

---

*Phase: 05-integration*
*Context gathered: 2026-06-28*
