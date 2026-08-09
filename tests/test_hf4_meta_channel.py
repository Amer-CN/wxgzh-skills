"""档HF-4/OBS-245/246/247 验收测试:meta 通道去冤 + content_description 直写
+ 纯 material 车道。

覆盖:
- x.com 风格页面(meta og:image 有大图、body 无 img)→ 不再因通道被拒,
  page_position=page-meta(页面 title)、content_description=og:title(page_context)
- content_description 传递:discover 写入 → media_manifest 携带 → continue
  从冻结清单重建后字段保留、既有身份字段逐字不变
- 纯 material 车道:discover 冻结 review_required → continue known_allowed
  → exit 0 且模拟上传成功(忠实复现 HF-2 lane1 生产序列,档HF-4R)
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

RUNNER = SKILL_ROOT / "scripts" / "run_media_enrichment.py"
EVIDENCE_SHA = "a1b2c3d4" * 8


def _make_x_fixture(root: Path) -> Path:
    html = root / "html"
    images = root / "images"
    html.mkdir(parents=True, exist_ok=True)
    images.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    Image.new("RGB", (1638, 2048), (90, 120, 200)).save(images / "x-photo.png", "PNG")
    (html / "123.html").write_text(
        "<!doctype html><html><head><title>某推文页面标题</title>"
        '<meta property="og:title" content="某推文页面标题">'
        '<meta property="og:description" content="推文正文摘要">'
        '<meta property="og:image" content="https://img.example-source.test/x-photo.png">'
        "</head><body><article><p>推文正文(SPA 渲染,无 DOM img)</p>"
        "</article></body></html>",
        encoding="utf-8",
    )
    return html


def _make_request(tmp_path: Path, material_status: str,
                  name: str = "media_request.json") -> Path:
    article = tmp_path / "final_article.md"
    article.write_text("# 标题\n\n推文正文摘要\n", encoding="utf-8")
    cr = {"status": material_status}
    if material_status == "known_allowed":
        cr.update({"reviewed_by": "hf4", "reviewed_at": "2026-08-09T00:00:00Z",
                   "evidence": EVIDENCE_SHA, "approval_id": "AP-M-001",
                   "approved_scope": "material"})
    req = {
        "schema_version": "1.0", "run_id": "hf4-meta-e2e",
        "article": {"path": str(article),
                    "sha256": __import__("hashlib").sha256(article.read_bytes()).hexdigest()},
        "materials": [{"material_id": "M-001",
                       "aihot_permalink": "https://x.com/someone/status/123",
                       "source_url": "https://x.com/someone/status/123",
                       "title": "示例素材", "selected_claim_ids": ["C-01"],
                       "copyright_review": cr}],
        "claims": [{"claim_id": "C-01", "claim_text": "推文正文摘要",
                    "material_id": "M-001",
                    "source_url": "https://x.com/someone/status/123",
                    "source_excerpt": "推文正文摘要"}],
        "asset_approvals": [],
        "config": {"network_mode": "offline_fixture", "upload_mode": "wechat_audit",
                   "max_images_per_material": 4, "max_total_images": 8,
                   "min_width": 480, "min_height": 200,
                   "allow_unknown_license_for_publish": False},
    }
    path = tmp_path / name
    path.write_text(json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _run(tmp_path, fixture_html, request, phase, discovery=None):
    out = tmp_path / ("out-" + phase)
    cmd = [sys.executable, "-X", "utf8", str(RUNNER),
           "--request", str(request), "--output-dir", str(out),
           "--fixture-dir", str(fixture_html), "--phase", phase]
    if discovery is not None:
        cmd += ["--discovery-manifest", str(discovery)]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=180)
    manifest = json.loads((out / "media_manifest.json").read_text(encoding="utf-8"))
    return proc, out, manifest


def test_hf4_meta_channel_not_rejected_and_page_meta_position(tmp_path):
    """x.com 风格页面:meta 通道图不再因通道被拒;位置=page-meta。"""
    fixture_html = _make_x_fixture(tmp_path / "fixture")
    request = _make_request(tmp_path, "unknown")
    proc, _, manifest = _run(tmp_path, fixture_html, request, "discover")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    source = [a for a in manifest["assets"] if a["asset_origin"] == "source"]
    assert source, "meta 通道图必须被发现"
    asset = source[0]
    assert asset["decision"] == "review_required"
    assert not any("social share card" in r for r in (asset.get("reasons") or []))
    assert asset["page_position"] == {"known": True, "heading": "某推文页面标题",
                                      "level": "page-meta"}
    assert asset["content_description"] == "某推文页面标题 推文正文摘要"
    assert asset["content_description_source"] == "page_context"


def test_hf4_content_description_passed_through_continue(tmp_path):
    """discover 直写 content_description → continue 重建后字段保留,身份字段不变。"""
    fixture_html = _make_x_fixture(tmp_path / "fixture")
    request = _make_request(tmp_path, "known_allowed")
    proc, out, manifest = _run(tmp_path, fixture_html, request, "discover")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    asset = next(a for a in manifest["assets"] if a["asset_origin"] == "source")
    assert asset["content_description"] == "某推文页面标题 推文正文摘要"
    assert asset["content_description_source"] == "page_context"
    identity = asset["asset_identity_sha256"]
    sha = asset["sha256"]

    frozen = out / "asset_discovery_manifest.json"
    proc2, _, manifest2 = _run(tmp_path, fixture_html, request, "continue", frozen)
    assert proc2.returncode == 0, proc2.stdout + proc2.stderr
    asset2 = next(a for a in manifest2["assets"] if a["asset_origin"] == "source")
    assert asset2["content_description"] == "某推文页面标题 推文正文摘要"
    assert asset2["content_description_source"] == "page_context"
    assert asset2["asset_identity_sha256"] == identity
    assert asset2["sha256"] == sha


def test_hf4_pure_material_lane_exit0_and_upload(tmp_path):
    """纯 material 车道忠实复现 HF-2 lane1 生产序列:discover 时版权 unknown
    (discover 产出 decision=review_required 并冻结身份)→ continue 时
    copyright_review.status=
    known_allowed → 重分类块把 decision 转 eligible → exit 0 且模拟上传成功。

    不变量(档HF-4R,与 run_media_enrichment.py 重分类块一致):
    - restricted 资产永远到不了重分类块(Loop 1 不会把 restricted 置
      known_allowed);
    - single_asset 身份核验未通过的资产到不了这里(copyright 保持 unknown
      且已记 mismatch 错误);
    - single_asset 消费成功与 material/source_url 批准两类资产都会到这里。
    """
    fixture_html = _make_x_fixture(tmp_path / "fixture")
    discover_request = _make_request(tmp_path, "unknown",
                                     name="media_request_discover.json")
    proc, out, discover_manifest = _run(tmp_path, fixture_html, discover_request,
                                        "discover")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    frozen = out / "asset_discovery_manifest.json"
    discover_asset = next(
        a for a in discover_manifest["assets"] if a["asset_origin"] == "source")
    assert discover_asset["decision"] == "review_required", \
        "生产序列:discover 时版权 unknown → 资产 decision=review_required"
    frozen_ids = {a["asset_id"] for a in
        json.loads(frozen.read_text(encoding="utf-8"))["assets"]}
    assert discover_asset["asset_id"] in frozen_ids, \
        "冻结清单必须含该 review_required 资产(identity 冻结)"
    continue_request = _make_request(tmp_path, "known_allowed",
                                     name="media_request_continue.json")
    proc2, _, manifest2 = _run(tmp_path, fixture_html, continue_request,
                               "continue", frozen)
    assert proc2.returncode == 0, proc2.stdout + proc2.stderr
    asset = next(a for a in manifest2["assets"] if a["asset_origin"] == "source")
    assert asset["decision"] == "eligible"
    assert asset["upload"]["status"] == "success"
    events = json.loads((out.parent / "out-continue" / "upload_events.json").read_text(encoding="utf-8"))
    assert any(e["status"] == "success" for e in events["events"])


def test_hf4_unapproved_material_blocked_fail_closed(tmp_path):
    """未知素材的候选资产无批准依据 → FAIL_CLOSED(任务 3 验收②)。

    discover 产出 review_required 资产并冻结身份(版权 unknown 的 discover
    序列,与
    lane1 生产序列一致);continue 仍无任何批准依据 → 守卫拦下并 exit != 0。
    """
    fixture_html = _make_x_fixture(tmp_path / "fixture")
    request = _make_request(tmp_path, "unknown")
    proc, out, manifest = _run(tmp_path, fixture_html, request, "discover")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    frozen = out / "asset_discovery_manifest.json"
    discover_asset = next(
        a for a in manifest["assets"] if a["asset_origin"] == "source")
    assert discover_asset["decision"] == "review_required", \
        "冻结对应资产必须为 review_required(版权 unknown 的 discover 序列)"
    frozen_ids = {a["asset_id"] for a in
        json.loads(frozen.read_text(encoding="utf-8"))["assets"]}
    assert discover_asset["asset_id"] in frozen_ids, \
        "冻结清单必须含该 review_required 资产(identity 冻结)"
    proc2, _, manifest2 = _run(tmp_path, fixture_html, request, "continue", frozen)
    assert proc2.returncode != 0
    assert any("upload candidates without approval basis" in e
               for e in manifest2.get("errors", []))
