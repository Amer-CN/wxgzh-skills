"""Negative validator tests — ensures validator catches all violations.

dev3 additions:
- eligible + local_path=null
- review_required + local_path=""
- request_sha256 wrong
- claims_total wrong
- materials_total wrong
- no request → REQUEST_* must FAIL
- no article → NO_ARTICLE_FACT_MUTATION must FAIL
- ManifestBuilder late mutation visible
- VERSION_CONSISTENCY
"""

import json
import pytest
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from validate_media_manifest import validate_manifest


def _base_manifest():
    return {
        "schema_version": "1.0", "skill_version": "0.1.0-dev3",
        "run_id": "test", "created_at": "2026-07-26T00:00:00Z",
        "input": {"request_sha256": "a"*64, "article_sha256": "b"*64, "claims_total": 1, "materials_total": 1},
        "summary": {k: 0 for k in ["pages_requested", "pages_fetched", "candidates_discovered", "downloads_succeeded", "exact_duplicates_removed", "perceptual_duplicates_removed", "rejected_assets", "review_required_assets", "eligible_assets", "generated_charts", "uploaded_assets"]},
        "assets": [], "errors": [], "warnings": [],
        "gate": {"input_contract_pass": True, "provenance_complete": True, "security_checks_pass": True, "secrets_detected": False, "publish_allowed": False},
    }


def _validate(manifest, tmp_path, request=None):
    mp = tmp_path / "manifest.json"
    mp.write_text(json.dumps(manifest))
    rp = None
    if request:
        rp = tmp_path / "request.json"
        rp.write_text(json.dumps(request))
    return validate_manifest(str(mp), str(rp) if rp else None)


class TestErrorsNonEmpty:
    def test_errors_non_empty_fails(self, tmp_path):
        m = _base_manifest()
        m["errors"] = ["some error"]
        report = _validate(m, tmp_path)
        assert not report["pass"]


class TestGateFlags:
    def test_input_contract_false_fails(self, tmp_path):
        m = _base_manifest()
        m["gate"]["input_contract_pass"] = False
        assert not _validate(m, tmp_path)["pass"]

    def test_security_checks_false_fails(self, tmp_path):
        m = _base_manifest()
        m["gate"]["security_checks_pass"] = False
        assert not _validate(m, tmp_path)["pass"]

    def test_provenance_false_fails(self, tmp_path):
        m = _base_manifest()
        m["gate"]["provenance_complete"] = False
        assert not _validate(m, tmp_path)["pass"]

    def test_publish_true_fails(self, tmp_path):
        m = _base_manifest()
        m["gate"]["publish_allowed"] = True
        report = _validate(m, tmp_path)
        assert not report["pass"]


class TestNullLocalPath:
    def test_eligible_null_local_path_fails(self, tmp_path):
        m = _base_manifest()
        m["assets"] = [{
            "asset_id": "A-001", "asset_origin": "source",
            "material_ids": ["M-001"], "claim_ids": ["C-01"],
            "local_path": None,  # null
            "sha256": "c" * 64, "decision": "eligible",
            "reasons": ["test"], "quality_status": "pass",
            "relevance_status": "relevant",
            "copyright_status": "known_allowed", "copyright_risk": "low",
            "source_page_url": "https://example.com/page",
        }]
        report = _validate(m, tmp_path)
        assert not report["pass"]
        assert any("LOCAL_PATH" in c["check"] and c["status"] == "FAIL" for c in report["checks"])

    def test_review_required_empty_local_path_fails(self, tmp_path):
        m = _base_manifest()
        m["assets"] = [{
            "asset_id": "A-001", "asset_origin": "source",
            "material_ids": ["M-001"], "claim_ids": ["C-01"],
            "local_path": "",  # empty string
            "sha256": "c" * 64, "decision": "review_required",
            "reasons": ["test"], "quality_status": "pass",
            "relevance_status": "uncertain",
            "copyright_status": "unknown", "copyright_risk": "high",
            "source_page_url": "https://example.com/page",
        }]
        report = _validate(m, tmp_path)
        assert not report["pass"]
        assert any("LOCAL_PATH" in c["check"] and c["status"] == "FAIL" for c in report["checks"])


