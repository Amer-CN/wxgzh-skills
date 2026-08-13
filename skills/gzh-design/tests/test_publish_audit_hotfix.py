#!/usr/bin/env python3
"""dev2-hotfix1 tests: publish_wechat_draft.py audit mode.

Proves the audit mode writes draft_before/after/creation_result.json with
AFTER = BEFORE + 1, and in --dry-run does it with ZERO network / ZERO real
draft (simulated=true). Also asserts the script has NO formal-publish capability.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
PUBLISH = SKILL_ROOT / "scripts" / "publish_wechat_draft.py"

# minimal WeChat-compliant fragment (passes preflight: ERROR=0, WARNING=0)
CLEAN_HTML = ('<section style="color:#555555;font-size:14px;">'
              '<span leaf="">这是一段用于草稿审计的中文测试内容。</span></section>')


def _run_audit(dry_run=True):
    td = Path(tempfile.mkdtemp())
    html = td / "final.html"
    html.write_text(CLEAN_HTML, encoding="utf-8")
    audit = td / "audit"
    argv = [sys.executable, "-X", "utf8", str(PUBLISH),
            "--html", str(html), "--title", "草稿审计测试",
            "--audit-dir", str(audit)]
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
