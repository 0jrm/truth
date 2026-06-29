from truth.index.db import init_schema, open_db
from truth.index.events import list_events


def recent_changes(n: int = 20) -> list[dict]:
    conn = open_db()
    try:
        init_schema(conn)
        return list_events(conn, n)
    finally:
        conn.close()


if __name__ == "__main__":
    events = recent_changes(5)
    assert isinstance(events, list)
    print("changes ok")
