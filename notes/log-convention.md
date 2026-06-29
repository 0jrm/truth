---
type: Concept
title: "Log Convention"
tags: [okf, log]
timestamp: 2026-06-28T12:00:00Z
---

OKF optionally includes a `log.md` file — a chronological, human-readable changelog of knowledge updates.

When an agent calls `memory_write()`, Truth appends a timestamped line to `log.md` under the notes root. This complements the machine-readable `events` table used by `truth changes`.

See [agent workflow](agent-workflow.md) for when to write, and [OKF format](okf-format.md) for frontmatter rules.
