# Phase 2: Hybrid Index - Research

**Researched:** 2026-06-28
**Domain:** SQLite hybrid search, local embeddings, incremental indexing, file watching
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- `all-MiniLM-L6-v2` via sentence-transformers (384-dim, CPU)
- Paragraph chunking ~512 chars, ~64 overlap
- `memory.db` default at project root; `TRUTH_DB_PATH` override
- FTS5 trigram + sqlite-vec vec0; RRF k=60
- Skip invalid notes with warning
- Watchdog 500ms debounce
- `memory_search()` in `truth.index.search` for Phase 2
- Transactional per-file re-index (IDX-05)
- Import `truth.store` for parse — no duplicate frontmatter logic

### the agent's Discretion
- SQL vs Python RRF implementation
- `python -m truth.index` self-check shape

### Deferred
- nomic-embed upgrade, wiki links, link graph table, memory_write (Phase 3), CLI serve (Phase 5)

</user_constraints>

<architectural_responsibility_map>
## Architectural Responsibility Map

| Capability | Module | Rationale |
|------------|--------|-----------|
| Schema + DB open | `truth/index/db.py` | Single connection helper, load sqlite-vec |
| Chunk + embed + upsert | `truth/index/indexer.py` | Core index loop |
| Hybrid search + RRF | `truth/index/search.py` | `memory_search` public API |
| Content hash | `truth/index/hashutil.py` | SHA-256 of file bytes |
| Watcher | `truth/index/watcher.py` | watchdog observer + debounce |
| Events | `truth/index/events.py` | append-only events table writes |

</architectural_responsibility_map>

<research_summary>
## Summary

Phase 2 adds a derived SQLite index over OKF markdown notes. The standard pattern (validated by sqlite-vec author and multiple hybrid-RAG writeups): base `chunks` table + FTS5 virtual table + `vec0` virtual table sharing `rowid`, embeddings from sentence-transformers in Python, hybrid retrieval via parallel FTS5 BM25 and vector KNN, merged with Reciprocal Rank Fusion.

Incremental indexing uses SHA-256 content hashes stored per file path — unchanged hash skips re-embedding. Watchdog triggers debounced per-file re-index on create/modify/delete. Events table records ops for Phase 4 `truth changes`.

Phase 1's `parse_note_file` supplies body text and metadata; indexer never writes markdown.

**Primary recommendation:** `truth/index/` package with ~4 focused modules; keep indexer orchestration under 200 lines; ponytail global embed lock acceptable for v1 single-user.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| sqlite3 | stdlib | Database | Project constraint |
| sqlite-vec | latest pip | vec0 vector search | Official extension, pip-installable |
| sentence-transformers | 3.x | Local embeddings | ONNX/CPU, no API keys |
| watchdog | 4.x | Filesystem events | Vision doc stack |
| all-MiniLM-L6-v2 | HF model | 384-dim embeddings | Fast, small, documented in VISION |

### Schema pattern
```sql
-- files: track content hash per note path
CREATE TABLE files (
  path TEXT PRIMARY KEY,
  content_hash TEXT NOT NULL,
  indexed_at TEXT NOT NULL
);

-- chunks: canonical row store
CREATE TABLE chunks (
  rowid INTEGER PRIMARY KEY,
  path TEXT NOT NULL,
  chunk_index INTEGER NOT NULL,
  text TEXT NOT NULL,
  note_type TEXT,
  note_title TEXT
);

-- FTS5 + vec0 share chunks.rowid
CREATE VIRTUAL TABLE chunks_fts USING fts5(text, tokenize='trigram');
CREATE VIRTUAL TABLE chunks_vec USING vec0(embedding float[384]);

CREATE TABLE events (
  id INTEGER PRIMARY KEY,
  path TEXT NOT NULL,
  op TEXT NOT NULL CHECK(op IN ('create','update','delete')),
  ts TEXT NOT NULL
);
```

