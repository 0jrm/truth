from datetime import datetime, timezone

def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def record_event(conn, path: str, op: str) -> None:
    if op not in {"create", "update", "delete"}:
        raise ValueError(f"invalid event op: {op}")
    conn.execute(
        "INSERT INTO events (path, op, ts) VALUES (?, ?, ?)",
        (path, op, _utc_now()),
    )


def list_events(conn, n: int = 20) -> list[dict]:
    rows = conn.execute(
        """
        SELECT path, op, ts
        FROM events
        ORDER BY id DESC
        LIMIT ?
        """,
        (n,),
    ).fetchall()
    return [{"path": r["path"], "op": r["op"], "ts": r["ts"]} for r in rows]
