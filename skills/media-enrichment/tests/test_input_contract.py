"""Tests for input contract: missing article = error, fail-closed."""

import json
import pytest
from pathlib import Path
from media_enrichment.input_contract import validate_request

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


class TestInputContractPositive:
    def test_valid_example_passes(self, tmp_path):
        # Create a dummy article file matching example SHA
        article = tmp_path / "article.md"
        article.write_text("test")
        # Compute real SHA
        from media_enrichment.input_contract import compute_file_sha256
        sha = compute_file_sha256(article)

        request = json.loads((EXAMPLES / "media_enrichment_request.example.json").read_text(encoding="utf-8"))
        request["article"]["path"] = "article.md"
        request["article"]["sha256"] = sha
        request["config"]["network_mode"] = "offline_fixture"

        req_path = tmp_path / "request.json"
        req_path.write_text(json.dumps(request))
        result = validate_request(req_path)
        assert result.valid, f"Errors: {result.errors}"


class TestMissingArticle:
    def test_missing_article_file_is_error(self, tmp_path):
        request = {
            "schema_version": "1.0", "run_id": "test-missing-article",
            "article": {"path": "nonexistent.md", "sha256": "a" * 64},
            "materials": [{"material_id": "M-001", "aihot_permalink": "https://aihot.virxact.com/items/1", "source_url": "https://example.com/1", "title": "T", "selected_claim_ids": ["C-01"]}],
            "claims": [{"claim_id": "C-01", "claim_text": "A", "material_id": "M-001", "source_url": "https://example.com/1", "source_excerpt": "A"}],
            "config": {"network_mode": "offline_fixture", "upload_mode": "dry_run"},
        }
        req_path = tmp_path / "request.json"
        req_path.write_text(json.dumps(request))
        result = validate_request(req_path)
        assert not result.valid
        assert any("Article file not found" in e for e in result.errors)


class TestDuplicateClaimID:
    def test_duplicate_claim_id_fails(self, tmp_path):
        request = {
            "schema_version": "1.0", "run_id": "test-dup-claim",
            "article": {"path": "article.md", "sha256": "a" * 64},
            "materials": [{"material_id": "M-001", "aihot_permalink": "https://aihot.virxact.com/items/1", "source_url": "https://example.com/1", "title": "T", "selected_claim_ids": ["C-01"]}],
            "claims": [
                {"claim_id": "C-01", "claim_text": "A", "material_id": "M-001", "source_url": "https://example.com/1", "source_excerpt": "A"},
                {"claim_id": "C-01", "claim_text": "B", "material_id": "M-001", "source_url": "https://example.com/1", "source_excerpt": "B"},
            ],
            "config": {"network_mode": "offline_fixture", "upload_mode": "dry_run"},
        }
        req_path = tmp_path / "request.json"
        req_path.write_text(json.dumps(request))
        result = validate_request(req_path)
        assert not result.valid
        assert any("Duplicate claim_id" in e for e in result.errors)


class TestClaimMaterialMismatch:
    def test_nonexistent_material(self, tmp_path):
        request = {
            "schema_version": "1.0", "run_id": "test-mismatch",
            "article": {"path": "article.md", "sha256": "a" * 64},
            "materials": [{"material_id": "M-001", "aihot_permalink": "https://aihot.virxact.com/items/1", "source_url": "https://example.com/1", "title": "T", "selected_claim_ids": ["C-01"]}],
            "claims": [{"claim_id": "C-01", "claim_text": "A", "material_id": "M-999", "source_url": "https://example.com/1", "source_excerpt": "A"}],
            "config": {"network_mode": "offline_fixture", "upload_mode": "dry_run"},
        }
        req_path = tmp_path / "request.json"
        req_path.write_text(json.dumps(request))
        result = validate_request(req_path)
        assert not result.valid
        assert any("non-existent material_id" in e for e in result.errors)

    def test_source_url_mismatch(self, tmp_path):
        request = {
            "schema_version": "1.0", "run_id": "test-url-mismatch",
            "article": {"path": "article.md", "sha256": "a" * 64},
            "materials": [{"material_id": "M-001", "aihot_permalink": "https://aihot.virxact.com/items/1", "source_url": "https://example.com/correct", "title": "T", "selected_claim_ids": ["C-01"]}],
            "claims": [{"claim_id": "C-01", "claim_text": "A", "material_id": "M-001", "source_url": "https://example.com/wrong", "source_excerpt": "A"}],
            "config": {"network_mode": "offline_fixture", "upload_mode": "dry_run"},
        }
        req_path = tmp_path / "request.json"
        req_path.write_text(json.dumps(request))
        result = validate_request(req_path)
        assert not result.valid
        assert any("does not match" in e for e in result.errors)


class TestSHA256Mismatch:
    def test_sha256_mismatch_fails(self, tmp_path):
        article = tmp_path / "article.md"
        article.write_text("test content")
        request = {
            "schema_version": "1.0", "run_id": "test-sha-mismatch",
            "article": {"path": "article.md", "sha256": "0" * 64},
            "materials": [{"material_id": "M-001", "aihot_permalink": "https://aihot.virxact.com/items/1", "source_url": "https://example.com/1", "title": "T", "selected_claim_ids": ["C-01"]}],
            "claims": [{"claim_id": "C-01", "claim_text": "A", "material_id": "M-001", "source_url": "https://example.com/1", "source_excerpt": "A"}],
            "config": {"network_mode": "offline_fixture", "upload_mode": "dry_run"},
        }
        req_path = tmp_path / "request.json"
        req_path.write_text(json.dumps(request))
        result = validate_request(req_path)
        assert not result.valid
        assert any("SHA256 mismatch" in e for e in result.errors)


class TestFailClosed:
    def test_no_request_returned_on_failure(self, tmp_path):
        request = {
            "schema_version": "1.0", "run_id": "test-fail",
            "article": {"path": "article.md", "sha256": "a" * 64},
            "materials": [],
            "claims": [],
            "config": {"network_mode": "offline_fixture", "upload_mode": "dry_run"},
        }
        req_path = tmp_path / "request.json"
        req_path.write_text(json.dumps(request))
        result = validate_request(req_path)
        assert not result.valid
        assert result.request is None


class TestUnknownLicenseConfig:
    def test_allow_unknown_license_rejected(self, tmp_path):
        request = {
            "schema_version": "1.0", "run_id": "test-license",
            "article": {"path": "article.md", "sha256": "a" * 64},
            "materials": [{"material_id": "M-001", "aihot_permalink": "https://aihot.virxact.com/items/1", "source_url": "https://example.com/1", "title": "T", "selected_claim_ids": ["C-01"]}],
            "claims": [{"claim_id": "C-01", "claim_text": "A", "material_id": "M-001", "source_url": "https://example.com/1", "source_excerpt": "A"}],
            "config": {"network_mode": "offline_fixture", "upload_mode": "dry_run", "allow_unknown_license_for_publish": True},
        }
        req_path = tmp_path / "request.json"
        req_path.write_text(json.dumps(request))
        result = validate_request(req_path)
        assert not result.valid
        assert any("allow_unknown_license_for_publish" in e for e in result.errors)
