"""77Y/OBS-366+367+371:basis 机械生成 / auto_rule 车道条件 / user 车道圆形证据封堵。

覆盖:
1. OBS-366 basis 机械生成(+3):①实时合同值入账且 0srcql 式手填死条款 basis 被
   机械值替代;②死条款不可能(改合同值→basis 随变,不含旧值);③证据链断(approvable
   =false)/受限/分类器拒 → 机械车道不 blessed(返回 None,手填无效,走既有 fail-fast);
2. OBS-371 圆形证据封堵(+2):①user + 仅 pipeline 自产 approval_evidence_sha256
   (无 user_images/user_action)→ 拒;②真实证据(user_images 匹配 或 user_action
   三要素齐)→ 过。

纯函数单测,零网络零微信;合同值经 mock dict / 临时 yaml 注入。
"""
from __future__ import annotations

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
sys.path.insert(0, str(SKILL_ROOT / "src"))

import run_media_enrichment as runner  # noqa: E402

CONFIG = {"domain_blacklist": ["ithome.com", "img.ithome.com"]}
READINESS_OK = {"asset_id": "A-001", "approvable": True,
                "approvable_blockers": []}
ASSET_OK = {
    "asset_id": "A-001", "decision": "review_required",
    "copyright_status": "unknown",
    "resolved_original_url": "https://www.example-source.test/a.png",
}
CONTRACT_LIVE = {
    "COPYRIGHT_POLICY": "ALLOW_UNLESS_EXPLICITLY_PROHIBITED",
    "USER_BLANKET_APPROVAL": False,
    "PER_IMAGE_MANUAL_REVIEW_REQUIRED": False,
}
# 0srcql 式手填 basis(死条款 USER_BLANKET_APPROVAL=true 引用,77Y/OBS-366 实证原形)
HAND_FILLED_DEAD_BASIS = "04 合同 copyright_policy 节 USER_BLANKET_APPROVAL=true"


# ── OBS-366:basis 机械生成(77Y 规格 B 测试 +3)─────────────────────────

def test_77y_mechanical_basis_generated_with_live_values():
    """①机械生成:mock 合同值+证据链齐 → basis 含实时值,且 0srcql 式手填
    死条款 basis 被机械值替代(单值不等+内容不含死条款)。"""
    basis = runner._mechanical_basis(
        "live", CONFIG, CONTRACT_LIVE, READINESS_OK, ASSET_OK)
    assert basis is not None
    assert "auto_rule lane(77Y/OBS-367)" in basis
    assert "COPYRIGHT_POLICY=ALLOW_UNLESS_EXPLICITLY_PROHIBITED" in basis
    assert "USER_BLANKET_APPROVAL=False" in basis
    assert "PER_IMAGE_MANUAL_REVIEW_REQUIRED=False" in basis
    assert "approval_readiness.approvable=true" in basis
    assert "分类器=review_required" in basis
    assert "domain www.example-source.test 非水印高危" in basis
    # 手填 basis 一律忽略:机械值 != 0srcql 式手填,且不含手填死条款内容
    assert basis != HAND_FILLED_DEAD_BASIS
    assert "USER_BLANKET_APPROVAL=true" not in basis
    assert HAND_FILLED_DEAD_BASIS.split()[1] not in basis.split()


def test_77y_mechanical_basis_tracks_contract_change(tmp_path):
    """②死条款不可能:改 mock 合同值(true)→ basis 随变,断言不含旧值。"""
    changed = {"COPYRIGHT_POLICY": "REVIEW_REQUIRED",
               "USER_BLANKET_APPROVAL": True,
               "PER_IMAGE_MANUAL_REVIEW_REQUIRED": True}
    basis = runner._mechanical_basis(
        "live", CONFIG, changed, READINESS_OK, ASSET_OK)
    assert basis is not None
    assert "COPYRIGHT_POLICY=REVIEW_REQUIRED" in basis
    assert "USER_BLANKET_APPROVAL=True" in basis
    assert "PER_IMAGE_MANUAL_REVIEW_REQUIRED=True" in basis
    assert "USER_BLANKET_APPROVAL=False" not in basis
    assert "PER_IMAGE_MANUAL_REVIEW_REQUIRED=False" not in basis
    # 实时读取路径:_load_media_contract 解析临时 yaml 文件后生成同口径 basis
    yaml_file = tmp_path / "04_media_enrichment.yaml"
    yaml_file.write_text(
        "stage: media_enrichment\n"
        "copyright_policy:\n"
        "  COPYRIGHT_POLICY: REVIEW_REQUIRED\n"
        "  USER_BLANKET_APPROVAL: true\n"
        "  PER_IMAGE_MANUAL_REVIEW_REQUIRED: true\n",
        encoding="utf-8")
    loaded = runner._load_media_contract(yaml_file)
    assert loaded == changed
    basis2 = runner._mechanical_basis(
        "live", CONFIG, loaded, READINESS_OK, ASSET_OK)
    assert "USER_BLANKET_APPROVAL=True" in basis2


