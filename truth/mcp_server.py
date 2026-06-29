"""Stdio MCP server exposing Truth agent memory tools."""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from truth.index.indexer import index_all
from truth.index.watcher import start_watcher
from truth.store.paths import notes_root
from truth.tools import memory_delete as _memory_delete
from truth.tools import memory_search as _memory_search
from truth.tools import memory_write as _memory_write


@asynccontextmanager
async def lifespan(_mcp: FastMCP) -> AsyncIterator[None]:
    root = notes_root()
    indexed = index_all(root)
    print(f"Indexed {indexed} file(s) on startup", file=sys.stderr, flush=True)
    observer = start_watcher(block=False, notes=root)
    print(f"Watching notes at {root}", file=sys.stderr, flush=True)
    try:
        yield
    finally:
        observer.stop()
        observer.join()


mcp = FastMCP("Truth", json_response=True, lifespan=lifespan)


@mcp.tool(name="memory_search")
def mcp_memory_search(
    query: str,
    k: int = 5,
    type: str | None = None,
    tags: list[str] | None = None,
) -> list[dict]:
    return _memory_search(query, k=k, type=type, tags=tags)


@mcp.tool(name="memory_write")
def mcp_memory_write(
    path: str,
    content: str,
    type: str = "Note",
    title: str | None = None,
    summary: str | None = None,
) -> dict:
    return _memory_write(path, content, type=type, title=title, summary=summary)


@mcp.tool(name="memory_delete")
def mcp_memory_delete(path: str) -> dict:
    return _memory_delete(path)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
