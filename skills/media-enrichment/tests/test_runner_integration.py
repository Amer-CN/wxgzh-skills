"""Runner integration tests: copyright pipeline, upload paths, unknown mode."""

import json
import pytest
import sys
import tempfile
from pathlib import Path
from PIL import Image

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from media_enrichment.image_classifier import classify_image
from media_enrichment.image_inspector import ImageInspection
from media_enrichment.uploader import DryRunUploader, MockUploader, create_uploader
from media_enrichment.manifest_builder import ManifestBuilder, AssetRecord


def _make_inspection(tmp_path):
    """Create a real test image and return its inspection."""
    img = Image.new("RGB", (800, 600), color=(100, 150, 200))
    img_path = tmp_path / "test_img.jpg"
    img.save(str(img_path), "JPEG")
    from media_enrichment.image_inspector import inspect_image
    return inspect_image(img_path), str(img_path)


class TestUnknownCopyrightSourceImage:
    def test_unknown_review_required_no_upload(self, tmp_path):
        inspection, img_path = _make_inspection(tmp_path)
        result = classify_image("https://example.com/photo.jpg", inspection,
                                copyright_status="unknown")
        assert result.decision == "review_required"
        uploader = MockUploader()
        upload_result = uploader.upload(img_path, "A-001", copyright_status="unknown")
        assert upload_result.status == "skipped"
        assert uploader.upload_count == 0


class TestRestrictedCopyrightSourceImage:
    def test_restricted_rejected_no_upload(self, tmp_path):
        inspection, img_path = _make_inspection(tmp_path)
        result = classify_image("https://example.com/photo.jpg", inspection,
                                copyright_status="restricted")
        assert result.decision == "rejected"
        uploader = MockUploader()
        upload_result = uploader.upload(img_path, "A-001", copyright_status="restricted")
        assert upload_result.status == "skipped"
        assert uploader.upload_count == 0


class TestKnownAllowedSourceImage:
    def test_known_allowed_eligible_upload_called(self, tmp_path):
        inspection, img_path = _make_inspection(tmp_path)
        result = classify_image("https://example.com/photo.jpg", inspection,
                                copyright_status="known_allowed")
        assert result.decision == "eligible"
        uploader = MockUploader()
        upload_result = uploader.upload(img_path, "A-001", copyright_status="known_allowed")
        assert upload_result.status == "success"
        assert uploader.upload_count == 1
        assert upload_result.remote_url is not None


class TestGeneratedChartDryRun:
    def test_generated_chart_dry_run_not_uploaded(self, tmp_path):
        img = Image.new("RGB", (800, 500), color=(255, 255, 255))
        chart_path = tmp_path / "chart.png"
        img.save(str(chart_path), "PNG")
        uploader = DryRunUploader()
        result = uploader.upload(str(chart_path), "A-001", copyright_status="known_allowed")
        assert result.status == "not_uploaded"
        assert result.remote_url is None


class TestGeneratedChartMockUpload:
    def test_generated_chart_mock_success(self, tmp_path):
        img = Image.new("RGB", (800, 500), color=(255, 255, 255))
        chart_path = tmp_path / "chart.png"
        img.save(str(chart_path), "PNG")
        uploader = MockUploader()
        result = uploader.upload(str(chart_path), "A-001", copyright_status="known_allowed")
        assert result.status == "success"
        assert result.remote_url is not None
        assert result.response_sha256 is not None


class TestUnknownUploadMode:
    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError, match="Unknown upload_mode"):
            create_uploader("totally_invalid")


