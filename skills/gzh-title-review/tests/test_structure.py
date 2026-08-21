"""gzh-title-review 结构自检（77D 任务 2）。

校验:frontmatter 合法 / 目录名与 name 一致 / 必需文件在场。
本 Skill 不入锁、不接编排器,自检为独立单元测试。
"""
from __future__ import annotations

import re
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "SKILL.md",
    "references/title-review-playbook.md",
    "tests/test_structure.py",
}


def _frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            out[k.strip()] = v.strip()
    return out


def test_directory_name_matches_name():
    fm = _frontmatter((SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8"))
    assert fm.get("name") == "gzh-title-review"
    assert SKILL_ROOT.name == fm.get("name") or SKILL_ROOT.name == "gzh-title-review"


def test_required_files_present():
    missing = [r for r in REQUIRED if not (SKILL_ROOT / r).is_file()]
    assert missing == [], f"缺必需文件: {missing}"


def test_frontmatter_has_description_and_boundary_marker():
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    fm = _frontmatter(text)
    assert fm.get("description"), "缺 frontmatter description"
    assert "流水线外" in text or "不接编排器" in text
    assert "不入锁" in text
