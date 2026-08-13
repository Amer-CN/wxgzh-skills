"""dev2 tests: exercise the REAL orchestration machinery in fake_live mode
(agent handshake + real subprocess + real official validators + receipt hash
recompute) with fake sub-skills and a fake WeChat client. No real side effects.

Covers the dev2 deliverable items:
  7 fake-live six-stage results   8 agent handshake results
  9 receipt tampering detection  10 release_audit runs the full suite
plus the P0 fix (live no longer crashes) and the new gates (doctor credential
parsing, mmbiz exact host, dynamic chapter/TOC gate, delivery draft_created).
"""
import hashlib
import json
from pathlib import Path

import pytest

from conftest import load_validator, FAKE_FIXTURE
from wxgzh_pipeline import STAGES, secrets as SEC
from wxgzh_pipeline import agent_handshake as AH
from wxgzh_pipeline.execmodel import AGENT_EXPECTED_OUTPUTS, EXPECTED_OUTPUTS, STAGE_EXEC, AGENT
from wxgzh_pipeline.state import load_state
from wxgzh_pipeline.receipts import load_receipt, receipt_valid, verify_receipt


# ---- 7. fake-live six-stage results (real machinery, no side effects) ----
def test_fake_live_six_stages(orch):
    out = orch.run("Claude Opus 5")
    assert out["status"] == "COMPLETE"
    assert out["completed_stages"] == STAGES
    rd = Path(out["run_dir"])
    st = load_state(rd)
    assert st.draft_created is True and st.formally_published is False
    assert st.uploaded_image_count == 8
    for s in STAGES:
        assert receipt_valid(rd, s), f"{s} receipt invalid"
    # executable stages ran a REAL official validator subprocess (exit 0)
    for s in ("media_enrichment", "gzh_design"):
        r = load_receipt(rd, s)
        assert r["official_validator"]["exit_code"] == 0
        assert r["entrypoint_sha256"] and r["network_mode"] == "fake_live"
    # no real side effects: the fake WeChat client marks real_api_call False
    dres = json.loads((rd / "wechat_draft" / "draft_creation_result.json").read_text(encoding="utf-8"))
    assert dres["real_api_call"] is False and dres["formally_published"] is False


# ---- 8. agent handshake results (+ tamper breaks the token) ----
def test_agent_handshake(orch):
    out = orch.run("t")
    rd = Path(out["run_dir"])
    for stage in [s for s in STAGES if STAGE_EXEC[s] == AGENT]:
        sd = rd / stage
        assert (sd / "agent_handshake_request.json").is_file()
        assert (sd / "agent_handshake.json").is_file()
        ok, rep = AH.verify_ack(sd, stage, AGENT_EXPECTED_OUTPUTS[stage])
        assert ok and rep["HANDSHAKE"] == "PASS"
    # tamper an agent output AFTER the ack -> token no longer matches
    sd = rd / "aihot"
    tampered = sd / EXPECTED_OUTPUTS["aihot"][0]
    tampered.write_text(tampered.read_text(encoding="utf-8") + "\n// tamper", encoding="utf-8")
    ok, rep = AH.verify_ack(sd, "aihot", EXPECTED_OUTPUTS["aihot"])
    assert not ok and rep["token_ok"] is False


# ---- 9. receipt tampering detection ----
def test_receipt_tamper(orch):
    out = orch.run("t")
    rd = Path(out["run_dir"])
    ok, mism, _ = verify_receipt(rd, "media_enrichment")
    assert ok and mism == []
    man = rd / "media_enrichment" / "media_manifest.json"
    man.write_bytes(man.read_bytes() + b" ")  # tamper an output file
    ok2, mism2, _ = verify_receipt(rd, "media_enrichment")
    assert not ok2 and any("media_manifest.json" in m for m in mism2)


