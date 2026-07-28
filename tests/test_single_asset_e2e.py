"""hotfix4 P0#2 e2e: single_asset copyright approvals are consumed by the REAL
media-enrichment CLI, per-asset, AFTER the real asset_id is produced.

Real subprocess run of scripts/run_media_enrichment.py in offline_fixture mode
(offline page + offline image fixtures, wechat_audit uploader — ZERO network,
ZERO WeChat side effects). One material yields A-001 and A-002; only A-001 is
approved:
  - A-001 enters the upload call (upload_events contains ONLY A-001);
  - A-002 stays skipped/not uploaded;
  - manifest: A-001 known_allowed (+approval fields, consumed=True), A-002 unknown;
  - the material itself stays unknown;
  - an approval for a non-existent asset is recorded as NOT consumed.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

from media_enrichment.input_contract import validate_request  # noqa: E402

H = "e" * 64
SRC_URL = "https://www.example-source.test/single-asset-e2e"
PERMALINK = "https://aihot.virxact.com/items/single-asset-e2e"


def _approval(asset_id, **over):
    rec = {"asset_id": asset_id, "approval_id": f"AP-{asset_id}",
           "approved_scope": "single_asset", "approved_by": "real-user",
           "approved_at": "2026-07-29T00:00:00Z", "evidence": H}
    rec.update(over)
    return rec


def _write_request(tmp_path: Path, approvals):
    article = tmp_path / "final_article.md"
    article.write_text("# 标题\n\n示例论点一。\n\n正文说明两张图。\n", encoding="utf-8")
    req = {
        "schema_version": "1.0", "run_id": "e2e-single-asset",
        "article": {"path": "final_article.md",
                    "sha256": hashlib.sha256(article.read_bytes()).hexdigest()},
        "materials": [{"material_id": "M-001", "aihot_permalink": PERMALINK,
                       "source_url": SRC_URL, "title": "示例素材",
                       "selected_claim_ids": ["C-01"],
                       "copyright_review": {"status": "unknown"}}],
        "claims": [{"claim_id": "C-01", "claim_text": "示例论点一",
                    "material_id": "M-001", "source_url": SRC_URL,
                    "source_excerpt": "原文摘录"}],
        "asset_approvals": approvals,
        "config": {"network_mode": "offline_fixture", "upload_mode": "wechat_audit",
                   "max_images_per_material": 3, "max_total_images": 8,
                   "allow_unknown_license_for_publish": False},
    }
    p = tmp_path / "media_request.json"
    p.write_text(json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _run_cli(tmp_path: Path, approvals):
    req = _write_request(tmp_path, approvals)
    out = tmp_path / "out"
    r = subprocess.run(
        [sys.executable, "-X", "utf8", str(SKILL_ROOT / "scripts" / "run_media_enrichment.py"),
         "--request", str(req), "--output-dir", str(out),
         "--fixture-dir", str(SKILL_ROOT / "fixtures" / "html")],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    manifest = json.loads((out / "media_manifest.json").read_text(encoding="utf-8")) \
        if (out / "media_manifest.json").is_file() else None
    events = json.loads((out / "upload_events.json").read_text(encoding="utf-8")) \
        if (out / "upload_events.json").is_file() else None
    return r, manifest, events


class TestSingleAssetEndToEnd:
    def test_only_approved_asset_uploads(self, tmp_path):
        r, manifest, events = _run_cli(tmp_path, [_approval("A-001")])
        assert r.returncode == 0, r.stdout[-800:] + r.stderr[-400:]
        assets = {a["asset_id"]: a for a in manifest["assets"]}
        assert set(assets) == {"A-001", "A-002"}, assets.keys()

        a1, a2 = assets["A-001"], assets["A-002"]
        # A-001: approved -> known_allowed, eligible, REAL upload call succeeded
        assert a1["copyright_status"] == "known_allowed"
        assert a1["decision"] == "eligible"
        assert a1["asset_approval_consumed"] is True
        assert a1["approval_id"] == "AP-A-001" and a1["approved_scope"] == "single_asset"
        assert a1["approval_evidence"] == H
        assert a1["upload"]["status"] == "success"
        assert a1["upload"]["remote_url"].startswith("https://mmbiz.qpic.cn/")
        # A-002: NOT approved -> unknown, never uploaded (approval must not leak)
        assert a2["copyright_status"] == "unknown"
        assert a2["decision"] == "review_required"
        assert a2["asset_approval_consumed"] is False
        assert a2["approval_id"] is None
        assert a2["upload"]["status"] in ("not_uploaded", "skipped")
        # upload_events: ONLY A-001 ever entered the uploader
        ids = [e["asset_id"] for e in events["events"]]
        assert ids == ["A-001"], ids

    def test_no_approvals_nothing_uploads(self, tmp_path):
        r, manifest, events = _run_cli(tmp_path, [])
        assert r.returncode == 0, r.stdout[-800:]
        assets = {a["asset_id"]: a for a in manifest["assets"]}
        assert all(a["copyright_status"] == "unknown" for a in assets.values())
        assert all(a["upload"]["status"] != "success" for a in assets.values())
        assert events["events"] == []

    def test_unmatched_approval_recorded_as_unconsumed(self, tmp_path):
        r, manifest, events = _run_cli(tmp_path, [_approval("A-999")])
        assert r.returncode == 0
        assert any("A-999" in w and "NOT consumed" in w for w in manifest["warnings"]), \
            manifest["warnings"]
        assert [e["asset_id"] for e in events["events"]] == []
        # nothing silently pretended: no asset carries the unmatched approval
        assert all(not a["asset_approval_consumed"] for a in manifest["assets"])


class TestAssetApprovalContract:
    def _req(self, tmp_path, approvals):
        return validate_request(_write_request(tmp_path, approvals))

    def test_valid_approval_passes(self, tmp_path):
        assert self._req(tmp_path, [_approval("A-001")]).valid is True

    def test_wrong_scope_rejected(self, tmp_path):
        v = self._req(tmp_path, [_approval("A-001", approved_scope="material")])
        assert v.valid is False

    def test_bad_evidence_rejected(self, tmp_path):
        v = self._req(tmp_path, [_approval("A-001", evidence="not-a-hash")])
        # rejected either by the JSON schema pattern or by the 64-hex contract check
        assert v.valid is False
        assert any("64-hex" in e or "[a-fA-F0-9]{64}" in e for e in v.errors), v.errors

    def test_conflicting_approvals_rejected(self, tmp_path):
        v = self._req(tmp_path, [_approval("A-001"),
                                 _approval("A-001", approved_by="someone-else")])
        assert v.valid is False and any("conflicting" in e for e in v.errors)

    def test_duplicate_approval_rejected(self, tmp_path):
        v = self._req(tmp_path, [_approval("A-001"), _approval("A-001")])
        assert v.valid is False and any("duplicate" in e for e in v.errors)
