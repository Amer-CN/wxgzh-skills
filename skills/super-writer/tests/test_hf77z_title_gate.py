"""77Z 规格 C:VSP --product handoff 标题候选逐候选证据完备门(OBS-376)。

四场景(+4):全候选齐过 / 缺分组 FAIL / 缺五维 FAIL(tlztos 场景——只评主
标题) / 缺风险标记 FAIL(含「无」未显式写出场景)。历史三篇 RUN 干跑见验收。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest  # noqa: F401

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import validate_single_product as VSP  # noqa: E402


def _handoff_yaml(candidates_block: str, reason: str) -> str:
    return f"""handoff:
  schema_version: "2.2"
  prose_craft_applied: true
  prose_craft_version: "1.0"
  title_candidates:
{candidates_block}
  hook_line: "钩子"
  selected_title: "标题甲"
  title_selection_reason: "{reason}"
  formatter:
    cover:
      kicker: null
      strike: null
      tags: null
"""


FULL_CANDIDATES = """    - 标题甲
    - 标题乙
    - 标题丙"""

# 逐候选齐备 reason:每候选「组=标题」映射位 + 窗口内五维 + 显式风险标记。
FULL_REASON = ("四组覆盖：稳健准确=标题甲，点击欲望4/事实匹配5/人群匹配4/差异化3/长期价值4，风险标记：无；"
               "网感点击=标题乙，点击欲望5/事实匹配4/人群匹配4/差异化4/长期价值3，风险标记：无堆砌；"
               "专业权威=标题丙，点击欲望3/事实匹配5/人群匹配5/差异化3/长期价值5，风险标记：时效（复盘组豁免注明）。"
               "推荐主=标题甲。")


def _check(tmp_path, candidates_block: str, reason: str):
    p = tmp_path / "handoff.yaml"
    p.write_text(_handoff_yaml(candidates_block, reason), encoding="utf-8")
    return VSP.check_handoff(p)


# ---------- ① 全候选齐过 ----------

def test_77z_all_candidates_complete_pass(tmp_path):
    errors, checks = _check(tmp_path, FULL_CANDIDATES, FULL_REASON)
    assert errors == [], errors


# ---------- ② 缺分组 FAIL ----------

def test_77z_candidate_missing_group_fails(tmp_path):
    """候选丁在 reason 无任何「组=标题」映射位 → 逐候选层 FAIL 指路 playbook。"""
    candidates = FULL_CANDIDATES + "\n    - 标题丁"
    reason = FULL_REASON + "另提一句：标题丁作为对照。"
    errors, _ = _check(tmp_path, candidates, reason)
    assert errors, errors
    assert "references/title-playbook.md" in errors[0]
    assert any("候选4 缺分组归属" in e for e in errors)
    # 前三候选证据齐备,不误伤
    assert not any("候选1 缺分组" in e or "候选2 缺分组" in e or "候选3 缺分组" in e
                   for e in errors)


# ---------- ③ 缺五维 FAIL(tlztos 场景——只评主标题) ----------

def test_77z_only_main_title_scored_fails(tmp_path):
    """历史 tlztos 形态:reason 只给选定主标题一套五维 → 其余候选逐候选 FAIL。"""
    reason = ("四组覆盖：稳健准确=标题甲；网感点击=标题乙；专业权威=标题丙。"
              "五维评分（选定主标题）：点击欲望4、事实匹配5、人群匹配4、差异化3、长期价值4。"
              "风险标记：无标题党、无堆砌、有据、时效强。推荐主=标题甲。")
    errors, _ = _check(tmp_path, FULL_CANDIDATES, reason)
    assert errors, errors
    assert "references/title-playbook.md" in errors[0]
    assert any("候选2 缺五维评分" in e for e in errors)
    assert any("候选3 缺五维评分" in e for e in errors)
    assert "禁只评选定主标题" in " ".join(errors)


# ---------- ④ 缺风险标记 FAIL(含「无」未显式写出场景) ----------

def test_77z_candidate_missing_risk_marker_fails(tmp_path):
    """候选丙段写了五维但无任何风险表述(「无」未显式写出) → FAIL。"""
    reason = ("稳健准确=标题甲，点击欲望4/事实匹配5/人群匹配4/差异化3/长期价值4，风险标记：无；"
              "网感点击=标题乙，点击欲望5/事实匹配4/人群匹配4/差异化4/长期价值3，风险标记：标题党风险已核对为无；"
              "专业权威=标题丙，点击欲望3/事实匹配5/人群匹配5/差异化3/长期价值5。推荐主=标题甲。")
    errors, _ = _check(tmp_path, FULL_CANDIDATES, reason)
    assert errors, errors
    assert any("候选3 缺显式风险标记" in e for e in errors)
    assert "「无」必须显式" in " ".join(errors)
