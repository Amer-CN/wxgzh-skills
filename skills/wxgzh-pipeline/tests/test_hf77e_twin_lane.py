"""77E/OBS-314:池道孪生位置继承测试。

同 sha256 且同 material 的孪生,当 canonical(位置已知且可批准)存在时继承
page_position(OBS-296 从文档纪律落到机械层);不同 material 不继承。
"""
from __future__ import annotations

import json
from pathlib import Path

from wxgzh_pipeline import approval_evidence as AE


def _manifest(assets):
    return {"schema_version": "1.0", "discovery_manifest_sha256": "0" * 64,
            "assets": assets}


def _asset(aid, sha, material, pos_known, decision="eligible"):
    a = {"asset_id": aid, "asset_sha256": sha, "perceptual_hash": None,
         "material_id": material, "decision": decision,
         "content_description": f"真实的页面内图片描述 {aid}",
         "content_description_source": "page_alt",
         "resolved_original_url": f"https://src.example/{aid}"}
    if pos_known:
        a["page_position"] = {"known": True, "heading": f"章节{aid}", "level": "h2"}
    else:
        a["page_position"] = {"known": False, "heading": None, "level": None}
    return a


def _build(tmp_path, assets) -> dict:
    rd = tmp_path / "run"
    d = rd / "media_enrichment" / "discover"
    d.mkdir(parents=True)
    (rd / "super_writer").mkdir(parents=True)
    (rd / "super_writer" / "canonical_claim_registry.json").write_text(
        json.dumps({"claims": [{"claim_id": "C-01", "claim_text": "正文主题句。",
                                 "material_id": "M-01", "source_url": "https://s.example/a",
                                 "source_excerpt": "摘录"}],
                    "materials": [{"material_id": "M-01", "dedup_id": "d-1",
                                                  "source_url": "https://s.example/a"},
                                                 {"material_id": "M-02", "dedup_id": "d-2",
                                                  "source_url": "https://s.example/b"}]},
        ensure_ascii=False), encoding="utf-8")
    (d / "media_manifest.json").write_text(
        json.dumps(_manifest(assets), ensure_ascii=False), encoding="utf-8")
    return AE.build_approval_readiness(rd)


def test_pool_twin_inherits_position_from_canonical(tmp_path):
    sha = "aa" * 32
    readiness = _build(tmp_path, [
        _asset("A-001", sha, "M-01", True),
        _asset("A-002", sha, "M-01", False),
    ])
    by_id = {r["asset_id"]: r for r in readiness["assets"]}
    rec = by_id["A-002"]
    assert rec["approvable"] is True, rec["approvable_blockers"]
    assert rec["page_position"]["known"] is True
    assert rec["page_position"].get("inherited_from") == "A-001"
    assert by_id["A-001"]["approvable"] is True


def test_pool_twin_different_material_not_inherited(tmp_path):
    sha = "bb" * 32
    readiness = _build(tmp_path, [
        _asset("A-003", sha, "M-01", True),
        _asset("A-004", sha, "M-02", False),
    ])
    by_id = {r["asset_id"]: r for r in readiness["assets"]}
    rec = by_id["A-004"]
    assert rec["approvable"] is False
    assert "页面位置未知" in rec["approvable_blockers"]
    assert "inherited_from" not in rec["page_position"]
