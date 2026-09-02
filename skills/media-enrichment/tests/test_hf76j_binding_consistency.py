"""76J/OBS-270:站内页绑定一致性——continue 重分类的 source 一致性检查认可
aihot_internal_url(站内页)与 source_page_url 相等,与 links.original(source_url)
同等合法;无站内页字段的素材行为不变(xboc9w 形态回归:站内页图不再因
「source_page_url 与 material 原始 URL 不一致」被挡在绑定层外)。"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

RUNNER = SKILL_ROOT / "scripts" / "run_media_enrichment.py"
EVIDENCE_SHA = "e" * 64

INTERNAL_URL = "https://aihot.example/items/ipage76j"
SOURCE_URL = "https://www.example-source.test/ipage76j-original"


def _mk_fixture(tmp_path: Path) -> Path:
    html = tmp_path / "html"
    images = tmp_path / "images"
    html.mkdir(parents=True, exist_ok=True)
    images.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (800, 450), (40, 90, 200)).save(images / "ip76j.png", "PNG")
    (html / "ipage76j.html").write_text(
        "<!doctype html><html><head><title>站内页 76J · AIHOT</title></head>"
        "<body><article><h1>站内页 76J</h1>"
        '<img class="x-tweet-media-img" src="https://img.example-source.test/ip76j.png">'
        "</article></body></html>", encoding="utf-8")
    return html


def _mk_request(tmp_path: Path, with_internal_url: bool = True) -> Path:
    article = tmp_path / "final_article.md"
    article.write_text("# 站内页绑定测试\n\n正文段落。\n", encoding="utf-8")
    material = {
        "material_id": "M-76J", "aihot_permalink": INTERNAL_URL,
        "aihot_internal_url": INTERNAL_URL,
        "source_url": SOURCE_URL, "title": "站内页素材",
        "selected_claim_ids": ["C-76J"],
        "copyright_review": {"status": "unknown"}}
    if not with_internal_url:
        material.pop("aihot_internal_url")
    req = {
        "schema_version": "1.0", "run_id": "hf76j-binding",
        "article": {"path": str(article),
                    "sha256": hashlib.sha256(article.read_bytes()).hexdigest()},
        "materials": [material],
        "claims": [{"claim_id": "C-76J", "claim_text": "站内页绑定测试",
                    "material_id": "M-76J", "source_url": SOURCE_URL,
                    "source_excerpt": "站内页素材"}],
        "asset_approvals": [],
        "config": {"network_mode": "offline_fixture", "upload_mode": "wechat_audit",
                   "max_images_per_material": 8, "max_total_images": 8,
                   "min_width": 480, "min_height": 200,
                   "allow_unknown_license_for_publish": False},
    }
    p = tmp_path / "media_request.json"
    p.write_text(json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _approval(discovery: dict, asset_id: str) -> dict:
    asset = next(a for a in discovery["assets"] if a["asset_id"] == asset_id)
    record = dict(asset)
    record.update({
        "discovery_manifest_sha256": discovery["discovery_manifest_sha256"],
        "approval_id": f"AP-{asset_id}", "approved_scope": "single_asset",
        "approved_by": "user", "approved_at": "2026-08-13T00:00:00Z",
        "approval_evidence_sha256": EVIDENCE_SHA,
    })
    return record


def _run(tmp_path: Path, fixture_html: Path, phase: str,
         request: Path, discovery_manifest: Path | None = None):
    out = tmp_path / f"out-{phase}"
    cmd = [sys.executable, "-X", "utf8", str(RUNNER),
           "--request", str(request), "--output-dir", str(out),
           "--fixture-dir", str(fixture_html), "--phase", phase]
    if discovery_manifest is not None:
        cmd.extend(["--discovery-manifest", str(discovery_manifest)])
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=180)
    return proc, out


def test_internal_page_asset_passes_continue_consistency(tmp_path):
    """站内页图(source_page_url=aihot_internal_url)在 continue 不再被
    material/source changed 拒——eligible 且上传成功。"""
    fixture_html = _mk_fixture(tmp_path / "fixture")
    req = _mk_request(tmp_path)
    proc, out = _run(tmp_path, fixture_html, "discover", req)
    assert proc.returncode == 0, proc.stdout[-1200:] + proc.stderr[-1200:]
    discovery = json.loads(
        (out / "asset_discovery_manifest.json").read_text(encoding="utf-8"))
    internal_assets = [a for a in discovery["assets"]
                       if a["source_page_url"] == INTERNAL_URL]
    assert internal_assets, "站内页图应进 discover 候选"

    reqd = json.loads(req.read_text(encoding="utf-8"))
    reqd["asset_approvals"] = [_approval(discovery, internal_assets[0]["asset_id"])]
    req.write_text(json.dumps(reqd, ensure_ascii=False, indent=2), encoding="utf-8")
    proc2, out2 = _run(tmp_path, fixture_html, "continue", req,
                       out / "asset_discovery_manifest.json")
    assert proc2.returncode == 0, proc2.stdout[-1200:] + proc2.stderr[-1200:]
    man = json.loads((out2 / "media_manifest.json").read_text(encoding="utf-8"))
    assert not any("material/source changed" in e for e in man["errors"])
    target = next(a for a in man["assets"]
                  if a["asset_id"] == internal_assets[0]["asset_id"])
    assert target["decision"] == "eligible", target["reasons"]
    assert target["upload"]["status"] == "success"


def test_internal_page_asset_still_rejected_without_internal_field(tmp_path):
    """负向对照(R55):素材无 aihot_internal_url 时行为不变——source_page_url
    与 source_url 不一致仍拒(material/source changed)。"""
    fixture_html = _mk_fixture(tmp_path / "fixture2")
    req = _mk_request(tmp_path, with_internal_url=False)
    proc, out = _run(tmp_path, fixture_html, "discover", req)
    assert proc.returncode == 0, proc.stdout[-1200:] + proc.stderr[-1200:]
    discovery = json.loads(
        (out / "asset_discovery_manifest.json").read_text(encoding="utf-8"))
    internal_assets = [a for a in discovery["assets"]
                       if a["source_page_url"] == INTERNAL_URL]
    # 无站内页字段时 discover 走 source_url 兜底(抓不到 fixture 页),此处构造
    # 等价形态:直接冻结站内页候选,continue 时素材无 internal 字段。
    assert internal_assets

    reqd = json.loads(req.read_text(encoding="utf-8"))
    reqd["asset_approvals"] = [_approval(discovery, internal_assets[0]["asset_id"])]
    req.write_text(json.dumps(reqd, ensure_ascii=False, indent=2), encoding="utf-8")
    proc2, out2 = _run(tmp_path, fixture_html, "continue", req,
                       out / "asset_discovery_manifest.json")
    man = json.loads((out2 / "media_manifest.json").read_text(encoding="utf-8"))
    assert any("material/source changed" in e for e in man["errors"])
