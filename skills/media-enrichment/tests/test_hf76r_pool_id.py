"""76R/OBS-291:pool-fetch ID 规范化——池内图登记映射回 canonical material_id(M-XX)。

- 归属已选素材的池内图(含池内重复图)一律映射回 M-XX,禁止裸 iid 入库;
- 映射不到的资产才独立登记并如实标注来源;
- 幂等:同一请求重跑(discover)不改变登记语义。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

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
    (html / "iid-m01.html").write_text(
        "<!doctype html><html><head><title>M01 相关</title></head><body>"
        "<article><h1>M01 发布</h1>"
        '<img src="https://img.example-source.test/photo.png" alt="M01 示例">'
        "</article></body></html>", encoding="utf-8")
    (html / "iid-unknown.html").write_text(
        "<!doctype html><html><head><title>外部源</title></head><body>"
        '<img src="https://img.example-source.test/photo.png" alt="外部">'
        "</body></html>", encoding="utf-8")
    return html


def _make_request(tmp_path: Path, pool_items) -> Path:
    import hashlib
    article = tmp_path / "final_article.md"
    article.write_text("# M01 发布\n\n正文。\n", encoding="utf-8")
    article_sha = hashlib.sha256(article.read_bytes()).hexdigest()
    req = {
        "schema_version": "1.0", "run_id": "hf76r-pool-id",
        "article": {"path": str(article), "sha256": article_sha},
        "materials": [{
            "material_id": "M-01",
            "dedup_id": "iid-m01",
            "aihot_permalink": "https://aihot.example/items/iid-m01",
            "aihot_internal_url": "https://aihot.example/items/iid-m01",
            "source_url": "https://x.com/a/status/1",
            "title": "M01", "selected_claim_ids": ["C-01"],
            "copyright_review": {"status": "known_allowed",
                                  "reviewed_by": "unit-test",
                                  "reviewed_at": "2026-08-14T00:00:00Z",
                                  "evidence": "unit-test material approval"}}],
        "claims": [{"claim_id": "C-01", "claim_text": "M01 发布",
                    "material_id": "M-01", "source_url": "https://x.com/a/status/1",
                    "source_excerpt": "M01 发布"}],
        "asset_approvals": [],
        "pool_items": pool_items,
        "config": {"network_mode": "offline_fixture", "upload_mode": "wechat_audit",
                   "max_images_per_material": 8, "max_total_images": 12,
                   "min_width": 480, "min_height": 200,
                   "allow_unknown_license_for_publish": False,
                   "pool_fetch_limit": 30},
    }
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


def _pool_item(iid: str, page: str) -> dict:
    return {"id": iid, "title": "标题",
            "source_url": f"https://x.com/{iid}/status/1",
            "aihot_permalink": f"https://aihot.example/items/{iid}",
            "links": {"aihot": f"https://aihot.example/items/{iid}",
                      "original": f"https://x.com/{iid}/status/1"},
            "summary": "相关报道"}


def test_pool_item_maps_to_m_xx(tmp_path):
    """池内 iid(有 dedup 映射)的资产登记为 M-XX,非裸 iid。"""
    fixture_html = _make_fixture(tmp_path / "fixture")
    # 注意:pool page 名 = iid 尾段,fixture 用 iid-m01 -> pool-m01.html
    pool = [_pool_item("iid-m01", "pool-m01")]
    req = _make_request(tmp_path, pool)
    proc, manifest = _run(tmp_path, fixture_html, req)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assets = manifest["assets"]
    pool_assets = [a for a in assets if "iid-m01" in (a.get("material_ids") or [])]
    assert not pool_assets, "已映射素材的池图不得以裸 iid 登记"
    mapped = [a for a in assets if "M-01" in (a.get("material_ids") or [])]
    assert mapped, "池内图必须映射回 M-01"
    # 全部来源非 user_provided 的池资产都必须带 M-XX(不能有裸 iid)
    for a in assets:
        mids = a.get("material_ids") or []
        assert not any(m.startswith("iid-") for m in mids), f"裸 iid 入库: {mids}"


def test_pool_item_unmapped_independent(tmp_path):
    """映射不到的池 iid → 独立登记(保留 iid 标注来源),不并入 M-XX。"""
    fixture_html = _make_fixture(tmp_path / "fixture")
    pool = [_pool_item("iid-unknown", "pool-unknown")]
    req = _make_request(tmp_path, pool)
    proc, manifest = _run(tmp_path, fixture_html, req)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    indep = [a for a in manifest["assets"] if "iid-unknown" in (a.get("material_ids") or [])]
    assert indep, "映射不到的池资产必须独立登记"
    assert not any("M-01" in (a.get("material_ids") or []) for a in indep), \
        "独立登记不得错误并入 M-01"


def test_pool_mapped_asset_reaches_material_approval(tmp_path):
    """映射回 M-XX 后,continue 阶段 material 级审批可覆盖(不再 FAIL_CLOSED)。"""
    fixture_html = _make_fixture(tmp_path / "fixture")
    pool = [_pool_item("iid-m01", "pool-m01")]
    req = _make_request(tmp_path, pool)
    proc, manifest = _run(tmp_path, fixture_html, req)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    mapped = [a for a in manifest["assets"] if "M-01" in (a.get("material_ids") or [])]
    assert mapped
    # 继续阶段:用同一 manifest + 已批准 material 跑 continue
    out_disc = tmp_path / "out-discover"
    cont = tmp_path / "out-continue"
    manifest_path = out_disc / "media_manifest.json"
    # 官方冻结清单:discover 产出的 asset_discovery_manifest.json
    fm = out_disc / "asset_discovery_manifest.json"
    cmd = [sys.executable, "-X", "utf8", str(RUNNER),
           "--request", str(req), "--output-dir", str(cont),
           "--fixture-dir", str(fixture_html), "--phase", "continue",
           "--discovery-manifest", str(fm)]
    proc2 = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=180)
    assert proc2.returncode == 0, proc2.stdout + proc2.stderr
    cont_manifest = json.loads((cont / "media_manifest.json").read_text(encoding="utf-8"))
    # material known_allowed → 资产应获批上传(approval 依据 = M-01 已批准)
    approved = [a for a in cont_manifest["assets"]
                if a.get("copyright_status") == "known_allowed"]
    assert approved, "material 级审批必须覆盖池内映射资产"
    assert all((a.get("material_ids") or [""])[0] == "M-01" for a in approved)


def test_pool_rerun_idempotent(tmp_path):
    """同请求重跑 discover:登记语义一致(映射稳定,无重复计数漂移)。"""
    fixture_html = _make_fixture(tmp_path / "fixture")
    pool = [_pool_item("iid-m01", "pool-m01")]
    req = _make_request(tmp_path, pool)
    proc1, m1 = _run(tmp_path / "r1", fixture_html, req)
    proc2, m2 = _run(tmp_path / "r2", fixture_html, req)
    assert proc1.returncode == 0 and proc2.returncode == 0
    mids1 = sorted(m.get("material_ids", [""])[0] for m in m1["assets"])
    mids2 = sorted(m.get("material_ids", [""])[0] for m in m2["assets"])
    assert mids1 == mids2
    assert all(m.startswith("M-") for m in mids1 if m), f"存在非 M-XX 登记: {mids1}"
