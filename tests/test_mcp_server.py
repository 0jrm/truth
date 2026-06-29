"""MCP server tool registration and wrapper smoke tests."""

from __future__ import annotations

from truth.index.indexer import index_all
from truth.mcp_server import mcp, mcp_memory_delete, mcp_memory_search, mcp_memory_write


def test_mcp_tools_callable(isolated_truth):
    created = mcp_memory_write("mcp/smoke.md", "MCP smoke test note body for search.")
    assert created["path"] == "mcp/smoke.md"

    index_all(isolated_truth)

    hits = mcp_memory_search("MCP smoke test", k=5)
    paths = {h["path"] for h in hits}
    assert "mcp/smoke.md" in paths, hits

    deleted = mcp_memory_delete("mcp/smoke.md")
    assert deleted["path"] == "mcp/smoke.md"


def test_mcp_tool_names_registered():
    names = {tool.name for tool in mcp._tool_manager.list_tools()}
    assert names == {"memory_search", "memory_write", "memory_delete"}
