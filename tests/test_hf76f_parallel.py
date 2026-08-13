"""76F/OBS-275:discover 快失败 + 有界并行。

- x.com/twitter.com 原文页短超时(5s)失败即跳过,记 discovery_side_effects,
  不拖整段;aihot 站内页 / 官方源保持 15s;
- 页面抓取有界并行(worker=4),资产构建串行 —— 资产 id 顺序稳定。
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

RUNNER = SKILL_ROOT / "scripts" / "run_media_enrichment.py"

_spec = importlib.util.spec_from_file_location("rm76f", str(RUNNER))
rm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rm)


class _FakeFetch:
    """记录 timeout 参数并返回可控结果的假 fetch_page。"""

    def __init__(self, fail_urls=()):
        self.calls: list[tuple[str, int]] = []
        self.fail_urls = set(fail_urls)

    def __call__(self, url, mode="live", fixture_dir=None, timeout=15):
        self.calls.append((url, timeout))
        from media_enrichment.page_fetcher import FetchResult
        if url in self.fail_urls:
            return FetchResult(success=False, url=url, error="boom", duration_ms=5000)
        return FetchResult(
            success=True, url=url, final_url=url, status_code=200,
            content="<html><body><article><h1>T</h1>"
                    '<img src="https://img.example.test/a.png"></article></body></html>',
            duration_ms=10)


def test_x_com_source_short_timeout_and_side_effect(monkeypatch):
    fake = _FakeFetch(fail_urls={"https://x.com/A/status/1"})
    monkeypatch.setattr(rm, "fetch_page", fake)
    mat = {
        "material_id": "M-X",
        "aihot_internal_url": "https://aihot.example/items/mx",
        "aihot_permalink": "https://x.com/A/status/1",
        "source_url": "https://x.com/A/status/1",
        "selected_claim_ids": [],
    }
    res = rm._fetch_material_pages(mat, "live", None,
                                   frozenset(rm.SHORT_TIMEOUT_DOMAINS))
    by_url = {u: t for u, t in fake.calls}
    # 站内页 15s;x.com 原文页 5s 短超时
    assert by_url["https://aihot.example/items/mx"] == 15
    assert by_url["https://x.com/A/status/1"] == rm.SHORT_TIMEOUT_SECONDS == 5
    # 失败即跳过并留痕(不因 x.com 拖整段)
    assert res["page_url"] == "https://aihot.example/items/mx"
    assert any(e.get("skipped_reason") == "short_timeout_domain:x.com"
               for e in res["side_effects"])


def test_non_x_source_keeps_default_timeout(monkeypatch):
    fake = _FakeFetch()
    monkeypatch.setattr(rm, "fetch_page", fake)
    mat = {
        "material_id": "M-O",
        "aihot_internal_url": "https://aihot.example/items/mo",
        "aihot_permalink": "https://x.com/O/status/1",
        "source_url": "https://official.example/blog",
        "selected_claim_ids": [],
    }
    res = rm._fetch_material_pages(mat, "live", None,
                                   frozenset(rm.SHORT_TIMEOUT_DOMAINS))
    by_url = {u: t for u, t in fake.calls}
    assert by_url["https://official.example/blog"] == rm.DEFAULT_FETCH_TIMEOUT == 15
    assert res["side_effects"] == []


def _mk_fixture(tmp_path: Path) -> Path:
    html = tmp_path / "html"
    images = tmp_path / "images"
    html.mkdir(parents=True, exist_ok=True)
    images.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    Image.new("RGB", (800, 450), (10, 120, 220)).save(images / "p76f.png", "PNG")
    for slug in ("m1", "m2"):
        (html / f"{slug}.html").write_text(
            "<!doctype html><html><body><article><h1>页" + slug + "</h1>"
            '<img src="https://img.example-source.test/p76f.png"></article>'
            "</body></html>", encoding="utf-8")
    return html


def _mk_request(tmp_path: Path) -> Path:
    article = tmp_path / "final_article.md"
    article.write_text("# 并行测试\n\n正文。\n", encoding="utf-8")
    req = {
        "schema_version": "1.0", "run_id": "hf76f-parallel",
        "article": {"path": str(article),
                    "sha256": hashlib.sha256(article.read_bytes()).hexdigest()},
        "materials": [
            {"material_id": "M-1", "aihot_internal_url": "https://aihot.example/items/m1",
             "aihot_permalink": "https://x.com/1", "source_url": "https://x.com/1",
             "title": "素材一", "selected_claim_ids": [],
             "copyright_review": {"status": "unknown"}},
            {"material_id": "M-2", "aihot_internal_url": "https://aihot.example/items/m2",
             "aihot_permalink": "https://x.com/2", "source_url": "https://x.com/2",
             "title": "素材二", "selected_claim_ids": [],
             "copyright_review": {"status": "unknown"}},
        ],
        "claims": [],
        "asset_approvals": [],
        "config": {"network_mode": "offline_fixture", "upload_mode": "wechat_audit",
                   "max_images_per_material": 4, "max_total_images": 8,
                   "min_width": 480, "min_height": 200,
                   "allow_unknown_license_for_publish": False},
    }
    p = tmp_path / "media_request.json"
    p.write_text(json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def test_parallel_discover_preserves_asset_order_and_side_effects(tmp_path):
    """并行预抓后资产 id 仍按素材顺序(A-001=M-1,A-002=M-2);
    manifest 含 discovery_side_effects 键。"""
    fixture_html = _mk_fixture(tmp_path / "fixture")
    req = _mk_request(tmp_path)
    out = tmp_path / "out"
    cmd = [sys.executable, "-X", "utf8", str(RUNNER),
           "--request", str(req), "--output-dir", str(out),
           "--fixture-dir", str(fixture_html), "--phase", "discover"]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=180)
    assert proc.returncode == 0, proc.stdout[-1200:] + proc.stderr[-1200:]
    man = json.loads((out / "media_manifest.json").read_text(encoding="utf-8"))
    assert "discovery_side_effects" in man
    src_assets = [a for a in man["assets"]
                  if a.get("material_ids") and a["material_ids"][0] in ("M-1", "M-2")]
    assert src_assets, "两素材站内页应进候选"
    by_mid = {a["material_ids"][0]: a["asset_id"] for a in src_assets}
    assert by_mid.get("M-1", "") < by_mid.get("M-2", ""), \
        "资产 id 顺序必须与素材顺序一致(并行不换序)"
