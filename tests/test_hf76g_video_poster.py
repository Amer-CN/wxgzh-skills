"""76G 增补/OBS-266:视频封面采集通道——poster 抽取、video_poster 标记、进候选。"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

RUNNER = SKILL_ROOT / "scripts" / "run_media_enrichment.py"


def _extract(html: str, page_url: str):
    from media_enrichment.image_extractor import extract_images
    return extract_images(html, page_url=page_url)


def test_video_poster_extracted():
    html = ('<html><head><meta property="og:video" content="https://x.example/v.mp4">'
            '<meta property="og:image" content="https://img.example/cover.jpg"></head>'
            '<body><video poster="https://img.example/poster.jpg" src="https://x.example/v.mp4">'
            "</video></body></html>")
    ex = _extract(html, "https://aihot.example/items/v1")
    posters = [c for c in ex.candidates if c.video_poster]
    methods = sorted(c.extraction_method for c in posters)
    assert "video_poster" in methods, methods  # <video poster>
    assert "og:image" in methods, methods  # og:video 页的 og:image = 封面
    urls = {c.url for c in posters}
    assert "https://img.example/poster.jpg" in urls
    assert "https://img.example/cover.jpg" in urls


def test_twitter_player_image_marked():
    html = ('<html><head><meta name="twitter:player" content="https://x.example/player">'
            '<meta name="twitter:player:image" content="https://img.example/thumb.jpg">'
            "</head><body></body></html>")
    ex = _extract(html, "https://aihot.example/items/v2")
    tp = [c for c in ex.candidates if c.extraction_method == "twitter:player:image"]
    assert tp and tp[0].video_poster is True
    assert tp[0].url == "https://img.example/thumb.jpg"


def test_img_proxy_thumb_marked_on_video_page():
    html = ('<html><head><meta property="og:video" content="https://x.example/v.mp4"></head>'
            '<body><img src="https://aihot.example/api/img-proxy?u=https%3A%2F%2Fimg.example%2Fv.jpg"></body></html>')
    ex = _extract(html, "https://aihot.example/items/v3")
    thumbs = [c for c in ex.candidates if c.video_poster]
    assert thumbs, "视频页 img-proxy thumb 应标 video_poster"
    assert all("img-proxy" in c.url for c in thumbs)


def test_non_video_page_not_marked():
    html = ('<html><head><meta property="og:image" content="https://img.example/photo.jpg"></head>'
            "<body><img src='https://img.example/photo.jpg'></body></html>")
    ex = _extract(html, "https://aihot.example/items/n1")
    assert all(c.video_poster is False for c in ex.candidates)


def _mk_fixture(root: Path) -> Path:
    html = root / "html"
    images = root / "images"
    html.mkdir(parents=True, exist_ok=True)
    images.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    Image.new("RGB", (800, 450), (30, 120, 220)).save(images / "vp.png", "PNG")
    # 视频页 fixture:站内页形态(og:video + og:image 封面 + video poster)
    (html / "vpage.html").write_text(
        "<!doctype html><html><head>"
        '<meta property="og:video" content="https://x.example/clip.mp4">'
        '<meta property="og:image" content="https://img.example-source.test/vp.png">'
        '<meta name="twitter:player:image" content="https://img.example-source.test/vp.png">'
        "</head><body><article><h1>视频素材页</h1>"
        '<video poster="https://img.example-source.test/vp.png" src="https://x.example/clip.mp4"></video>'
        "</article></body></html>",
        encoding="utf-8")
    (html / "npage.html").write_text(
        "<!doctype html><html><body><article><h1>普通页</h1>"
        '<img src="https://img.example-source.test/vp.png"></article></body></html>',
        encoding="utf-8")
    return html


def _mk_request(tmp_path: Path) -> Path:
    article = tmp_path / "final_article.md"
    article.write_text("# 视频素材测试\n\n正文。\n", encoding="utf-8")
    req = {
        "schema_version": "1.0", "run_id": "hf76g-video",
        "article": {"path": str(article),
                    "sha256": hashlib.sha256(article.read_bytes()).hexdigest()},
        "materials": [{
            "material_id": "M-V1", "aihot_permalink": "https://x.example/vpage",
            "aihot_internal_url": "https://aihot.example/items/vpage",
            "source_url": "https://x.example/vpage",
            "title": "视频素材", "selected_claim_ids": [],
            "copyright_review": {"status": "unknown"}}],
        "claims": [{"claim_id": "C-1", "claim_text": "视频素材测试", "material_id": "M-V1",
                    "source_url": "https://x.example/vpage", "source_excerpt": "视频素材"}],
        "asset_approvals": [],
        "config": {"network_mode": "offline_fixture", "upload_mode": "wechat_audit",
                   "max_images_per_material": 8, "max_total_images": 8,
                   "min_width": 480, "min_height": 200,
                   "allow_unknown_license_for_publish": False},
    }
    p = tmp_path / "media_request.json"
    p.write_text(json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def test_video_poster_enters_candidates(tmp_path):
    """端到端:视频素材页封面(og:image/poster/twitter:player:image 去重后)进候选,
    manifest 资产带 video_poster=true。"""
    fixture_html = _mk_fixture(tmp_path / "fixture")
    req = _mk_request(tmp_path)
    out = tmp_path / "out-discover"
    cmd = [sys.executable, "-X", "utf8", str(RUNNER),
           "--request", str(req), "--output-dir", str(out),
           "--fixture-dir", str(fixture_html), "--phase", "discover"]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=180)
    assert proc.returncode == 0, proc.stdout[-1200:]
    man = json.loads((out / "media_manifest.json").read_text(encoding="utf-8"))
    vp = [a for a in man["assets"] if a.get("video_poster")]
    assert vp, "视频封面应作为候选进入 manifest"
    assert all(a["decision"] in ("eligible", "review_required", "rejected") for a in vp)
    # 视频本体不下载:资产 URL 均为图片(非 .mp4)
    assert all(not (a.get("resolved_original_url") or "").endswith(".mp4") for a in vp)