# ---- 10. release_audit really runs the whole suite + strict P0#9 gating ----
def test_release_audit_runs_all_tests(orch, tmp_path, monkeypatch):
    from wxgzh_pipeline.orchestrator import Orchestrator
    # stub the (recursion-guarded) full-suite + integration so we can exercise the
    # STRICT gating deterministically without re-spawning pytest inside pytest.
    marker = tmp_path / "integration.json"
    marker.write_text('{"ran": true, "exit_code": 0}', encoding="utf-8")
    monkeypatch.setenv("WXGZH_INTEGRATION_RESULT", str(marker))
    monkeypatch.setattr(Orchestrator, "_run_full_tests",
                        staticmethod(lambda: {"ran": True, "exit_code": 0}))
    rep = orch.release_audit()
    assert rep["RELEASE_AUDIT"] == "PASS", rep
    assert rep["no_formal_publish_capability"] is True
    assert rep["tests_ran"] is True and rep["tests"]["exit_code"] == 0
    assert rep["cross_repo_integration"]["ran"] is True

    # P0#9: exit_code=None must NOT pass
    monkeypatch.setattr(Orchestrator, "_run_full_tests",
                        staticmethod(lambda: {"ran": False, "exit_code": None, "skipped_nested": True}))
    assert orch.release_audit()["RELEASE_AUDIT"] == "FAIL"
    # P0#9: missing cross-repo integration must NOT pass
    monkeypatch.setattr(Orchestrator, "_run_full_tests",
                        staticmethod(lambda: {"ran": True, "exit_code": 0}))
    monkeypatch.delenv("WXGZH_INTEGRATION_RESULT", raising=False)
    assert orch.release_audit()["RELEASE_AUDIT"] == "FAIL"


# ---- P0 FIX: live mode PAUSES for the agent instead of crashing at aihot ----
def test_live_awaits_agent_not_crash(tmp_path, monkeypatch):
    from wxgzh_pipeline.orchestrator import Orchestrator
    o = Orchestrator(project_root=tmp_path, network_mode="live", skills_home=tmp_path)
    monkeypatch.setattr(o, "doctor", lambda **k: (True, {"skills": {}}))
    out = o.run("Claude Opus 5")
    assert out["status"] == "AWAITING_AGENT" and out["stage"] == "aihot"
    assert Path(out["handshake_request"]).is_file()


# ---- doctor: non-empty credential parsing (never logs values) ----
def test_doctor_credential_parsing(tmp_path):
    ok_empty, d1 = SEC.wechat_credentials_present({"WECHAT_APP_ID": "", "WECHAT_APP_SECRET": "x"})
    ok_ph, d2 = SEC.wechat_credentials_present({"WECHAT_APP_ID": "your_app_id", "WECHAT_APP_SECRET": "s"})
    ok_full, d3 = SEC.wechat_credentials_present({"WECHAT_APP_ID": "wx123456", "WECHAT_APP_SECRET": "abcdef123456"})
    assert ok_empty is False and ok_ph is False and ok_full is True
    from wxgzh_pipeline.orchestrator import Orchestrator
    o = Orchestrator(project_root=tmp_path, network_mode="live", skills_home=tmp_path,
                     env={"WECHAT_APP_ID": "", "WECHAT_APP_SECRET": ""})
    ok, rep = o.doctor(require_wechat=True)
    assert ok is False and rep["wechat_config_present"] is False and rep["FAIL_CLOSED"] is True


# ---- mmbiz exact-host verification (reject look-alikes) ----
@pytest.mark.parametrize("host,good", [
    ("mmbiz.qpic.cn", True),
    ("mmbiz.qlogo.cn", True),
    ("mmbiz.qpic.cn.evil.com", False),
    ("evilmmbiz.qpic.cn", False),
])
def test_mmbiz_exact_host(tmp_path, host, good):
    v = load_validator("validate_media_bindings")
    assets = [{"asset_id": f"A-{i}", "decision": "eligible", "sha256": str(i),
               "upload": {"status": "success", "remote_url": f"https://{host}/x"}} for i in range(6)]
    body = [{"asset_id": f"A-{i}", "sha256": str(i), "wechat_remote_url": f"https://{host}/x"} for i in range(6)]
    mp = tmp_path / "m.json"; mp.write_text(json.dumps({"assets": assets}), encoding="utf-8")
    bp = tmp_path / "b.json"; bp.write_text(json.dumps({"body_images": body}), encoding="utf-8")
    code, rep = v.validate(mp, bp)
    assert (code == 0) == good


