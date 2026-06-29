import threading

from sentence_transformers import SentenceTransformer

_MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"
_DOC_PREFIX = "search_document: "
_QUERY_PREFIX = "search_query: "

_MODEL: SentenceTransformer | None = None
_LOCK = threading.Lock()


def get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        with _LOCK:
            if _MODEL is None:
                # ponytail: global singleton; upgrade path = swap model name in one place
                _MODEL = SentenceTransformer(_MODEL_NAME)
    return _MODEL


def embed_texts(texts: list[str], *, query: bool = False) -> list[list[float]]:
    if not texts:
        return []
    prefix = _QUERY_PREFIX if query else _DOC_PREFIX
    prefixed = [f"{prefix}{t}" for t in texts]
    vectors = get_model().encode(prefixed, normalize_embeddings=True)
    return vectors.tolist()


if __name__ == "__main__":
    doc_vec = embed_texts(["hello world"])[0]
    query_vec = embed_texts(["hello"], query=True)[0]
    assert len(doc_vec) == 768, len(doc_vec)
    assert len(query_vec) == 768, len(query_vec)
    print("ok")