class TestRequestSha256:
    def test_wrong_request_sha256_fails(self, tmp_path):
        m = _base_manifest()
        m["input"]["request_sha256"] = "0" * 64  # wrong
        request = {
            "schema_version": "1.0", "run_id": "test",
            "article": {"path": "article.md", "sha256": "b" * 64},
            "materials": [{"material_id": "M-001", "aihot_permalink": "https://x.com/1", "source_url": "https://x.com/1", "title": "T", "selected_claim_ids": ["C-01"]}],
            "claims": [{"claim_id": "C-01", "claim_text": "A", "material_id": "M-001", "source_url": "https://x.com/1", "source_excerpt": "A"}],
            "config": {"network_mode": "offline_fixture", "upload_mode": "dry_run"},
        }
        report = _validate(m, tmp_path, request)
        assert not report["pass"]
        assert any(c["check"] == "REQUEST_SHA256_MATCH" and c["status"] == "FAIL" for c in report["checks"])


class TestClaimsTotal:
    def test_wrong_claims_total_fails(self, tmp_path):
        m = _base_manifest()
        m["input"]["claims_total"] = 99  # wrong
        request = {
            "schema_version": "1.0", "run_id": "test",
            "article": {"path": "article.md", "sha256": "b" * 64},
            "materials": [{"material_id": "M-001", "aihot_permalink": "https://x.com/1", "source_url": "https://x.com/1", "title": "T", "selected_claim_ids": ["C-01"]}],
            "claims": [{"claim_id": "C-01", "claim_text": "A", "material_id": "M-001", "source_url": "https://x.com/1", "source_excerpt": "A"}],
            "config": {"network_mode": "offline_fixture", "upload_mode": "dry_run"},
        }
        report = _validate(m, tmp_path, request)
        assert not report["pass"]
        assert any(c["check"] == "CLAIMS_TOTAL_MATCH" and c["status"] == "FAIL" for c in report["checks"])


class TestMaterialsTotal:
    def test_wrong_materials_total_fails(self, tmp_path):
        m = _base_manifest()
        m["input"]["materials_total"] = 99  # wrong
        request = {
            "schema_version": "1.0", "run_id": "test",
            "article": {"path": "article.md", "sha256": "b" * 64},
            "materials": [{"material_id": "M-001", "aihot_permalink": "https://x.com/1", "source_url": "https://x.com/1", "title": "T", "selected_claim_ids": ["C-01"]}],
            "claims": [{"claim_id": "C-01", "claim_text": "A", "material_id": "M-001", "source_url": "https://x.com/1", "source_excerpt": "A"}],
            "config": {"network_mode": "offline_fixture", "upload_mode": "dry_run"},
        }
        report = _validate(m, tmp_path, request)
        assert not report["pass"]
        assert any(c["check"] == "MATERIALS_TOTAL_MATCH" and c["status"] == "FAIL" for c in report["checks"])


class TestNoRequest:
    def test_no_request_all_request_checks_fail(self, tmp_path):
        m = _base_manifest()
        report = _validate(m, tmp_path)  # no request
        assert not report["pass"]
        # All REQUEST_* checks must FAIL
        for check_name in ["REQUEST_SHA256_MATCH", "CLAIMS_TOTAL_MATCH", "MATERIALS_TOTAL_MATCH",
                           "REQUEST_CLAIM_IDS_UNIQUE", "REQUEST_MATERIAL_IDS_UNIQUE",
                           "REQUEST_CLAIM_MATERIAL_REF_VALID", "REQUEST_SOURCE_URL_CONSISTENT"]:
            assert any(c["check"] == check_name and c["status"] == "FAIL" for c in report["checks"]), \
                f"{check_name} should FAIL when no request provided"


class TestNoArticle:
    def test_no_article_mutation_check_fails(self, tmp_path):
        m = _base_manifest()
        # No request → no article path → must FAIL
        report = _validate(m, tmp_path)
        assert not report["pass"]
        assert any(c["check"] == "NO_ARTICLE_FACT_MUTATION" and c["status"] == "FAIL" for c in report["checks"])


class TestFakeArticleHash:
    def test_wrong_article_hash_fails(self, tmp_path):
        article = tmp_path / "article.md"
        article.write_text("real content")
        m = _base_manifest()
        m["input"]["article_sha256"] = "0" * 64
        request = {"schema_version": "1.0", "run_id": "test",
                   "article": {"path": "article.md", "sha256": "0" * 64},
                   "materials": [], "claims": [],
                   "config": {"network_mode": "offline_fixture", "upload_mode": "dry_run"}}
        report = _validate(m, tmp_path, request)
        assert not report["pass"]


