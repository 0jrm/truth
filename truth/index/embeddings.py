import threading

from sentence_transformers import SentenceTransformer

_MODEL: SentenceTransformer | None = None
_LOCK = threading.Lock()


def get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        with _LOCK:
            if _MODEL is None:
                # ponytail: global singleton; upgrade path = swap model name in one place
                _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    return _MODEL


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    vectors = get_model().encode(texts, normalize_embeddings=True)
    return vectors.tolist()
