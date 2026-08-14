"""76V/OBS-297:align_outline_budget 分节加权预算测试。

- 按各节 evidence_ids 数量(素材密度)分配权重,不再均分/原比例;
- 输出每节 ±5% 容差区间;
- 无 evidence 时回退原比例(76F 语义);
- 76R material_exhausted 语义回归(align 不触碰保护域)。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from align_outline_budget import align_outline, parse_sections  # noqa: E402


OUTLINE_WEIGHTED = """# Outline

## 文章配置
- article_mode: medium
- target_visible_chars: 6000

## 第一节(重)
- weight_percent: 60
- planned_chars: 3600
- minimum_chars: 3400
- maximum_chars: 3800
- evidence_ids: [e-1, e-2, e-3, e-4, e-5, e-6, e-7, e-8]
- event_ids: [ev-1]
- unique_information_goal: 目标甲

## 第二节(轻)
- weight_percent: 40
- planned_chars: 2400
- minimum_chars: 2200
- maximum_chars: 2600
- evidence_ids: [e-9, e-10]
- event_ids: [ev-2]
- unique_information_goal: 目标乙
"""


def test_weighted_allocation_by_evidence_density():
    """证据密度 8:2 → 预算 80%:20%(6000 → 4800/1200),不再均分。"""
    new_text, info, errors = align_outline(OUTLINE_WEIGHTED, 6000)
    assert not errors, errors
    assert info["total_new"] == 6000
    assert info["allocation_mode"] == "evidence_weighted"
    sections = parse_sections(new_text)
    by_title = {s["title"]: s for s in sections}
    assert by_title["第一节(重)"]["planned"] == 4800
    assert by_title["第二节(轻)"]["planned"] == 1200
    # 各节 evidence_count 与 weight 输出
    sec_info = {s["title"]: s for s in info["sections"]}
    assert sec_info["第一节(重)"]["evidence_count"] == 8
    assert round(sec_info["第一节(重)"]["weight"], 2) == 0.8


def test_tolerance_range_output():
    """每节输出 ±5% 容差区间。"""
    new_text, info, errors = align_outline(OUTLINE_WEIGHTED, 6000)
    assert not errors
    assert info["tolerance"] == "±5%"
    sections = parse_sections(new_text)
    by_title = {s["title"]: s for s in sections}
    # 4800 的 ±5% = 4560~5040;1200 的 ±5% = 1140~1260
    assert by_title["第一节(重)"]["min_c"] == 4560
    assert by_title["第一节(重)"]["max_c"] == 5040
    assert by_title["第二节(轻)"]["min_c"] == 1140
    assert by_title["第二节(轻)"]["max_c"] == 1260


def test_no_evidence_falls_back_original_proportional():
    """无 evidence_ids → 回退原 planned 比例(76F 语义)。"""
    outline = OUTLINE_WEIGHTED.replace("- evidence_ids: [e-1, e-2, e-3, e-4, e-5, e-6, e-7, e-8]", "- evidence_ids: []")
    outline = outline.replace("- evidence_ids: [e-9, e-10]", "- evidence_ids: []")
    new_text, info, errors = align_outline(outline, 6000)
    assert not errors
    assert info["allocation_mode"] == "original_proportional"
    sections = parse_sections(new_text)
    by_title = {s["title"]: s for s in sections}
    # 原比例 60:40 → 3600/2400
    assert by_title["第一节(重)"]["planned"] == 3600
    assert by_title["第二节(轻)"]["planned"] == 2400


def test_weight_percent_synced_with_planned():
    """76W/OBS-300:写回时 planned_chars 与 weight_percent 原子一致。"""
    new_text, info, errors = align_outline(OUTLINE_WEIGHTED, 6000)
    assert not errors
    # 4800/6000=80.0, 1200/6000=20.0
    assert "- weight_percent: 80.0" in new_text
    assert "- weight_percent: 20.0" in new_text
    assert "- planned_chars: 4800" in new_text
    assert "- planned_chars: 1200" in new_text


def test_weight_percent_sync_fallback_path():
    """76W/OBS-300:无 evidence 回退路径两字段仍一致。"""
    outline = OUTLINE_WEIGHTED.replace("- evidence_ids: [e-1, e-2, e-3, e-4, e-5, e-6, e-7, e-8]", "- evidence_ids: []")
    outline = outline.replace("- evidence_ids: [e-9, e-10]", "- evidence_ids: []")
    new_text, info, errors = align_outline(outline, 6000)
    assert not errors
    # 原比例 60:40 → 3600/2400 → 权重 60.0/40.0
    assert "- weight_percent: 60.0" in new_text
    assert "- weight_percent: 40.0" in new_text
    assert "- planned_chars: 3600" in new_text
    assert "- planned_chars: 2400" in new_text


def test_material_exhausted_semantics_preserved():
    """76R 语义回归:align 不触碰保护域(weight/evidence_ids/event_ids/目标),素材耗尽语义不变。"""
    new_text, info, errors = align_outline(OUTLINE_WEIGHTED, 3000)
    assert not errors
    # 76W/OBS-300:weight_percent 与 planned_chars 原子同步(80.0/20.0,3000 目标)
    assert "- weight_percent: 80.0" in new_text
    assert "- weight_percent: 20.0" in new_text
    assert "- evidence_ids: [e-1, e-2, e-3, e-4, e-5, e-6, e-7, e-8]" in new_text
    assert "- event_ids: [ev-1]" in new_text
    assert "- unique_information_goal: 目标甲" in new_text
    # 8:2 → 2400/600
    sections = parse_sections(new_text)
    by_title = {s["title"]: s for s in sections}
    assert by_title["第一节(重)"]["planned"] == 2400
    assert by_title["第二节(轻)"]["planned"] == 600