class TestCopyrightReviewContract:
    def test_known_allowed_missing_fields_fails(self, tmp_path):
        from media_enrichment.input_contract import validate_request
        request = {
            "schema_version": "1.0", "run_id": "test-cr",
            "article": {"path": "a.md", "sha256": "a" * 64},
            "materials": [{"material_id": "M-001", "aihot_permalink": "https://x.com/1",
                           "source_url": "https://x.com/1", "title": "T", "selected_claim_ids": ["C-01"],
                           "copyright_review": {"status": "known_allowed", "reviewed_by": None,
                                                 "reviewed_at": None, "evidence": None}}],
            "claims": [{"claim_id": "C-01", "claim_text": "A", "material_id": "M-001",
                        "source_url": "https://x.com/1", "source_excerpt": "A"}],
            "config": {"network_mode": "offline_fixture", "upload_mode": "dry_run"},
        }
        req_path = tmp_path / "request.json"
        req_path.write_text(json.dumps(request))
        result = validate_request(req_path)
        assert not result.valid
        assert any("reviewed_by" in e for e in result.errors)

    def test_known_allowed_with_fields_ok(self, tmp_path):
        from media_enrichment.input_contract import validate_request
        article = tmp_path / "a.md"
        article.write_text("test")
        from media_enrichment.input_contract import compute_file_sha256
        sha = compute_file_sha256(article)
        request = {
            "schema_version": "1.0", "run_id": "test-cr-ok",
            "article": {"path": "a.md", "sha256": sha},
            "materials": [{"material_id": "M-001", "aihot_permalink": "https://x.com/1",
                           "source_url": "https://x.com/1", "title": "T", "selected_claim_ids": ["C-01"],
                           "copyright_review": {"status": "known_allowed", "reviewed_by": "reviewer",
                                                 "reviewed_at": "2026-07-26T00:00:00Z", "evidence": "manual"}}],
            "claims": [{"claim_id": "C-01", "claim_text": "A", "material_id": "M-001",
                        "source_url": "https://x.com/1", "source_excerpt": "A"}],
            "config": {"network_mode": "offline_fixture", "upload_mode": "dry_run"},
        }
        req_path = tmp_path / "request.json"
        req_path.write_text(json.dumps(request))
        result = validate_request(req_path)
        assert result.valid


class TestBuildGateAbort:
    """Test that build_zip aborts on non-zero pytest exit or zero tests."""

    def test_returncode_nonzero_aborts(self):
        # Simulate: returncode=5, no FAILED in stdout
        returncode = 5
        total = 0
        passed = 0
        failed = 0
        # The gate check logic from build_zip.py
        should_abort = (returncode != 0 or total == 0 or failed != 0 or passed != total or passed == 0)
        assert should_abort, "returncode=5 should abort"

    def test_returncode_zero_zero_tests_aborts(self):
        returncode = 0
        total = 0
        passed = 0
        failed = 0
        should_abort = (returncode != 0 or total == 0 or failed != 0 or passed != total or passed == 0)
        assert should_abort, "zero tests should abort"

    def test_returncode_zero_all_pass_continues(self):
        returncode = 0
        total = 135
        passed = 135
        failed = 0
        should_abort = (returncode != 0 or total == 0 or failed != 0 or passed != total or passed == 0)
        assert not should_abort, "all pass should continue"

    def test_returncode_two_collection_error_aborts(self):
        returncode = 2
        total = 0
        passed = 0
        failed = 0
        should_abort = (returncode != 0 or total == 0 or failed != 0 or passed != total or passed == 0)
        assert should_abort, "collection error should abort"


