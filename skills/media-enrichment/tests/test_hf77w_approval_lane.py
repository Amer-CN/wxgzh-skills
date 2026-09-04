"""77W/OBS-357+359:审批车道枚举/basis 依据/用户证据门 + supplemental permalink 通道。

覆盖:
1. OBS-357 ①approved_by 枚举外值拒;②auto_rule 无 basis 拒;
   ③user 无证据拒 / 有 user_images 证据(既有通道)通过(mock 最小结构);
2. OBS-359 ①supplemental+aihot_permalink=null 通过;
   ②supplemental+permalink=外站(huggingface.co/blog)构造填充拒。

零网络零微信:车道校验为纯函数单测;permalink 分流走 validate_manifest
最小 manifest/request 结构,只断言本档新增检查项。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
sys.path.insert(0, str(SKILL_ROOT / "src"))

import run_media_enrichment as runner  # noqa: E402
from validate_media_manifest import validate_manifest  # noqa: E402


def _approval(**overrides) -> dict:
    record = {
        "asset_id": "A-001", "material_id": "M-001",
        "source_page_url": "https://www.example-source.test/a",
        "approved_by": "user",
        "approval_evidence_sha256": "e" * 64,
    }
    record.update(overrides)
    return record


# ── OBS-357:审批车道(77W 规格 B 测试 +3)─────────────────────────────

def test_77w_approved_by_out_of_enum_rejected():
    """①枚举外值拒:错误含指路 schema 的措辞。"""
    error = runner._approval_lane_error(_approval(approved_by="real-user"), {})
    assert error is not None
    assert "77W/OBS-357" in error and "枚举外值" in error
    assert "real-user" in error
    assert "schemas/media_enrichment_request.schema.json" in error
    # 合法枚举三值均不报「枚举外值」(auto_* 可能报 basis 缺失;user 车道按 77Y
    # 口径可能报证据缺失,均不属枚举外值)
    err_user = runner._approval_lane_error(_approval(approval_evidence_sha256=""), {})
    assert err_user is None or "枚举外值" not in err_user
    for lane in ("auto_rule", "auto_approve"):
        error = runner._approval_lane_error(
            _approval(approved_by=lane, approval_evidence_sha256=None), {})
        assert error is None or "枚举外值" not in error


def test_77w_auto_rule_without_basis_rejected():
    """②auto_rule 无 basis 拒;带 basis 依据通过;auto_approve 同口径。"""
    error = runner._approval_lane_error(
        _approval(approved_by="auto_rule", approval_evidence_sha256=None), {})
    assert error is not None and "basis" in error
    error = runner._approval_lane_error(
        _approval(approved_by="auto_approve", basis="  "), {})
    assert error is not None and "basis" in error
    assert runner._approval_lane_error(
        _approval(approved_by="auto_rule", basis="76R/OBS-289"), {}) is None
    assert runner._approval_lane_error(
        _approval(approved_by="auto_approve",
                  basis="04 合同 copyright_policy 节"), {}) is None


def test_77w_user_lane_evidence_gate():
    """③user 无证据拒 / 有 user_images 证据(既有通道)通过。
    77Y/OBS-371:圆形证据封堵——approval_evidence_sha256 非空即过分支作废;
    user_action 三要素为新增合法通道。"""
    # 无证据:无 user_images 且 approval 不带任何用户动作工件 → 拒(77Y 文案)
    error = runner._approval_lane_error(
        _approval(approval_evidence_sha256=""), {})
    assert error is not None and "user 车道需用户真实动作工件" in error
    assert "77Y/OBS-371" in error and "77W/OBS-357" in error
    # 有 user_images 证据(source_url 命中既有通道)→ 通过
    request = {"user_images": [{"url": "https://img.example.test/1.png",
                                "source_url": "https://www.example-source.test/a"}]}
    assert runner._approval_lane_error(
        _approval(approval_evidence_sha256=""), request) is None
    # 有 user_images 证据(material_id 命中既有通道)→ 通过
    request = {"user_images": [{"url": "https://img.example.test/1.png",
                                "material_id": "M-001"}]}
    assert runner._approval_lane_error(
        _approval(approval_evidence_sha256=""), request) is None
    # 77Y/OBS-371:圆形证据拒——仅 pipeline 自产 approval_evidence_sha256,无
    # user_images/user_action → 拒(pipeline 自产 sha 不算用户动作证据)
    error = runner._approval_lane_error(_approval(), {})
    assert error is not None and "77Y/OBS-371" in error
    # user_action 三要素齐(user/action=approved/at 为 ISO)→ 通过
    assert runner._approval_lane_error(_approval(
        approval_evidence_sha256="",
        user_action={"user": " operator ", "action": "approved",
                     "at": "2026-09-05T12:00:00Z"}), {}) is None


# ── OBS-359:supplemental permalink 通道(77W 规格 D 测试 +2)──────────

def _permalink_lane_check(tmp_path: Path, material: dict) -> dict:
    manifest_path = tmp_path / "media_manifest.json"
    request_path = tmp_path / "media_request.json"
    article = tmp_path / "final_article.md"
    article.write_text("# 77W\n\n正文。\n", encoding="utf-8")
    manifest_path.write_text(json.dumps({"schema_version": "1.0"}),
                             encoding="utf-8")
    request_path.write_text(json.dumps(
        {"article": {"path": "final_article.md", "sha256": "a" * 64},
         "materials": [material]}, ensure_ascii=False), encoding="utf-8")
    report = validate_manifest(str(manifest_path), str(request_path))
    return next(c for c in report["checks"]
                if c["check"] == "REQUEST_MATERIAL_PERMALINK_LANE")


def test_77w_supplemental_null_permalink_passes(tmp_path):
    """①supplemental+permalink=null 通过(无站内页不猜不填)。"""
    check = _permalink_lane_check(tmp_path, {
        "material_id": "M-SUP", "aihot_permalink": None,
        "source_url": "https://huggingface.co/blog/a", "title": "官方博客",
        "selected_claim_ids": [], "provenance": "supplemental",
    })
    assert check["status"] == "PASS", check["detail"]


def test_77w_supplemental_offsite_permalink_rejected(tmp_path):
    """②supplemental+permalink=外站构造填充拒,错误指路应填 null。"""
    check = _permalink_lane_check(tmp_path, {
        "material_id": "M-SUP", "aihot_permalink": "https://huggingface.co/blog",
        "source_url": "https://huggingface.co/blog/a", "title": "官方博客",
        "selected_claim_ids": [], "provenance": "supplemental",
    })
    assert check["status"] == "FAIL"
    assert "supplemental 无站内页应填 null" in check["detail"]
