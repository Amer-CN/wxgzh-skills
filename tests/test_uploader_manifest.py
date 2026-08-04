"""Tests for uploader, manifest idempotency, copyright control."""

import json
import pytest
from pathlib import Path
from media_enrichment.uploader import (
    DryRunUploader, MockUploader, sanitize_response, scan_for_secrets,
    create_uploader, _scrub_token, timed_upload, UploadResult,
    WechatImageHostUploader,
)
from media_enrichment.manifest_builder import ManifestBuilder, AssetRecord


class TestDryRunUploader:
    def test_dry_run_not_uploaded(self):
        result = DryRunUploader().upload("/nonexistent/path.jpg")
        assert result.status == "not_uploaded"
        assert result.remote_url is None


class TestMockUploader:
    def test_mock_success(self):
        # Need a real file for MIME detection
        from PIL import Image
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            Image.new("RGB", (100, 100)).save(f.name, "PNG")
            result = MockUploader().upload(f.name, "A-001", copyright_status="known_allowed")
        assert result.status == "success"
        assert result.remote_url is not None
        assert result.actual_mime == "image/png"

    def test_mock_failure(self):
        result = MockUploader(simulate_failure=True).upload("/path", "A-001", copyright_status="known_allowed")
        assert result.status == "failed"

    def test_mock_timeout(self):
        result = MockUploader(simulate_timeout=True).upload("/path", "A-001", copyright_status="known_allowed")
        assert result.status == "failed"

    def test_unknown_copyright_skips_upload(self):
        result = MockUploader().upload("/path", "A-001", copyright_status="unknown")
        assert result.status == "skipped"

    def test_restricted_copyright_skips_upload(self):
        result = MockUploader().upload("/path", "A-001", copyright_status="restricted")
        assert result.status == "skipped"


class TestUnknownUploadMode:
    def test_unknown_mode_raises_error(self):
        with pytest.raises(ValueError, match="Unknown upload_mode"):
            create_uploader("totally_invalid_mode")

    def test_dry_run_accepted(self):
        u = create_uploader("dry_run")
        assert isinstance(u, DryRunUploader)


class TestTokenScrubbing:
    def test_access_token_scrubbed(self):
        text = "https://api.example.com/upload?access_token=secret123&other=val"
        scrubbed = _scrub_token(text)
        assert "secret123" not in scrubbed
        assert "access_token=[REDACTED]" in scrubbed


class TestUploadObservability:
    def test_timed_upload_records_observation_fields_without_token(self):
        class FakeUploader:
            def upload(self, local_path, asset_id, copyright_status):
                return UploadResult(
                    mode="wechat_image_host", status="failed",
                    http_status=401, wechat_errcode=40164,
                    wechat_errmsg="invalid ip", request_elapsed_seconds=0.25,
                    endpoint_path="/cgi-bin/media/uploadimg",
                    request_attempt_index=1,
                )
        events = []
        timed_upload(FakeUploader(), events, "unused.png", "A-003", "known_allowed")
        event = events[0]
        assert event["http_status"] == 401
        assert event["wechat_errcode"] == 40164
        assert event["wechat_errmsg"] == "invalid ip"
        assert event["endpoint_path"] == "/cgi-bin/media/uploadimg"
        assert event["media_id"] is None
        assert "access_token" not in json.dumps(event)


class TestCredentialSourceAndTokenCache:
    def test_missing_credentials_fail_closed(self, monkeypatch):
        monkeypatch.delenv("WECHAT_APP_ID", raising=False)
        monkeypatch.delenv("WECHAT_APP_SECRET", raising=False)
        result = WechatImageHostUploader().upload("missing.png", "A-003", "known_allowed")
        assert result.status == "failed"
        assert result.media_id is None

    def test_token_cached_within_uploader_instance(self, monkeypatch):
        import sys
        from types import SimpleNamespace
        monkeypatch.setenv("WECHAT_APP_ID", "wx-test-id")
        monkeypatch.setenv("WECHAT_APP_SECRET", "test-secret")
        calls = []
        response = SimpleNamespace(
            status_code=200,
            json=lambda: {"access_token": "test-token-value"},
        )
        fake_requests = SimpleNamespace(
            get=lambda *args, **kwargs: (calls.append(1) or response),
        )
        monkeypatch.setitem(sys.modules, "requests", fake_requests)
        uploader = WechatImageHostUploader()
        assert uploader._get_access_token() == ("test-token-value", "")
        assert uploader._get_access_token() == ("test-token-value", "")
        assert len(calls) == 1


