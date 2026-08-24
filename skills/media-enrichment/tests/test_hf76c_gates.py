"""档76C/OBS-248/254/255 验收测试:域名黑名单 + discover 扩池 + 用户供图注入。

- 黑名单:config.domain_blacklist 命中即拒(ithome.com 类);非命中放行。
- user_images:user_provided 资产免版权审批,decision 依尺寸/质量。
- pool_items:全池潜力源扩池扫描,站内页(h1)候选可进。
"""
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
    # 站内页(h1,单篇):直出 HTML,图片可提取;URL 尾段=pool-001 -> pool-001.html
    (html / "pool-001.html").write_text(
        "<!doctype html><html><head><title>Seedance 相关报道</title></head>"
        "<body><article><h1>Seedance 视频模型正式发布</h1>"
        '<img src="https://img.example-source.test/photo.png" alt="Seedance 示例">'
        "</article></body></html>",
        encoding="utf-8")
    (html / "x-page.html").write_text(
        "<!doctype html><html><head><title>Post</title></head><body>"
        '<img src="https://img.example-source.test/photo.png" alt="x">'
        "</body></html>",
        encoding="utf-8")
    return html


def _make_request(tmp_path: Path, extra_config=None, user_images=None,
                  pool_items=None) -> Path:
    import hashlib
    article = tmp_path / "final_article.md"
    article.write_text("# Seedance 视频模型正式发布\n\n正文。\n", encoding="utf-8")
    article_sha = hashlib.sha256(article.read_bytes()).hexdigest()
    req = {
        "schema_version": "1.0", "run_id": "hf76c-e2e",
        "article": {"path": str(article), "sha256": article_sha},
        "materials": [{
            "material_id": "M-001", "aihot_permalink": "https://aihot.example/items/x",
            "source_url": "https://x.com/seedance/status/x-page",
            "title": "Seedance 发布", "selected_claim_ids": ["C-01"],
            "copyright_review": {"status": "unknown"}}],
        "claims": [{"claim_id": "C-01", "claim_text": "Seedance 视频模型正式发布",
                    "material_id": "M-001", "source_url": "https://x.com/seedance/status/x-page",
                    "source_excerpt": "Seedance 视频模型正式发布"}],
        "asset_approvals": [],
        "config": {"network_mode": "offline_fixture", "upload_mode": "wechat_audit",
                   "max_images_per_material": 8, "max_total_images": 12,
                   "min_width": 480, "min_height": 200,
                   "allow_unknown_license_for_publish": False},
    }
    if extra_config:
        req["config"].update(extra_config)
    if user_images is not None:
        req["user_images"] = user_images
    if pool_items is not None:
        req["pool_items"] = pool_items
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


def test_h76c_domain_blacklist_rejects(tmp_path):
    """76C/OBS-248:命中黑名单域名 → rejected(domain blacklisted)。"""
    fixture_html = _make_fixture(tmp_path / "fixture")
    # 源页引图位于被黑域名 img.ithome.com
    (fixture_html / "x-page.html").write_text(
        '<html><body><img src="https://img.ithome.com/ads.png" alt="ad"></body></html>',
        encoding="utf-8")
    req = _make_request(tmp_path, extra_config={"domain_blacklist": ["ithome.com", "img.ithome.com"]})
    proc, manifest = _run(tmp_path, fixture_html, req)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    rejected = [a for a in manifest["assets"]
                if any("domain blacklisted" in r for r in (a.get("reasons") or []))]
    assert rejected, "黑名单域名必须命中即拒"
    assert all("img.ithome.com" in r for a in rejected for r in (a.get("reasons") or []))


def test_h76c_domain_blacklist_non_match_passes(tmp_path):
    """76C/OBS-248:非黑名单域名不受影响(正常进候选)。"""
    fixture_html = _make_fixture(tmp_path / "fixture")
    req = _make_request(tmp_path, extra_config={"domain_blacklist": ["ithome.com"]})
    proc, manifest = _run(tmp_path, fixture_html, req)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert not any("domain blacklisted" in r for a in manifest["assets"]
                   for r in (a.get("reasons") or []))


def test_h76c_user_images_injected(tmp_path):
    """76C/OBS-255:user_images 注入 → user_provided 资产,尺寸达标即 eligible。"""
    fixture_html = _make_fixture(tmp_path / "fixture")
    req = _make_request(tmp_path, user_images=[
        {"url": "https://img.example-source.test/photo.png", "caption": "用户供图",
         "source_url": "https://user.example/source"}])
    proc, manifest = _run(tmp_path, fixture_html, req)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    ups = [a for a in manifest["assets"] if a.get("asset_origin") == "user_provided"]
    assert ups, "user_provided 资产必须存在"
    assert ups[0]["decision"] == "eligible"
    assert ups[0]["copyright_status"] == "user_granted"
    assert ups[0]["content_description_source"] == "user_provided"
    # 77G/OBS-317:user description/source URL is accepted position evidence.
    assert ups[0]["page_position"]["known"] is True
    assert ups[0]["page_position"]["level"] == "user-evidence"


def test_h77g_user_image_manifest_schema_enums():
    """77G/OBS-317:manifest schema accepts the user-provided asset lane."""
    schema = json.loads((SKILL_ROOT / "schemas" / "media_manifest.schema.json").read_text(
        encoding="utf-8"))
    asset = schema["properties"]["assets"]["items"]["properties"]
    assert "user_provided" in asset["asset_origin"]["enum"]
    assert "user_provided" in asset["page_region"]["enum"]
    assert "user_granted" in asset["copyright_status"]["enum"]


def test_h76c_pool_items_expands_discovery(tmp_path):
    """76C/OBS-254:pool_items 扩池——站内页(h1)候选进入 discover。"""
    fixture_html = _make_fixture(tmp_path / "fixture")
    pool = [{"id": "pool-001", "title": "Seedance 相关报道",
             "source_url": "https://x.com/seedance/status/pool-001",
             "aihot_permalink": "https://aihot.example/items/pool-001",
             "links": {"aihot": "https://aihot.example/items/pool-001",
                       "original": "https://x.com/seedance/status/pool-001"},
             "summary": "Seedance 视频模型相关"}]
    req = _make_request(tmp_path, pool_items=pool)
    proc, manifest = _run(tmp_path, fixture_html, req)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    pool_assets = [a for a in manifest["assets"]
                   if "pool-001" in (a.get("material_ids") or [])]
    assert pool_assets, "pool 素材的资产必须进入 discover"
    assert any(a.get("decision") != "rejected" for a in pool_assets)
