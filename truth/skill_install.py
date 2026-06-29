"""Install truth-memory agent skill files into a project or user Cursor config."""

from __future__ import annotations

import shutil
from pathlib import Path


def _bundled_root() -> Path:
    return Path(__file__).resolve().parent / "bundled"


def _copy(src: Path, dest: Path, *, force: bool) -> bool:
    if dest.exists() and not force:
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return True


def install_skill(
    target: Path | None = None,
    *,
    personal: bool = False,
    force: bool = False,
    mcp: bool = True,
) -> list[str]:
    """Copy bundled skill, rule, prompt, and optional MCP config. Returns paths written."""
    bundled = _bundled_root()
    if personal:
        root = Path.home() / ".cursor"
    else:
        root = (target or Path.cwd()).resolve()

    written: list[str] = []

    skill_src = bundled / "truth-memory" / "SKILL.md"
    if personal:
        skill_dest = root / "skills" / "truth-memory" / "SKILL.md"
    else:
        skill_dest = root / ".cursor" / "skills" / "truth-memory" / "SKILL.md"
    if _copy(skill_src, skill_dest, force=force):
        written.append(str(skill_dest))

    if not personal:
        rule_src = bundled / "cursor" / "rules" / "truth-memory.mdc"
        rule_dest = root / ".cursor" / "rules" / "truth-memory.mdc"
        if _copy(rule_src, rule_dest, force=force):
            written.append(str(rule_dest))

        prompt_src = bundled / "prompts" / "system.md"
        prompt_dest = root / "prompts" / "system.md"
        if _copy(prompt_src, prompt_dest, force=force):
            written.append(str(prompt_dest))

    if mcp and not personal:
        mcp_dest = root / ".cursor" / "mcp.json"
        example = bundled / "cursor" / "mcp.json.example"
        if not mcp_dest.exists():
            if _copy(example, mcp_dest, force=True):
                written.append(str(mcp_dest))
        elif force:
            if _copy(example, mcp_dest, force=True):
                written.append(str(mcp_dest))

    return written


def bundled_assets_present() -> bool:
    """Quick check that wheel/sdist includes agent bundle files."""
    root = _bundled_root()
    static = Path(__file__).resolve().parent / "static" / "inspector.html"
    return all(
        p.is_file()
        for p in (
            root / "truth-memory" / "SKILL.md",
            root / "prompts" / "system.md",
            root / "cursor" / "mcp.json.example",
            static,
        )
    )
