# Truth — Vision

Forward-looking vision for Truth: local-first OKF agent memory where markdown files are the durable record and SQLite is a derived search index.

## What Truth is

Truth gives an AI agent persistent memory without cloud services, Docker, or a graph database. Agents write what they learn as OKF-compliant markdown under `notes/`, search that knowledge before answering, and the index stays current automatically via a file watcher.

The core contract is simple: **markdown in `notes/` is truth; `memory.db` is the index**. Agents never write to SQLite directly — they write files; the indexer keeps the database in sync.

Truth runs entirely offline on a single machine. Embeddings are computed locally; hybrid search runs in-process against SQLite. One install (`pip install -e .`), one notes folder, one index file colocated with your notes.

## OKF alignment

Google's Open Knowledge Format (OKF, June 2026) stores knowledge as a directory of markdown files with YAML frontmatter. The only required field per concept is `type`. Concepts link to each other with standard markdown links, forming a knowledge graph. Bundles can optionally include `index.md` for navigation and `log.md` for chronological history.

Truth implements OKF as its storage model:

| OKF convention | Truth implementation |
|---|---|
| Markdown files as source of truth | `notes/` folder — every `.md` file is a concept |
| YAML frontmatter with `type` | Enforced on write via `memory_write`; indexer skips files missing `type` |
| Cross-links between concepts | Standard markdown links; parsed at index time for the link graph |
| Optional `log.md` changelog | Appended automatically on every `memory_write` (write-time log) |
| No SDK required to read | Plain files — readable in any editor, renderable on GitHub |

The distinction from RAG matters: RAG re-derives knowledge at query time from raw chunks. An OKF bundle stores curated, cross-linked concepts that an agent reads and updates directly. OKF is parseable with standard tools — load a bundle by reading every `.md` file, parsing frontmatter, and building the link graph from markdown links.

## Architecture

```
notes/*.md  ──► agent (memory_write) ──► log.md
     ▲                  │
     │                  ▼
     └── watcher ──► indexer ──► memory.db (SQLite)
                                      │
                    memory_search ◄───┘
```

**Write path:** An agent calls `memory_write` (or writes a file directly). The watcher detects the change within ~500ms, the indexer re-embeds only changed chunks, and an event is recorded in the events table.

**Read path:** An agent calls `memory_search`. The query is embedded locally, run through vector search and BM25 keyword search, merged with Reciprocal Rank Fusion (RRF), and top-k chunks are returned with path and score.

**Delete path:** An agent calls `memory_delete`. The file is removed from disk; the watcher cleans up index rows on the next pass.

Human observability (CLI inspector, optional browser export) sits beside this loop — useful for debugging and browsing, not required for the agent to function.

## Agent tools

Truth exposes three tools for function-calling LLMs (Ollama, OpenAI-compatible APIs, etc.). The system prompt in `prompts/system.md` defines the agent loop:

- **Search before answer** — call `memory_search` when the user asks about facts, preferences, past work, or project context.
- **Write after learn** — call `memory_write` when you discover durable facts, decisions, or outcomes.
- **Overwrite safely** — `memory_write` returns `previous` (full prior file text on overwrite, `null` on create); read it before clobbering existing content.

### memory_search

```
memory_search(query, k=5, type=None, tags=None)
```

Hybrid vector + keyword search over indexed notes. Optional `type` filters by OKF frontmatter type; optional `tags` requires all listed tags (AND). Returns ranked chunks with path, score, and snippet.

### memory_write

```
memory_write(path, content, type="Note", title=None, summary=None)
```

Creates or updates a `.md` file under the notes directory. Enforces YAML frontmatter with at least `type`. Appends a human-readable entry to `log.md`. Returns `{"path": ..., "previous": ...}`.

### memory_delete

```
memory_delete(path)
```

Removes a note by relative path. Cannot delete `log.md`. Index cleanup happens via the watcher.

Wire these tools with `truth.tools.tool_schemas()` for OpenAI-compatible runtimes. Run `truth serve` (or `truth index` for one-shot) so the index stays current.

## Index and search

The indexer walks `notes/`, chunks each markdown file, embeds chunks with a local ONNX model, and stores vectors plus text in SQLite via [sqlite-vec](https://github.com/asg017/sqlite-vec).

| Component | Detail |
|---|---|
| Embeddings | `nomic-ai/nomic-embed-text-v1.5` via sentence-transformers (768-dim, CPU, ~550MB one-time download) |
| Vector search | sqlite-vec cosine distance |
| Keyword search | FTS5 with porter unicode61 tokenizer |
| Merge | Reciprocal Rank Fusion (RRF) across both result sets |
| Incremental indexing | Content-hash change detection — unchanged files are skipped |
| Exclusions | `log.md` and files with `skip_index: true` in frontmatter are not semantically indexed |

A file watcher (watchdog) debounces filesystem events and re-indexes only what changed. An events table tracks create, update, and delete operations for the changelog inspector.

## Human observability

Truth includes a memory inspector for humans — observability, not part of the agent loop.

**CLI commands:**

- `truth tree` — notes folder hierarchy with type and title from frontmatter
- `truth links <path>` — incoming and outgoing links for a note
- `truth changes [-n N]` — recent file operations from the events table
- `truth graph [--json]` — link graph as text or JSON

**Optional browser inspector:**

- `truth export` — copies a static HTML page into the notes folder
- Serve `notes/` over HTTP (e.g. `python -m http.server`) and open `inspector.html`; reads `memory.db` via sql.js — **`file://` does not work** (browsers block local `fetch()`)

These tools help you see what the agent wrote, trace link relationships, and review the changelog. The agent does not need them to search or write.

## What's next

Current milestone work (v1.1) focuses on quality and completeness:

- **Phase 9 (in progress)** — rewrite this vision doc; consolidate regression tests into pytest (`tests/test_search_quality.py`, chunker boundary, delete/filter integration)
- **Phase 10** — inspector note viewer, in-browser search, live refresh after index updates
- **Phase 11** — MCP stdio server exposing Truth tools + project skill for agent runtimes

Phases 1–8 shipped the OKF store, hybrid index, agent tools (including delete and search filters), CLI inspector, and integration CLI (`truth index`, `truth serve`, `truth export`).

## Philosophy

**The filesystem is the API.** An OKF-compatible agent writes a markdown file — no authentication, no SDK, no runtime dependency to read the data. Plain files survive tool churn; SQLite is rebuildable from markdown at any time.

**Agents maintain cross-links.** As Andrej Karpathy put it: LLMs don't get bored, don't forget to update a cross-reference, and can touch fifteen files in one pass. The bookkeeping that causes humans to abandon personal wikis is exactly what LLMs are good at. Truth gives them search-before-answer and write-after-learn tools; the system prompt does the rest.

**Local-only by design.** All data and embeddings stay on disk. No cloud sync, no external API calls for the core loop. Search works without Ollama or any LLM runtime — only the agent conversation needs a model.

**Index is derived, not authoritative.** If `memory.db` is lost or corrupted, run `truth index` to rebuild from markdown. Never edit SQLite by hand; never teach agents to write rows directly.

**Inspector is for humans.** The agent loop is two tools and a prompt. Everything else — tree, links, graph, browser export — is optional visibility for the person curating the knowledge base.
