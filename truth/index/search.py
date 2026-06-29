import re

import sqlite_vec

from .db import get_db
from .embeddings import embed_texts

_RRF_K = 60
_CHANNEL_LIMIT = 50


def _sanitize_fts_query(query: str) -> str:
    tokens = re.findall(r"\w+", query)
    if not tokens:
        return '""'
    return " OR ".join(tokens)


def _fts_search(conn, query: str, limit: int = _CHANNEL_LIMIT) -> dict[int, int]:
    fts_query = _sanitize_fts_query(query)
    rows = conn.execute(
        """
        SELECT rowid, rank
        FROM chunks_fts
        WHERE text MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        (fts_query, limit),
    ).fetchall()
    return {int(r["rowid"]): i + 1 for i, r in enumerate(rows)}


def _vec_search(conn, query_vec: list[float], limit: int = _CHANNEL_LIMIT) -> dict[int, int]:
    packed = sqlite_vec.serialize_float32(query_vec)
    rows = conn.execute(
        """
        SELECT rowid, distance
        FROM chunks_vec
        WHERE embedding MATCH ?
          AND k = ?
        ORDER BY distance
        """,
        (packed, limit),
    ).fetchall()
    return {int(r["rowid"]): i + 1 for i, r in enumerate(rows)}


def rrf_merge(
    fts_ranks: dict[int, int],
    vec_ranks: dict[int, int],
    k: int = _RRF_K,
) -> list[tuple[int, float]]:
    scores: dict[int, float] = {}
    for ranks in (fts_ranks, vec_ranks):
        for rowid, rank in ranks.items():
            scores[rowid] = scores.get(rowid, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda item: -item[1])


def memory_search(query: str, k: int = 5) -> list[dict]:
    conn = get_db()
    query_vec = embed_texts([query], query=True)[0]
    fts_ranks = _fts_search(conn, query)
    vec_ranks = _vec_search(conn, query_vec)
    merged = rrf_merge(fts_ranks, vec_ranks)[:k]

    results: list[dict] = []
    for rowid, score in merged:
        row = conn.execute(
            """
            SELECT path, text, chunk_index, note_type
            FROM chunks
            WHERE rowid = ?
            """,
            (rowid,),
        ).fetchone()
        if row is None:
            continue
        results.append(
            {
                "path": row["path"],
                "text": row["text"],
                "score": score,
                "chunk_index": row["chunk_index"],
                "note_type": row["note_type"],
            }
        )
    return results


if __name__ == "__main__":
    hits = memory_search("hybrid BM25 vector", k=3)
    for hit in hits:
        print(hit["path"], f"score={hit['score']:.4f}")
