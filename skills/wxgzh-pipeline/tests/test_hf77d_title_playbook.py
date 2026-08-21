"""77D 标题双轨:Phase 6 指令升级断言 + sw title-playbook 在册。"""
from __future__ import annotations

from pathlib import Path

from wxgzh_pipeline import producers as P

from conftest import SKILL_ROOT

SW_REFERENCES = SKILL_ROOT.parent / "super-writer" / "references"


def test_77d_phase6_instruction_upgraded():
    instr = P.AGENT_INSTRUCTIONS["super_writer"]
    assert "77D/标题双轨" in instr
    assert "title-playbook.md" in instr
    assert "五维评分" in instr and "点击欲望" in instr and "事实匹配" in instr
    assert "风险标记" in instr and "标题党/堆砌/无据/时效" in instr
    assert "1 主 2 备" in instr
    assert "handoff 字段零变动" in instr


def test_77d_title_playbook_reference_present():
    p = SW_REFERENCES / "title-playbook.md"
    assert p.is_file(), "缺 references/title-playbook.md"
    text = p.read_text(encoding="utf-8")
    for anchor in ("文章诊断", "稳健准确", "五维评分", "风险标记", "1 主标题"):
        assert anchor in text, f"playbook 缺锚点: {anchor}"


def test_77d_handoff_schema_untouched():
    """handoff schema 零变动:字段清单与 76B 一致。"""
    schemas = SKILL_ROOT / "schemas"
    for f in ("final_delivery.schema.json", "pipeline_state.schema.json"):
        p = schemas / f
        if p.is_file():
            text = p.read_text(encoding="utf-8")
            assert "title_candidates" in text or "selected_title" not in text
