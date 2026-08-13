"""hotfix4 real CLI tests for material/source_url/single_asset precedence.

All runs use offline fixtures and the deterministic wechat_audit uploader.
No real network or WeChat API is reachable.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

SKILL_ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_SHA = "e" * 64


def _make_fixture(root: Path, slug: str, image_name: str, color: tuple[int, int, int],
                  *, no_repost: bool = False) -> None:
    html = root / "html"
    images = root / "images"
    html.mkdir(parents=True, exist_ok=True)
    images.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (1000, 700), color).save(images / image_name, "PNG")
    restriction = "<p>未经许可不得转载</p>" if no_repost else ""
    (html / f"{slug}.html").write_text(
        "<!doctype html><html><body><article>"
        f"{restriction}<p>relevant body figure</p>"
        f'<img src="https://img.example-source.test/{image_name}" '
        'alt="relevant body figure">'
        "</article></body></html>",
        encoding="utf-8",
    )


def _copyright(status: str, scope: str | None = None) -> dict:
    if status != "known_allowed":
        return {"status": status}
    return {
        "status": "known_allowed",
        "reviewed_by": "scope-reviewer",
        "reviewed_at": "2026-07-29T00:00:00Z",
        "evidence": EVIDENCE_SHA,
        "approval_id": f"AP-{scope}",
        "approved_scope": scope,
    }


def _request(tmp_path: Path, materials: list[dict], approvals=()) -> Path:
    article = tmp_path / "final_article.md"
    article.write_text("# title\n\nrelevant body figure\n", encoding="utf-8")
    claims = []
    for index, material in enumerate(materials, 1):
        claims.append({
            "claim_id": f"C-{index:02d}",
            "claim_text": "relevant body figure",
            "material_id": material["material_id"],
            "source_url": material["source_url"],
            "source_excerpt": "relevant body figure",
        })
        material["selected_claim_ids"] = [f"C-{index:02d}"]
    payload = {
        "schema_version": "1.0",
        "run_id": "approval-scope-cli-e2e",
        "article": {
            "path": "final_article.md",
            "sha256": hashlib.sha256(article.read_bytes()).hexdigest(),
        },
        "materials": materials,
        "claims": claims,
        "asset_approvals": list(approvals),
        "config": {
            "network_mode": "offline_fixture",
            "upload_mode": "wechat_audit",
            "max_images_per_material": 4,
            "max_total_images": 8,
            "allow_unknown_license_for_publish": False,
        },
    }
    path = tmp_path / "media_request.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _material(mid: str, slug: str, status: str = "unknown",
              scope: str | None = None) -> dict:
    return {
        "material_id": mid,
        "aihot_permalink": f"https://aihot.virxact.com/items/aihot-{slug}",
        "source_url": f"https://source.example.test/{slug}",
        "title": slug,
        "selected_claim_ids": [],
        "copyright_review": _copyright(status, scope),
    }


def _run(tmp_path: Path, fixture: Path, request: Path, phase: str,
         frozen: Path | None = None) -> tuple[subprocess.CompletedProcess, Path, dict, dict]:
    out = tmp_path / f"out-{phase}-{len(list(tmp_path.glob('out-*')))}"
    cmd = [
        sys.executable, "-X", "utf8",
        str(SKILL_ROOT / "scripts" / "run_media_enrichment.py"),
        "--request", str(request),
        "--output-dir", str(out),
        "--fixture-dir", str(fixture / "html"),
        "--phase", phase,
    ]
    if frozen is not None:
        cmd.extend(["--discovery-manifest", str(frozen)])
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=180,
    )
    manifest = json.loads((out / "media_manifest.json").read_text(encoding="utf-8"))
    events = json.loads((out / "upload_events.json").read_text(encoding="utf-8"))
    return result, out, manifest, events


def _discover_continue(tmp_path: Path, fixture: Path, request: Path):
    discovered, discover_out, discover_manifest, discover_events = _run(
        tmp_path, fixture, request, "discover",
    )
    assert discovered.returncode == 0, discovered.stdout + discovered.stderr
    assert discover_events["events"] == []
    continued, continue_out, continue_manifest, continue_events = _run(
        tmp_path, fixture, request, "continue",
        discover_out / "asset_discovery_manifest.json",
    )
    return continued, continue_out, continue_manifest, continue_events


def test_material_approval_uploads_without_explicit_asset_approval(tmp_path):
    """档HF-4/OBS-246:守卫语义修正后,纯 material 车道不再被计数比较误杀——
    M-001(material 批准)的资产是唯一候选且有依据 → exit 0 并上传;
    M-002 资产因感知哈希去重 rejected(非候选),不上传。"""
    fixture = tmp_path / "fixture"
    _make_fixture(fixture, "url-a", "material-a.png", (210, 40, 40))
    _make_fixture(fixture, "url-b", "material-b.png", (40, 40, 210))
    request = _request(tmp_path, [
        _material("M-001", "url-a", "known_allowed", "material"),
        _material("M-002", "url-b"),
    ])
    result, _, manifest, events = _discover_continue(tmp_path, fixture, request)
    assert result.returncode == 0, result.stdout + result.stderr
    assert [e["asset_id"] for e in events["events"]] == ["A-001"]
    assets = {a["asset_id"]: a for a in manifest["assets"]}
    assert assets["A-001"]["upload"]["status"] == "success"
    assert assets["A-002"]["upload"]["status"] != "success"


def test_source_url_approval_uploads_without_explicit_asset_approval(tmp_path):
    """档HF-4/OBS-246:source_url 批准与 material 批准同为素材级依据,
    纯 source_url 车道同样不再被计数比较误杀 → exit 0 并上传。"""
    fixture = tmp_path / "fixture"
    _make_fixture(fixture, "url-a", "url-a.png", (180, 80, 20))
    _make_fixture(fixture, "url-b", "url-b.png", (20, 160, 80))
    request = _request(tmp_path, [
        _material("M-001", "url-a", "known_allowed", "source_url"),
        _material("M-002", "url-b"),
    ])
    result, _, manifest, events = _discover_continue(tmp_path, fixture, request)
    assert result.returncode == 0, result.stdout + result.stderr
    assert [e["asset_id"] for e in events["events"]] == ["A-001"]
    assets = {a["asset_id"]: a for a in manifest["assets"]}
    assert assets["A-001"]["upload"]["status"] == "success"
    assert assets["A-002"]["upload"]["status"] != "success"


def test_no_repost_overrides_material_approval(tmp_path):
    fixture = tmp_path / "fixture"
    _make_fixture(fixture, "blocked", "blocked.png", (100, 50, 150), no_repost=True)
    request = _request(tmp_path, [
        _material("M-001", "blocked", "known_allowed", "material"),
    ])
    result, _, manifest, events = _discover_continue(tmp_path, fixture, request)
    # 档HF-4/OBS-246:restricted/no-repost 资产 decision=rejected,不是上传候选,
    # 不参与「无依据候选」检查;material 批准无法覆盖 restricted(优先级不变),
    # 资产保持 restricted 且不上传,整体 exit 0。
    assert result.returncode == 0, result.stdout + result.stderr
    assert events["events"] == []
    asset = next(a for a in manifest["assets"] if a["asset_origin"] == "source")
    assert asset["copyright_status"] == "restricted"
    assert asset["upload"]["status"] != "success"


def test_unknown_without_approval_never_uploads(tmp_path):
    fixture = tmp_path / "fixture"
    _make_fixture(fixture, "unknown", "unknown.png", (80, 120, 160))
    request = _request(tmp_path, [_material("M-001", "unknown")])
    result, _, manifest, events = _discover_continue(tmp_path, fixture, request)
    # 档HF-4/OBS-246:无批准依据的上传候选 → FAIL_CLOSED(验收②「含未批准
    # 资产的材料仍被拦」);未知素材的资产不进上传。
    assert result.returncode != 0
    assert events["events"] == []
    assert any("upload candidates without approval basis" in e for e in manifest["errors"])
    asset = next(a for a in manifest["assets"] if a["asset_origin"] == "source")
    assert asset["copyright_status"] == "unknown"
    assert asset["upload"]["status"] != "success"
