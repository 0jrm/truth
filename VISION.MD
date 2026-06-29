Google's Open Knowledge Format (OKF), announced June 12 2026, represents knowledge as a directory of markdown files with YAML frontmatter, with a small set of agreed-upon conventions. It requires no SDK, no runtime, no complex compression scheme — just files. A bundle is just markdown, just files, just YAML frontmatter — readable in any editor, renderable on GitHub, indexable by any search tool.

The only required field per concept is `type`. Everything optional: `title`, `description`, `resource`, `tags`, `timestamp`, and any producer-defined key-value pairs. Concepts link to each other with standard markdown links, forming a knowledge graph. Bundles can optionally include `index.md` files for navigation and `log.md` files for chronological history.

**The SQLite MVP is already ~95% OKF-compliant** because its source of truth is a folder of markdown files. The only structural difference:

| OKF requirement | SQLite MVP | Gap? |
|---|---|---|
| Markdown files as source | ✅ your `notes/` folder | None |
| YAML frontmatter with `type` field | ⚠️ not enforced by default | Small — just add frontmatter |
| Cross-links between concepts | ✅ standard markdown links work | None |
| `index.md` / `log.md` conventions | Optional, not required | None |
| No SDK required to read | ✅ | None |

The distinction from RAG is important: RAG re-derives knowledge at query time from raw chunks. An OKF bundle stores curated, cross-linked concepts that an agent reads and updates directly. OKF is parseable with standard tools — a bundle loads by reading every `.md` file, parsing frontmatter, and building the link graph from markdown links.

So the fix is trivial: when writing or ingesting any file, ensure it has a YAML frontmatter block with at least a `type` field. An agent can enforce this as it writes.

---

## How agents maintain the SQLite index

The key insight: **the markdown files are the truth, the SQLite file is just the index**. Agents write markdown; the indexer keeps SQLite in sync. You never directly write to SQLite.

As Andrej Karpathy put it: "LLMs don't get bored, don't forget to update a cross-reference, and can touch 15 files in one pass." The bookkeeping that causes humans to abandon personal wikis is exactly what LLMs are good at.

The agent's write loop is simple:

1. Agent writes or updates a `.md` file (its "memory")
2. A watcher (like `watchdog` in Python) detects the change
3. The indexer re-embeds only changed chunks and updates SQLite
4. Next query instantly sees the new content

The `sqlite-memory` library already handles this with content-hash change detection — it skips unchanged files, atomically replaces modified ones, and cleans up deleted ones. Transactional safety means failed files don't leave partial rows.

For the embedding step with a local model — no Ollama needed for search. You use a small ONNX embedding model (like `nomic-embed-text` or `all-MiniLM-L6-v2`) that runs entirely in-process, about 80MB, CPU-only. Projects like AIngram use `nomic-embed-text-v1.5` running locally via ONNX — 768-dimensional embeddings, CPU or GPU, no external API.

---

## How an agent learns to rely on this

This is the most important part — and it's solved by the **system prompt**, not by code. You give the agent two tools and tell it to use them:

```
Tools:
  memory_search(query) → returns top-k relevant chunks from your knowledge base
  memory_write(path, content) → writes/updates a markdown file in your knowledge base

Rules:
  - Before answering any question, call memory_search first
  - After learning anything new or completing a task, call memory_write to record it
  - Memory files must have YAML frontmatter with a `type` field
```

That's it. The agent becomes self-maintaining. It reads before it acts, writes after it learns. With a local model (Ollama + `llama3`, `mistral`, `qwen2.5` etc.) you point the function-calling at those two tools and the loop runs entirely offline.

An OKF-compatible agent just writes a markdown file — no API, no authentication, no SDK. The file system IS the API.

---

Here's the full MVP architecture:---

## Getting started — the minimal path

**Step 1 — your knowledge folder:**
```
mkdir -p ~/brain/notes ~/~/brain/projects
```
Each file needs a frontmatter block for OKF compliance:
```markdown
---
type: Note
title: "How SQLite vector search works"
tags: [sqlite, vector, search]
timestamp: 2026-06-28T10:00:00Z
---
Content here, [[links]] to other concepts.
```

**Step 2 — the index (~50 lines of Python):**
```bash
pip install sqlite-vec sentence-transformers watchdog
```
Then a script that:
- Walks the folder, chunks each `.md` file
- Embeds chunks with a local ONNX model (first run downloads ~80MB, stays local forever)
- Stores vectors + text in `memory.db`
- Watches for file changes and re-indexes only what changed

**Step 3 — two tools for the agent:**
```python
def memory_search(query: str, k: int = 5) -> list[dict]:
    # embed query → vector search → BM25 search → RRF merge → return top-k

def memory_write(path: str, content: str) -> None:
    # write markdown to ~/brain/path.md
    # watcher picks it up automatically
```

**Step 4 — the system prompt (the most important part):**
```
You have persistent memory stored as markdown files.
BEFORE answering, always call memory_search() to check what you know.
AFTER learning something new, call memory_write() to record it.
Files must start with YAML frontmatter including a `type` field.
```

Point Ollama at these tools and the agent self-maintains its own OKF-compliant knowledge base, entirely locally, with no Docker, no graph DB, no cloud.

---

Build the actual Python scripts for the indexer and the two tool functions.
