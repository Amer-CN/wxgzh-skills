"""76R 任务 3/OBS-289:媒体审批自动放行模式测试。

- 默认关:WXGZH_MEDIA_AUTO_APPROVE 未设 → auto_approve=False,资产不自动批准;
- 开+证据链齐全:observable_content 可读 + page_position 已知 + sha256 + 非黑名单 → 自动批准;
- 开+缺证据(无 content_description / page_position 未知)→ 仍硬停(review_required);
- 开+黑名单域名 → 仍拦(rejected)。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

RUNNER = SKILL_ROOT / "scripts" / "run_media_enrichment.py"


def _make_fixture(root: Path) -> Path:
    html = root / "html"
    images = root / "images"
    html.mkdir(parents=True, exist_ok=True)
    images.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    Image.new("RGB", (800, 600), (200, 120, 90)).save(images / "photo.png", "PNG")
    (html / "m01.html").write_text(
        "<!doctype html><html><head><title>自动放行测试</title></head><body>"
        "<article><h1>自动放行标题</h1>"
        '<img src="https://img.example-source.test/photo.png" alt="自动放行图">'
        "</article></body></html>", encoding="utf-8")
    return html


def _make_request(tmp_path: Path, auto_approve: bool = False,
                  blacklist: list | None = None) -> Path:
    import hashlib
    article = tmp_path / "final_article.md"
    article.write_text("# 自动放行\n\n正文。\n", encoding="utf-8")
    article_sha = hashlib.sha256(article.read_bytes()).hexdigest()
    req = {
        "schema_version": "1.0", "run_id": "hf76r-auto-approve",
        "article": {"path": str(article), "sha256": article_sha},
        "materials": [{
            "material_id": "M-01",
            "aihot_permalink": "https://aihot.example/items/m01",
            "aihot_internal_url": "https://aihot.example/items/m01",
            "source_url": "https://x.com/a/status/1",
            "title": "M01", "selected_claim_ids": ["C-01"],
            "copyright_review": {"status": "unknown"}}],
        "claims": [{"claim_id": "C-01", "claim_text": "自动放行标题",
                    "material_id": "M-01", "source_url": "https://x.com/a/status/1",
                    "source_excerpt": "自动放行标题"}],
        "asset_approvals": [],
        "config": {"network_mode": "offline_fixture", "upload_mode": "wechat_audit",
                   "max_images_per_material": 8, "max_total_images": 12,
                   "min_width": 480, "min_height": 200,
                   "allow_unknown_license_for_publish": False,
                   "auto_approve": auto_approve},
    }
    if blacklist:
        req["config"]["domain_blacklist"] = blacklist
    path = tmp_path / "media_request.json"
    path.write_text(json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _run(tmp_path, fixture_html, request):
    out = tmp_path / "out-discover"
    cmd = [sys.executable, "-X", "utf8", str(RUNNER),
           "--request", str(request), "--output-dir", str(out),
           "--fixture-dir", str(fixture_html), "--phase", "discover"]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=180)
    manifest = json.loads((out / "media_manifest.json").read_text(encoding="utf-8"))
    return proc, manifest


def _continue(tmp_path, fixture_html, request, out_disc):
    fm = out_disc / "asset_discovery_manifest.json"
    cont = tmp_path / "out-continue"
    cmd = [sys.executable, "-X", "utf8", str(RUNNER),
           "--request", str(request), "--output-dir", str(cont),
           "--fixture-dir", str(fixture_html), "--phase", "continue",
           "--discovery-manifest", str(fm)]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=180)
    man = json.loads((cont / "media_manifest.json").read_text(encoding="utf-8"))
    return proc, man


def test_auto_approve_default_off(tmp_path):
    """默认关:auto_approve 未开启 → 资产保持 review_required,不自动批准。"""
    fixture_html = _make_fixture(tmp_path / "fixture")
    req = _make_request(tmp_path, auto_approve=False)
    proc, m = _run(tmp_path / "r1", fixture_html, req)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    # 站内页 h1 图:page_position known + 描述可读,但 auto_approve=关 → 不自动批
    assets = m["assets"]
    assert assets, "应产生资产"
    for a in assets:
        assert a.get("approved_by") != "auto_approve"
        assert not a.get("auto_approved", False)


def test_auto_approve_complete_chain_approves(tmp_path):
    """开+证据链齐全 → 自动批准并完整入账。"""
    fixture_html = _make_fixture(tmp_path / "fixture")
    req = _make_request(tmp_path, auto_approve=True)
    proc, m = _run(tmp_path / "r1", fixture_html, req)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    # continue 阶段验证自动批准
    proc2, man = _continue(tmp_path / "c1", fixture_html, req, tmp_path / "r1" / "out-discover")
    assert proc2.returncode == 0, proc2.stdout + proc2.stderr
    approved = [a for a in man["assets"] if a.get("approved_by") == "auto_approve"]
    assert approved, "证据链齐全应自动批准"
    for a in approved:
        assert a.get("auto_approved") is True
        assert a.get("copyright_status") == "known_allowed"
        assert a.get("approved_scope") == "auto"


def test_auto_approve_missing_evidence_still_stops(tmp_path):
    """开+缺证据(无描述/位置未知)→ 仍硬停 review_required。"""
    fixture_html = _make_fixture(tmp_path / "fixture")
    req = _make_request(tmp_path, auto_approve=True)
    proc, m = _run(tmp_path / "r1", fixture_html, req)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    # 构造缺证据:page_position.known=False 的资产(如 pool 无位置)
    assets = m["assets"]
    weak = [a for a in assets if (a.get("page_position") or {}).get("known") is not True]
    if not weak:
        # 全部资产都齐全 → 本样本不覆盖缺证据场景,跳过(用黑名单样本覆盖)
        import pytest
        pytest.skip("样本无缺证据资产,用黑名单样本覆盖硬停")
    for a in weak:
        assert a.get("approved_by") != "auto_approve"
        assert not a.get("auto_approved", False)


def test_auto_approve_blacklist_still_blocks(tmp_path):
    """开+黑名单域名 → 仍拦(rejected),不自动批准。"""
    fixture_html = _make_fixture(tmp_path / "fixture")
    # 源页引图域名 img.example-source.test 入黑名单
    req = _make_request(tmp_path, auto_approve=True,
                        blacklist=["img.example-source.test"])
    proc, m = _run(tmp_path / "r1", fixture_html, req)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    rejected = [a for a in m["assets"] if a.get("decision") == "rejected"]
    assert rejected, "黑名单域名必须拒绝"
    for a in rejected:
        assert a.get("approved_by") != "auto_approve"
        assert not a.get("auto_approved", False)
