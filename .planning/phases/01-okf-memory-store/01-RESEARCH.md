# Phase 1: OKF Memory Store - Research

**Researched:** 2026-06-28
**Domain:** OKF markdown store, YAML frontmatter, markdown link graph
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

No CONTEXT.md exists — decisions from PROJECT.md, REQUIREMENTS.md, VISION.MD, and AGENTS.md.

### Locked Decisions (from project docs)
- Markdown files in `notes/` are source of truth; never write SQLite from agent code
- Every memory file requires YAML frontmatter with at least `type` (OKF)
- Python 3.11+, prefer stdlib; mark intentional shortcuts with `ponytail:` comments
- Configurable knowledge root, default `notes/`
- Indexer logic stays minimal (~50–200 lines core); Phase 1 is store layer only

### Claude's Discretion
- PyYAML vs `python-frontmatter` package (prefer PyYAML + manual split for fewer deps)
- Exact package layout under `truth/store/`
- Whether missing `type` is rejected vs auto-added default (build validator supporting both; default reject)
- Wiki-link `[[note]]` support in v1 (defer — standard markdown `[text](path.md)` only for MEM-04)

### Deferred Ideas (OUT OF SCOPE)
- SQLite index, embeddings, watcher (Phase 2)
- `memory_write` tool (Phase 3) — but validator API must be ready for it
- Inspector CLI (Phase 4)
- `[[wiki]]` links, `index.md` generation, `log.md` append (later phases)

</user_constraints>

<architectural_responsibility_map>
## Architectural Responsibility Map

Single-tier application — all Phase 1 capabilities reside in the Python library + filesystem.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Frontmatter parse/validate | Python library (`truth/store`) | Filesystem (`notes/`) | Validation at write boundary |
| Link graph extraction | Python library (`truth/store/links`) | — | Pure function over parsed markdown |
| Sample seed notes | Filesystem (`notes/`) | — | Human/agent-readable truth layer |

</architectural_responsibility_map>

<research_summary>
## Summary

Phase 1 establishes the OKF truth layer: a configurable `notes/` directory, a small Python package that parses YAML frontmatter and enforces the required `type` field, and a link extractor that yields `(source, target)` pairs from standard markdown links.

OKF (June 2026) requires only `type` in frontmatter; everything else is optional. The vision doc already specifies the gap: enforce frontmatter on write. Phase 1 builds the shared validation/parsing module that Phase 2 (indexer) and Phase 3 (`memory_write`) will import — no duplicate parsing logic later.

For Python, splitting on `---` delimiters and parsing the middle block with PyYAML is the minimal approach (stdlib has no YAML). Link extraction uses regex over the body after frontmatter removal — no AST library needed for v1. Relative paths resolve against the source file's directory.

**Primary recommendation:** `truth/store/` with `frontmatter.py`, `links.py`, `paths.py`; PyYAML as sole new dependency; reject writes missing `type` by default with optional auto-add helper for Phase 3.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.11+ | Runtime | Project constraint |
| PyYAML | 6.x | Frontmatter YAML parse | No stdlib YAML; tiny, stable |
| pathlib | stdlib | Path resolution | Relative link targets |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| re | stdlib | Markdown link regex | Phase 1 link extraction |
| dataclasses | stdlib | ParsedNote, LinkEdge types | Clean return types |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PyYAML + manual split | python-frontmatter | One dep vs two concepts bundled; manual split is ~15 lines |
| Regex links | markdown-it-py / mistletoe | AST is heavier; regex covers `[text](path)` for v1 |
| Auto-add `type` | Reject only | REQUIREMENTS allow both; implement `ensure_frontmatter()` for Phase 3 |

**Installation:**
```bash
pip install pyyaml
# Full project (Phase 1 scaffold):
pip install -e .
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Data Flow

```
memory_write (Phase 3) ──► validate_frontmatter() ──► write .md to notes/
                                    ▲
