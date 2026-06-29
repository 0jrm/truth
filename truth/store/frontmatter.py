import yaml
from dataclasses import dataclass
from pathlib import Path

_FRONTMATTER_DELIM = "---"


@dataclass(frozen=True)
class ParsedNote:
    path: Path | None
    meta: dict
    body: str


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Split OKF --- YAML --- body. No frontmatter → ({}, full text)."""
    if not text.startswith(f"{_FRONTMATTER_DELIM}\n"):
        return {}, text

    end = text.find(f"\n{_FRONTMATTER_DELIM}\n", len(_FRONTMATTER_DELIM) + 1)
    if end == -1:
        return {}, text

    yaml_block = text[len(_FRONTMATTER_DELIM) + 1 : end]
    body = text[end + len(f"\n{_FRONTMATTER_DELIM}\n") :]
    meta = yaml.safe_load(yaml_block)
    if meta is None:
        meta = {}
    if not isinstance(meta, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return meta, body


def validate_frontmatter(meta: dict, *, auto_type: str | None = None) -> dict:
    """MEM-02/MEM-03: require type unless auto_type set (then default to auto_type, e.g. 'Note')."""
    result = dict(meta)
    type_val = result.get("type")
    if not type_val:
        if auto_type is None:
            raise ValueError("missing required frontmatter field: type")
        result["type"] = auto_type
    return result


def format_note(meta: dict, body: str) -> str:
    """Serialize with --- wrapper. Use yaml.safe_dump(sort_keys=False)."""
    validated = validate_frontmatter(meta)
    yaml_block = yaml.safe_dump(validated, sort_keys=False, allow_unicode=True).strip()
    return f"{_FRONTMATTER_DELIM}\n{yaml_block}\n{_FRONTMATTER_DELIM}\n{body}"


def parse_note(text: str, path: Path | None = None) -> ParsedNote:
    """split + validate (no auto_type — missing type raises ValueError)."""
    meta, body = split_frontmatter(text)
    validated = validate_frontmatter(meta)
    return ParsedNote(path=path, meta=validated, body=body)


def parse_note_file(path: Path) -> ParsedNote:
    """Read UTF-8 file, parse_note with path set."""
    text = path.read_text(encoding="utf-8")
    return parse_note(text, path=path)


if __name__ == "__main__":
    sample = "---\ntype: Note\ntitle: test\n---\nBody.\n"
    n = parse_note(sample)
    assert n.meta["type"] == "Note" and n.body == "Body.\n"
    assert validate_frontmatter({}, auto_type="Note")["type"] == "Note"
    try:
        validate_frontmatter({})
        raise SystemExit("expected ValueError")
    except ValueError:
        pass
    print("frontmatter ok")
