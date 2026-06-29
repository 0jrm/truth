---
type: Concept
title: "Agent Workflow"
tags: [agent, workflow]
timestamp: 2026-06-28T12:00:00Z
---

Truth agents follow a simple loop: **search before answer, write after learn**.

1. Before responding, call `memory_search()` to retrieve relevant notes.
2. After learning something durable, call `memory_write()` to persist it as OKF markdown.
3. The watcher (via `truth serve`) re-indexes writes within ~500ms.

Human-readable history accumulates in [log.md](log-convention.md). Search quality depends on [hybrid search](hybrid-search.md) over the SQLite index.