### RRF (Python-side, ponytail-simple)
```python
def rrf_merge(fts_ranks: dict[int, int], vec_ranks: dict[int, int], k: int = 60) -> list[tuple[int, float]]:
    scores: dict[int, float] = {}
    for ranks in (fts_ranks, vec_ranks):
        for rowid, rank in ranks.items():
            scores[rowid] = scores.get(rowid, 0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: -x[1])
```

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Data Flow
```
notes/*.md ──► parse_note_file() ──► chunk body ──► embed ──► SQLite (chunks + fts + vec)
     ▲                                              │
     └── watchdog (debounced) ──► index_file() ◄────┘
                              └──► events table
query ──► embed query ──► vector KNN + FTS5 MATCH ──► RRF ──► top-k results
```

### Per-file transactional update
1. BEGIN
2. DELETE FROM chunks WHERE path = ? (cascade fts/vec via rowid)
3. INSERT new chunks + fts + vec rows
4. UPSERT files.content_hash
5. INSERT events (create/update)
6. COMMIT

On delete: steps 2-3 skipped; DELETE chunks; DELETE files row; event delete.

### Hash skip
```python
new_hash = sha256_bytes(path.read_bytes())
if files.content_hash == new_hash:
    return  # no re-embed
```

### Anti-Patterns
- Writing SQLite from agent/store code — violates core architecture
- Re-embedding unchanged files — wastes CPU; hash gate required
- Using file mtime alone for changelog — events table is truth for inspector
- Loading embed model per chunk — singleton required

</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Vector storage | NumPy files on disk | sqlite-vec vec0 | Single DB file, JOIN with FTS |
| BM25 scoring | Custom TF-IDF | FTS5 `bm25()` / rank | Battle-tested |
| Embeddings API | Raw ONNX boilerplate | sentence-transformers | Model download + encode API |
| File events | Polling mtime | watchdog Observer | Reliable create/delete |

</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: sqlite-vec not loaded
**Fix:** `import sqlite_vec; sqlite_vec.load(conn)` on every connection open.

### Pitfall 2: FTS5 rowid sync
**Fix:** Insert chunks first, use `last_insert_rowid()` for fts/vec inserts with same rowid.

### Pitfall 3: Dimension mismatch
**Fix:** vec0 schema `float[384]` must match all-MiniLM-L6-v2 output; assert on first embed.

### Pitfall 4: Watcher fires on indexer write
**Fix:** Only watch `notes/`; never write markdown from indexer. DB writes don't trigger watchdog.

### Pitfall 5: Partial index on error
**Fix:** Per-file transaction; exception → ROLLBACK, log error, continue next file.

</common_pitfalls>

<code_examples>
## Code Examples

### Load sqlite-vec
```python
import sqlite3
import sqlite_vec

conn = sqlite3.connect(db_path)
conn.enable_load_extension(True)
sqlite_vec.load(conn)
conn.enable_load_extension(False)
```

### Embed with sentence-transformers
```python
from sentence_transformers import SentenceTransformer

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def embed_texts(texts: list[str]) -> list[list[float]]:
    return get_model().encode(texts, normalize_embeddings=True).tolist()
```

### Vector search query (sqlite-vec)
```sql
SELECT rowid, distance
FROM chunks_vec
WHERE embedding MATCH ?
  AND k = ?
ORDER BY distance
```

</code_examples>

<open_questions>
## Open Questions

1. **Trigram vs porter FTS tokenizer** — trigram is language-agnostic; good for mixed technical notes. Locked unless user complains.
2. **Chunk store link metadata** — defer; search uses text only in v1.

</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `.planning/phases/02-hybrid-index/02-CONTEXT.md` — locked decisions
- `VISION.MD` — architecture and stack
- Alex Garcia sqlite-vec hybrid search blog + GitHub issue #48 (FTS5 + vec0 + RRF)
- Phase 1 `truth/store/` implementation

### Secondary (MEDIUM confidence)
- DEV Community "Hybrid RAG in 200 Lines" — trigram FTS5 + RRF pattern
- `.planning/research/SUMMARY.md` — stack validation

</sources>

<metadata>
**Research scope:** SQLite schema, embeddings, chunking, hybrid search, watcher, events
**Confidence:** HIGH for stack; MEDIUM for exact SQL RRF (Python fallback acceptable)
**Research date:** 2026-06-28
**Valid until:** 2026-07-28
</metadata>

---

*Phase: 02-hybrid-index*
*Research completed: 2026-06-28*
*Ready for planning: yes*

## RESEARCH COMPLETE