class TestSecretsSanitization:
    def test_sanitize_response_removes_token(self):
        data = {"url": "https://cdn.example.com/img.jpg", "token": "secret123"}
        s = sanitize_response(data)
        assert s["token"] == "[REDACTED]"
        assert s["url"] == "https://cdn.example.com/img.jpg"

    def test_scan_finds_token(self):
        findings = scan_for_secrets({"access_token": "abc123"})
        assert any("token" in f.lower() for f in findings)

    def test_scan_clean(self):
        findings = scan_for_secrets({"url": "https://cdn.example.com/img.jpg", "size": 1024})
        assert len(findings) == 0

    def test_secrets_detected_field_not_flagged(self):
        findings = scan_for_secrets({"secrets_detected": False})
        assert len(findings) == 0


class TestManifestIdempotency:
    def test_build_idempotent(self):
        builder = ManifestBuilder(
            run_id="test", request_sha256="a" * 64, article_sha256="b" * 64,
            claims_total=1, materials_total=1,
        )
        builder.add_asset(AssetRecord(
            asset_id="A-001", asset_origin="source", material_ids=["M-001"], claim_ids=["C-01"],
            decision="eligible", reasons=["test"], sha256="c" * 64, source_page_url="https://example.com",
        ))
        m1 = builder.build()
        m2 = builder.build()
        m3 = builder.build()
        # Same summary counts (no double counting)
        assert m1["summary"]["eligible_assets"] == m2["summary"]["eligible_assets"] == m3["summary"]["eligible_assets"]
        assert m1["summary"]["eligible_assets"] == 1

    def test_publish_allowed_always_false(self):
        builder = ManifestBuilder(
            run_id="test", request_sha256="a" * 64, article_sha256="b" * 64,
            claims_total=0, materials_total=0,
        )
        assert builder.build()["gate"]["publish_allowed"] is False


class TestManifestLateMutation:
    """Test that appending errors after build() is reflected in next build()."""

    def test_late_mutation_visible(self):
        """build() → append error → build() must include new error and gate=false."""
        builder = ManifestBuilder(
            run_id="test-mutation", request_sha256="a" * 64, article_sha256="b" * 64,
            claims_total=1, materials_total=1,
        )
        builder.add_asset(AssetRecord(
            asset_id="A-001", asset_origin="source", material_ids=["M-001"], claim_ids=["C-01"],
            decision="eligible", reasons=["test"], sha256="c" * 64, source_page_url="https://example.com",
        ))

        # First build — no errors
        m1 = builder.build()
        assert len(m1["errors"]) == 0
        assert m1["gate"]["input_contract_pass"] is True

        # Append an error
        builder.errors.append("SECRET_DETECTED: something bad")

        # Second build — must reflect the new error
        m2 = builder.build()
        assert len(m2["errors"]) == 1
        assert "SECRET_DETECTED" in m2["errors"][0]
        assert m2["gate"]["input_contract_pass"] is False
        assert m2["gate"]["security_checks_pass"] is False


class TestVersionConsistency:
    """Test that all version sources agree on 0.1.0-dev3."""

    def test_version_files_consistent(self):
        import re as _re
        SKILL_ROOT = Path(__file__).resolve().parents[1]
        version_files = {
            "VERSION": SKILL_ROOT / "VERSION",
            "__init__.py": SKILL_ROOT / "src" / "media_enrichment" / "__init__.py",
            "input_contract.py": SKILL_ROOT / "src" / "media_enrichment" / "input_contract.py",
        }
        all_versions = set()
        for name, path in version_files.items():
            assert path.exists(), f"{name} not found"
            content = path.read_text(encoding="utf-8")
            m = _re.search(r"0\.1\.0-dev\d+(?:-hotfix\d+)?", content)
            assert m, f"version not found in {name}"
            all_versions.add(m.group(0))

        assert len(all_versions) == 1, f"inconsistent versions: {all_versions}"
        assert "0.1.0-dev9" in all_versions, f"expected 0.1.0-dev9, got {all_versions}"

    def test_deterministic_ordering(self):
        b1 = ManifestBuilder(run_id="t", request_sha256="a"*64, article_sha256="b"*64, claims_total=1, materials_total=1)
        b2 = ManifestBuilder(run_id="t", request_sha256="a"*64, article_sha256="b"*64, claims_total=1, materials_total=1)
        for b, aid in [(b1, "A-002"), (b1, "A-001")]:
            b.add_asset(AssetRecord(asset_id=aid, asset_origin="source", material_ids=["M-001"], claim_ids=["C-01"], decision="rejected", reasons=["test"]))
        for b, aid in [(b2, "A-001"), (b2, "A-002")]:
            b.add_asset(AssetRecord(asset_id=aid, asset_origin="source", material_ids=["M-001"], claim_ids=["C-01"], decision="rejected", reasons=["test"]))
        assert [a["asset_id"] for a in b1.build()["assets"]] == [a["asset_id"] for a in b2.build()["assets"]]
