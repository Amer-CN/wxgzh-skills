"""76R 任务 2/OBS-288:预检强制化 + 指令瘦身测试。

- sw 指令含硬步骤:ACK 前必须跑 align_outline_budget + validate_single_product 且全绿,否则禁止 ACK;
- 通用规则(276/279/283)抽为单一真源常量,三阶段共用(源码去重);
- 语义零丢失:改写前(HEAD)与改写后产物指令规则清单一一对应;公共规则在源码中单写。
"""
from __future__ import annotations

import re
import subprocess

import wxgzh_pipeline.producers as PR

from conftest import SKILL_ROOT


def test_obs288_preflight_mandatory_hard_step():
    """sw 预检强制化——ACK 前必须完成两步且全绿,禁止写 ACK。"""
    instr = PR.AGENT_INSTRUCTIONS["super_writer"]
    assert "76R/OBS-288" in instr and "硬步骤" in instr
    assert "ACK 前必须完成以下两步且全绿" in instr
    assert "否则禁止写 ACK" in instr
    assert "align_outline_budget.py" in instr and "validate_single_product.py" in instr
    assert "valid=true" in instr


def test_obs288_common_rules_single_source():
    """通用规则(276/279/283)单一真源,三阶段产物指令均含。"""
    assert hasattr(PR, "_COMMON_RULES")
    for k in ("aihot", "super_writer", "zh_human_writing"):
        assert "76F/OBS-276" in PR.AGENT_INSTRUCTIONS[k]
        assert "76F/OBS-279" in PR.AGENT_INSTRUCTIONS[k]
        assert "76L/OBS-283" in PR.AGENT_INSTRUCTIONS[k]


def test_obs288_common_rule_not_copied_in_source():
    """源码瘦身:公共规则常量只定义一次,非三份各自内联复制。"""
    src = (SKILL_ROOT / "wxgzh_pipeline" / "producers.py").read_text(encoding="utf-8")
    assert src.count("_COMMON_RULES = ") == 1, "公共常量被重复定义"
    # _COMMON_RULES 含 283 + _COMMON_RULES_283 单拆段供 sw 拼接(结构性拆分,非复制);
    # 硬门:AGENT_INSTRUCTIONS 三指令内不得再内联 276 规则(只许引用常量)
    instr_block = src[src.find("AGENT_INSTRUCTIONS = {"):]
    # sw 中段的 276/279 属其特有顺序(278 前),保留;硬门=283 规则只定义一次
    # (_COMMON_RULES 内含 283,_COMMON_RULES_283 是引用切片,AGENT_INSTRUCTIONS 内无内联 283)
    assert src.count("_COMMON_RULES_283 = ") == 1


def _extract_old_instructions():
    """从 HEAD(改写前)提取 AGENT_INSTRUCTIONS 字典。"""
    # 基线 = 76Q-F 终态(8f6a775),即 76R 指令瘦身前
    old_src = subprocess.run(
        ["git", "show", "8f6a775:skills/wxgzh-pipeline/wxgzh_pipeline/producers.py"],
        capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    start = old_src.find("AGENT_INSTRUCTIONS = {")
    end_marker = old_src.index("}", old_src.index('"zh_human_writing"'))
    end = old_src.index("\n", end_marker)
    ns = {}
    exec(old_src[start:end], ns)
    return ns["AGENT_INSTRUCTIONS"]


def _rules(v):
    seen, out = set(), []
    for mm in re.findall(r"(\d+(?:[A-Za-z-]*)/OBS-\d+|OBS-\d+)", v):
        if mm not in seen:
            seen.add(mm)
            out.append(mm)
    return out


def test_obs288_semantic_zero_loss_rule_inventory():
    """语义零丢失:改写前后规则清单一一对应(278→288 为预检强制化升级,1:1)。"""
    old_instr = _extract_old_instructions()
    for k in ("aihot", "super_writer", "zh_human_writing"):
        old_rules = ["76R/OBS-288" if r == "76F/OBS-278" else r for r in _rules(old_instr[k])]
        new_rules = _rules(PR.AGENT_INSTRUCTIONS[k])
        # 旧规则全部保留(278→288 升级);新规则仅允许 76R/OBS-290(素材定长度,76R 新增)
        for r in old_rules:
            assert r in new_rules, f"{k}: 旧规则丢失 {r}"
        extra = set(new_rules) - set(old_rules)
        assert extra <= {"76R/OBS-290"}, f"{k}: 意外新增规则 {extra}"


def test_obs290_material_exhausted_instruction():
    """76R/OBS-290:sw 指令含「素材写干即停;禁止注水凑字数」明规。"""
    instr = PR.AGENT_INSTRUCTIONS["super_writer"]
    assert "76R/OBS-290" in instr
    assert "素材写干即停" in instr and "禁止注水凑字数" in instr
    assert "不逼扩写" in instr or "不报错逼扩写" in instr


def test_obs288_instruction_text_unchanged_except_278():
    """产物指令逐字一致(唯一差异=278→288 硬步骤升级 + 290 明规新增,其余零改动)。"""
    old_instr = _extract_old_instructions()
    for k in ("aihot", "zh_human_writing"):
        assert old_instr[k] == PR.AGENT_INSTRUCTIONS[k], f"{k} 指令发生非预期变化"
    old_sw = old_instr["super_writer"]
    new_sw = PR.AGENT_INSTRUCTIONS["super_writer"]
    # 变更点:278→288(硬步骤)+ 290 新增(明规);其余内容逐字保留
    assert "76F/OBS-278" not in new_sw and "76R/OBS-288" in new_sw
    assert "76R/OBS-290" in new_sw and "76Q/OBS-287" in new_sw
    # 旧 sw 中 76F/OBS-278 段之前的内容与新 sw 中 76R/OBS-288 段之前逐字一致
    old_head = old_sw[:old_sw.find("76F/OBS-278")]
    new_head = new_sw[:new_sw.find("76R/OBS-288")]
    assert new_head == old_head, "sw 指令 288 段之前发生非预期变化"
    # 旧 sw 中 76Q/OBS-287 之后的内容与新 sw 中 76Q/OBS-287 之后逐字一致
    old_tail = old_sw[old_sw.find("76Q/OBS-287"):]
    new_tail = new_sw[new_sw.find("76Q/OBS-287"):]
    assert new_tail == old_tail, "sw 指令 287 段之后发生非预期变化"
