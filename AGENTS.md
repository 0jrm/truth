<!-- GSD:project-start source:PROJECT.md -->
## Project

**Truth** — Local-first OKF agent memory. Markdown files are truth; SQLite is the search index. Agents use `memory_search` / `memory_write`. HTML dashboard for browse, link navigation, and change tracking.

See `.planning/PROJECT.md` for full context.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:STACK.md -->
## Technology Stack

- **Language**: Python 3.11+
- **Index**: SQLite + sqlite-vec
- **Embeddings**: sentence-transformers (local ONNX, CPU)
- **Watcher**: watchdog
- **Search**: vector + BM25 + RRF
- **Dashboard**: static HTML + Python HTTP server (stdlib or minimal deps)
- **Format**: OKF markdown + YAML frontmatter

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

- Markdown files in `notes/` are the source of truth — never write to SQLite directly from agent code
- Every memory file requires YAML frontmatter with at least `type`
- Keep core indexer logic minimal; prefer stdlib where possible
- Mark intentional shortcuts with `ponytail:` comments

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

```
notes/*.md  ──write──►  agent (memory_write)
     ▲                        │
     │                        ▼
     └──watcher──►  indexer  ──►  memory.db (SQLite)
                                       │
                    memory_search ◄────┤
                    dashboard API ◄────┘
                         │
                         ▼
                    browser (HTML dashboard)
```

Build order: store → index → tools → dashboard → CLI

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project-local skills yet.

<!-- GSD:skills-end -->

<!-- GSD:workflow-start -->
## GSD Workflow

This project uses [Get Shit Done](https://github.com/gsd-build/get-shit-done) for phased execution.

**Current phase:** 1 — OKF Memory Store
**Roadmap:** `.planning/ROADMAP.md`
**State:** `.planning/STATE.md`

### Commands

| Command | Purpose |
|---------|---------|
| `$gsd-discuss-phase 1` | Gather context before planning Phase 1 |
| `$gsd-plan-phase 1` | Create execution plans for Phase 1 |
| `$gsd-execute-phase 1` | Execute Phase 1 plans |
| `$gsd-progress` | Check project status |

### Rules for agents

1. Read `.planning/STATE.md` first in every session
2. Read `.planning/PROJECT.md` for requirements and decisions
3. Execute current phase plans in order; don't skip ahead
4. Update STATE.md after significant progress
5. Never write directly to SQLite — markdown is truth

<!-- GSD:workflow-end -->
