# Phase 3: Agent Tools - Context

**Gathered:** 2026-06-28
**Status:** Ready for planning
**Mode:** Auto-selected assumptions (pipeline advance)

<domain>
## Phase Boundary

Clean Python agent API: `memory_search` and `memory_write` as importable tools, OKF `log.md` append on writes, function-calling schemas, and a system prompt template documenting the search-before-answer / write-after-learn loop. Agents write markdown only — the existing watcher/indexer keeps SQLite in sync.

</domain>

<decisions>
## Implementation Decisions

### Public API surface
- **D-01:** Agent-facing module is `truth.tools` — `from truth.tools import memory_search, memory_write`
- **D-02:** `memory_search` re-exports `truth.index.search.memory_search` unchanged (Phase 2 already implements hybrid search)
- **D-03:** Export `tool_schemas()` returning a list of JSON-schema dicts suitable for Ollama/OpenAI function calling (TOOL-02)

### memory_write behavior
- **D-04:** Signature `memory_write(path: str, content: str, *, type: str = "Note", title: str | None = None, summary: str | None = None) -> Path`
- **D-05:** Path is relative to `notes_root()`; reject `..`, absolute paths outside root, and non-`.md` targets
- **D-06:** If `content` lacks frontmatter, wrap with `format_note(validate_frontmatter({type, title?}, auto_type=type), body)`; if content has frontmatter, parse + validate (auto_type fallback)
- **D-07:** Write file with UTF-8; create parent dirs; do NOT touch SQLite — watcher indexes asynchronously (document ~500ms debounce + embed latency)
- **D-08:** Optional `summary` param defaults to first line of body (truncated) for log entry

### OKF log.md
- **D-09:** Append to `{notes_root}/log.md` on every successful write
- **D-10:** Entry format: `- {ISO8601 UTC} **{relative_path}** — {summary}` (markdown list item, human-readable)
- **D-11:** Create `log.md` with minimal frontmatter (`type: Log`) if missing

### System prompt
- **D-12:** `prompts/system.md` documents: search before answer, write after learn, frontmatter `type` requirement, example tool calls
- **D-13:** Include note that watcher must be running for immediate search visibility (Phase 5 `truth serve` bundles this)

### the agent's Discretion
- Exact path normalization (resolve vs strict string check)
- Whether `memory_write` returns written path or None
- Tool schema field descriptions wording

</decisions>

<canonical_refs>
## Canonical References

### Requirements & architecture
- `.planning/PROJECT.md` — core value, markdown-as-truth constraint
- `.planning/REQUIREMENTS.md` — TOOL-01..04
- `.planning/ROADMAP.md` — Phase 3 success criteria
- `VISION.MD` — tool signatures, system prompt sketch
- `AGENTS.md` — never write SQLite from agent code

### Existing implementations to reuse
- `truth/index/search.py` — `memory_search`
- `truth/store/frontmatter.py` — `parse_note`, `format_note`, `validate_frontmatter`
- `truth/store/paths.py` — `notes_root()`
- `truth/index/watcher.py` — async index after write

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `validate_frontmatter(..., auto_type="Note")` — MEM-03 ready for write path
- `format_note(meta, body)` — OKF serialization
- `memory_search` in `truth.index` — hybrid search complete

### Established Patterns
- Self-check via `python -m truth.tools.write` (or module `__main__`)
- ponytail: path traversal guard at trust boundary
- Markdown truth: write file, watcher updates index

### Integration Points
- New `truth/tools/__init__.py` re-exports public API
- `truth/tools/write.py` implements memory_write + log append
- `truth/tools/schemas.py` optional — tool JSON schemas
- `prompts/system.md` new file at repo root

</code_context>

<specifics>
## Specific Ideas

- Match VISION.MD tool signatures closely for Ollama hookup in Phase 5 README
- System prompt is "the most important part" per vision — keep it concise and copy-paste ready

</specifics>

<deferred>
## Deferred Ideas

- Pre-built Ollama modelfile export — v2 (AGNT-01)
- Synchronous index-after-write option — watcher is sufficient for v1
- `memory_write` delete/archive helper — out of scope
- CLI `truth write` subcommand — Phase 5

</deferred>

---

*Phase: 03-agent-tools*
*Context gathered: 2026-06-28*
