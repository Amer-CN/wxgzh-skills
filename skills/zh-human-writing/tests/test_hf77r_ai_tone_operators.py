"""77R/OBS-342: upstream-validated AI-tone six-family operator tests."""
from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "pattern_audit.py"
spec = importlib.util.spec_from_file_location("pattern_audit_77r", SCRIPT)
pattern_audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pattern_audit)


def _hits(text: str):
    masked = pattern_audit.mask_non_prose(text)
    return pattern_audit.detect_ai_tone_families(masked, text, "essay", [])


def _ids(text: str):
    return {finding["rule_id"] for finding in _hits(text)}


def test_zero_reference_comment_hits_and_first_paragraph_is_exempt():
    hit = "第一段足够长。\n\n听起来很有希望。"
    exempt = "听起来很有希望。\n\n这个结果值得继续验证。"
    assert "LT-001" in _ids(hit)
    assert "LT-001" not in _ids(exempt)


def test_personified_metaphor_hits_and_specific_human_is_exempt():
    hit = "这个系统像一位智慧的导师，会指出盲点。"
    exempt = "他像一个人脉很广的医生朋友，帮我们约到了专家。"
    assert "LT-002" in _ids(hit)
    assert "LT-002" not in _ids(exempt)


def test_opening_formula_hits_and_code_is_exempt():
    hit = "这一节足够长。\n\n说白了，结论只有一个。"
    exempt = "```\n说白了，这里不能执行。\n```"
    assert "LT-003" in _ids(hit)
    assert "LT-003" not in _ids(exempt)


def test_ordinal_heading_run_hits_and_short_run_is_exempt():
    hit = "# 一、背景\n\n# 二、方法\n\n# 三、结论"
    exempt = "# 一、背景\n\n# 二、方法"
    assert "LT-004" in _ids(hit)
    assert "LT-004" not in _ids(exempt)


def test_dense_enum_hits_and_markdown_list_is_exempt():
    hit = "这个平台支持采集、存储、展示三类能力。"
    exempt = "- 采集\n- 存储\n- 展示"
    assert "LT-005" in _ids(hit)
    assert "LT-005" not in _ids(exempt)


def test_adjacent_isomorphism_hits_and_varied_sentences_are_exempt():
    hit = "工具降低了门槛，成本也开始下降。团队扩大了规模，收入也开始上涨。"
    exempt = "工具降低了门槛。随后的成本也下降，但维护责任反而增加了。"
    assert "LT-005" in _ids(hit)
    assert "LT-005" not in _ids(exempt)


def test_translationese_hits_and_list_is_exempt():
    hit = "对于早期团队来说，招聘是最难的事。"
    exempt = "- 对于早期团队来说，招聘是最难的事。"
    assert "LT-006" in _ids(hit)
    assert "LT-006" not in _ids(exempt)
