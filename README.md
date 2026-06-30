# Truth — local-first, OKF-native memory for AI agents

> Give your AI agent a memory it owns. No cloud, no Docker, no graph database — just a folder of markdown files and one pip install.

**Repository:** [github.com/0jrm/truth](https://github.com/0jrm/truth) · **PyPI:** [truth-memory](https://pypi.org/project/truth-memory/) · **Docs:** [GitHub Pages](https://0jrm.github.io/truth/)

In June 2026, Google standardized **[OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)** (Open Knowledge Format) — agent-readable markdown with YAML frontmatter and cross-links. Truth is the first local-first, OKF-native memory store built for coding agents: markdown is truth, SQLite is a rebuildable search index.

## The problem

Every conversation with an AI starts from zero. You explain your project stack again. You re-share the decision you made last week. You paste in context the agent should already know.

The usual fixes — Mem0, Cognee, LocalRecall — often mean Docker, accounts, or multi-service setups. They solve forgetting by adding infrastructure.

Truth inverts that. The agent's memory is a folder of markdown files in OKF format. Read every note in any text editor. `git commit` it. Search it with `grep`. When the agent learns something, it writes a file. When it needs to remember, it searches. The index is SQLite — one `memory.db` file beside your notes, rebuildable anytime, never authoritative.

## How it works

```
notes/*.md  ──► agent (memory_write) ──► log.md
     ▲                  │
     │                  ▼
     └── watcher ──► indexer ──► memory.db (SQLite)
                                      │
                    memory_search ◄───┘
```

Hybrid vector + keyword search over your notes. A file watcher keeps the index current as the agent (or you) writes. Lose `memory.db`? Run `truth index` to rebuild from markdown.

## Who it's for

**Developers using Cursor or Claude Code** — Truth is a persistent memory layer for your coding agent. It remembers architecture decisions, team naming conventions, and why you chose that library. Point it at your `notes/` folder and your agent stops asking the same questions.

**Solo builders and indie hackers** — Your AI assistant finally has memory that survives between sessions and belongs to you. Every fact it learns lives in a markdown file in your git repo. No subscription, no account, no cloud.

**Privacy-conscious users** — All data and embeddings stay on your machine. Truth uses a local embedding model (`nomic-ai/nomic-embed-text-v1.5` via sentence-transformers / PyTorch on CPU). Nothing leaves your disk — not even for search.

## Install

```bash
pip install truth-memory
```

For development:

```bash
git clone https://github.com/0jrm/truth.git
cd truth
pip install -e ".[test]"
```

The first index run downloads the embedding model (~550MB one-time for nomic-embed-text-v1.5, stays local).

### Agent skill (Cursor)

After installing the package, wire the **truth-memory** skill into your project:

```bash
truth skill install
```

This writes:

- `.cursor/skills/truth-memory/SKILL.md` — search-before-answer / write-after-learn workflow
- `.cursor/rules/truth-memory.mdc` — always-on rule pointing at the skill
- `prompts/system.md` — full tool contract for other runtimes
- `.cursor/mcp.json` — MCP server config (only if missing)

Use `--personal` to install the skill globally under `~/.cursor/skills/`. Use `--force` to overwrite existing files.

## Tests

```bash
pip install -e ".[test]"
pytest
```

Regression coverage includes search quality (5-note rank-1), agent API filters/overwrite/delete, watcher concurrency, and an end-to-end smoke pipeline — all via `pytest`. Optional MCP stress harness: `python tests/stress_mcp_shared_notes.py`.

## Performance

Timed on this machine against real `notes/` (7 indexed files, nomic-embed on CPU).

| Operation | Time | Notes |
|---|---|---|
| Model cold load (first embed) | ~2.5 s | In-process, one-time per process |
| `truth index` CLI (subprocess) | ~11–13 s | New Python process reloads model every time, even if nothing changed |
| `index_all` in-process, warm, unchanged | ~5–7 ms | Hash skip — almost all work avoided |
| `index_all` in-process, warm, 12 md files | ~107 ms | Full pass with some reindexing |
| Embed 1 doc, warm | ~51–69 ms | |
| Embed 10 docs, warm | ~159–181 ms | |
| `index_file` new note (embed + SQLite) | ~135 ms | Direct, no watcher |
| `memory_write` (disk only) | <1 ms | Watcher indexes separately |
| `memory_search` k=5, warm | ~55–68 ms | |
| `open_db` + `init_schema` | ~1 ms | |
| Watcher round-trip (write → indexed) | ~625–665 ms | ~500 ms debounce + ~135 ms index |
| `truth mcp` cold boot (`initialize`) | ~7.5 s | `index_all` + model load + watcher per subprocess |
| `memory_write` via MCP | ~17 ms | RPC only; indexing still async |
| MCP write → `memory_search` hit | ~2.2 s | Debounce + index + search poll (agent-visible latency) |
| `memory_search` via MCP, warm | ~58 ms | After index caught up |

**What dominates**

1. **Embedding model load** — ~2.5 s in-process, ~7.5 s MCP boot, ~12 s per CLI subprocess.
2. **Watcher debounce** — fixed 500 ms floor on every write.
3. **Actual index work, warm** — ~135 ms/note. Search is ~60 ms/query.

Everything else (SQLite, markdown I/O) is noise at this scale. Agents using MCP feel (2) + (3) as ~2 s before a write is searchable.

## Quick start

Create a `notes/` folder (or set `TRUTH_NOTES_ROOT`) with at least one OKF markdown file, then:

**1. Index your notes**

```bash
truth index
# indexed_files=5
```

**2. Start the file watcher** (keeps the index live as you or the agent write)

```bash
truth serve
# Ctrl+C to stop
```

**3. Use the tools in Python**

```python
from truth.tools import memory_search, memory_write

# search
results = memory_search("hybrid search", k=5)
for r in results:
    print(r["path"], r["score"])

# write
memory_write(
    "decisions/storage.md",
    "We use SQLite + sqlite-vec for the hybrid index.",
    title="Storage decision"
)
```

## Configuration

| Variable | Default | Description |
|---|---|---|
| `TRUTH_NOTES_ROOT` | `notes/` | Folder of markdown knowledge files |
| `TRUTH_DB_PATH` | `{notes_root}/memory.db` | SQLite index file (colocated with notes for browser inspector) |

If you have an older `memory.db` at the project root, move it: `mv memory.db notes/` or set `TRUTH_DB_PATH`.

### Upgrading from v1.0

v1.1 changes the embedding model (384-dim MiniLM → 768-dim nomic) and the FTS tokenizer (trigram → porter unicode61). Both require a **full re-index** — old chunk vectors and FTS tokens are incompatible.

```bash
# back up if needed, then remove the stale index
rm notes/memory.db
truth index
```

On first open, an existing database auto-migrates index tables (drops old chunks/vec/fts) via `init_schema`, but you still must run `truth index` to rebuild embeddings.

## Browser inspector

Export the static inspector into your notes folder (beside `memory.db`):

```bash
truth export
```

Serve the notes folder over HTTP and open the inspector in your browser:

```bash
cd notes   # or $TRUTH_NOTES_ROOT
python -m http.server 8765
# http://127.0.0.1:8765/inspector.html
```

**Do not open `inspector.html` via `file://`.** Modern browsers block `fetch()` from `file://` pages to other local files (`memory.db`, `vendor/sql-wasm.wasm`, note `.md` files). The UI shell loads but Tree, Note, Links, and Changes stay empty. Use a local HTTP server (as above) — the page still reads `memory.db` via sql.js with no Truth backend.

**Four panels:** Tree, Note (raw markdown from disk, including frontmatter), Links, Changes. The Note panel fetches `.md` files directly; disk may be ahead of the index until the watcher reindexes.

**Search** filters the tree by path, title, or type (instant substring match). It also runs FTS over indexed chunk text in `memory.db` (not hybrid vector search). Search and changelog reflect the index; the Note panel shows current file content from disk.

**Live** (checkbox, default off) polls `memory.db` every ~5s and auto-refreshes when the database changes — useful with `truth serve` running for near-live debugging. **Refresh** manually reloads the database when Live is off.

## Note format (OKF)

Every file needs YAML frontmatter with at least a `type` field:

```markdown
---
type: Note
title: "My note"
tags: [example]
timestamp: 2026-06-28T10:00:00Z
---

Body content here. Link to [another concept](other.md).
```

`memory_write` enforces this automatically. Files missing `type` are skipped by the indexer with a warning.

**Indexing exclusions:** `log.md` is never semantically indexed (changelog only). Files with `skip_index: true` in frontmatter are tracked in the file tree but excluded from chunk/vector/FTS indexing:

```markdown
---
type: Note
title: "Scratch pad"
skip_index: true
---

Draft content not meant for agent search.
```

## Wiring to an agent (Ollama / any function-calling LLM)

**System prompt** — install with `truth skill install` (writes `prompts/system.md`), or copy from `truth/bundled/prompts/system.md`, or paste this:

```
You have persistent memory stored as OKF markdown files on disk.

- Before answering, call memory_search() to check what you know.
- After learning something new, call memory_write() to record it.
- Every note must have YAML frontmatter with at least a `type` field.
```

**Tool schemas** (OpenAI-compatible, works with Ollama):

```python
from truth.tools import tool_schemas, memory_search, memory_write

schemas = tool_schemas()  # pass to your LLM's tools= parameter
```

**Tool dispatch loop** (minimal example):

```python
import json, ollama
from truth.tools import memory_search, memory_write, tool_schemas

def run(user_message: str):
    messages = [{"role": "user", "content": user_message}]
    tools = tool_schemas()

    while True:
        resp = ollama.chat(model="llama3", messages=messages, tools=tools)
        msg = resp["message"]
        messages.append(msg)

        if not msg.get("tool_calls"):
            return msg["content"]

        for call in msg["tool_calls"]:
            name = call["function"]["name"]
            args = call["function"]["arguments"]

            if name == "memory_search":
                result = memory_search(**args)
            elif name == "memory_write":
                result = str(memory_write(**args))
            else:
                result = f"unknown tool: {name}"

            messages.append({
                "role": "tool",
                "content": json.dumps(result),
            })
```

The watcher re-indexes writes within ~500ms. The agent's next `memory_search` will see what it just wrote.

## MCP (Cursor / Claude Code)

Expose `memory_search`, `memory_write`, and `memory_delete` to Cursor or Claude Code via stdio MCP.

**Prerequisites:** `pip install truth-memory` and a one-time `truth index` (downloads the embedding model on first run). Run `truth skill install` to add the agent skill and MCP config to your project.

**Spawn command:**

```bash
truth mcp
```

**Cursor** — `truth skill install` writes `.cursor/mcp.json` for you. Otherwise create it manually:

```json
{
  "mcpServers": {
    "truth": {
      "command": "truth",
      "args": ["mcp"]
    }
  }
}
```

Optional env overrides in the server block:

```json
"env": {
  "TRUTH_NOTES_ROOT": "/path/to/notes",
  "TRUTH_DB_PATH": "/path/to/notes/memory.db"
}
```

**Claude Code:**

```bash
claude mcp add truth -- truth mcp
```

On startup the MCP server runs `index_all` and starts the file watcher (same bootstrap as `truth serve`). Each Truth process starts its own watcher and loads its own embedding model — do not run a second `truth serve` on the same notes root. See [Concurrency](#concurrency) for how many agents can safely share one `notes/` folder.

Agent workflow (search-before-answer, write-after-learn): install with `truth skill install` or see `.cursor/skills/truth-memory/SKILL.md` in your project.

## Project structure

```
truth/
├── store/          # OKF frontmatter parse, link graph, notes root
├── index/          # SQLite schema, chunker, embedder, indexer, watcher, search
└── tools/          # memory_search, memory_write, tool_schemas (agent API)

notes/              # your markdown knowledge base (source of truth)
truth/bundled/      # canonical agent skill, rule, prompt (installed via truth skill install)
notes/memory.db     # generated — do not commit
notes/inspector.html  # optional — from truth export
```

## Stack

- Python 3.11+
- [sqlite-vec](https://github.com/asg017/sqlite-vec) — vector search in SQLite
- [sentence-transformers](https://www.sbert.net/) — local PyTorch embeddings (`nomic-ai/nomic-embed-text-v1.5`, 768-dim)
- [watchdog](https://github.com/gorakhargosh/watchdog) — file system events
- Search: vector + BM25 (FTS5 porter unicode61) + Reciprocal Rank Fusion

## Roadmap

- [x] Phase 1 — OKF markdown store with frontmatter enforcement
- [x] Phase 2 — Hybrid SQLite index with watcher and events table
- [x] Phase 3 — Agent tools (`memory_search`, `memory_write`), `log.md`, system prompt
- [x] Phase 4 — Memory inspector CLI (`truth tree`, `truth links`, `truth changes`, `truth graph`)
- [x] Phase 5 — `truth serve` / `truth index`, env config, static sql.js inspector, docs
- [x] Phase 6 — Search quality fixes (nomic embeddings, porter FTS, RRF tuning)
- [x] Phase 7 — Indexer and watcher correctness
- [x] Phase 8 — Agent API completion (`memory_delete`, filters)
- [x] Phase 9 — Docs and test suite
- [x] Phase 10 — Inspector upgrades
- [x] Phase 11 — MCP stdio server (`truth mcp`), project skill, dogfood decision note

## Concurrency

Stress-tested with `tests/stress_mcp_shared_notes.py`: N concurrent MCP clients, each spawning `truth mcp` (stdio) against one shared `notes/` + `memory.db` on one machine (2026-06-30). Success = `memory_write` then `memory_search` returns the new path — the same path agents actually use.

| MCP clients | Result | Searchable | Indexed / disk | Errors | Wall time | DB integrity |
|------------:|--------|------------|----------------|--------|-----------|--------------|
| 1 | OK | 1/1 | 1/1 | 0 | 10.2 s | ok |
| 2 | OK | 2/2 | 2/2 | 0 | 12.2 s | ok |
| 4 | fail | 3/4 | 3/3 | 1 bootstrap | 14.8 s | ok |
| 8 | OK | 8/8 | 8/8 | 0 | 30.9 s | ok |
| 16 | fail | 10/16 | 10/16 | 6 search timeouts | 60.5 s | ok |

Baseline notes were never corrupted; `PRAGMA integrity_check` stayed ok at every level.

**What changes vs in-process testing**

- Each client is a real `truth mcp` subprocess: `index_all` + watcher + model load on every connect (~7.5 s cold boot).
- Writes are validated through `memory_search`, not a direct SQLite poll — closer to Cursor / Claude Code behavior.
- MCP boot is heavier than calling `memory_write` in Python, but the index path is the same once warm.

**Practical guidance**

- **Same machine, 1–8 MCP sessions** on one `notes/` — passed in testing (4 had one flaky parallel bootstrap). Budget ~8 s first tool call per new MCP process and ~2 s before a write is searchable.
- **16+ MCP processes** — boot contention (30–40 s) and index lag; some writes never become searchable within the test window.
- **Network drive / multiple machines** — not stress-tested. SQLite WAL + one-watcher-per-process still make this risky.

Reproduce: `python tests/stress_mcp_shared_notes.py` (writes `tests/stress_mcp_results.json`; uses `/tmp/truth-mcp-golden`, does not touch project `notes/`).

## Known ceilings (v1)

- One watcher per `truth mcp` process; same `notes/` supports ~8 concurrent MCP clients in testing (see [Concurrency](#concurrency))
- `log.md` grows unbounded; trim manually or rotate at a future milestone
- Porter FTS stems English aggressively; non-English corpora may need a different tokenizer
- Very large corpora (10k+ notes) may need tuning of chunk size or R3 limits
