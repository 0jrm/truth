"""Tests for truth skill install command."""

from __future__ import annotations

from pathlib import Path

from truth.skill_install import bundled_assets_present, install_skill


def test_bundled_assets_present():
    assert bundled_assets_present()


def test_install_skill_writes_cursor_files(tmp_path):
    written = install_skill(tmp_path, force=True)
    paths = {Path(p) for p in written}
    assert tmp_path / ".cursor" / "skills" / "truth-memory" / "SKILL.md" in paths
    assert tmp_path / ".cursor" / "rules" / "truth-memory.mdc" in paths
    assert tmp_path / "prompts" / "system.md" in paths
    assert tmp_path / ".cursor" / "mcp.json" in paths


def test_install_skill_skips_existing_without_force(tmp_path):
    install_skill(tmp_path)
    again = install_skill(tmp_path)
    assert again == []
