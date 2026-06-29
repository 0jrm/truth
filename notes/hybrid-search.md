---
type: Concept
title: "Hybrid Search"
tags: [search, bm25, rrf]
---

Pure vector search misses exact keyword matches; pure keyword search misses semantic similarity. Hybrid search runs vector and BM25 retrieval in parallel, then fuses rankings with Reciprocal Rank Fusion (RRF).

Truth's indexer will combine both signals over OKF notes, building on [SQLite vectors](sqlite-vectors.md) for the embedding side.
