"""77AD/OBS-381:审批台账机械回写封堵 + 手填行为留痕。

覆盖（全部零网络零微信、进程内跑 main、不开子进程）:
1. 14j153 形状重放:2 条手填 basis=True(auto_rule) → 落账
   copyright_approval.json 全为机械值 False + provenance 标记；manifest
   reasons 含机械值与 `basis regenerated mechanically`；warnings 含
   hand_filled_basis_ignored=2；exit 0。
2. 伪造机械标记:basis_provenance 不可信 → 拒收并指路 77AD/OBS-381；
   落账文件不被改写。
3. 机械值为 None(approvable=false):记账 error 走 77W fail-fast，该资产
   不落账（落账文件保持手填原值），exit 1。
4. 回写 helper:缺失文件/损坏文件/无对应记录 → False；正常回写只动
   basis/basis_provenance 两键。
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
sys.path.insert(0, str(SKILL_ROOT / "src"))

import run_media_enrichment as runner  # noqa: E402
from media_enrichment.asset_approval import (  # noqa: E402
    freeze_discovery_manifest,
    stable_asset_identity,
    write_discovery_manifest,
)
from media_enrichment.manifest_builder import AssetRecord  # noqa: E402
from PIL import Image  # noqa: E402

# 14j153 落账文件原形（逐字形状）：手填 True + 伪装机械尾缀。
HAND_TRUE_14J153 = (
    "auto_rule lane(77Y/OBS-367): 04_media_enrichment.yaml "
    "COPYRIGHT_POLICY=ALLOW_UNLESS_EXPLICITLY_PROHIBITED + "
    "USER_BLANKET_APPROVAL=True + PER_IMAGE_MANUAL_REVIEW_REQUIRED=False; "
    "approval_readiness.approvable=true; 分类器=review_required; 域名非水印高危——"
    "机械 basis 由 run_media_enrichment 按 04 合同实时值重生成入账"
    "（77Y/OBS-366，本字段手填值将被忽略）"
)

DOMAIN = "https://www.example-source.test"
CONFIG = {
    "network_mode": "offline_fixture",
    "upload_mode": "wechat_audit",
    "min_width": 480,
    "min_height": 200,
    "domain_blacklist": [],
    "max_images_per_material": 8,
    "max_total_images": 8,
}


def _png(path: Path, color=(11, 99, 177)) -> str:
    Image.new("RGB", (900, 600), color).save(path, "PNG")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _frozen_assets(png_shas):
    assets = []
    for i, (aid, sha) in enumerate(png_shas):
        mid = f"mat-ad-{i + 1}"
        src_page = f"{DOMAIN}/a{i + 1}"
        resolved = f"{DOMAIN}/a{i + 1}.png"
        assets.append({
            "asset_id": aid,
            "asset_origin": "source",
            "material_id": mid,
            "source_page_url": src_page,
            "resolved_original_url": resolved,
            "asset_sha256": sha,
            "asset_identity_sha256": stable_asset_identity(
                mid, src_page, resolved, sha),
        })
    return assets


def _sibling_assets(frozen_assets, png_by_aid):
    out = []
    for rec in frozen_assets:
        png = png_by_aid[rec["asset_id"]]
        mid = rec["material_id"]
        cid = "C-" + mid.split("mat-ad-")[-1]
        out.append(AssetRecord(
            asset_id=rec["asset_id"], asset_origin="source",
            material_ids=[mid], claim_ids=[cid],
            source_page_url=rec["source_page_url"],
            discovered_url=rec["resolved_original_url"],
            resolved_original_url=rec["resolved_original_url"],
            extraction_method="img.src", local_path=str(png),
            decision="review_required", copyright_status="unknown",
            reasons=[], content_description="77AD 夹具图",
            content_description_source="page_alt",
        ).to_dict())
    return out


def _approval_record(frozen, manifest_sha, basis=HAND_TRUE_14J153, **overrides):
    record = {
        "approval_id": f"AP-{frozen['asset_id']}",
        "approved_scope": "single_asset",
        "approved_at": "2026-09-11T19:27:47Z",
        "approved_by": "auto_rule",
        "approval_evidence_sha256": "e" * 64,
        "asset_id": frozen["asset_id"],
        "material_id": frozen["material_id"],
        "source_page_url": frozen["source_page_url"],
        "resolved_original_url": frozen["resolved_original_url"],
        "asset_sha256": frozen["asset_sha256"],
        "asset_identity_sha256": frozen["asset_identity_sha256"],
        "discovery_manifest_sha256": manifest_sha,
        "basis": basis,
    }
    record.update(overrides)
    return record


def _build(tmp_path: Path, approvable=True, approval_overrides=None,
           n=2):
    disc = tmp_path / "disc"
    (disc / "images").mkdir(parents=True)
    png_by_aid = {}
    for i in range(n):
        aid = f"A-10{i + 1}"
        png = disc / "images" / f"ad-{i + 1}.png"
        png_by_aid[aid] = png
        _png(png, (11 + i, 99, 177))
    frozen_assets = _frozen_assets(
        [(aid, hashlib.sha256(png_by_aid[aid].read_bytes()).hexdigest())
         for aid in sorted(png_by_aid)])
    frozen = freeze_discovery_manifest(frozen_assets)
    write_discovery_manifest(disc / "asset_discovery_manifest.json", frozen)
    (disc / "media_manifest.json").write_text(json.dumps(
        {"assets": _sibling_assets(frozen["assets"], png_by_aid)},
        ensure_ascii=False), encoding="utf-8")

    article = tmp_path / "final_article.md"
    article.write_text("# 77AD\n\n正文段落。\n", encoding="utf-8")
    request = {
        "schema_version": "1.0", "run_id": "hf77ad-replay",
        "article": {"path": str(article),
                   "sha256": hashlib.sha256(
                       article.read_bytes()).hexdigest()},
        "materials": [{"material_id": rec["material_id"],
                       "aihot_permalink": f"{DOMAIN}/items/ad",
                       "source_url": rec["source_page_url"],
                       "title": "77AD 素材",
                       "selected_claim_ids": ["C-" + rec["material_id"].split("mat-ad-")[-1]],
                       "copyright_review": {"status": "unknown"}}
                      for rec in frozen["assets"]],
        "claims": [{"claim_id": "C-" + rec["material_id"].split("mat-ad-")[-1],
                    "claim_text": "77AD D 守卫",
                    "material_id": rec["material_id"],
                    "source_url": rec["source_page_url"],
                    "source_excerpt": "77AD 素材"}
                   for rec in frozen["assets"]],
        "asset_approvals": [
            _approval_record(
                rec, frozen["discovery_manifest_sha256"],
                **(approval_overrides or {}))
            for rec in frozen["assets"]],
        "config": dict(CONFIG),
    }
    req_path = tmp_path / "media_continuation_request.json"
    req_path.write_text(json.dumps(request, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    approval_file = tmp_path / "copyright_approval.json"
    approval_file.write_text(json.dumps(
        {"schema_version": "1.0", "run_id": "hf77ad-replay",
         "discovery_manifest_sha256": frozen["discovery_manifest_sha256"],
         "approval_readiness_sha256": "e" * 64,
         "approvals": request["asset_approvals"]},
        ensure_ascii=False, indent=2), encoding="utf-8")
    (tmp_path / "approval_readiness.json").write_text(json.dumps(
        {"assets": [{"asset_id": rec["asset_id"], "approvable": approvable}
                    for rec in frozen["assets"]]},
        ensure_ascii=False), encoding="utf-8")
    return req_path, disc / "asset_discovery_manifest.json"


def _run_continue(monkeypatch, req_path: Path, frozen_path: Path,
                  out: Path) -> int:
    monkeypatch.setattr(sys, "argv", [
        "run_media_enrichment.py", "--request", str(req_path),
        "--output-dir", str(out), "--phase", "continue",
        "--discovery-manifest", str(frozen_path)])
    with pytest.raises(SystemExit) as exc:
        runner.main()
    return exc.value.code


def test_77ad_replay_hand_true_rewritten_to_mechanical_false(
        tmp_path, monkeypatch):
    """①14j153 形状重放:手填 True → 落账文件全机械值 False + 标记；
    warnings 计数=2；exit 0。"""
    req_path, frozen_path = _build(tmp_path)
    out = tmp_path / "out-continue"
    code = _run_continue(monkeypatch, req_path, frozen_path, out)
    assert code == 0
    landed = json.loads(
        (tmp_path / "copyright_approval.json").read_text(encoding="utf-8"))
    assert len(landed["approvals"]) == 2
    for rec in landed["approvals"]:
        assert "USER_BLANKET_APPROVAL=False" in rec["basis"]
        assert "USER_BLANKET_APPROVAL=True" not in rec["basis"]
        assert rec["basis_provenance"] == runner.MECHANICAL_BASIS_PROVENANCE
        assert rec["asset_id"] in ("A-101", "A-102")
    manifest = json.loads(
        (out / "media_manifest.json").read_text(encoding="utf-8"))
    assert any("hand_filled_basis_ignored=2" in w
               and "77AD/OBS-381" in w for w in manifest["warnings"])
    for asset in manifest["assets"]:
        assert "basis regenerated mechanically (77Y/OBS-366)" in asset["reasons"]
        assert any("USER_BLANKET_APPROVAL=False" in r
                   for r in asset["reasons"])


def test_77ad_forged_provenance_rejected(tmp_path, monkeypatch):
    """②伪造机械标记 → 拒收并指路 77AD/OBS-381；落账文件不被改写。"""
    req_path, frozen_path = _build(
        tmp_path, approval_overrides={
            "basis_provenance": "hand forged mechanical"})
    out = tmp_path / "out-continue"
    code = _run_continue(monkeypatch, req_path, frozen_path, out)
    assert code != 0
    manifest = json.loads(
        (out / "media_manifest.json").read_text(encoding="utf-8"))
    assert any("77AD/OBS-381" in e for e in manifest["errors"])
    landed = json.loads(
        (tmp_path / "copyright_approval.json").read_text(encoding="utf-8"))
    for rec in landed["approvals"]:
        assert "USER_BLANKET_APPROVAL=True" in rec["basis"]
        assert rec["basis_provenance"] == "hand forged mechanical"


def test_77ad_mechanical_none_fail_fast_no_ledger(tmp_path, monkeypatch):
    """③机械值为 None(approvable=false):记账 error 走 77W fail-fast；
    落账文件保持手填原值（不落账），exit 1。"""
    req_path, frozen_path = _build(tmp_path, approvable=False)
    out = tmp_path / "out-continue"
    code = _run_continue(monkeypatch, req_path, frozen_path, out)
    assert code != 0
    manifest = json.loads(
        (out / "media_manifest.json").read_text(encoding="utf-8"))
    assert any("77AD/OBS-381" in e and "fail-fast" in e
               for e in manifest["errors"])
    landed = json.loads(
        (tmp_path / "copyright_approval.json").read_text(encoding="utf-8"))
    for rec in landed["approvals"]:
        assert "USER_BLANKET_APPROVAL=True" in rec["basis"]
        assert "basis_provenance" not in rec


def test_77ad_rewrite_helper_missing_or_broken_file(tmp_path):
    """④回写 helper:文件缺失/损坏/无对应记录 → False；正常回写只动两键。"""
    assert runner._rewrite_approval_basis_file(
        tmp_path / "nope.json", "A-101", "MB") is False
    bad = tmp_path / "bad.json"
    bad.write_text("{oops", encoding="utf-8")
    assert runner._rewrite_approval_basis_file(bad, "A-101", "MB") is False
    target = tmp_path / "approval.json"
    target.write_text(json.dumps(
        {"approvals": [
            {"asset_id": "A-101", "approved_scope": "single_asset",
             "approved_by": "auto_rule", "basis": "HAND",
             "material_id": "mat-ad", "note": "keep-me"},
            {"asset_id": "A-999", "approved_scope": "single_asset",
             "approved_by": "auto_rule", "basis": "HAND"}]},
        ensure_ascii=False), encoding="utf-8")
    assert runner._rewrite_approval_basis_file(
        target, "A-101", "MECH") is True
    data = json.loads(target.read_text(encoding="utf-8"))
    rec = data["approvals"][0]
    assert rec["basis"] == "MECH"
    assert rec["basis_provenance"] == runner.MECHANICAL_BASIS_PROVENANCE
    assert rec["material_id"] == "mat-ad" and rec["note"] == "keep-me"
    assert data["approvals"][1]["basis"] == "HAND"
    assert runner._rewrite_approval_basis_file(
        target, "A-404", "MECH") is False
