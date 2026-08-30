"""77O: hard instruction anchors for LIVE default and receipt discipline."""
from __future__ import annotations

from pathlib import Path

PRODUCERS = Path(__file__).parents[1] / "wxgzh_pipeline" / "producers.py"


def _rules() -> str:
    return PRODUCERS.read_text(encoding="utf-8")


def test_obs337_live_default_is_explicitly_limited():
    rules = _rules()
    assert "77O/OBS-337(LIVE 默认纪律)" in rules
    assert "发文流程默认 LIVE 建草稿" in rules
    assert "WXGZH_WECHAT_API_ALLOWED=1" in rules
    assert "dry-run 仅限用户明说预览/凭证缺失/ALLOWED=0 三种情形" in rules
    assert "必须在体检第 1 项如实标注" in rules


def test_obs338_receipt_no_handwriting_has_no_exception():
    rules = _rules()
    assert "手工编辑/手写/补写,无例外" in rules
    assert "含演练、fake_live、dry-run、断档恢复" in rules
    assert "orchestrator 续发/重跑,不是补写" in rules


def test_77o_role_boundary_instruction():
    rules = _rules()
    assert "体检报告只报事实与风险" in rules
    assert "不得向用户索要流程内决断" in rules
    assert "流程内决断一律由审核方出档" in rules
