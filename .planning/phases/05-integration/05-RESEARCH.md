# Phase 5: Integration - Research

**Researched:** 2026-06-28
**Domain:** Unified CLI serve, env config, sql.js static inspector, indexer graph tables
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01–D-04:** `truth serve` = `index_all()` on startup + daemon watcher thread + main-thread block until Ctrl+C; no HTTP server
- **D-05–D-08:** sql.js vendored offline; `truth export` copies static assets beside `memory.db`; browser reads DB via `fetch('memory.db')`; default DB inside notes root
- **D-09–D-10:** New `notes` + `edges` SQLite tables populated at index time
- **D-11–D-12:** Env-only config (`TRUTH_NOTES_ROOT`, `TRUTH_DB_PATH`); no `truth.toml` in v1
- **D-13–D-14:** Ship `truth index`; do not ship `truth write` CLI
- **D-15–D-18:** Update existing README; expand sample notes; README + smoke script + pytest for e2e

### Claude's Discretion
- Default hidden path (`notes/memory.db` vs `notes/.truth/memory.db`) — recommend `notes/memory.db` (simplest `file://` colocation)
- CLI inspect keeps filesystem reads (smallest diff); browser uses DB tables only
- sql.js asset versions pinned in `truth/static/vendor/`

### Deferred
- `truth.toml`, HTTP inspector, `truth write` CLI, Ollama modelfile export, in-browser markdown viewer

</user_constraints>

<architectural_responsibility_map>
## Architectural Responsibility Map

| Capability | Module | Rationale |
|------------|--------|-----------|
| Env config resolution | `truth/store/paths.py` + `truth/index/db.py` | Single source for notes root and DB path |
| Headless serve loop | `truth/serve.py` (refactor) | Replaces HTTP server; orchestrates index + watcher |
| CLI subcommands | `truth/cli.py` | `serve`, `index`, `export`; remove HTTP `--port` from serve |
| Graph metadata in DB | `truth/index/db.py` + `truth/index/indexer.py` | `notes`/`edges` tables for sql.js inspector |
| Static inspector | `truth/static/inspector.html` + vendored sql.js | `file://` workflow, no server |
| Export assets | new `truth/export.py` or inline in cli | Copy HTML + wasm/js to notes root |
| Watcher daemon mode | `truth/index/watcher.py` | Already supports `block=False`; join on shutdown |

</architectural_responsibility_map>

<research_summary>
## Summary

Phase 5 wires existing Phase 1–4 modules into one runnable CLI workflow. The main semantic shift: **`truth serve` becomes headless** (index + watcher only) and the browser inspector moves to **static sql.js reading `memory.db` directly** — Phase 4's `ThreadingHTTPServer` is removed, not extended.

**Config:** Centralize path resolution in `paths.py`. When `TRUTH_DB_PATH` is unset, default to `{notes_root}/memory.db` (breaking change from project-root `memory.db`; document one-time move in README).

**Indexer extension:** Add `notes(path, type, title, mtime)` and `edges(source, target, label)` tables. On each `index_file`: upsert note row, replace outgoing edges via `extract_links`. On `delete_file_from_index`: remove note row and edges where source or target matches. Browser inspector queries these tables; CLI inspect modules can keep filesystem reads (zero regression risk).

