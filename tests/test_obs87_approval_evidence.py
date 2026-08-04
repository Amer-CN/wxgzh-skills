"""档61 OBS-87:批准信息链闸门测试。

覆盖:
1. claim 派生文本检测(placement_planner L67-68 模式:alt=ct[:60], caption=图：ct[:40])
2. 内容描述评估:派生/空/不可验证/可验证 四态
3. 六张真实资产回归夹具:全部「内容不明」+ 页面位置指向汽车/机票章节,全部不可批准
4. ★反向验证:档50 对 A-109 的「内容适配性」批准在新闸门下必须被拦
5. 旧批准合同(AP-…-001/002 形态,无 approval_readiness_sha256)自动失效
6. rejected 资产(A-107/A-108 真实样本)不得写入/消费批准合同
7. 有完整字段的资产正常放行
8. 渲染 alt 路径不受影响(readiness 构建不修改 manifest/bindings)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from wxgzh_pipeline import producers as PR
from wxgzh_pipeline import approval_evidence as AE

FIX = Path(__file__).parent / "fixtures" / "obs87"
CLAIM_TEXTS = json.loads((FIX / "claims.json").read_text(encoding="utf-8"))["claim_texts"]
FIX_MANIFEST = json.loads((FIX / "manifest.json").read_text(encoding="utf-8"))
PAGE_SECTIONS = json.loads((FIX / "page_sections.json").read_text(encoding="utf-8"))
SIX_IDS = ["A-109", "A-110", "A-111", "A-112", "A-113", "A-114"]


def _asset(aid: str) -> dict:
    return next(a for a in FIX_MANIFEST["assets"] if a["asset_id"] == aid)


def _synthetic_ithome_html() -> str:
    """由冻结的页面位置映射构造最小 HTML:每个 h2 后跟其图片(与真实 DOM 文档序一致)。"""
    parts = ["<html><head><title>IT 早报</title></head><body>"]
    order = ["A-113", "A-114", "A-109", "A-110", "A-111", "A-112"]
    for aid in order:
        asset = _asset(aid)
        url = asset["resolved_original_url"]
        heading = PAGE_SECTIONS[url]["heading"]
        parts.append(f"<h2>{heading}</h2>")
        parts.append(f'<img srcset="{url} 800w" src="{url}">')
    parts.append("</body></html>")
    return "".join(parts)


def _write_readiness(tmp_path: Path, readiness: dict) -> Path:
    p = tmp_path / "media_enrichment" / "approval_readiness.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(readiness, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _build_fixture_readiness(tmp_path: Path) -> tuple[dict, Path]:
    rd = tmp_path / "run"
    (rd / "media_enrichment" / "discover").mkdir(parents=True)
    (rd / "media_enrichment" / "discover" / "media_manifest.json").write_text(
        json.dumps(FIX_MANIFEST, ensure_ascii=False), encoding="utf-8")
    readiness = AE.build_approval_readiness(
        rd, claim_texts=CLAIM_TEXTS, html_provider=lambda url: _synthetic_ithome_html())
    rp = _write_readiness(rd, readiness)
    return readiness, rp


# ── 1. 派生检测 ──────────────────────────────────────────────

def test_claim_derived_detection_exact_patterns():
    ct = CLAIM_TEXTS[[i for i, t in enumerate(CLAIM_TEXTS) if t.startswith("OpenAI 于 7 月 31 日")][0]]
    # alt == claim_text[:60](placement_planner L67-68 模式)
    assert AE.is_claim_derived_text(ct[:60], None, CLAIM_TEXTS) is True
    # caption == "图：" + claim_text[:40]
    assert AE.is_claim_derived_text(None, f"图：{ct[:40]}", CLAIM_TEXTS) is True
    # 与任何 claim 无关的文本不是派生
    assert AE.is_claim_derived_text("一辆深色 SUV 的夜景照片", None, CLAIM_TEXTS) is False
    assert AE.is_claim_derived_text(None, None, CLAIM_TEXTS) is False


def test_six_real_assets_alt_is_claim_derived():
    # 档60 取证:六张图 alt_text 全部等于 C-06 claim 前缀
    for aid in SIX_IDS:
        asset = _asset(aid)
        assert AE.is_claim_derived_text(
            asset["alt_text"], asset["caption"], CLAIM_TEXTS) is True, aid


# ── 2. 内容评估四态 ──────────────────────────────────────────

def test_assess_content_states():
    ct = CLAIM_TEXTS[0]
    assert AE.assess_content({"alt_text": ct[:60]}, CLAIM_TEXTS)["kind"] == "claim_derived"
    assert AE.assess_content({"alt_text": "", "caption": ""}, CLAIM_TEXTS)["kind"] == "empty"
    assert AE.assess_content({"alt_text": "一些无法验证来源的文本"}, CLAIM_TEXTS)["kind"] == "unverifiable"
    good = {"content_description": "小米 SUV 夜间实拍照片",
            "content_description_source": "page_alt"}
    assert AE.assess_content(good, CLAIM_TEXTS)["kind"] == "verified"
    # content_description 本身是 claim 派生 -> 仍判派生,不放行
    bad = {"content_description": ct[:60], "content_description_source": "page_alt"}
    assert AE.assess_content(bad, CLAIM_TEXTS)["kind"] == "claim_derived"
    # 来源字段无效 -> 不可验证
    no_src = {"content_description": "任意文本", "content_description_source": "invented"}
    assert AE.assess_content(no_src, CLAIM_TEXTS)["kind"] == "unverifiable"


# ── 3. 六张真实资产:内容不明 + 位置指向汽车章节 + 全部不可批准 ──

def test_six_real_assets_blocked_with_true_labels(tmp_path):
    readiness, _ = _build_fixture_readiness(tmp_path)
    by_id = {r["asset_id"]: r for r in readiness["assets"]}
    assert readiness["summary"]["total"] >= 6
    assert readiness["summary"]["approvable"] == 0
    for aid in SIX_IDS:
        rec = by_id[aid]
        assert rec["content"]["kind"] == "claim_derived", aid
        assert "内容不明" in rec["content"]["description"], aid
        assert rec["page_position"]["known"] is True, aid
        assert rec["approvable"] is False, aid
        assert any("缺少可验证内容描述" in b for b in rec["approvable_blockers"]), aid
    # 位置必须指向真实章节:四张电车图 + 机票图,而不是文章主题章节
    assert "小米澎程 N90 Max" in by_id["A-109"]["page_position"]["heading"]
    assert "比亚迪大汉" in by_id["A-110"]["page_position"]["heading"]
    assert "比亚迪日本海獭" in by_id["A-111"]["page_position"]["heading"]
    assert "特斯拉全球第 1000 万辆电动车" in by_id["A-112"]["page_position"]["heading"]
    assert "OpenAI 下调 GPT-5.6 Luna" in by_id["A-113"]["page_position"]["heading"]
    assert "携程" in by_id["A-114"]["page_position"]["heading"]


# ── 4. ★反向验证:档50 式批准必须被拦 ────────────────────────

def test_reverse_validation_block_obs50_style_approval(tmp_path):
    """档50 曾以「alt_text(claim 派生)= 内容适配性」批准 A-109。新闸门必须拦下。"""
    readiness, rp = _build_fixture_readiness(tmp_path)
    approvals = [{
        "asset_id": "A-109",
        "approval_readiness_sha256": PR.sha256_file(rp),
    }]
    with pytest.raises(AE.ApprovalEvidenceError) as exc:
        AE.enforce_approval_readiness(rp, readiness, approvals)
    msg = str(exc.value)
    assert "A-109" in msg and "not approvable" in msg
    assert "缺少可验证内容描述(claim_derived)" in msg


# ── 5. 旧合同自动失效 ────────────────────────────────────────

def test_old_contract_without_readiness_ref_invalidated(tmp_path):
    readiness, rp = _build_fixture_readiness(tmp_path)
    # AP-20260803T194207-… 形态:无 approval_readiness_sha256 字段
    old = [{"asset_id": "A-110", "approval_id": "AP-20260803T194207-INDEPENDENT-REVIEW-001"}]
    with pytest.raises(AE.ApprovalEvidenceError, match="旧批准合同自动失效"):
        AE.enforce_approval_readiness(rp, readiness, old)


def test_stale_readiness_ref_invalidated(tmp_path):
    readiness, rp = _build_fixture_readiness(tmp_path)
    stale = [{"asset_id": "A-113", "approval_readiness_sha256": "f" * 64}]
    with pytest.raises(AE.ApprovalEvidenceError, match="旧批准合同自动失效"):
        AE.enforce_approval_readiness(rp, readiness, stale)


def test_missing_readiness_file_fail_closed(tmp_path):
    readiness, _ = _build_fixture_readiness(tmp_path)
    missing = tmp_path / "nope" / "approval_readiness.json"
    with pytest.raises(AE.ApprovalEvidenceError, match="approval_readiness.json missing"):
        AE.enforce_approval_readiness(missing, readiness, [])


# ── 6. rejected 资产不得写入/消费批准合同 ────────────────────

def test_rejected_assets_never_approvable(tmp_path):
    """A-107/A-108 真实样本:即使尺寸达标(避开 OBS-82),decision=rejected 仍被拦。"""
    readiness, rp = _build_fixture_readiness(tmp_path)
    by_id = {r["asset_id"]: r for r in readiness["assets"]}
    assert "A-107" in by_id and "A-108" in by_id
    for aid in ("A-107", "A-108"):
        rec = by_id[aid]
        assert rec["approvable"] is False, aid
        assert any("decision=rejected" in b for b in rec["approvable_blockers"]), aid
    approvals = [{"asset_id": "A-107", "approval_readiness_sha256": PR.sha256_file(rp)}]
    with pytest.raises(AE.ApprovalEvidenceError) as exc:
        AE.enforce_approval_readiness(rp, readiness, approvals)
    assert "A-107" in str(exc.value) and "decision=rejected" in str(exc.value)


# ── 7. 完整字段资产正常放行 ──────────────────────────────────

def test_verified_asset_with_position_passes(tmp_path):
    rd = tmp_path / "run"
    d = rd / "media_enrichment" / "discover"
    d.mkdir(parents=True)
    url = "https://img.example.test/car-photo.jpg"
    good_asset = {
        "asset_id": "A-900", "decision": "review_required",
        "source_page_url": "https://example.test/page",
        "resolved_original_url": url,
        "content_description": "小米 SUV 夜间实拍照片", "content_description_source": "page_alt",
    }
    manifest = {"schema_version": "1.0", "run_id": "test", "assets": [good_asset]}
    (d / "media_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    html = f'<html><body><h2>小米汽车发布会</h2><img src="{url}"></body></html>'
    readiness = AE.build_approval_readiness(rd, claim_texts=CLAIM_TEXTS,
                                            html_provider=lambda u: html)
    rec = readiness["assets"][0]
    assert rec["content"]["kind"] == "verified"
    assert rec["page_position"] == {"known": True, "heading": "小米汽车发布会", "level": "h2"}
    assert rec["approvable"] is True
    rp = _write_readiness(rd, readiness)
    approvals = [{"asset_id": "A-900", "approval_readiness_sha256": PR.sha256_file(rp)}]
    AE.enforce_approval_readiness(rp, readiness, approvals)  # 不抛异常


def test_position_unknown_blocks_even_with_description(tmp_path):
    rd = tmp_path / "run"
    d = rd / "media_enrichment" / "discover"
    d.mkdir(parents=True)
    good_asset = {
        "asset_id": "A-901", "decision": "review_required",
        "source_page_url": "https://example.test/page",
        "resolved_original_url": "https://img.example.test/x.jpg",
        "content_description": "一张内容描述", "content_description_source": "human",
    }
    manifest = {"schema_version": "1.0", "assets": [good_asset]}
    (d / "media_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    # html_provider 返回 None -> 位置未知 -> 不得进入批准点(不降级)
    readiness = AE.build_approval_readiness(rd, claim_texts=CLAIM_TEXTS,
                                            html_provider=lambda u: None)
    rec = readiness["assets"][0]
    assert rec["page_position"]["known"] is False
    assert rec["approvable"] is False
    assert any("页面位置未知" in b for b in rec["approvable_blockers"])


# ── 8. 渲染 alt 不受影响 ─────────────────────────────────────

def test_readiness_build_never_mutates_run_artifacts(tmp_path):
    rd = tmp_path / "run"
    d = rd / "media_enrichment" / "discover"
    d.mkdir(parents=True)
    manifest_bytes = json.dumps(FIX_MANIFEST, ensure_ascii=False, indent=2).encode("utf-8")
    (d / "media_manifest.json").write_bytes(manifest_bytes)
    (d / "article_image_bindings.json").write_text(
        json.dumps({"body_images": [{"asset_id": "A-109", "alt_text": "渲染用 alt(claim 派生)"}]}),
        encoding="utf-8")
    bindings_before = (d / "article_image_bindings.json").read_bytes()
    AE.build_approval_readiness(rd, claim_texts=CLAIM_TEXTS,
                                html_provider=lambda u: _synthetic_ithome_html())
    assert (d / "media_manifest.json").read_bytes() == manifest_bytes
    assert (d / "article_image_bindings.json").read_bytes() == bindings_before


# ── 9. 取不到 manifest / registry 即 FAIL_CLOSED ─────────────

def test_missing_manifest_fail_closed(tmp_path):
    with pytest.raises(AE.ApprovalEvidenceError, match="discover media_manifest.json missing"):
        AE.build_approval_readiness(tmp_path, claim_texts=CLAIM_TEXTS,
                                    html_provider=lambda u: None)


def test_missing_registry_fail_closed(tmp_path):
    rd = tmp_path / "run"
    d = rd / "media_enrichment" / "discover"
    d.mkdir(parents=True)
    (d / "media_manifest.json").write_text(json.dumps({"assets": []}), encoding="utf-8")
    with pytest.raises(AE.ApprovalEvidenceError, match="canonical_claim_registry.json missing"):
        AE.build_approval_readiness(rd, html_provider=lambda u: None)


# ── 10. 与 OBS-82 预检并存(producers 接线可见) ───────────────

def test_wiring_visible_in_producers():
    assert PR.build_approval_readiness is AE.build_approval_readiness
    assert PR.enforce_approval_readiness is AE.enforce_approval_readiness
    assert PR.ApprovalEvidenceError is AE.ApprovalEvidenceError
