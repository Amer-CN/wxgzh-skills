"""77W/OBS-358:04 合同 copyright_policy 单一真源 + 规则冲突停机立规锚点。

守卫口径(照 catalog 守卫先例):contracts/04_media_enrichment.yaml 的
copyright_policy 节仅镜像 media-enrichment SKILL.md「自动决策边界」节,
两文一致才绿;producers media 阶段指令(approval_contract_rule)必须携带
「规则冲突一律停机上报,禁止执行端自裁」措辞。
"""
from pathlib import Path

import wxgzh_pipeline.producers as PR

from conftest import SKILL_ROOT


def test_77w_contract_single_source_keys():
    """04 合同键值 + SINGLE_SOURCE_REF 在册且指向 SKILL.md。77Y:值随用户裁决更新。"""
    text = (SKILL_ROOT / "contracts" / "04_media_enrichment.yaml").read_text(
        encoding="utf-8")
    assert "USER_BLANKET_APPROVAL: false" in text
    # 77Y/OBS-367:终审点=草稿箱发布动作,过程道非人工——true→false
    assert "PER_IMAGE_MANUAL_REVIEW_REQUIRED: false" in text
    # 77Y/OBS-368:rejected_with_reason 一等公民
    assert "REJECTED_WITH_REASON_FIRST_CLASS: true" in text
    assert "77Y/OBS-367 用户裁决 2026-09-05，终审点=草稿箱发布动作" in text
    ref_line = next(l for l in text.splitlines()
                    if l.strip().startswith("SINGLE_SOURCE_REF:"))
    assert "skills/media-enrichment/SKILL.md#自动决策边界" in ref_line
    assert "77W/OBS-358" in text


def test_77w_single_source_guard_media_skill_boundary():
    """守卫:media SKILL.md「自动决策边界」节与合同镜像两文一致才绿。
    77Y 口径:auto_rule 车道合法+终审点=发布键+rejected_with_reason 正路。"""
    text = (SKILL_ROOT.parent / "media-enrichment" / "SKILL.md").read_text(
        encoding="utf-8")
    assert "### 自动决策边界" in text
    assert "auto_rule 规则车道合法（77Y/OBS-367，用户裁决 2026-09-05）" in text
    assert "basis 机械生成（77Y/OBS-366，agent 手填 basis 一律忽略" in text
    assert "auto_approve 机器车道开启（WXGZH_MEDIA_AUTO_APPROVE=1，默认关，非 live）" in text
    assert "**人工终审点**：用户草稿箱发布动作（发布前过目图片）" in text
    assert "rejected_with_reason 处置（带理由，77Y/OBS-368" in text
    assert "守卫清零只针对「存活未处置」资产" in text


def test_77w_conflict_rule_instruction_anchor():
    """锚点:media 阶段指令(approval_contract_rule)含 77W/OBS-358 立规措辞。"""
    rule = PR.APPROVAL_CONTRACT_RULE
    assert "77W/OBS-358" in rule
    assert "任何两份规则文件(合同/协议/SKILL.md/指令)冲突时" in rule
    assert "一律停机上报审核方" in rule
    assert "禁止执行端自裁" in rule
    assert "原文贴回等档" in rule
    # 既有 77A 措辞不丢失(追加模式,非改写)
    assert "77A/OBS-308" in rule and "approval_readiness_sha256" in rule
