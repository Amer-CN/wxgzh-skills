"""77A/OBS-308: 审批合同 approval_readiness_sha256 硬步骤断言。

批准合同每条 single_asset 必带 approval_readiness_sha256，一律从最新
approval_readiness_report.json 原样照抄——缺字段/引用过期 FAIL_CLOSED。
"""
from pathlib import Path

from wxgzh_pipeline import producers as P


def test_approval_contract_rule_hard_step_text():
    rule = P.APPROVAL_CONTRACT_RULE
    assert "77A/OBS-308" in rule
    assert "硬步骤" in rule
    assert "approval_readiness_sha256" in rule
    assert "禁止自算" in rule
    assert "FAIL_CLOSED" in rule


def test_contract_yaml_hard_step_in_place():
    p = Path(P.__file__).parent.parent / "contracts" / "04_media_enrichment.yaml"
    text = p.read_text(encoding="utf-8")
    assert "77A/OBS-308(审批合同,硬步骤)" in text
    assert "必带 approval_readiness_sha256" in text
    assert "原样照抄、禁止自算、禁止引用旧轮" in text


def test_approval_meta_carries_rule():
    src = Path(P.__file__).read_text(encoding="utf-8")
    assert src.count('meta["approval_contract_rule"] = APPROVAL_CONTRACT_RULE') >= 1
    assert '"approval_contract_rule": APPROVAL_CONTRACT_RULE,' in src