def test_mmbiz_http_and_tricks_rejected(tmp_path):
    """hotfix2 P0#4: http:// and every off-host trick must FAIL even when the
    exact allow-listed host name appears somewhere in the URL. These are the
    exact cases from the spec (query / subdomain / path / userinfo / scheme)."""
    v = load_validator("validate_media_bindings")
    for url in ("https://evil.example/?x=mmbiz.qpic.cn",
                "https://mmbiz.qpic.cn.evil.example/a.png",
                "https://evil.example/mmbiz.qlogo.cn/a.png",
                "https://mmbiz.qpic.cn@evil.example/a.png",
                "http://mmbiz.qpic.cn/a.png"):
        assets = [{"asset_id": f"A-{i}", "decision": "eligible", "sha256": str(i),
                   "upload": {"status": "success", "remote_url": url}} for i in range(6)]
        body = [{"asset_id": f"A-{i}", "sha256": str(i)} for i in range(6)]
        mp = tmp_path / "m.json"; mp.write_text(json.dumps({"assets": assets}), encoding="utf-8")
        bp = tmp_path / "b.json"; bp.write_text(json.dumps({"body_images": body}), encoding="utf-8")
        code, rep = v.validate(mp, bp)
        assert code == 1, url


# ---- dynamic chapter/TOC gate: derived from article, not hard-coded ----
def test_dynamic_chapter_gate(orch):
    out = orch.run("t")
    rd = Path(out["run_dir"])
    # the frozen article has 6 H2 headings; the theme report must reflect 6
    rep = json.loads((rd / "gzh_design" / "theme_identity_report.json").read_text(encoding="utf-8"))
    assert rep["expected_chapters"] == 6 and rep["HAMMER_CHAPTER_TITLE_COUNT"] == 6
    # fake_live uses a simulated executor: SIMULATED, never claimed official (P0#8)
    assert rep["HAMMER_TOC_MATCHES_CHAPTERS"] is True and rep["THEME_IDENTITY"] == "SIMULATED"
    assert rep["OFFICIAL_GZH_CALL"] is False
    # a 4-chapter expectation against 6-chapter HTML must FAIL; None also fails
    v = load_validator("validate_theme_identity")
    html = (rd / "gzh_design" / "final.html")
    code4, _ = v.validate(html, expected_chapters=4, usage_out=rd / "u4.json")
    code0, _ = v.validate(html, expected_chapters=None, usage_out=rd / "u0.json")
    assert code4 == 1 and code0 == 1


# ---- delivery must require draft_created=true ----
def test_delivery_requires_draft_created(tmp_path):
    v = load_validator("validate_delivery")
    for s in STAGES:
        (tmp_path / s).mkdir(parents=True, exist_ok=True)
        (tmp_path / s / "stage_receipt.json").write_text("{}", encoding="utf-8")
    delivery = {"formally_published": False, "draft_created": False}
    (tmp_path / "final_delivery.json").write_text(json.dumps(delivery), encoding="utf-8")
    files = [{"path": "final_delivery.json",
              "sha256": hashlib.sha256((tmp_path / "final_delivery.json").read_bytes()).hexdigest()}]
    (tmp_path / "MANIFEST.json").write_text(json.dumps({"files": files, "file_count": 1}), encoding="utf-8")
    code, rep = v.validate(tmp_path)
    assert code == 1 and rep["draft_created_true"] is False and rep["DELIVERY"] == "FAIL"