**sql.js:** Vendor `sql-wasm.js` + `sql-wasm.wasm` from [sql.js](https://github.com/sql-js/sql.js) releases under `truth/static/vendor/`. Inspector loads WASM, fetches colocated `memory.db`, runs SQL for tree/links/changes panels. Refresh = re-fetch DB (live on disk while watcher runs).

**Serve loop:** `index_all()` → `observer = start_watcher(block=False)` → `signal.signal(SIGINT, handler)` → `threading.Event().wait()` or sleep loop → on interrupt: `observer.stop(); observer.join()`.

**Verification:** Smoke script + pytest integration test using temp dir env vars; no test framework beyond stdlib `unittest` or minimal pytest if already a dep (add pytest as optional dev dep or use `python -m unittest`).

**Primary recommendation:** Two plans — 05-01 core wiring (config, schema, serve, export, sql.js inspector); 05-02 docs, sample notes, e2e tests.
</research_summary>

<standard_stack>
## Standard Stack

### Core (existing)
| Component | Purpose |
|-----------|---------|
| argparse | CLI subcommands (no click) |
| watchdog + threading | Daemon watcher on serve |
| sqlite3 + sqlite-vec | Index + sql.js reads same file |

### New (Phase 5)
| Asset | Purpose | Notes |
|-------|---------|-------|
| sql.js 1.x wasm | Browser SQLite | Vendored offline; pin version in static/vendor |
| signal / threading.Event | Clean Ctrl+C shutdown | Join observer, no orphan threads |

### sql.js integration pattern
```javascript
// inspector.html (conceptual)
const SQL = await initSqlJs({ locateFile: f => 'vendor/' + f });
const buf = await (await fetch('memory.db')).arrayBuffer();
const db = new SQL.Database(new Uint8Array(buf));
const tree = db.exec("SELECT path, type, title FROM notes ORDER BY path");
```

**file:// constraint:** HTML, wasm, and `memory.db` must live in same directory (or relative paths work). `truth export` copies all to notes root.

### Schema addition
```sql
CREATE TABLE IF NOT EXISTS notes (
  path TEXT PRIMARY KEY,
  type TEXT,
  title TEXT,
  mtime REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS edges (
  source TEXT NOT NULL,
  target TEXT NOT NULL,
  label TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (source, target, label)
);
CREATE INDEX IF NOT EXISTS edges_target ON edges(target);
```

Edge targets stored as **relative paths** (same as `files.path`) via `_relative_path()` after `resolve_link`.
</standard_stack>

<breaking_changes>
## Breaking Changes

| Change | Migration |
|--------|-----------|
| Default `memory.db` moves from project root to `notes/memory.db` | README note: `mv memory.db notes/` or set `TRUTH_DB_PATH` |
| `truth serve --port` removed | Use `truth export` + open `file://.../inspector.html` |
| HTTP `/api/*` routes removed | Browser uses sql.js queries |

</breaking_changes>

<pitfalls>
## Pitfalls

1. **CORS / file:// fetch** — `fetch('memory.db')` works when HTML and DB are same folder; broken if DB stays at project root while HTML exported to notes/
2. **Edge target paths** — Must store rel paths consistent with CLI (`hybrid-search.md` not absolute)
3. **Watcher + serve shutdown** — Must join observer; cancel debounce timers or accept brief race on exit
4. **sql.js bundle size** — ~1MB wasm; acceptable for offline vendoring
5. **ROADMAP drift** — Update Phase 5 success criteria to reflect headless serve + sql.js (not HTTP inspector together)

</pitfalls>

<files_to_touch>
## Expected File Changes

| File | Change |
|------ |--------|
| `truth/store/paths.py` | `db_path()` helper or import from db; notes-relative default |
| `truth/index/db.py` | notes/edges schema; default path uses notes root |
| `truth/index/indexer.py` | Write notes/edges on index/delete |
| `truth/serve.py` | Replace HTTP with headless serve loop |
| `truth/cli.py` | `index`, `export`; refactor `serve` (no port/host) |
| `truth/export.py` | Copy static assets to notes root (new, ~30 lines) |
| `truth/static/inspector.html` | sql.js queries instead of fetch API |
| `truth/static/vendor/*` | sql-wasm.js, sql-wasm.wasm |
| `README.md` | Quickstart, config, inspector workflow |
| `notes/*.md` | 2–3 new linked concepts |
| `tests/test_integration.py` or `truth/smoke.py` | E2E verification |
| `prompts/system.md` | Reference `truth serve` |
| `.planning/ROADMAP.md` | Phase 5 success criteria alignment |

</files_to_touch>

## RESEARCH COMPLETE
