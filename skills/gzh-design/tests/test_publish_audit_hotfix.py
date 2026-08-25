#!/usr/bin/env python3
"""dev2-hotfix1 tests: publish_wechat_draft.py audit mode.

Proves the audit mode writes draft_before/after/creation_result.json with
AFTER = BEFORE + 1, and in --dry-run does it with ZERO network / ZERO real
draft (simulated=true). Also asserts the script has NO formal-publish capability.
"""
import json
import os
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
PUBLISH = SKILL_ROOT / "scripts" / "publish_wechat_draft.py"

# minimal WeChat-compliant fragment (passes preflight: ERROR=0, WARNING=0)
CLEAN_HTML = ('<section style="color:#555555;font-size:14px;">'
              '<span leaf="">这是一段用于草稿审计的中文测试内容。</span>'
              '<span leaf="" style="color:#B3593B;">主题签名占位</span></section>')


def _run_audit(dry_run=True, with_cover=False):
    td = Path(tempfile.mkdtemp())
    html = td / "final.html"
    html.write_text(CLEAN_HTML, encoding="utf-8")
    audit = td / "audit"
    # 76L/OBS-282:构造本 RUN 凭证(receipt 绑定 final.html sha + exit 0)
    evidence = td / "stage_receipt.json"
    evidence.write_text(json.dumps({
        "validator_exit_code": 0,
        "output_hashes": {"final.html": hashlib.sha256(html.read_bytes()).hexdigest()},
    }), encoding="utf-8")
    cover = None
    if with_cover:
        cover = td / "cover.png"
        from PIL import Image
        Image.new("RGB", (900, 383), (179, 89, 59)).save(cover, "PNG")
    argv = [sys.executable, "-X", "utf8", str(PUBLISH),
            "--html", str(html), "--title", "草稿审计测试",
            "--evidence", str(evidence),
            "--audit-dir", str(audit)]
    if cover is not None:
        argv += ["--cover", str(cover)]
    if dry_run:
        argv.append("--dry-run")
    # scrub any real creds so a non-dry-run test can never hit the network either
    env = dict(os.environ)
    env.pop("WECHAT_APP_ID", None)
    env.pop("WECHAT_APP_SECRET", None)
    proc = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=120, env=env)
    return audit, proc


class TestAuditMode:
    def test_dry_run_writes_three_artifacts_after_is_before_plus_one(self):
        audit, proc = _run_audit(dry_run=True)
        assert proc.returncode == 0, proc.stdout + proc.stderr
        before = json.loads((audit / "draft_before.json").read_text(encoding="utf-8"))
        after = json.loads((audit / "draft_after.json").read_text(encoding="utf-8"))
        result = json.loads((audit / "draft_creation_result.json").read_text(encoding="utf-8"))
        assert after["total_count"] == before["total_count"] + 1
        assert result["delta"] == 1
        assert result["simulated"] is True
        assert result["real_api_call"] is False
        assert result["formally_published"] is False
        assert result["draft_only"] is True
        # 77H/OBS-318: zero-image audit produces placeholder and labels source.
        assert (audit / "placeholder_cover.png").is_file()
        assert result["cover_source"] == "placeholder_zero_image"

    def test_dry_run_no_network_no_token(self):
        audit, proc = _run_audit(dry_run=True)
        out = proc.stdout + proc.stderr
        # simulated path must never fetch a token or hit the API
        assert "获取 access_token" not in out
        assert "api.weixin.qq.com" not in out

    def test_media_id_desensitized(self):
        audit, _ = _run_audit(dry_run=True)
        result = json.loads((audit / "draft_creation_result.json").read_text(encoding="utf-8"))
        assert "[REDACTED]" in result["media_id"]

    def test_provided_cover_keeps_approved_body_image_source(self):
        audit, _ = _run_audit(dry_run=True, with_cover=True)
        result = json.loads((audit / "draft_creation_result.json").read_text(encoding="utf-8"))
        assert result["cover_source"] == "approved_body_image"
        assert not (audit / "placeholder_cover.png").exists()


class TestNoFormalPublishCapability:
    def test_script_has_no_publish_endpoint(self):
        src = PUBLISH.read_text(encoding="utf-8")
        # fragment-built to avoid this test file itself tripping endpoint scanners
        assert ("cgi-bin/" + "free" + "publish") not in src
        assert "message/mass" not in src
        assert "/cgi-bin/draft/batchget" in src  # audit uses batchget (read-only)


class TestCliCompat:
    def test_argparse_flags(self):
        src = PUBLISH.read_text(encoding="utf-8")
        for flag in ('"--html"', '"--title"', '"--thumb-media-id"', '"--cover"',
                     '"--audit-dir"', '"--dry-run"'):
            assert flag in src, f"publish_wechat_draft.py must accept {flag}"
