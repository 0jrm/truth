# Truth

Local-first OKF agent memory. Markdown files are truth; SQLite is the search index.

**Repository:** [github.com/0jrm/truth](https://github.com/0jrm/truth) · **Docs site:** [GitHub Pages](https://0jrm.github.io/truth/) (enable Pages → `/docs` folder on `master`)

## What it is

Truth gives an AI agent persistent memory: it writes what it learns as OKF-compliant markdown, searches it before answering, and the index stays current automatically. No cloud, no Docker, no graph database — one `memory.db` file alongside your notes.

```
notes/*.md  ──► agent (memory_write) ──► log.md
     ▲                  │
     │                  ▼
     └── watcher ──► indexer ──► memory.db (SQLite)
                                      │
                    memory_search ◄───┘
```

## Install

```bash
pip install truth-source
```

For development:

```bash
git clone https://github.com/0jrm/truth.git
cd truth
pip install -e ".[test]"
```

The first index run downloads the embedding model (~550MB one-time for nomic-embed-text-v1.5, stays local).

## Tests

```bash
pip install -e ".[test]"
pytest
```

Manual regression gates (also run by pytest wrappers):

```bash
python -m truth.index.search_quality   # search_quality=ok
python -m truth.tools.agent_api_check    # agent_api_check=ok
python -m truth.smoke                    # smoke ok
```

## Quick start

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

Optional sanity check after re-indexing:

```bash
python -m truth.index.search_quality
# search_quality=ok
```

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

**System prompt** — copy from `prompts/system.md`, or paste this:

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

**Prerequisites:** `pip install -e .` and a one-time `truth index` (downloads the embedding model on first run).

**Spawn command:**

```bash
truth mcp
```

**Cursor** — copy `.cursor/mcp.json.example` to `.cursor/mcp.json` (or add directly):

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

On startup the MCP server runs `index_all` and starts the file watcher (same bootstrap as `truth serve`). Do not run a second `truth serve` on the same notes root — one watcher per notes directory.

Agent workflow (search-before-answer, write-after-learn): see [skills/truth-memory/SKILL.md](skills/truth-memory/SKILL.md).

## Project structure

```
truth/
├── store/          # OKF frontmatter parse, link graph, notes root
├── index/          # SQLite schema, chunker, embedder, indexer, watcher, search
└── tools/          # memory_search, memory_write, tool_schemas (agent API)

notes/              # your markdown knowledge base (source of truth)
prompts/system.md   # copy-paste agent system prompt
notes/memory.db     # generated — do not commit
notes/inspector.html  # optional — from truth export
```

## Stack

- Python 3.11+
- [sqlite-vec](https://github.com/asg017/sqlite-vec) — vector search in SQLite
- [sentence-transformers](https://www.sbert.net/) — local ONNX embeddings (`nomic-ai/nomic-embed-text-v1.5`, 768-dim)
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

## Known ceilings (v1)

- `log.md` grows unbounded; trim manually or rotate at a future milestone
- Porter FTS stems English aggressively; non-English corpora may need a different tokenizer
- Very large corpora (10k+ notes) may need tuning of chunk size or R3 limits
