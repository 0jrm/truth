#!/usr/bin/env python3
"""MCP stress test: N `truth mcp` subprocesses, one shared notes/ + memory.db.

Run: python tests/stress_mcp_shared_notes.py
"""

from __future__ import annotations

import asyncio
import json
import multiprocessing as mp
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

REPO = Path(__file__).resolve().parents[1]
SOURCE_NOTES = REPO / "notes"
GOLDEN = Path("/tmp/truth-mcp-golden")
WORK = Path("/tmp/truth-mcp-stress-work")
STRESS_PREFIX = "stress"
LEVELS = [1, 2, 4, 8, 16]
# ponytail: cold MCP boot ~7–12s; 20s covers debounce + first search
SEARCH_TIMEOUT_SEC = 20
JOIN_EXTRA_SEC = 25
BASELINE = {
    "agent-workflow.md",
    "decisions/mcp-integration.md",
    "hybrid-search.md",
    "log-convention.md",
    "log.md",
    "okf-format.md",
    "sqlite-vectors.md",
}


def _snapshot_db(db_path: Path) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    files = {r["path"] for r in conn.execute("SELECT path FROM files")}
    stress = sorted(p for p in files if p.startswith(f"{STRESS_PREFIX}/"))
    return {
        "integrity": conn.execute("PRAGMA integrity_check").fetchone()[0],
        "files_total": len(files),
        "chunks_total": conn.execute("SELECT COUNT(*) n FROM chunks").fetchone()["n"],
        "stress_files_indexed": len(stress),
        "missing_baseline": sorted(BASELINE - files),
    }


def _ensure_golden() -> None:
    if (GOLDEN / "memory.db").exists():
        snap = _snapshot_db(GOLDEN / "memory.db")
        if snap["stress_files_indexed"] == 0 and not snap["missing_baseline"]:
            return
    if GOLDEN.exists():
        shutil.rmtree(GOLDEN)
    GOLDEN.mkdir(parents=True, exist_ok=True)
    for rel in BASELINE:
        src = SOURCE_NOTES / rel
        dest = GOLDEN / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    os.environ["TRUTH_NOTES_ROOT"] = str(GOLDEN)
    os.environ["TRUTH_DB_PATH"] = str(GOLDEN / "memory.db")
    from truth.index.db import reset_db_singleton
    from truth.index.indexer import index_all

    reset_db_singleton()
    index_all(GOLDEN)


def _reset_work() -> Path:
    if WORK.exists():
        shutil.rmtree(WORK)
    shutil.copytree(GOLDEN, WORK)
    stress = WORK / STRESS_PREFIX
    if stress.exists():
        shutil.rmtree(stress)
    return WORK / "memory.db"


def _mcp_env(notes: Path) -> dict[str, str]:
    return {
        **os.environ,
        "TRUTH_NOTES_ROOT": str(notes),
        "TRUTH_DB_PATH": str(notes / "memory.db"),
        "PYTHONUNBUFFERED": "1",
    }


def _server_params(notes: Path) -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "truth.cli", "mcp"],
        env=_mcp_env(notes),
    )


def _tool_json(result) -> object:
    if not result.content:
        return None
    return json.loads(result.content[0].text)


def _search_paths(result) -> list[str]:
    data = _tool_json(result)
    if isinstance(data, dict) and "path" in data:
        return [data["path"]]
    if isinstance(data, list):
        return [h["path"] for h in data if isinstance(h, dict) and "path" in h]
    return []


async def _mcp_timings(notes: Path) -> dict:
    params = _server_params(notes)
    token = f"mcp-timing-{int(time.time())}"
    rel = f"{STRESS_PREFIX}/timing.md"
    t0 = time.monotonic()
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            boot = time.monotonic()
            await session.initialize()
            init = time.monotonic()
            await session.call_tool(
                "memory_write",
                {"path": rel, "content": f"{token} " + ("t" * 200), "title": "timing"},
            )
            write_done = time.monotonic()
            deadline = time.monotonic() + SEARCH_TIMEOUT_SEC
            roundtrip = None
            while time.monotonic() < deadline:
                sr = await session.call_tool("memory_search", {"query": token, "k": 5})
                if rel in _search_paths(sr):
                    roundtrip = time.monotonic() - write_done
                    break
                await asyncio.sleep(0.1)
            s1 = time.monotonic()
            await session.call_tool("memory_search", {"query": token, "k": 5})
            warm_search_sec = round(time.monotonic() - s1, 3)
    return {
        "mcp_cold_boot_sec": round(init - boot, 2),
        "mcp_write_sec": round(write_done - init, 3),
        "mcp_write_to_search_sec": round(roundtrip, 2) if roundtrip is not None else None,
        "mcp_search_warm_sec": warm_search_sec,
        "mcp_session_sec": round(time.monotonic() - t0, 1),
    }