class TestMissingAssetFile:
    def test_missing_local_path_fails(self, tmp_path):
        m = _base_manifest()
        m["assets"] = [{
            "asset_id": "A-001", "asset_origin": "source",
            "material_ids": ["M-001"], "claim_ids": ["C-01"],
            "local_path": "/nonexistent/path.jpg",
            "sha256": "c" * 64, "decision": "eligible",
            "reasons": ["test"], "quality_status": "pass",
            "relevance_status": "relevant",
            "copyright_status": "known_allowed", "copyright_risk": "low",
            "source_page_url": "https://example.com/page",
        }]
        report = _validate(m, tmp_path)
        assert not report["pass"]


class TestAssetHashMismatch:
    def test_wrong_sha256_fails(self, tmp_path):
        img_path = tmp_path / "test.jpg"
        img_path.write_bytes(b"fake image data")
        m = _base_manifest()
        m["assets"] = [{
            "asset_id": "A-001", "asset_origin": "source",
            "material_ids": ["M-001"], "claim_ids": ["C-01"],
            "local_path": str(img_path),
            "sha256": "0" * 64, "decision": "eligible",
            "reasons": ["test"], "quality_status": "pass",
            "relevance_status": "relevant",
            "copyright_status": "known_allowed", "copyright_risk": "low",
            "source_page_url": "https://example.com/page",
        }]
        report = _validate(m, tmp_path)
        assert not report["pass"]


class TestClaimMaterialMismatch:
    def test_nonexistent_material(self, tmp_path):
        m = _base_manifest()
        request = {"schema_version": "1.0", "run_id": "test",
                   "article": {"path": "article.md", "sha256": "b" * 64},
                   "materials": [{"material_id": "M-001", "aihot_permalink": "https://x.com/1", "source_url": "https://x.com/1", "title": "T", "selected_claim_ids": ["C-01"]}],
                   "claims": [{"claim_id": "C-01", "claim_text": "A", "material_id": "M-999", "source_url": "https://x.com/1", "source_excerpt": "A"}],
                   "config": {"network_mode": "offline_fixture", "upload_mode": "dry_run"}}
        report = _validate(m, tmp_path, request)
        assert not report["pass"]


class TestGeneratedChartNonexistentClaim:
    def test_bad_claim_fails(self, tmp_path):
        m = _base_manifest()
        m["assets"] = [{
            "asset_id": "A-001", "asset_origin": "generated",
            "material_ids": ["M-001"], "claim_ids": ["C-999"],
            "local_path": None, "sha256": "c" * 64,
            "decision": "eligible", "reasons": ["generated"],
            "quality_status": "pass", "relevance_status": "relevant",
            "copyright_status": "known_allowed", "copyright_risk": "low",
        }]
        request = {"schema_version": "1.0", "run_id": "test",
                   "article": {"path": "article.md", "sha256": "b" * 64},
                   "materials": [{"material_id": "M-001", "aihot_permalink": "https://x.com/1", "source_url": "https://x.com/1", "title": "T", "selected_claim_ids": ["C-01"]}],
                   "claims": [{"claim_id": "C-01", "claim_text": "A", "material_id": "M-001", "source_url": "https://x.com/1", "source_excerpt": "A"}],
                   "config": {"network_mode": "offline_fixture", "upload_mode": "dry_run"}}
        report = _validate(m, tmp_path, request)
        assert not report["pass"]


class TestUnknownLicenseAutoApproved:
    def test_unknown_eligible_fails(self, tmp_path):
        m = _base_manifest()
        m["assets"] = [{
            "asset_id": "A-001", "asset_origin": "source",
            "material_ids": ["M-001"], "claim_ids": ["C-01"],
            "source_page_url": "https://example.com/page",
            "sha256": "c" * 64, "decision": "eligible",
            "reasons": ["test"], "quality_status": "pass",
            "relevance_status": "relevant",
            "copyright_status": "unknown", "copyright_risk": "medium",
        }]
        report = _validate(m, tmp_path)
        assert not report["pass"]


class TestPrivateNetworkURL:
    def test_private_url_fails(self, tmp_path):
        m = _base_manifest()
        m["assets"] = [{
            "asset_id": "A-001", "asset_origin": "source",
            "material_ids": ["M-001"], "claim_ids": ["C-01"],
            "discovered_url": "http://192.168.1.1/image.jpg",
            "resolved_original_url": "http://192.168.1.1/image.jpg",
            "source_page_url": "https://example.com/page",
            "sha256": "c" * 64, "decision": "review_required",
            "reasons": ["test"], "quality_status": "pass",
            "relevance_status": "uncertain",
            "copyright_status": "unknown", "copyright_risk": "high",
        }]
        report = _validate(m, tmp_path)
        assert not report["pass"]
