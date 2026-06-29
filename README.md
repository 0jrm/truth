# Truth

Local-first OKF agent memory. Markdown files are truth; SQLite is the search index.

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
pip install -e .
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
# open file:///.../notes/inspector.html in your browser
```

The page reads `memory.db` directly via sql.js (offline, no server). Click **Refresh** after `truth serve` or `truth index` updates the database.

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

## Known ceilings (v1)

- `log.md` grows unbounded; trim manually or rotate at a future milestone
- Porter FTS stems English aggressively; non-English corpora may need a different tokenizer
- Very large corpora (10k+ notes) may need tuning of chunk size or R3 limits