async def _mcp_worker(worker_id: int, notes: Path) -> dict:
    params = _server_params(notes)
    rel = f"{STRESS_PREFIX}/mcp-w{worker_id:04d}.md"
    token = f"mcp-stress-{worker_id}"
    errors: list[str] = []
    t0 = time.monotonic()
    boot_sec = None
    write_sec = None
    search_sec = None
    found = False

    try:
        async with stdio_client(params) as (read, write):
            boot_start = time.monotonic()
            async with ClientSession(read, write) as session:
                await session.initialize()
                boot_sec = round(time.monotonic() - boot_start, 1)
                w0 = time.monotonic()
                await session.call_tool(
                    "memory_write",
                    {
                        "path": rel,
                        "content": f"{token} " + ("y" * 200),
                        "title": f"mcp stress {worker_id}",
                    },
                )
                write_sec = round(time.monotonic() - w0, 3)
                deadline = time.monotonic() + SEARCH_TIMEOUT_SEC
                while time.monotonic() < deadline:
                    sr = await session.call_tool("memory_search", {"query": token, "k": 5})
                    if rel in _search_paths(sr):
                        found = True
                        search_sec = round(time.monotonic() - w0, 2)
                        break
                    await asyncio.sleep(0.1)
                if not found:
                    errors.append(f"timeout: not searchable via memory_search: {rel}")
    except Exception as exc:
        errors.append(f"bootstrap: {type(exc).__name__}: {exc}")

    return {
        "worker_id": worker_id,
        "errors": errors,
        "searchable": found,
        "boot_sec": boot_sec,
        "write_sec": write_sec,
        "search_sec": search_sec,
        "elapsed_sec": round(time.monotonic() - t0, 1),
    }


def _worker_entry(worker_id: int, notes: str, out: mp.Queue) -> None:
    sys.path.insert(0, str(REPO))
    out.put(asyncio.run(_mcp_worker(worker_id, Path(notes))))


def run_level(n_clients: int, notes: Path, db_path: Path) -> dict:
    _reset_work()
    expected = n_clients

    ctx = mp.get_context("spawn")
    out: mp.Queue = ctx.Queue()
    t0 = time.monotonic()
    procs = [
        ctx.Process(target=_worker_entry, args=(wid, str(notes), out))
        for wid in range(1, n_clients + 1)
    ]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=SEARCH_TIMEOUT_SEC + JOIN_EXTRA_SEC + 30)
        if p.is_alive():
            p.kill()
            p.join()

    workers = []
    for _ in procs:
        try:
            workers.append(out.get(timeout=3))
        except Exception:
            workers.append({"worker_id": -1, "errors": ["no result"], "searchable": False})

    elapsed = round(time.monotonic() - t0, 1)
    after = _snapshot_db(db_path)
    disk = len(list((notes / STRESS_PREFIX).rglob("*.md"))) if (notes / STRESS_PREFIX).exists() else 0
    all_errors = [e for w in workers for e in w.get("errors", [])]
    searchable = sum(1 for w in workers if w.get("searchable"))

    return {
        "clients": n_clients,
        "elapsed_sec": elapsed,
        "disk_stress_md": disk,
        "indexed_stress_files": after["stress_files_indexed"],
        "searchable_via_mcp": searchable,
        "missing_search": max(0, expected - searchable),
        "worker_errors": len(all_errors),
        "errors_sample": all_errors[:6],
        "integrity": after["integrity"],
        "baseline_intact": not after["missing_baseline"],
        "worker_boot_sec": [w.get("boot_sec") for w in workers],
        "worker_elapsed": [w.get("elapsed_sec") for w in workers],
        "robust": (
            after["integrity"] == "ok"
            and not after["missing_baseline"]
            and len(all_errors) == 0
            and searchable == expected
            and disk == expected
        ),
    }


def _self_check() -> None:
    class _Part:
        def __init__(self, text: str) -> None:
            self.text = text

    class _Result:
        def __init__(self, text: str) -> None:
            self.content = [_Part(text)]

    assert _search_paths(_Result('{"path":"a.md"}')) == ["a.md"]
    assert _search_paths(_Result('[{"path":"b.md"}]')) == ["b.md"]


def main() -> int:
    sys.path.insert(0, str(REPO))
    _ensure_golden()
    db_path = _reset_work()
    notes = WORK

    print("golden:", json.dumps(_snapshot_db(GOLDEN / "memory.db")))
    timings = asyncio.run(_mcp_timings(notes))
    print("timings:", json.dumps(timings))
    _reset_work()

    levels = []
    for n in LEVELS:
        print(f"\n--- {n} mcp clients ---", flush=True)
        r = run_level(n, notes, db_path)
        levels.append(r)
        print(json.dumps(r))

    payload = {"timings": timings, "levels": levels, "via": "truth mcp stdio"}
    out = REPO / "tests" / "stress_mcp_results.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("\n=== summary ===")
    print(json.dumps(timings))
    for r in levels:
        ok = "OK" if r["robust"] else "FAIL"
        print(
            f"{ok}  n={r['clients']:>2}  mcp_search={r['searchable_via_mcp']}/{r['clients']}  "
            f"idx={r['indexed_stress_files']}/{r['disk_stress_md']}  err={r['worker_errors']}  "
            f"{r['elapsed_sec']}s"
        )
    print(f"results -> {out}")
    return 0 if all(r["robust"] for r in levels) else 1


if __name__ == "__main__":
    _self_check()
    raise SystemExit(main())
