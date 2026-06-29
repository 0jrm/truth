---
type: Concept
title: "SQLite Vector Search"
tags: [sqlite, vector, embeddings]
---

Local-first memory needs fast similarity search without shipping data to the cloud. SQLite with the sqlite-vec extension stores embedding vectors alongside text chunks in a single `memory.db` file.

This pairs naturally with [Open Knowledge Format](okf-format.md): markdown remains human-readable truth while vectors accelerate recall.
