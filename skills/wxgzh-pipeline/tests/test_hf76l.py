"""76L/OBS-282/283:反顶包明规与红旗规则断言。"""
from __future__ import annotations

import wxgzh_pipeline.producers as PR

from conftest import SKILL_ROOT


def test_instructions_contain_anti_supplantation_rule():
    for key in ("aihot", "super_writer", "zh_human_writing"):
        instr = PR.AGENT_INSTRUCTIONS[key]
        assert "76L/OBS-283(反顶包明规" in instr, key
        assert "禁止手写 HTML 或其他脚本顶包 gzh_design 渲染产物" in instr, key
        assert "禁止绕过阶段直接调用 publish_wechat_draft.py" in instr, key
        assert "遇阻的正确动作=停下并报告" in instr, key


def test_instructions_mention_evidence_gate():
    for key in ("aihot", "super_writer", "zh_human_writing"):
        instr = PR.AGENT_INSTRUCTIONS[key]
        assert "--evidence" in instr, key
        assert "只认管线 wechat_draft 阶段" in instr, key


def test_readme_contains_red_flag_rule():
    text = (SKILL_ROOT / "README.md").read_text(encoding="utf-8")
    assert "交付边界" in text and "76L/OBS-282/283" in text
    assert "禁止顶包" in text
    assert "顶包红旗" in text and "不可发" in text
    assert "公众号后台手动" in text


def test_fake_live_shim_requires_evidence():
    shim = (SKILL_ROOT / "fake_live" / "skills" / "gzh-design"
            / "publish_wechat_draft.py").read_text(encoding="utf-8")
    assert "--evidence" in shim
    assert "交付凭证缺失" in shim
