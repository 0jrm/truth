---
status: complete
phase: 02-hybrid-index
source: 02-01-SUMMARY.md, 02-02-SUMMARY.md, 02-03-SUMMARY.md, 02-04-SUMMARY.md
started: 2026-06-28T12:00:00Z
updated: 2026-06-28T12:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Index
expected: index_all() on fresh DB populates chunks, FTS, and vec tables from notes/
result: pass

### 2. Hash Skip
expected: Re-running index_all on unchanged files returns 0 re-indexed files (no re-embed)
result: pass

### 3. Hybrid Search
expected: memory_search(query, k) returns path, text, and score for relevant chunks
result: pass

### 4. RRF Merge
expected: Vector and BM25 channels contribute via reciprocal rank fusion
result: pass

### 5. Watcher Create
expected: New .md file after watcher start is indexed within debounce window
result: pass

### 6. Watcher Delete
expected: Deleting a note removes its chunks and records a delete event
result: pass

### 7. Events Table
expected: create/update/delete operations write rows queryable via list_events
result: pass

### 8. Invalid Note Skip
expected: Files missing frontmatter type are skipped with warning, index continues
result: pass

### 9. Transactional Safety
expected: Per-file index uses BEGIN/COMMIT; failed parse does not corrupt prior index
result: pass

## Summary

total: 9
passed: 9
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
