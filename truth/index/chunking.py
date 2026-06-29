def chunk_text(body: str, target: int = 512, overlap: int = 64) -> list[str]:
    """Paragraph-first chunker with character overlap between consecutive chunks."""
    body = body.strip()
    if not body:
        return []

    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    def flush() -> None:
        nonlocal current
        if current.strip():
            chunks.append(current.strip())
        current = ""

    for para in paragraphs:
        if not current:
            current = para
            continue
        if len(current) + 2 + len(para) <= target:
            current = f"{current}\n\n{para}"
            continue
        flush()
        current = para

    flush()

    if len(chunks) <= 1:
        return _split_long(chunks[0] if chunks else body, target, overlap)

    overlapped: list[str] = []
    for i, chunk in enumerate(chunks):
        if len(chunk) > target:
            overlapped.extend(_split_long(chunk, target, overlap))
            continue
        if i > 0 and overlap:
            prev = overlapped[-1]
            tail = prev[-overlap:] if len(prev) > overlap else prev
            chunk = f"{tail}\n\n{chunk}" if tail else chunk
        overlapped.append(chunk)
    return overlapped


def _split_long(text: str, target: int, overlap: int) -> list[str]:
    if len(text) <= target:
        return [text] if text else []
    out: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + target, len(text))
        out.append(text[start:end])
        if end >= len(text):
            break
        start = max(end - overlap, start + 1)
    return out


if __name__ == "__main__":
    p1 = "A" * 40
    p2 = "B" * 40
    body = f"{p1}\n\n{p2}"
    chunks = chunk_text(body, target=50, overlap=20)
    assert len(chunks) >= 2, chunks
    assert any("\n\n" in c and "A" in c and "B" in c for c in chunks[1:]), chunks
    print("ok")
