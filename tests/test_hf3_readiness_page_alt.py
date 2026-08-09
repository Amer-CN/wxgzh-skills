"""档HF-3/OBS-245:OBS-87 内容描述接缝——build_approval_readiness page_alt 提取
+ 尺寸门槛 480x200(用户裁决 2026-08-09)。

场景覆盖(html_provider 注入缝,与 test_obs87 同型):
- 无 content_description + 页面 img 有 alt → verified/page_alt/approvable
- alt 为空 → 仍 blocked(empty)
- alt 与某 claim 前缀吻合 → 仍 blocked(claim_derived,防自证)
- 页面抓取失败(provider 返回 None) → 仍 blocked(fail-closed)
- 资产已有合法 content_description → 不触发提取(行为不变)
- precheck 边界:480x200 过 / 479x200 拦 / 480x199 拦
- request config 含 min_width=480/min_height=200
"""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from wxgzh_pipeline import approval_evidence as AE
from wxgzh_pipeline import producers as PR

CLAIM_TEXTS = ["Qwen3.8-Max于2026年8月3日正式发布",
               "API定价为输入$2/百万token、输出$6/百万token"]


def _asset(aid, url_suffix, heading="测试标题", desc=None):
    return {
        "asset_id": aid,
        "decision": "review_required",
        "source_page_url": "https://example.com/page-" + url_suffix,
        "resolved_original_url": "https://example.com/img-" + url_suffix + ".jpg",
        "page_position": {"heading": heading, "known": True, "level": "h1"},
        "width": 800, "height": 600,
        "content_description": desc,
        "content_description_source": None,
    }


def _write_manifest(run_dir, assets):
    d = run_dir / "media_enrichment" / "discover"
    d.mkdir(parents=True, exist_ok=True)
    (d / "media_manifest.json").write_text(
        json.dumps({"assets": assets}, ensure_ascii=False), encoding="utf-8")


def _readiness(run_dir, provider, claim_texts=None):
    return AE.build_approval_readiness(
        run_dir, claim_texts=claim_texts or CLAIM_TEXTS, html_provider=provider)


def _html_with(alt=None, title=None):
    parts = ['<html><body><h1>测试标题</h1>']
    if alt is not None or title is not None:
        parts.append(f'<img src="https://example.com/img-1.jpg" '
                     f'alt="{alt or ""}" title="{title or ""}">')
    parts.append('</body></html>')
    return "".join(parts)


def test_hf3_page_alt_verified_and_approvable(tmp_path):
    """无 content_description + 页面 img 有 alt → verified/page_alt/approvable。"""
    run_dir = tmp_path / "run"
    _write_manifest(run_dir, [_asset("A-101", "1")])
    rd = _readiness(run_dir, lambda url: _html_with(alt="一张产品发布现场的新闻图片"))
    rec = {r["asset_id"]: r for r in rd["assets"]}["A-101"]
    assert rec["content"] == {"kind": "verified",
                              "description": "一张产品发布现场的新闻图片",
                              "source": "page_alt", "verified": True}
    assert rec["approvable"] is True
    assert rec["approvable_blockers"] == []


def test_hf3_page_alt_empty_stays_blocked(tmp_path):
    """img 无 alt/title → 仍 blocked(empty)。"""
    run_dir = tmp_path / "run"
    _write_manifest(run_dir, [_asset("A-101", "1")])
    rd = _readiness(run_dir, lambda url: _html_with())
    rec = {r["asset_id"]: r for r in rd["assets"]}["A-101"]
    assert rec["content"]["verified"] is False
    assert rec["content"]["kind"] == "empty"
    assert rec["approvable"] is False
    assert "缺少可验证内容描述" in rec["approvable_blockers"][0]


def test_hf3_page_alt_claim_derived_stays_blocked(tmp_path):
    """alt 与某 claim 前缀吻合 → 仍 blocked(claim_derived,防自证)。"""
    run_dir = tmp_path / "run"
    _write_manifest(run_dir, [_asset("A-101", "1")])
    rd = _readiness(run_dir, lambda url: _html_with(alt=CLAIM_TEXTS[0][:60]))
    rec = {r["asset_id"]: r for r in rd["assets"]}["A-101"]
    assert rec["content"]["verified"] is False
    assert rec["content"]["kind"] == "claim_derived"
    assert rec["approvable"] is False


