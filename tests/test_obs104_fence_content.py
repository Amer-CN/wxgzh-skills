"""档71B OBS-104:围栏内容非代码 —— 提示型留痕回归测试。"""
from __future__ import annotations

import json
from pathlib import Path

from conftest import SKILL_ROOT

sys_path = SKILL_ROOT
import sys
sys.path.insert(0, str(sys_path))
from validators.validate_fence_content import (
    classify_fence_block,
    scan_fences,
    write_allowance,
)

# ① 16 行护栏文案(与 RUN 同形态)
GUARD_16 = "\n".join(
    [f"⛔ vibe-coding-guide 拦截：这是第 {i} 条护栏文案，确需执行请手动运行。"
     for i in range(1, 17)])

# ② 真 bash 脚本
REAL_BASH = """#!/bin/bash
for f in /tmp/*.log; do
  if [ -f "$f" ]; then
    echo "process $f"
    rm "$f"
  fi
done
"""

# ③ /plugin 两行
PLUGIN_2 = """/plugin marketplace add Amer-CN/vibe-coding-guide
/plugin install vibe-coding-guide@vibe-coding-guide
"""


def _article(lang: str, body: str) -> str:
    return f"# 标题\n\n## 章节\n\n```{lang}\n{body}\n```\n"


def test_obs104_guard_lines_hit_2_and_3(tmp_path):
    """① 16 行护栏文案 -> 命中 ②③,1 条 WARN + 1 条留痕,退出码不变。"""
    hits = classify_fence_block("bash", GUARD_16)
    assert 2 in hits and 3 in hits, hits
    md = _article("bash", GUARD_16)
    records = scan_fences(md)
    assert len(records) == 1
    assert records[0]["rule"] == "fence_content_not_code"
    audit = tmp_path / "audit"
    audit.mkdir(exist_ok=True)
    out = write_allowance(records, audit)
    assert out is not None and out.is_file()
    data = json.loads(out.read_text(encoding="utf-8"))
    assert any(e["rule"] == "fence_content_not_code" for e in data["entries"])


def test_obs104_real_bash_zero_hit():
    """② 真 bash 脚本 -> 零命中。"""
    hits = classify_fence_block("bash", REAL_BASH)
    assert hits == []


def test_obs104_plugin_lines_zero_hit():
    """③ /plugin 两行 -> 零命中。"""
    hits = classify_fence_block("text", PLUGIN_2)
    assert hits == []
    records = scan_fences(_article("text", PLUGIN_2))
    assert records == []


def test_obs104_no_records_no_allowance(tmp_path):
    """无 suspect -> 不写留痕文件。"""
    records = scan_fences(_article("text", PLUGIN_2))
    audit = tmp_path / "audit"
    audit.mkdir(exist_ok=True)
    out = write_allowance(records, audit)
    assert out is None
