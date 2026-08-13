"""档71B OBS-104:围栏内容非代码 —— 提示型留痕回归测试(档71B'-C 换真实样本)。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from conftest import SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT))
from validators.validate_fence_content import (
    classify_fence_block,
    scan_fences,
    write_allowance,
)

FIX104 = SKILL_ROOT / "tests" / "fixtures" / "obs104"
GUARD16_REAL = FIX104 / "guard16_real.txt"

# ② 合成样本(非 RUN 真实数据;仅用于回归合成形态)
GUARD16_SYNTHETIC = "\n".join(
    [f"⛔ vibe-coding-guide 拦截：这是第 {i} 条护栏文案，确需执行请手动运行。"
     for i in range(1, 17)])

# 真 bash 脚本
REAL_BASH = """#!/bin/bash
for f in /tmp/*.log; do
  if [ -f "$f" ]; then
    echo "process $f"
    rm "$f"
  fi
done
"""

# /plugin 两行
PLUGIN_2 = """/plugin marketplace add Amer-CN/vibe-coding-guide
/plugin install vibe-coding-guide@vibe-coding-guide
"""


def _article(lang: str, body: str) -> str:
    return f"# 标题\n\n## 章节\n\n```{lang}\n{body}\n```\n"


def test_obs104_guard16_real_sample_hits_123():
    """★真实样本(现 RUN bash 围栏 16 行,冻结 fixture):criteria_hit 至少含 {1,2,3}。"""
    assert GUARD16_REAL.is_file(), f"fixture missing: {GUARD16_REAL}"
    real = GUARD16_REAL.read_text(encoding="utf-8")
    hits = classify_fence_block("bash", real)
    assert {1, 2, 3}.issubset(hits), f"criteria_hit={hits}, expected to contain 1,2,3"


def test_obs104_synthetic_guard_lines_hit_2_and_3(tmp_path):
    """合成样本(非 RUN 真实数据):16 行护栏文案 -> 命中 ②③,1 条 WARN + 1 条留痕。"""
    hits = classify_fence_block("bash", GUARD16_SYNTHETIC)
    assert 2 in hits and 3 in hits, hits
    md = _article("bash", GUARD16_SYNTHETIC)
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
    """真 bash 脚本 -> 零命中。"""
    hits = classify_fence_block("bash", REAL_BASH)
    assert hits == []


def test_obs104_plugin_lines_zero_hit():
    """/plugin 两行 -> 零命中。"""
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