def test_77y_mechanical_basis_refused_when_evidence_chain_broken():
    """③证据链断拒批:approvable=false → 机械车道不 blessed(返回 None);
    受限/分类器拒/黑名单域名同口径(None)。"""
    assert runner._mechanical_basis(
        "live", CONFIG, CONTRACT_LIVE, {"approvable": False}, ASSET_OK) is None
    assert runner._mechanical_basis(
        "live", CONFIG, CONTRACT_LIVE, None, ASSET_OK) is None
    # 受限(77W 三道门之一:restricted 覆盖)
    restricted = dict(ASSET_OK, copyright_status="restricted")
    assert runner._mechanical_basis(
        "live", CONFIG, CONTRACT_LIVE, READINESS_OK, restricted) is None
    # 分类器水印/拒(decision=rejected)
    rejected = dict(ASSET_OK, decision="rejected")
    assert runner._mechanical_basis(
        "live", CONFIG, CONTRACT_LIVE, READINESS_OK, rejected) is None
    # 黑名单域名(水印高危域)
    blacklisted = dict(ASSET_OK,
                       resolved_original_url="https://img.ithome.com/a.png")
    assert runner._mechanical_basis(
        "live", CONFIG, CONTRACT_LIVE, READINESS_OK, blacklisted) is None


# ── OBS-371:圆形证据封堵(77Y 规格 C 测试 +2)─────────────────────────

def _approval(**overrides) -> dict:
    record = {
        "asset_id": "A-001", "material_id": "M-001",
        "source_page_url": "https://www.example-source.test/a",
        "approved_by": "user",
    }
    record.update(overrides)
    return record


def test_77y_circular_evidence_rejected():
    """①圆形证据拒:user + 仅 pipeline 自产 approval_evidence_sha256 +
    readiness sha(无 user_images/user_action)→ 拒,错误指路 77Y/OBS-371。"""
    circular = _approval(approval_evidence_sha256="e" * 64)
    assert runner._user_action_evidence(circular, {}) is False
    error = runner._approval_lane_error(circular, {})
    assert error is not None and "77Y/OBS-371" in error
    assert "pipeline 自产 sha 不算" in error
    # 空串/非 dict user_action 同拒
    assert runner._user_action_evidence(
        _approval(user_action=None), {}) is False
    assert runner._user_action_evidence(
        _approval(user_action={"user": "u", "action": "approved"}), {}) is False


def test_77y_real_user_evidence_passes():
    """②真实证据过:user_images 匹配(material_id/source_url 既有通道)
    或 user_action 三要素齐(user 非空+action=approved+at 为 ISO)→ 过。"""
    request = {"user_images": [{"url": "https://img.example.test/1.png",
                                "material_id": "M-001"}]}
    assert runner._user_action_evidence(_approval(), request) is True
    request = {"user_images": [{"url": "https://img.example.test/1.png",
                                "source_url": "https://www.example-source.test/a"}]}
    assert runner._user_action_evidence(_approval(), request) is True
    # user_action 三要素齐
    ua = {"user": " operator ", "action": "approved",
          "at": "2026-09-05T12:00:00Z"}
    assert runner._user_action_evidence(_approval(user_action=ua), {}) is True
    assert runner._approval_lane_error(
        _approval(user_action=ua), {}) is None
    # 三要素缺一/action 非 approved/at 非 ISO → 拒
    assert runner._user_action_evidence(
        _approval(user_action={"action": "approved", "at": ua["at"]}), {}) is False
    assert runner._user_action_evidence(
        _approval(user_action={"user": "u", "at": ua["at"]}), {}) is False
    assert runner._user_action_evidence(
        _approval(user_action={"user": "u", "action": "rejected",
                               "at": ua["at"]}), {}) is False
    assert runner._user_action_evidence(
        _approval(user_action={"user": "u", "action": "approved",
                               "at": "不是时间"}), {}) is False
