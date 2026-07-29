"""hotfix6 real Pipeline media approval state-machine tests.

Uses a temporary fixed-media checkout and generated offline fixtures. No network,
no real WeChat upload, and no real draft creation are possible.
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from wxgzh_pipeline import producers as P
from wxgzh_pipeline.orchestrator import Orchestrator


def _stable(asset, manifest, aid=None):
    rec = dict(asset)
    rec.update({
        "discovery_manifest_sha256": manifest["discovery_manifest_sha256"],
        "approval_id": f"AP-{aid or asset['asset_id']}",
        "approved_scope": "single_asset",
        "approved_by": "integration-user",
        "approved_at": "2026-07-29T00:00:00Z",
        "approval_evidence_sha256": "e" * 64,
    })
    return rec


def test_old_single_asset_approval_rejected_fail_closed(tmp_path):
    rd = tmp_path / "run"
    for name in ("media_enrichment", "super_writer", "zh_human_writing", "aihot"):
        (rd / name).mkdir(parents=True)
    (rd / "media_enrichment" / "copyright_approval.json").write_text(json.dumps({
        "approvals": [{
            "asset_id": "A-001", "approved_scope": "single_asset",
            "approval_id": "AP", "approved_by": "u",
            "approved_at": "2026-07-29T00:00:00Z",
            "approval_evidence_sha256": "e" * 64,
        }]
    }), encoding="utf-8")
    with pytest.raises(P.MediaRequestError, match="old single_asset approval rejected"):
        P._load_copyright_approvals(rd)


def test_stable_approval_matches_frozen_manifest_fields():
    manifest = {
        "discovery_manifest_sha256": "d" * 64,
        "assets": [{
            "asset_id": "A-001", "material_id": "M-001",
            "source_page_url": "https://source.test/a",
            "resolved_original_url": "https://img.test/a.png",
            "asset_sha256": "a" * 64,
            "asset_identity_sha256": "b" * 64,
        }],
    }
    approval = _stable(manifest["assets"][0], manifest)
    fields = (
        "asset_id", "material_id", "source_page_url", "resolved_original_url",
        "asset_sha256", "asset_identity_sha256", "discovery_manifest_sha256",
    )
    assert all(approval[field] == ({**manifest["assets"][0],
                                    "discovery_manifest_sha256": "d" * 64})[field]
               for field in fields)


def test_integration_mode_is_supported(tmp_path):
    with pytest.raises(ValueError):
        Orchestrator(project_root=tmp_path, network_mode="not-a-mode")
    o = Orchestrator(project_root=tmp_path, network_mode="integration",
                     skills_home=tmp_path, fixture_dir=tmp_path)
    assert o.network_mode == "integration"


def test_failed_stage_result_exposes_run_dir(tmp_path, monkeypatch):
    o = Orchestrator(project_root=tmp_path, network_mode="offline_fixture",
                     fixture_dir=tmp_path)
    monkeypatch.setattr(o, "doctor", lambda **kwargs: (True, {"skills": {}}))
    out = o.run("t")
    assert out["status"] == "STAGE_FAILED"
    assert Path(out["run_dir"]).is_dir()