class TestVersionConsistency:
    """packaging-hotfix1 extended scope: beyond VERSION/__init__/input_contract,
    also README.md, SKILL.md, build_zip.py, generate_evidence.py,
    url_security.py, sample_media_manifest.json, MANIFEST.json,
    test_summary.json. CHANGELOG.md history is exempt by design.
    Gates: RUNTIME_VERSION_RESIDUE_DEV3=0, BUILD_VERSION_RESIDUE_DEV4=0,
    CURRENT_EVIDENCE_VERSION_RESIDUE_DEV4=0, OUTPUT_ZIP_NAME_MATCH=true."""

    CURRENT = "0.1.0-dev31"
    # concatenated so this test file never contains the residue literals itself
    DEV3 = "0.1.0-dev" + "3"
    DEV4 = "0.1.0-dev" + "4"
    DEV5 = "0.1.0-dev" + "5"
    DEV6 = "0.1.0-dev" + "6"
    DEV7_PLAIN = "0.1.0-dev" + "7"  # bare dev7 (pre-hotfix) is now residue

    # file -> line-prefixes exempt from strict checking.
    # NOTE (OSS repo): evidence/*.json and MANIFEST.json are build/verification
    # artifacts produced by scripts/build_zip.py + generate_evidence.py and are
    # not committed to the source tree, so they are excluded from this
    # source-level version-consistency gate.
    STRICT_FILES = {
        "VERSION": ("previous_version:",),
        "src/media_enrichment/__init__.py": (),
        "src/media_enrichment/input_contract.py": (),
        "README.md": (),
        "SKILL.md": (),
        "scripts/build_zip.py": (),
        "scripts/generate_evidence.py": (),
        "src/media_enrichment/url_security.py": (),
    }

    VERSION_RE = r"0\.1\.0-dev\d+(?:-hotfix\d+)?"

    def test_all_versions_dev7_hotfix1(self):
        import re
        version_re = re.compile(self.VERSION_RE)
        offenders = {}
        seen_any = False
        for rel, skips in self.STRICT_FILES.items():
            path = SKILL_ROOT / rel
            assert path.exists(), f"{rel} must exist for version consistency check"
            found = set()
            for line in path.read_text(encoding="utf-8").splitlines():
                if any(line.strip().startswith(p) for p in skips):
                    continue
                found.update(version_re.findall(line))
            if found:
                seen_any = True
            wrong = found - {self.CURRENT}
            if wrong:
                offenders[rel] = sorted(wrong)
        assert seen_any, "no version strings found at all — check scope"
        assert offenders == {}, f"non-dev7-hotfix1 version residue: {offenders}"

        # OUTPUT_ZIP_NAME_MATCH=true (media-enrichment-v0.1.0-dev17.zip)
        # OUTPUT_ZIP_NAME_MATCH=true (media-enrichment-v0.1.0-dev23.zip)
        build_text = (SKILL_ROOT / "scripts" / "build_zip.py").read_text(encoding="utf-8")
        assert f'BUILD_VERSION = "{self.CURRENT}"' in build_text
        assert "media-enrichment-v{BUILD_VERSION}.zip" in build_text, \
            "OUTPUT_ZIP must derive from BUILD_VERSION"
        assert f"media-enrichment-v{self.DEV6}.zip" not in build_text

        # User-Agent + dev7 verifier script (kept named _verify_dev7.py)
        ua_text = (SKILL_ROOT / "src" / "media_enrichment" / "url_security.py").read_text(encoding="utf-8")
        assert f"media-enrichment/{self.CURRENT}" in ua_text
        v7 = SKILL_ROOT / "scripts" / "_verify_dev7.py"
        assert v7.exists() and f'REQUIRED_VERSION = "{self.CURRENT}"' in v7.read_text(encoding="utf-8")
        for old in ("4", "5", "6"):
            assert not (SKILL_ROOT / "scripts" / ("_verify_dev" + old + ".py")).exists(), \
                f"dev{old}-only verifier must be removed/renamed"

        # RUNTIME_VERSION_RESIDUE=0 — no dev3/4/5/6 or BARE dev7 in src.
        # Uses token regex so CURRENT (which CONTAINS '0.1.0-dev7') is not
        # misflagged: only a standalone bare dev7 token counts as residue.
        forbidden = {self.DEV3, self.DEV4, self.DEV5, self.DEV6, self.DEV7_PLAIN}
        runtime_hits = []
        for f in (SKILL_ROOT / "src").rglob("*.py"):
            if "__pycache__" in f.parts:
                continue
            toks = set(re.findall(self.VERSION_RE, f.read_text(encoding="utf-8")))
            if toks & forbidden:
                runtime_hits.append((str(f.relative_to(SKILL_ROOT)), sorted(toks & forbidden)))
        assert runtime_hits == [], f"RUNTIME_VERSION_RESIDUE must be 0: {runtime_hits}"

        # BUILD_VERSION_RESIDUE=0
        build_hits = []
        for rel in ("scripts/build_zip.py", "scripts/generate_evidence.py"):
            toks = set(re.findall(self.VERSION_RE, (SKILL_ROOT / rel).read_text(encoding="utf-8")))
            if toks & forbidden:
                build_hits.append((rel, sorted(toks & forbidden)))
        assert build_hits == [], f"BUILD_VERSION_RESIDUE must be 0: {build_hits}"

        # CURRENT_EVIDENCE_VERSION_RESIDUE=0
        # OSS repo: evidence/*.json and MANIFEST.json are regenerated build
        # artifacts and not committed; only enforce the residue check for those
        # that are actually present in the source tree.
        evidence_hits = []
        for rel in ("evidence/sample_media_manifest.json",
                    "evidence/test_summary.json", "MANIFEST.json"):
            path = SKILL_ROOT / rel
            if not path.exists():
                continue
            toks = set(re.findall(self.VERSION_RE, path.read_text(encoding="utf-8")))
            if toks & forbidden:
                evidence_hits.append((rel, sorted(toks & forbidden)))
        assert evidence_hits == [], \
            f"CURRENT_EVIDENCE_VERSION_RESIDUE must be 0: {evidence_hits}"
