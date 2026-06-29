# Phase 3: Agent Tools - Research

**Researched:** 2026-06-28
**Domain:** Agent tool APIs, OKF write path, function-calling schemas
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- `truth.tools` public API with memory_search re-export
- memory_write writes markdown only; watcher indexes
- Path traversal rejection at write boundary
- auto_type frontmatter injection
- log.md append with ISO timestamp
- prompts/system.md agent contract
- tool_schemas() for function calling

### Deferred
- Ollama modelfile export (v2)
- CLI write subcommand (Phase 5)

</user_constraints>

<research_summary>
## Summary

Phase 3 is a thin wrapper layer over existing store + index modules. No new dependencies required. The write path is the first agent-facing trust boundary — path validation and frontmatter enforcement are the critical security/correctness concerns.

`memory_search` already exists in `truth.index.search`. Phase 3 adds `memory_write` in `truth/tools/write.py`, log append helper, JSON schemas matching OpenAI function-calling format (type, function.name, function.parameters), and a static system prompt file.

Watcher debounce means agents should search after a brief delay or rely on running watcher — document in system prompt; optional `index_file` call after write is a ponytail shortcut if sync needed in tests only (not production API).

</research_summary>

<implementation_notes>
## Implementation Notes

### Path validation
```python
def _safe_note_path(rel: str, root: Path) -> Path:
    p = (root / rel).resolve()
    if not str(p).startswith(str(root.resolve())):
        raise ValueError("path escapes notes root")
    if p.suffix.lower() != ".md":
        raise ValueError("only .md files allowed")
    return p
```

### Tool schema shape (OpenAI-compatible)
```python
{
  "type": "function",
  "function": {
    "name": "memory_search",
    "description": "...",
    "parameters": {"type": "object", "properties": {...}, "required": [...]}
  }
}
```

### log.md entry
```
- 2026-06-28T12:00:00+00:00 **concepts/foo.md** — Added hybrid search notes
```

</implementation_notes>

---
*Phase: 03-agent-tools*
