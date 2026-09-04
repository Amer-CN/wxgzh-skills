"""hotfix5 P0#3 real CLI E2E for stable single_asset approval identity.

All subprocesses use offline fixtures and the deterministic wechat_audit uploader.
No network or real WeChat API is reachable from these tests.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

from media_enrichment.asset_approval import stable_asset_identity  # noqa: E402
from media_enrichment.input_contract import validate_request  # noqa: E402

SRC_URL = "https://www.example-source.test/single-asset-e2e"
PERMALINK = "https://aihot.virxact.com/items/single-asset-e2e"
EVIDENCE_SHA = "e" * 64


def _fixtures(tmp_path: Path) -> Path:
    root = tmp_path / "fixtures"
    shutil.copytree(SKILL_ROOT / "fixtures" / "html", root / "html")
    shutil.copytree(SKILL_ROOT / "fixtures" / "images", root / "images")
    return root


def _write_request(tmp_path: Path, approvals, material_id="M-001", with_chart=False) -> Path:
    article = tmp_path / "final_article.md"
    article.write_text("# 标题\n\n示例论点一。\n\n正文说明两张图。\n", encoding="utf-8")
    claim = {"claim_id": "C-01", "claim_text": "示例论点一",
             "material_id": material_id, "source_url": SRC_URL,
             "source_excerpt": "原文摘录"}
    claims = [claim]
    if with_chart:
        claim.update({"numbers": ["76.2%"], "chart_group": "MMLU",
                      "metric_name": "得分", "series_label": "模型A"})
        claims.append({
            "claim_id": "C-02", "claim_text": "示例论点二",
            "material_id": material_id, "source_url": SRC_URL,
            "source_excerpt": "第二条原文摘录", "numbers": ["68.4%"],
            "chart_group": "MMLU", "metric_name": "得分",
            "series_label": "模型B",
        })
    req = {
        "schema_version": "1.0", "run_id": "e2e-stable-single-asset",
        "article": {"path": "final_article.md",
                    "sha256": hashlib.sha256(article.read_bytes()).hexdigest()},
        "materials": [{"material_id": material_id, "aihot_permalink": PERMALINK,
                       "source_url": SRC_URL, "title": "示例素材",
                       "selected_claim_ids": ["C-01"],
                       "copyright_review": {"status": "unknown"}}],
        "claims": claims,
        "asset_approvals": approvals,
        "config": {"network_mode": "offline_fixture", "upload_mode": "wechat_audit",
                   "max_images_per_material": 4, "max_total_images": 8,
                   "allow_unknown_license_for_publish": False},
    }
    path = tmp_path / "media_request.json"
    path.write_text(json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _cli(tmp_path: Path, fixture_root: Path, phase: str, approvals=(),
         discovery_manifest: Path | None = None, material_id="M-001",
         with_chart=False):
    request = _write_request(
        tmp_path, list(approvals), material_id=material_id, with_chart=with_chart,
    )
    out = tmp_path / f"out-{phase}-{len(list(tmp_path.glob('out-*')))}"
    cmd = [
        sys.executable, "-X", "utf8",
        str(SKILL_ROOT / "scripts" / "run_media_enrichment.py"),
        "--request", str(request), "--output-dir", str(out),
        "--fixture-dir", str(fixture_root / "html"), "--phase", phase,
    ]
    if discovery_manifest is not None:
        cmd.extend(["--discovery-manifest", str(discovery_manifest)])
    result = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=180,
    )
    manifest = json.loads((out / "media_manifest.json").read_text(encoding="utf-8"))
    discovery = json.loads(
        (out / "asset_discovery_manifest.json").read_text(encoding="utf-8"))
    events = json.loads((out / "upload_events.json").read_text(encoding="utf-8"))
    return result, out, manifest, discovery, events


def _approval(discovery: dict, asset_id="A-001", **overrides) -> dict:
    asset = next(a for a in discovery["assets"] if a["asset_id"] == asset_id)
    record = dict(asset)
    record.update({
        "discovery_manifest_sha256": discovery["discovery_manifest_sha256"],
        "approval_id": f"AP-{asset_id}", "approved_scope": "single_asset",
        "approved_by": "user", "approved_at": "2026-07-29T00:00:00Z",
        "approval_evidence_sha256": EVIDENCE_SHA,
        # 77Y/OBS-371 夹具同步:圆形证据封堵后 user 车道须真实动作工件
        # (user_action 三要素);本组测试语义(身份/绑定/上传机制)不变。
        "user_action": {"user": "fixture-user", "action": "approved",
                        "at": "2026-07-29T00:00:00Z"},
    })
    record.update(overrides)
    return record


def _assert_no_upload(manifest, events):
    assert events["events"] == []
    assert all(a["upload"]["status"] != "success" for a in manifest["assets"])


class TestStableSingleAssetIdentityCli:
    def test_discovery_phase_never_uploads_and_emits_stable_manifest(self, tmp_path):
        fixtures = _fixtures(tmp_path)
        result, _, manifest, discovery, events = _cli(tmp_path, fixtures, "discover")
        assert result.returncode == 0, result.stdout + result.stderr
        _assert_no_upload(manifest, events)
        assert {a["asset_id"] for a in discovery["assets"]} == {"A-001", "A-002"}
        for asset in discovery["assets"]:
            assert asset["asset_identity_sha256"] == stable_asset_identity(
                asset["material_id"], asset["source_page_url"],
                asset["resolved_original_url"], asset["asset_sha256"])

    def test_discovery_with_generated_chart_has_zero_upload_attempts(self, tmp_path):
        fixtures = _fixtures(tmp_path)
        result, _, manifest, _, events = _cli(
            tmp_path, fixtures, "discover", with_chart=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        _assert_no_upload(manifest, events)
        charts = [a for a in manifest["assets"] if a["asset_origin"] == "generated"]
        assert charts, "fixture must exercise the generated-chart branch"
        assert all(a["upload"] == {
            "mode": "dry_run", "status": "not_uploaded",
            "remote_url": None, "response_sha256": None,
        } for a in charts)

    def test_inserted_source_image_after_discovery_does_not_change_frozen_upload(self, tmp_path):
        fixtures = _fixtures(tmp_path)
        _, out, _, frozen, _ = _cli(tmp_path, fixtures, "discover")
        approval = _approval(frozen)
        approval2 = _approval(frozen, "A-002")
        Image.new("RGB", (900, 600), (11, 99, 177)).save(
            fixtures / "images" / "inserted.png", "PNG")
        html = (fixtures / "html" / "single-asset-e2e.html").read_text(encoding="utf-8")
        html = html.replace("<img src=", '<img src="https://img.example-source.test/inserted.png">\n<img src=', 1)
        (fixtures / "html" / "single-asset-e2e.html").write_text(html, encoding="utf-8")
        result, _, manifest, _, events = _cli(
            tmp_path, fixtures, "continue", [approval, approval2],
            out / "asset_discovery_manifest.json")
        assert result.returncode == 0, result.stdout + result.stderr
        assert [e["asset_id"] for e in events["events"]] == ["A-001", "A-002"]
        a1 = next(a for a in manifest["assets"] if a["asset_id"] == "A-001")
        assert a1["asset_approval_consumed"] is True
        assert a1["sha256"] == approval["asset_sha256"]

    def test_changed_source_bytes_after_discovery_do_not_replace_frozen_bytes(self, tmp_path):
        fixtures = _fixtures(tmp_path)
        _, out, _, frozen, _ = _cli(tmp_path, fixtures, "discover")
        approval = _approval(frozen)
        approval2 = _approval(frozen, "A-002")
        Image.new("RGB", (1000, 700), (222, 17, 31)).save(
            fixtures / "images" / "e2e-photo-a.png", "PNG")
        result, _, manifest, _, events = _cli(
            tmp_path, fixtures, "continue", [approval, approval2],
            out / "asset_discovery_manifest.json")
        assert result.returncode == 0, result.stdout + result.stderr
        assert [e["asset_id"] for e in events["events"]] == ["A-001", "A-002"]
        a1 = next(a for a in manifest["assets"] if a["asset_id"] == "A-001")
        assert a1["sha256"] == approval["asset_sha256"]

    def test_same_content_different_material_does_not_inherit(self, tmp_path):
        fixtures = _fixtures(tmp_path)
        _, out, _, frozen, _ = _cli(tmp_path, fixtures, "discover")
        approval = _approval(frozen)
        approval2 = _approval(frozen, "A-002")
        result, _, manifest, _, events = _cli(
            tmp_path, fixtures, "continue", [approval, approval2],
            out / "asset_discovery_manifest.json", material_id="M-002")
        assert result.returncode != 0
        _assert_no_upload(manifest, events)
        assert any("material/source changed" in e for e in manifest["errors"])

    def test_modified_discovery_manifest_does_not_upload(self, tmp_path):
        fixtures = _fixtures(tmp_path)
        _, out, _, frozen, _ = _cli(tmp_path, fixtures, "discover")
        approval = _approval(frozen)
        approval2 = _approval(frozen, "A-002")
        frozen_path = out / "asset_discovery_manifest.json"
        tampered = json.loads(frozen_path.read_text(encoding="utf-8"))
        tampered["assets"][0]["source_page_url"] += "?tampered=1"
        frozen_path.write_text(json.dumps(tampered), encoding="utf-8")
        result, _, manifest, _, events = _cli(
            tmp_path, fixtures, "continue", [approval, approval2], frozen_path)
        assert result.returncode != 0
        _assert_no_upload(manifest, events)
        assert any("discovery manifest sha256 invalid" in e for e in manifest["errors"])

    def test_no_repost_detected_at_discovery_overrides_stable_approval(self, tmp_path):
        fixtures = _fixtures(tmp_path)
        html_path = fixtures / "html" / "single-asset-e2e.html"
        html_path.write_text(
            html_path.read_text(encoding="utf-8").replace(
                "<article>", "<article><p>未经许可不得转载</p>", 1,
            ),
            encoding="utf-8",
        )
        _, out, _, frozen, _ = _cli(tmp_path, fixtures, "discover")
        approval = _approval(frozen, "A-001")
        approval2 = _approval(frozen, "A-002")
        result, _, manifest, _, events = _cli(
            tmp_path, fixtures, "continue", [approval, approval2],
            out / "asset_discovery_manifest.json")
        assert result.returncode == 0, result.stdout + result.stderr
        _assert_no_upload(manifest, events)
        target = next(a for a in manifest["assets"] if a["asset_id"] == "A-001")
        assert target["copyright_status"] == "restricted"
        assert target["asset_approval_consumed"] is False
        assert any("restricted/no-repost overrides" in reason for reason in target["reasons"])

    def test_exact_frozen_identity_uploads_only_target(self, tmp_path):
        fixtures = _fixtures(tmp_path)
        _, out, _, frozen, _ = _cli(tmp_path, fixtures, "discover")
        approval = _approval(frozen, "A-001")
        approval2 = _approval(frozen, "A-002")
        result, _, manifest, _, events = _cli(
            tmp_path, fixtures, "continue", [approval, approval2],
            out / "asset_discovery_manifest.json")
        assert result.returncode == 0, result.stdout + result.stderr
        assert [e["asset_id"] for e in events["events"]] == ["A-001", "A-002"]
        assets = {a["asset_id"]: a for a in manifest["assets"]}
        assert assets["A-001"]["asset_approval_consumed"] is True
        assert assets["A-001"]["copyright_status"] == "known_allowed"
        assert assets["A-001"]["upload"]["status"] == "success"
        assert assets["A-002"]["asset_approval_consumed"] is True
        assert assets["A-002"]["copyright_status"] == "known_allowed"
        assert assets["A-002"]["upload"]["status"] == "success"

    def test_tampered_persisted_discovery_file_fails_closed(self, tmp_path):
        fixtures = _fixtures(tmp_path)
        _, out, manifest, frozen, _ = _cli(tmp_path, fixtures, "discover")
        approval = _approval(frozen, "A-001")
        approval2 = _approval(frozen, "A-002")
        target = next(a for a in manifest["assets"] if a["asset_id"] == "A-001")
        Path(target["local_path"]).write_bytes(b"tampered-discovery-bytes")
        result, _, continued, _, events = _cli(
            tmp_path, fixtures, "continue", [approval, approval2],
            out / "asset_discovery_manifest.json")
        assert result.returncode != 0
        assert any("frozen sha256 mismatch" in e for e in continued["errors"])
        assets = {a["asset_id"]: a for a in continued["assets"]}
        assert assets["A-001"]["upload"]["status"] != "success"
        assert assets["A-002"]["upload"]["status"] == "success"

    def test_existing_success_event_skips_reupload_and_reuses_url(self, tmp_path):
        fixtures = _fixtures(tmp_path)
        _, out, _, frozen, _ = _cli(tmp_path, fixtures, "discover")
        approval = _approval(frozen, "A-001")
        approval2 = _approval(frozen, "A-002")
        request = _write_request(tmp_path, [approval, approval2])
        phase_out = tmp_path / "idempotent" / "continue"
        cmd = [
            sys.executable, "-X", "utf8",
            str(SKILL_ROOT / "scripts" / "run_media_enrichment.py"),
            "--request", str(request), "--output-dir", str(phase_out),
            "--fixture-dir", str(fixtures / "html"), "--phase", "continue",
            "--discovery-manifest", str(out / "asset_discovery_manifest.json"),
        ]
        first = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=180)
        assert first.returncode == 0, first.stdout + first.stderr
        first_events = json.loads((phase_out / "upload_events.json").read_text(encoding="utf-8"))["events"]
        first_urls = {e["url"] for e in first_events if e["status"] == "success"}
        second = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=180)
        assert second.returncode == 0, second.stdout + second.stderr
        events = json.loads((phase_out / "upload_events.json").read_text(encoding="utf-8"))["events"]
        assert sum(e["status"] == "success" for e in events) == 2
        skipped = [e for e in events if e["status"] == "skipped_already_uploaded"]
        assert len(skipped) == 2 and {s["url"] for s in skipped} == first_urls

    def test_existing_success_does_not_bypass_frozen_file_sha(self, tmp_path):
        fixtures = _fixtures(tmp_path)
        _, out, manifest, frozen, _ = _cli(tmp_path, fixtures, "discover")
        approval = _approval(frozen, "A-001")
        approval2 = _approval(frozen, "A-002")
        request = _write_request(tmp_path, [approval, approval2])
        phase_out = tmp_path / "tamper-after-success" / "continue"
        cmd = [sys.executable, "-X", "utf8", str(SKILL_ROOT / "scripts" / "run_media_enrichment.py"),
               "--request", str(request), "--output-dir", str(phase_out),
               "--fixture-dir", str(fixtures / "html"), "--phase", "continue",
               "--discovery-manifest", str(out / "asset_discovery_manifest.json")]
        assert subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=180).returncode == 0
        target = next(a for a in manifest["assets"] if a["asset_id"] == "A-001")
        Path(target["local_path"]).write_bytes(b"tampered-after-success")
        second = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=180)
        assert second.returncode != 0
        continued = json.loads((phase_out / "media_manifest.json").read_text(encoding="utf-8"))
        assert any("frozen sha256 mismatch" in e for e in continued["errors"])

    def test_failed_event_is_not_reused(self, tmp_path):
        fixtures = _fixtures(tmp_path)
        _, out, _, frozen, _ = _cli(tmp_path, fixtures, "discover")
        approval = _approval(frozen, "A-001")
        approval2 = _approval(frozen, "A-002")
        request = _write_request(tmp_path, [approval, approval2])
        phase_out = tmp_path / "failed-event" / "continue"
        phase_out.mkdir(parents=True)
        (phase_out / "upload_events.json").write_text(
            json.dumps({"schema_version":"1.0","serial":True,"events":[
                {"asset_id":"A-001","status":"failed","url":None}]}), encoding="utf-8")
        cmd = [sys.executable, "-X", "utf8", str(SKILL_ROOT / "scripts" / "run_media_enrichment.py"),
               "--request", str(request), "--output-dir", str(phase_out),
               "--fixture-dir", str(fixtures / "html"), "--phase", "continue",
               "--discovery-manifest", str(out / "asset_discovery_manifest.json")]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=180)
        assert result.returncode == 0, result.stdout + result.stderr
        events = json.loads((phase_out / "upload_events.json").read_text(encoding="utf-8"))["events"]
        assert any(e.get("status") == "success" for e in events)
        assert not any(e.get("status") == "skipped_already_uploaded" for e in events)

    def test_continue_mirrors_required_outputs_to_stage_root(self, tmp_path):
        fixtures = _fixtures(tmp_path)
        _, out, _, frozen, _ = _cli(tmp_path, fixtures, "discover")
        approval = _approval(frozen, "A-001")
        approval2 = _approval(frozen, "A-002")
        request = _write_request(tmp_path, [approval, approval2])
        phase_out = tmp_path / "stage" / "continue"
        result = subprocess.run([
            sys.executable, "-X", "utf8",
            str(SKILL_ROOT / "scripts" / "run_media_enrichment.py"),
            "--request", str(request), "--output-dir", str(phase_out),
            "--fixture-dir", str(fixtures / "html"), "--phase", "continue",
            "--discovery-manifest", str(out / "asset_discovery_manifest.json"),
        ], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
        assert result.returncode == 0, result.stdout + result.stderr
        for name in ("media_manifest.json", "article_image_bindings.json", "upload_events.json"):
            assert (phase_out / name).read_bytes() == (phase_out.parent / name).read_bytes()


class TestStableApprovalContract:
    def test_valid_stable_approval_passes(self, tmp_path):
        fixtures = _fixtures(tmp_path)
        _, _, _, discovery, _ = _cli(tmp_path, fixtures, "discover")
        assert validate_request(_write_request(tmp_path, [_approval(discovery)])).valid

    def test_display_id_only_approval_is_rejected(self, tmp_path):
        approval = {
            "asset_id": "A-001", "approval_id": "AP-A-001",
            "approved_scope": "single_asset", "approved_by": "user",
            "approved_at": "2026-07-29T00:00:00Z",
            "approval_evidence_sha256": EVIDENCE_SHA,
        }
        validation = validate_request(_write_request(tmp_path, [approval]))
        assert not validation.valid

    def test_forged_stable_identity_is_rejected(self, tmp_path):
        fixtures = _fixtures(tmp_path)
        _, _, _, discovery, _ = _cli(tmp_path, fixtures, "discover")
        approval = _approval(discovery, asset_identity_sha256="f" * 64)
        validation = validate_request(_write_request(tmp_path, [approval]))
        assert not validation.valid
        assert any("stable identity fields" in error for error in validation.errors)
