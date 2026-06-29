---
type: Decision
title: MCP integration (v1.1)
tags:
- mcp
- agent
- v1.1
---

Locked choices for v1.1 MCP integration:

- **Transport:** stdio via official `mcp` SDK (`FastMCP`); stdout is protocol-only, logs to stderr
- **CLI entry:** `truth mcp` spawns the MCP server as a subprocess
- **Startup lifecycle:** `index_all` + background file watcher on MCP server startup (mirrors `truth serve` bootstrap)
- **Project skill:** agent workflow documented at `skills/truth-memory/SKILL.md`
- **Tool parity:** MCP tool names match `tool_schemas()` (`memory_search`, `memory_write`, `memory_delete`)

Deferred to v2: streamable HTTP transport, MCP resources/prompts beyond the three memory tools.
