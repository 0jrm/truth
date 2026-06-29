# Phase 5: Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-28
**Phase:** 5-integration
**Areas discussed:** Unified serve, Static sql.js inspector, Config, Deferred CLI, README, E2E verification, sql.js delivery, Inspector paths, DB schema

---

## Unified `truth serve`

| Option | Description | Selected |
|--------|-------------|----------|
| index_all → watcher → HTTP | Original Phase 4/5 plan | |
| index_all → watcher → block (no HTTP) | Headless daemon; browser reads DB via file:// | ✓ |
| Watcher + HTTP only | Skip startup index | |

**User's choice:** index_all on startup, watcher on daemon thread, main thread blocks; Ctrl+C stops both cleanly.

**Notes:** User rejected assumption that browser inspector needs a live HTTP server. Static file + sql.js reading `memory.db` is preferred.

---

## Static browser inspector

| Option | Description | Selected |
|--------|-------------|----------|
| HTTP server (Phase 4) | ThreadingHTTPServer + JSON API | |
| inspector.json export | Periodic JSON sync | |
| sql.js reads memory.db | WASM SQLite in browser, refresh for updates | ✓ |

**User's choice:** sql.js fetches `memory.db` from notes root; no JSON export; no watcher hook for HTML sync.

**Notes:** Tree/links require graph data in SQLite — user chose `notes` + `edges` tables populated at index time.

---

## Config & paths

| Option | Description | Selected |
|--------|-------------|----------|
| truth.toml + env override | ROADMAP CLI-02 literal | |
| Env-only | TRUTH_NOTES_ROOT + TRUTH_DB_PATH | ✓ |
| XDG global config | ~/.config/truth/ | |

**User's choice:** Env-only; two vars; default DB **inside notes root** (not project root).

---

## Deferred CLI (Phases 2–3)

| Option | Description | Selected |
|--------|-------------|----------|
| truth index | One-shot index_all | ✓ (also on serve startup) |
| truth write | CLI wrapper for memory_write | |
| Skip both | serve-only | |

**User's choice:** `truth index` yes; `truth write` no.

---

## README & E2E

| Option | Description | Selected |
|--------|-------------|----------|
| User README as baseline | Update in place | ✓ |
| All three verification | README + smoke script + pytest | ✓ |
| Expand sample notes | 2–3 more linked concepts | ✓ |

**Notes:** User created README.md before session; asked planner to read and adjust, not rewrite.

---

## sql.js & inspector placement

| Option | Description | Selected |
|--------|-------------|----------|
| Vendored sql.js | Offline in truth/static/ | ✓ |
| CDN sql.js | Network dependency | |
| truth export to notes root | Copy HTML+wasm beside memory.db | ✓ |

---

## Graph DB schema

| Option | Description | Selected |
|--------|-------------|----------|
| notes + edges tables | path/type/title + link edges at index time | ✓ |
| Extend files table only | Partial metadata | |
| Embed JSON in HTML | Rejected earlier | |

---

## Prior-phase items reviewed

| Item | Origin | Resolution |
|------|--------|------------|
| truth index CLI | Phase 2 CONTEXT discretion | Ship in v1 |
| truth write CLI | Phase 3 CONTEXT deferred | Declined |
| truth.toml | ROADMAP CLI-02 | Env-only v1 |
| Phase 4 discuss skipped | No 04-CONTEXT.md | Serve semantics superseded |
| HTTP inspector | Phase 4 04-02 | Removed for sql.js static |

## Deferred Ideas

- truth.toml config file
- truth write CLI
- HTTP inspector server as optional mode
- Ollama modelfile export (v2)
