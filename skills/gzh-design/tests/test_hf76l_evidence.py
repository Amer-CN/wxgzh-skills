"""76L/OBS-282:publish 凭证门专项测试(真实校验逻辑,不打桩)。

- 无凭证(--evidence 缺失)→ argparse 拒绝;
- 凭证存在但 receipt 校验未过(validator_exit_code != 0)→ FAIL_CLOSED;
- html sha 与 receipt 绑定不一致 → FAIL_CLOSED;
- HTML 缺主题签名 → FAIL_CLOSED;
- 正路径(凭证齐+sha 一致+签名在)→ 校验通过,进入后续 preflight。
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import publish_wechat_draft as pub  # noqa: E402

PUBLISH = SKILL_ROOT / "scripts" / "publish_wechat_draft.py"
SIGNED_HTML = ('<section style="color:#B3593B;"><span leaf="">中文正文</span></section>')


def _mk_evidence(html: Path, exit_code=0, sha=None) -> Path:
    ev = html.parent / "stage_receipt.json"
    ev.write_text(json.dumps({
        "validator_exit_code": exit_code,
        "output_hashes": {"final.html": sha or hashlib.sha256(html.read_bytes()).hexdigest()},
    }), encoding="utf-8")
    return ev


def _run_cli(args, env_scrub=True):
    env = dict(os.environ)
    if env_scrub:
        env.pop("WECHAT_APP_ID", None)
        env.pop("WECHAT_APP_SECRET", None)
    return subprocess.run([sys.executable, "-X", "utf8", str(PUBLISH), *args],
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=120, env=env)


def test_no_evidence_fails_closed():
    td = Path(tempfile.mkdtemp(prefix="76l-noev-"))
    html = td / "final.html"
    html.write_text(SIGNED_HTML, encoding="utf-8")
    proc = _run_cli(["--html", str(html), "--title", "t"])
    assert proc.returncode != 0
    assert "the following arguments are required: --evidence" in proc.stderr


def test_invalid_receipt_fails_closed():
    td = Path(tempfile.mkdtemp(prefix="76l-badev-"))
    html = td / "final.html"
    html.write_text(SIGNED_HTML, encoding="utf-8")
    ev = _mk_evidence(html, exit_code=1)
    proc = _run_cli(["--html", str(html), "--title", "t", "--evidence", str(ev)])
    assert proc.returncode != 0
    assert "validator_exit_code" in proc.stdout
    assert "走管线 wechat_draft 阶段" in proc.stdout


def test_sha_mismatch_fails_closed():
    td = Path(tempfile.mkdtemp(prefix="76l-shabad-"))
    html = td / "final.html"
    html.write_text(SIGNED_HTML, encoding="utf-8")
    ev = _mk_evidence(html, sha="0" * 64)
    proc = _run_cli(["--html", str(html), "--title", "t", "--evidence", str(ev)])
    assert proc.returncode != 0
    assert "HTML sha 与凭证不一致" in proc.stdout


def test_missing_theme_signature_fails_closed():
    td = Path(tempfile.mkdtemp(prefix="76l-nosig-"))
    html = td / "final.html"
    html.write_text('<section><span leaf="">无签名中文正文</span></section>', encoding="utf-8")
    ev = _mk_evidence(html)
    proc = _run_cli(["--html", str(html), "--title", "t", "--evidence", str(ev)])
    assert proc.returncode != 0
    assert "缺主题签名" in proc.stdout
    assert "FAIL_CLOSED" in proc.stdout


def test_valid_evidence_passes():
    """正路径:凭证齐 + sha 一致 + 签名在 → 凭证门过,继续 preflight(无中文会失败于
    preflight 而非凭证——本用例用有效中文,期望到达 API 前被 env/网络逻辑阻断前
    的 preflight 通过;用 dry-run 审计模式确认凭证段通过)。"""
    td = Path(tempfile.mkdtemp(prefix="76l-ok-"))
    html = td / "final.html"
    html.write_text(SIGNED_HTML, encoding="utf-8")
    ev = _mk_evidence(html)
    audit = td / "audit"
    proc = _run_cli(["--html", str(html), "--title", "t", "--evidence", str(ev),
                     "--audit-dir", str(audit), "--dry-run"])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "交付凭证验证通过" in proc.stdout
    assert (audit / "draft_creation_result.json").is_file()


def test_verify_function_direct():
    """单元级:verify_pipeline_evidence 四路径。"""
    td = Path(tempfile.mkdtemp(prefix="76l-unit-"))
    html = td / "final.html"
    html.write_text(SIGNED_HTML, encoding="utf-8")
    sha = hashlib.sha256(html.read_bytes()).hexdigest()
    ok, errs = pub.verify_pipeline_evidence(str(_mk_evidence(html)), str(html), sha, SIGNED_HTML)
    assert ok and not errs
    ok, errs = pub.verify_pipeline_evidence(str(html), str(html), sha, SIGNED_HTML)
    assert not ok and any("凭证不可读" in e for e in errs)
    ok, errs = pub.verify_pipeline_evidence(str(_mk_evidence(html, exit_code=3)),
                                            str(html), sha, SIGNED_HTML)
    assert not ok and any("validator_exit_code" in e for e in errs)
    ok, errs = pub.verify_pipeline_evidence(str(_mk_evidence(html, sha="a" * 64)),
                                            str(html), sha, SIGNED_HTML)
    assert not ok and any("sha 与凭证不一致" in e for e in errs)
    ok, errs = pub.verify_pipeline_evidence(str(_mk_evidence(html)),
                                            str(html), sha, "<p>无签名</p>")
    assert not ok and any("缺主题签名" in e for e in errs)