indexer (Phase 2) ──► parse_note() ──┘──► extract_links() ──► (source, target) pairs
human/editor ──► direct file edit ──► notes/*.md
```

### Recommended Project Structure
```
truth/
├── __init__.py
└── store/
    ├── __init__.py      # public API: parse_note, validate_frontmatter, extract_links
    ├── frontmatter.py   # split --- blocks, YAML load, type enforcement
    ├── links.py         # regex extract [text](target), resolve relative paths
    └── paths.py         # notes_root() from env TRUTH_NOTES_ROOT or default notes/

notes/
├── okf-format.md        # seed: explains OKF
├── sqlite-vectors.md    # seed: links to okf-format
└── hybrid-search.md     # seed: links to sqlite-vectors

pyproject.toml
```

### Pattern 1: Frontmatter Split
**What:** Split file on first two `---` lines; YAML between them; body after.
**When to use:** Every `.md` read/write in the system.
**Example:**
```python
import yaml

def split_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("unclosed frontmatter")
    meta = yaml.safe_load(parts[1]) or {}
    body = parts[2].lstrip("\n")
    return meta, body
```

### Pattern 2: Link Extraction
**What:** Find `[label](target)` in body; skip `http://` and `https://` targets for graph edges.
**When to use:** Index time (Phase 2) and inspector (Phase 4).
**Example:**
```python
import re
LINK_RE = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')

def extract_link_targets(body: str) -> list[str]:
    return [m.group(2) for m in LINK_RE.finditer(body)
            if not m.group(2).startswith(("http://", "https://", "#"))]
```

### Anti-Patterns to Avoid
- **Parsing frontmatter in indexer AND write path separately:** One module in `truth/store/`
- **Writing SQLite from store layer:** Store only touches markdown files
- **Using file mtime for anything:** Events table comes in Phase 2
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing | Custom key=value parser | PyYAML `safe_load` | Nested values, quoting, edge cases |
| Full markdown AST | Custom tokenizer | Regex for links only in v1 | MEM-04 needs links only, not rendering |
| Config framework | TOML loader in Phase 1 | `os.environ.get("TRUTH_NOTES_ROOT", "notes")` | CLI-02 is Phase 5; env var stub is enough |

**Key insight:** Phase 1 scope is narrow — parse, validate, extract links. Defer chunking, hashing, and embeddings to Phase 2.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Frontmatter Corruption on Write
**What goes wrong:** Agent appends content above `---` block or duplicates frontmatter.
**Why it happens:** String concat without structured write.
**How to avoid:** Always parse → merge meta → serialize with `---\n` wrapper.
**Warning signs:** Multiple `---` blocks in one file.

### Pitfall 2: Broken Relative Link Resolution
**What goes wrong:** `../other.md` resolves wrong from nested folders.
**Why it happens:** Resolving against CWD instead of source file parent.
**How to avoid:** `Path(source).parent / target` then normalize.
**Warning signs:** Graph edges pointing to non-existent absolute paths.

### Pitfall 3: Empty or Non-Dict Frontmatter
**What goes wrong:** `---\n---\n` or `---\ntype: Note\n---` with scalar YAML mistakes.
**Why it happens:** YAML can load to non-dict.
**How to avoid:** After `safe_load`, assert `isinstance(meta, dict)`.
**Warning signs:** `type` KeyError at runtime.
</common_pitfalls>

<code_examples>
## Code Examples

### Validate Required `type`
```python
def validate_frontmatter(meta: dict, *, auto_type: str | None = None) -> dict:
    if not isinstance(meta, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    if "type" not in meta or not meta["type"]:
        if auto_type:
            meta = {**meta, "type": auto_type}
        else:
            raise ValueError("missing required frontmatter field: type")
    return meta
```

### Serialize Note for Write
```python
def format_note(meta: dict, body: str) -> str:
    return f"---\n{yaml.safe_dump(meta, sort_keys=False).rstrip()}\n---\n{body}"
```
</code_examples>

<sota_updates>
## State of the Art (2024-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Chunk-only RAG | OKF curated concepts + links | OKF June 2026 | Phase 1 aligns with graph-friendly store |
| Cloud embeddings required | Local ONNX in-process | sqlite-vec ecosystem | Not Phase 1 — but notes format must be stable |

**Deprecated/outdated:**
- Storing knowledge only in vector DB without markdown truth — contradicts project core value
</sota_updates>

<open_questions>
## Open Questions

1. **Default `type` when auto-adding**
   - What we know: OKF examples use `Note`, `Concept`, etc.
   - Recommendation: default auto_type=`Note` in `ensure_frontmatter()`; Phase 3 decides policy.

2. **Support `.md` files without frontmatter in existing folders**
   - What we know: Phase 1 seeds controlled sample notes.
   - Recommendation: `parse_note` raises on missing frontmatter; indexer can skip or quarantine in Phase 2.
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `VISION.MD` — OKF alignment, architecture, frontmatter examples
- `.planning/PROJECT.md` — constraints and decisions
- `.planning/REQUIREMENTS.md` — MEM-01 through MEM-04
- Google OKF announcement (June 2026) — cited in VISION.MD

### Secondary (MEDIUM confidence)
- `.planning/research/SUMMARY.md` — stack recommendations (PyYAML, avoid python-frontmatter unless needed)

</sources>

<metadata>
## Metadata

**Research scope:** OKF store layer, frontmatter, link extraction, Python packaging
**Confidence breakdown:** Standard stack HIGH, Architecture HIGH, Pitfalls HIGH, Code examples HIGH
**Research date:** 2026-06-28
**Valid until:** 2026-07-28
</metadata>

---

*Phase: 01-okf-memory-store*
*Research completed: 2026-06-28*
*Ready for planning: yes*

## RESEARCH COMPLETE
