"""77G/OBS-316: zero-image delivery falls back instead of killing the run."""

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

from wxgzh_pipeline import producers as PR


def _write_discover(run_dir: Path, manifest: dict) -> Path:
    discover = run_dir / "media_enrichment" / "discover"
    discover.mkdir(parents=True)
    path = discover / "media_manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return path


def test_zero_candidates_with_bounded_fetch_errors_are_recoverable(tmp_path):
    _write_discover(tmp_path, {
        "run_id": "zero", "input": {"claims_total": 1},
        "summary": {"eligible_assets": 0, "review_required_assets": 0},
        "errors": ["Failed to fetch page for M-001"],
    })
    result = PR._discover_degraded_recoverable(
        tmp_path / "media_enrichment" / "discover")
    assert result == {
        "errors": ["Failed to fetch page for M-001"],
        "zero_image_fallback": True,
    }


def test_zero_image_fallback_does_not_mask_fatal_media_errors(tmp_path):
    _write_discover(tmp_path, {
        "run_id": "fatal", "input": {"claims_total": 1},
        "summary": {"eligible_assets": 0, "review_required_assets": 0},
        "errors": ["SECRET_DETECTED: token=secret"],
    })
    assert PR._discover_degraded_recoverable(
        tmp_path / "media_enrichment" / "discover") is None


def test_zero_readiness_arms_empty_shortfall_contract_only(tmp_path):
    approval = tmp_path / "copyright_approval.json"
    armed = PR._write_zero_image_fallback_approval(
        {"summary": {"approvable": 0}}, approval, "a" * 64)
    contract = json.loads(approval.read_text(encoding="utf-8"))
    assert armed is True
    assert contract["mode"] == "zero_image_shortfall"
    assert contract["approvals"] == []

    armed_again = PR._write_zero_image_fallback_approval(
        {"summary": {"approvable": 1}}, tmp_path / "unused.json", "b" * 64)
    assert armed_again is False


def test_blacklisted_asset_remains_rejected_under_fallback():
    asset = {
        "asset_id": "A-001", "decision": "rejected",
        "reasons": ["user image rejected: domain blacklisted: img.ithome.com (76C)"],
    }
    readiness_record = {
        "asset_id": "A-001", "approvable": False,
        "approvable_blockers": [
            "decision=rejected — 非可批准状态,不得写入批准合同"],
    }
    assert asset["decision"] == "rejected"
    assert readiness_record["approvable"] is False


def test_empty_bindings_select_no_live_cover(tmp_path):
    media = tmp_path / "media_enrichment"
    media.mkdir()
    bindings = media / "article_image_bindings.json"
    bindings.write_text(json.dumps({"body_images": []}), encoding="utf-8")
    assert PR._select_live_cover(SimpleNamespace(run_dir=tmp_path)) == (None, None)


def test_gzh_renderer_accepts_zero_body_images(tmp_path):
    repo_root = Path(__file__).resolve().parents[3]
    renderer = repo_root / "skills" / "gzh-design" / "scripts" / "render_article.py"
    article = tmp_path / "article.md"
    bindings = tmp_path / "bindings.json"
    article.write_text("# 标题\n\n正文段落。\n", encoding="utf-8")
    bindings.write_text(json.dumps({"body_images": []}), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(renderer),
         "--article", str(article), "--bindings", str(bindings),
         "--output-dir", str(tmp_path), "--theme", "smartisan"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    html = (tmp_path / "final.html").read_text(encoding="utf-8")
    assert (tmp_path / "component_usage_report.json").is_file()
    assert "<img" not in html.lower()
