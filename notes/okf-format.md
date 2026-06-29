---
type: Concept
title: "Open Knowledge Format"
tags: [okf, markdown]
---

Open Knowledge Format (OKF) is a minimal convention for agent-readable knowledge: markdown files with YAML frontmatter where `type` is the only required field. Everything else—title, tags, timestamps—is optional metadata for humans and tools.

Truth treats OKF markdown as the source of truth; SQLite and search indexes are derived views rebuilt from these files.

Agents using Truth follow the [agent workflow](agent-workflow.md) and append to [log.md](log-convention.md) on writes.
