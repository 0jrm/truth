# Truth v1.1 — Goals Queue

Consumed by `working_unsupervised_gsd`. Pending goals run top-to-bottom.
Each goal drives `/gsd/plan-phase` + `/gsd/execute-plan` for its phase (earlier completed phases skip automatically).

## Pending
<!-- v1.1 shipped 2026-06-29 — queue empty until next milestone -->

## In Progress
<!-- orchestrator moves goals here while running -->

## Done
- [x] Complete Phase 6: Search Quality Fixes — nomic embedding, chunker separator, porter FTS, DB singleton
- [x] Complete Phase 7: Indexer and Watcher Correctness — log.md skip, writer queue, thread-safe indexing
- [x] Complete Phase 8: Agent API Completion — memory_delete, search filters, overwrite conflict signal
- [x] Complete Phase 9: Docs and Test Suite — VISION.MD rewrite, search quality regression tests
- [x] Complete Phase 10: Inspector Upgrades — note viewer, search, lightweight live refresh
- [x] Complete Phase 11: MCP Server and Agent Self-Integration — stdio MCP, project skill, dogfooding
