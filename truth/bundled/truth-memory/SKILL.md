---
name: truth-memory
description: >-
  Use when working on Truth project memory, searching prior decisions or durable
  notes in notes/, or writing OKF markdown the agent should recall later.
---

# Truth Memory

Truth stores agent memory as OKF markdown on disk (`notes/`). SQLite (`memory.db`) is the search index only — never write to the database directly.

## When to use

- User asks about project context, past decisions, preferences, or prior work
- You learn a durable fact, decision, or outcome worth recalling later
- You need to check whether a note already exists before creating or updating one

## Workflow

1. **Search before answer** — call `memory_search(query, k=5)` when the question might depend on prior knowledge.
2. **Answer** — synthesize from search results and conversation.
3. **Write after learn** — call `memory_write(path, content, type=..., title=...)` for durable facts or decisions.

**Overwrite safely:** `memory_write` returns `previous` (full prior file text on update, `null` on create). Read `previous` and merge — do not clobber existing content.

**Never delete `log.md`** — it is the human-readable changelog.

## OKF rules

- Every note needs YAML frontmatter with at least `type` (e.g. `Note`, `Decision`, `Concept`).
- Paths are relative under `notes/`, e.g. `decisions/storage.md` — `.md` only, no `..` traversal.
- If `content` has no frontmatter block, pass `type` (and optional `title`) to `memory_write`.

## MCP

Expose tools to Cursor or Claude Code by running the stdio MCP server:

```bash
truth mcp
```

Install agent files into this project: `truth skill install` (writes `.cursor/skills/truth-memory/`, rule, and optional `mcp.json`).

The MCP server runs `index_all` and starts the file watcher on startup — do not also run `truth serve` on the same notes root.

## Environment

| Variable | Default | Purpose |
|---|---|---|
| `TRUTH_NOTES_ROOT` | `notes/` | Markdown knowledge base |
| `TRUTH_DB_PATH` | `{notes_root}/memory.db` | SQLite index |

Run `truth index` once before first MCP use (downloads embedding model on first run).

## Canonical prompt

Full tool contract: `prompts/system.md` (installed by `truth skill install`).
