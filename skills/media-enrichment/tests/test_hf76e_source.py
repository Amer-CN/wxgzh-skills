"""档76E/OBS-260/261:discovery 预算分离 + 图源优先级(站内页优先)回归。"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

RUNNER = SKILL_ROOT / "scripts" / "run_media_enrichment.py"


def _mk_fixture(root: Path, pages: dict[str, str]) -> Path:
    """pages: {url 尾段(不带 .html): html 内容}。图片 fixture 同 76C。"""
    html = root / "html"
    images = root / "images"
    html.mkdir(parents=True, exist_ok=True)
    images.mkdir(parents=True, exist_ok=True)
    from PIL import Image, ImageDraw
    for idx, name in enumerate(("photo.png", "photo2.png", "photo3.png")):
        im = Image.new("RGB", (800, 600), (20 + idx * 70, 30, 240 - idx * 70))
        d = ImageDraw.Draw(im)
        # 三张图不同布局(位置/形状),避免感知哈希判重
        d.rectangle([50 + idx * 60, 80, 150 + idx * 60, 220], fill=(255, 255, 255))
        d.ellipse([300, 250 + idx * 50, 480, 420 + idx * 50], fill=(0, 0, 0))
        im.save(images / name, "PNG")
    for stem, content in pages.items():
        (html / f"{stem}.html").write_text(content, encoding="utf-8")
    return html


def _mk_request(tmp_path: Path, materials: list[dict], claims: list[dict],
                extra_config=None) -> Path:
    article = tmp_path / "final_article.md"
    article.write_text("# 测试文章\n\n正文。\n", encoding="utf-8")
    req = {
        "schema_version": "1.0", "run_id": "hf76e-e2e",
        "article": {"path": str(article),
                    "sha256": hashlib.sha256(article.read_bytes()).hexdigest()},
        "materials": materials, "claims": claims,
        "asset_approvals": [],
        "config": {"network_mode": "offline_fixture", "upload_mode": "wechat_audit",
                   "max_images_per_material": 8, "max_total_images": 2,
                   "min_width": 480, "min_height": 200,
                   "allow_unknown_license_for_publish": False},
    }
    if extra_config:
        req["config"].update(extra_config)
    p = tmp_path / "media_request.json"
    p.write_text(json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _run(tmp_path, fixture_html, request) -> tuple[int, dict, str]:
    out = tmp_path / "out-discover"
    cmd = [sys.executable, "-X", "utf8", str(RUNNER),
           "--request", str(request), "--output-dir", str(out),
           "--fixture-dir", str(fixture_html), "--phase", "discover"]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=180)
    manifest = json.loads((out / "media_manifest.json").read_text(encoding="utf-8"))
    return proc.returncode, manifest, proc.stdout


def _page(title: str, img_src: str = "https://img.example-source.test/photo.png") -> str:
    return (f"<!doctype html><html><head><title>{title}</title></head>"
            f"<body><article><h1>{title}</h1>"
            f'<img src="{img_src}" alt="{title}"></article></body></html>')


def _mat(mid: str, internal_stem: str, source_stem: str) -> dict:
    return {
        "material_id": mid,
        "aihot_permalink": f"https://x.com/test/{source_stem}",
        "aihot_internal_url": f"https://aihot.example/items/{internal_stem}",
        "source_url": f"https://x.com/test/{source_stem}",
        "title": f"{mid} 素材", "selected_claim_ids": [],
        "copyright_review": {"status": "unknown"},
    }


def test_discovery_budget_not_capped_by_max_total(tmp_path):
    """76E/OBS-260:max_total_images=2 不再截断后续素材页——3 页全部被抓取,
    manifest 覆盖 3 个素材页,无 skipping warning(「skipping M-10」场景回归)。"""
    fixture_html = _mk_fixture(tmp_path / "fixture", {
        "m1": _page("素材一", "https://img.example-source.test/photo.png"),
        "m2": _page("素材二", "https://img.example-source.test/photo2.png"),
        "m3": _page("素材三", "https://img.example-source.test/photo3.png")})
    mats = [_mat("M-1", "m1", "m1"), _mat("M-2", "m2", "m2"), _mat("M-3", "m3", "m3")]
    claims = [{"claim_id": f"C-{i}", "claim_text": f"素材{i} 标题", "material_id": f"M-{i}",
               "source_url": f"https://x.com/test/m{i}", "source_excerpt": f"素材{i}"}
              for i in range(1, 4)]
    req = _mk_request(tmp_path, mats, claims)
    rc, manifest, out = _run(tmp_path, fixture_html, req)
    assert rc == 0, out[-1200:]
    pages = {a.get("source_page_url") for a in manifest["assets"]}
    assert len(pages) == 3, f"应抓取 3 个素材页,实际 {sorted(pages)}"
    joined = " | ".join(manifest.get("warnings", []))
    assert "skipping" not in joined and "stopping discovery" not in joined


def test_aihot_internal_page_preferred(tmp_path):
    """76E/OBS-260:站内页有候选 → 用站内页(source_page_url=aihot 站内页)。"""
    fixture_html = _mk_fixture(tmp_path / "fixture", {
        "internal-1": _page("站内页标题"), "src-1": "<html><body><p>原始页无图</p></body></html>"})
    mats = [_mat("M-1", "internal-1", "src-1")]
    claims = [{"claim_id": "C-1", "claim_text": "站内页标题", "material_id": "M-1",
               "source_url": "https://x.com/test/src-1", "source_excerpt": "站内页标题"}]
    req = _mk_request(tmp_path, mats, claims)
    rc, manifest, out = _run(tmp_path, fixture_html, req)
    assert rc == 0, out[-1200:]
    assets = manifest["assets"]
    assert assets, "站内页应产出候选"
    assert all(a["source_page_url"] == "https://aihot.example/items/internal-1" for a in assets)


def test_source_page_fallback_when_internal_empty(tmp_path):
    """76E/OBS-260:站内页无图 → 原始来源页兜底。"""
    fixture_html = _mk_fixture(tmp_path / "fixture", {
        "internal-2": "<html><body><p>站内页无图</p></body></html>",
        "src-2": _page("原始页标题")})
    mats = [_mat("M-2", "internal-2", "src-2")]
    claims = [{"claim_id": "C-2", "claim_text": "原始页标题", "material_id": "M-2",
               "source_url": "https://x.com/test/src-2", "source_excerpt": "原始页标题"}]
    req = _mk_request(tmp_path, mats, claims)
    rc, manifest, out = _run(tmp_path, fixture_html, req)
    assert rc == 0, out[-1200:]
    assets = manifest["assets"]
    assert assets, "原始页兜底应产出候选"
    assert all(a["source_page_url"] == "https://x.com/test/src-2" for a in assets)


def test_no_repost_scan_still_applies_with_internal_priority(tmp_path):
    """76E/OBS-260:站内页优先时,原始页 no-repost 扫描保留→素材 restricted。"""
    fixture_html = _mk_fixture(tmp_path / "fixture", {
        "internal-3": _page("站内页有图"),
        "src-3": "<html><body><p>本文禁止转载。图片禁止使用。</p></body></html>"})
    mats = [_mat("M-3", "internal-3", "src-3")]
    claims = [{"claim_id": "C-3", "claim_text": "站内页有图", "material_id": "M-3",
               "source_url": "https://x.com/test/src-3", "source_excerpt": "站内页有图"}]
    req = _mk_request(tmp_path, mats, claims)
    rc, manifest, out = _run(tmp_path, fixture_html, req)
    assert rc == 0, out[-1200:]
    joined = " | ".join(manifest.get("warnings", []))
    assert "no-repost" in joined or "禁止" in joined, joined
    for a in manifest["assets"]:
        assert a.get("copyright_status") == "restricted", a.get("asset_id")


def test_img_proxy_429_retry_backoff(monkeypatch, tmp_path):
    """76E/OBS-260:img-proxy 429 限流退避重试(429 实证)——前两次 429,第三次成功。"""
    from media_enrichment import downloader as DL
    calls = {"n": 0}

    def fake_download(url, output_path, max_bytes=15728640, timeout=30):
        calls["n"] += 1
        if calls["n"] < 3:
            raise RuntimeError("HTTP 429")
        output_path.write_bytes(b"fake-image-bytes")
        return "a" * 64, 16, "image/jpeg", [url]

    monkeypatch.setattr(DL, "safe_download_with_redirects", fake_download)
    from types import SimpleNamespace
    monkeypatch.setattr(DL, "is_safe_url",
                        lambda url: SimpleNamespace(safe=True, reasons=[]))
    result = DL.download_image("https://aihot.example/api/img-proxy?u=x",
                               tmp_path, mode="live")
    assert result.success is True
    assert calls["n"] == 3
