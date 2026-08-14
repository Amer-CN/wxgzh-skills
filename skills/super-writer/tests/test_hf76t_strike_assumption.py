"""76T/OBS-293:handoff formatter.cover.strike_assumption 校验(advisory)。

- 缺失:不 FAIL(渲染端划线句整行不渲染);
- 超长(>40 字):advisory 记入 checks,不 FAIL;
- 正常:通过。
"""
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
  title_candidates: ["A", "B"]
  hook_line: "钩子"
  selected_title: "A"
  title_selection_reason: "具体"
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


def test_strike_assumption_too_long_advisory_only(tmp_path):
    p = tmp_path / "handoff.yaml"
    long_text = "这是一个超过四十字长度的被否定的旧认知描述用来验证advisory不阻断交付的测试样本内容"
    p.write_text(_handoff_yaml(long_text), encoding="utf-8")
    errors, checks = VSP.check_handoff(p)
    # 超长 → advisory 记入 checks,不 FAIL
    assert not errors, errors
    assert "strike_assumption_warnings" in checks
    assert "40 字" in checks["strike_assumption_warnings"]
