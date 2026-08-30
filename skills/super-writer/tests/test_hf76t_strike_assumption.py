"""76T/OBS-293 strike_assumption shape checks; 77P makes overlength FAIL."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import validate_single_product as VSP  # noqa: E402


def _handoff_yaml(strike_assumption=None) -> str:
    import json
    sa = f"      strike_assumption: {json.dumps(strike_assumption, ensure_ascii=False)}\n" if strike_assumption is not None else ""
    return f"""handoff:
  schema_version: "2.2"
  prose_craft_applied: true
  prose_craft_version: "1.0"
  title_candidates: ["A", "B", "C"]
  hook_line: "钩子"
  selected_title: "A"
  title_selection_reason: "稳健准确4/网感点击4/专业权威3/长期价值2；五维评分：点击欲望4/事实匹配4/人群匹配4/差异化4/长期价值4；风险标记：无标题党、无堆砌、无据风险已核对、时效风险低"
  formatter:
    cover:
      kicker: null
{sa}      tags: null
"""


def test_strike_assumption_missing_not_fail(tmp_path):
    p = tmp_path / "handoff.yaml"
    p.write_text(_handoff_yaml(), encoding="utf-8")
    errors, checks = VSP.check_handoff(p)
    assert not errors, errors
    assert checks.get("strike_assumption") is None


def test_strike_assumption_normal_passes(tmp_path):
    p = tmp_path / "handoff.yaml"
    p.write_text(_handoff_yaml("你还觉得写作只能靠天赋？"), encoding="utf-8")
    errors, checks = VSP.check_handoff(p)
    assert not errors, errors
    assert checks.get("strike_assumption") == "你还觉得写作只能靠天赋？"


def test_strike_assumption_too_long_fails(tmp_path):
    """77P/OBS-339: the former advisory overlength is now a content gate."""
    p = tmp_path / "handoff.yaml"
    long_text = "这是一个超过四十字长度的被否定的旧认知描述用来验证advisory不阻断交付的测试样本内容"
    p.write_text(_handoff_yaml(long_text), encoding="utf-8")
    errors, checks = VSP.check_handoff(p)
    assert any("strike_assumption" in error and "18" in error for error in errors)
    assert checks["strike_assumption"] == long_text