def test_hf3_fetch_failure_stays_blocked(tmp_path):
    """页面抓取失败(provider 返回 None) → 仍 blocked(fail-closed)。"""
    run_dir = tmp_path / "run"
    _write_manifest(run_dir, [_asset("A-101", "1")])
    rd = _readiness(run_dir, lambda url: None)
    rec = {r["asset_id"]: r for r in rd["assets"]}["A-101"]
    assert rec["content"]["verified"] is False
    assert rec["approvable"] is False


def test_hf3_existing_description_skips_extract(tmp_path):
    """资产已有合法 content_description → 不触发提取(行为不变)。"""
    run_dir = tmp_path / "run"
    _write_manifest(run_dir, [_asset("A-101", "1",
                                     desc="人工核验的内容描述",
                                     )])
    # 手动补 source(manifest 里由 discover 写入合法来源)
    manifest_p = run_dir / "media_enrichment" / "discover" / "media_manifest.json"
    m = json.loads(manifest_p.read_text(encoding="utf-8"))
    m["assets"][0]["content_description_source"] = "human"
    manifest_p.write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")

    def _boom(url):
        raise AssertionError(f"provider 不应被调用: {url}")

    rd = _readiness(run_dir, _boom)
    rec = {r["asset_id"]: r for r in rd["assets"]}["A-101"]
    assert rec["content"]["verified"] is True
    assert rec["content"]["source"] == "human"
    assert rec["approvable"] is True


def _precheck_manifest(width, height):
    return {"assets": [{
        "asset_id": "A-1", "width": width, "height": height,
        "decision": "review_required"}]}


def test_hf3_precheck_boundaries(tmp_path):
    """precheck 边界:480x200 过 / 479x200 拦 / 480x199 拦。"""
    run_dir = tmp_path / "run"
    ok = _precheck_manifest(480, 200)
    (run_dir / "media_enrichment" / "discover").mkdir(parents=True, exist_ok=True)
    (run_dir / "media_enrichment" / "discover" / "media_manifest.json").write_text(
        json.dumps(ok), encoding="utf-8")
    pre = PR._approval_precheck(run_dir)
    assert pre["eligible"] == ["A-1"]
    assert pre["excluded"] == []
    assert pre["min_width"] == 480 and pre["min_height"] == 200

    bad_w = _precheck_manifest(479, 200)
    (run_dir / "media_enrichment" / "discover" / "media_manifest.json").write_text(
        json.dumps(bad_w), encoding="utf-8")
    pre = PR._approval_precheck(run_dir)
    assert pre["eligible"] == []
    assert pre["excluded"][0]["reason"] == "dimensions below minimum 480x200"

    bad_h = _precheck_manifest(480, 199)
    (run_dir / "media_enrichment" / "discover" / "media_manifest.json").write_text(
        json.dumps(bad_h), encoding="utf-8")
    pre = PR._approval_precheck(run_dir)
    assert pre["eligible"] == []
    assert pre["excluded"][0]["reason"] == "dimensions below minimum 480x200"


def _build_media_ctx(tmp_path):
    run_dir = tmp_path / "run"
    (run_dir / "super_writer").mkdir(parents=True)
    (run_dir / "super_writer" / "canonical_claim_registry.json").write_text(json.dumps({
        "claims": [{"claim_id": "c-1", "material_id": "mat-1", "claim_text": CLAIM_TEXTS[0]}],
        "materials": [{"material_id": "mat-1", "source_url": "https://example.com/x",
                       "title": "示例材料"}],
    }), encoding="utf-8")
    (run_dir / "aihot").mkdir(parents=True)
    (run_dir / "aihot" / "deduplicated_items.json").write_text(json.dumps({
        "items": [{"id": "mat-1", "title": "示例材料", "source_url": "https://example.com/x"}],
    }), encoding="utf-8")
    (run_dir / "zh_human_writing").mkdir(parents=True)
    (run_dir / "zh_human_writing" / "final_article.md").write_text("# 测试\n", encoding="utf-8")
    sd = run_dir / "media_enrichment"
    sd.mkdir(parents=True)
    ctx = SimpleNamespace(run_dir=str(run_dir), network_mode="integration", env={},
                          discovery={})
    return ctx, sd


def test_hf3_request_config_dimensions(tmp_path):
    """_build_media_request 的 request.config 含 min_width=480/min_height=200。"""
    ctx, sd = _build_media_ctx(tmp_path)
    state = SimpleNamespace(run_id="x", final_article_sha256=None)
    req_p = PR._build_media_request(ctx, sd, state, phase="discover")
    req = json.loads(req_p.read_text(encoding="utf-8"))
    assert req["config"]["min_width"] == 480
    assert req["config"]["min_height"] == 200
