# Phase 2: Hybrid Index - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-28
**Phase:** 2-Hybrid Index
**Areas discussed:** Embedding model, Chunking strategy, DB placement, Invalid note handling, Watcher debounce, Search API surface
**Mode:** Auto-selected (pipeline advance — user requested proceed on GSD pipeline)

---

## Embedding model

| Option | Description | Selected |
|--------|-------------|----------|
| all-MiniLM-L6-v2 | 384-dim, fast CPU, ~80MB download, matches vision doc | ✓ |
| nomic-embed-text-v1.5 | 768-dim, better recall, heavier | |

**Auto choice:** all-MiniLM-L6-v2 (recommended default for v1 personal KB)
**Notes:** Locked in PROJECT.md Key Decisions as "Local ONNX embeddings"

---

## Chunking strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Paragraph-based ~512 chars + overlap | Simple, OK for short OKF concept notes | ✓ |
| Fixed token windows | Better for long docs, needs tokenizer | |
| One chunk per file | Too coarse for search quality | |

**Auto choice:** Paragraph-based with ~64-char overlap

---

## DB placement

| Option | Description | Selected |
|--------|-------------|----------|
| `memory.db` at project root + `TRUTH_DB_PATH` env | Matches vision; prep for Phase 5 config | ✓ |
| DB alongside notes/ | Couples index to knowledge root moves | |

**Auto choice:** Project root default with env override

---

## Invalid note handling

| Option | Description | Selected |
|--------|-------------|----------|
| Skip with warning, continue index | Ponytail-friendly; one bad file doesn't block | ✓ |
| Quarantine folder | Extra moving parts | |
| Fail entire index run | Too brittle for agent-written notes | |

**Auto choice:** Skip with warning (Phase 1 RESEARCH recommendation)

---

## Watcher debounce

| Option | Description | Selected |
|--------|-------------|----------|
| 500ms debounce | Avoids re-index storms on rapid saves | ✓ |
| Immediate re-index | Simpler but noisy on multi-write editors | |

**Auto choice:** 500ms debounce

---

## Search API surface

| Option | Description | Selected |
|--------|-------------|----------|
| `truth.index.search.memory_search()` in Phase 2; Phase 3 re-exports | Satisfies SRCH reqs + ROADMAP success criteria | ✓ |
| Search internal only until Phase 3 | Delays verification of hybrid search | |

**Auto choice:** Expose `memory_search` from `truth.index.search` in Phase 2

---

## the agent's Discretion

- RRF in SQL vs Python
- Minimal `python -m truth.index` self-check vs `truth index` CLI subcommand

## Deferred Ideas

- nomic-embed upgrade, wiki-links, link graph table, memory_write (Phase 3), full CLI (Phase 5)
