"""Theme-identity negatives + infra (secrets, cross-platform paths, reproducible
zip, install->doctor). Covers spec test items 16-23, 26-30.
"""
import os
import re
from pathlib import Path

from conftest import load_validator, SKILL_ROOT, SKILLS_HOME
from wxgzh_pipeline import paths as P
from wxgzh_pipeline import skill_discovery as SD
from wxgzh_pipeline import secrets as SEC
from wxgzh_pipeline.zipping import deterministic_zip, copy_tree


def _pass_html():
    return (SKILL_ROOT / "fixtures" / "offline_pipeline_fixture" / "gzh_design" / "outputs" / "final.html").read_text(encoding="utf-8")


def _theme(html, tmp_path, expected=6, exec_evidence=None, network_mode=None,
           lock_entry=None):
    v = load_validator("validate_theme_identity")
    p = tmp_path / "final.html"
    p.write_text(html, encoding="utf-8")
    return v.validate(p, expected_chapters=expected, usage_out=tmp_path / "usage.json",
                      exec_evidence=exec_evidence, network_mode=network_mode,
                      lock_entry=lock_entry)


def test_theme_baseline_copied_html_without_execution_fails(tmp_path):
    """P0#8: structurally perfect HTML with NO gzh execution evidence = FAIL
    (fingerprints can be copied; the execution receipt cannot)."""
    code, rep = _theme(_pass_html(), tmp_path)
    assert code == 1 and rep["THEME_IDENTITY"] == "FAIL"
    assert rep["structure_ok"] is True
    assert "copied HTML" in rep.get("fail_reason", "")


def test_theme_simulated_executor_never_official(tmp_path):
    """fake_live simulated executor => SIMULATED (accepted for orchestration),
    NEVER reported as an official gzh-design call."""
    code, rep = _theme(_pass_html(), tmp_path,
                       exec_evidence={"simulated": True, "official_gzh_call": False},
                       network_mode="fake_live")
    assert code == 0 and rep["THEME_IDENTITY"] == "SIMULATED"
    assert rep["OFFICIAL_GZH_CALL"] is False


def test_theme_official_pass_requires_real_hashes(tmp_path):
    """hotfix2: OFFICIAL PASS needs official_gzh_call + ACTUAL on-disk render-entry
    & component-source hashes matching the lock + installed root/manifest match +
    install-source commit match + network_mode=live. Lock fields alone never pass."""
    import hashlib
    entry = tmp_path / "render_article.py"; entry.write_text("# entry\n", encoding="utf-8")
    comp = tmp_path / "generate_hammer_upgrade_samples.py"; comp.write_text("# comp\n", encoding="utf-8")

    def _nsha(p):  # newline-normalized, matching the lock + validator hashing
        d = p.read_bytes()
        return hashlib.sha256(d.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
                              if b"\x00" not in d else d).hexdigest()
    entry_sha = _nsha(entry)
    comp_sha = _nsha(comp)
    lock_entry = {"entrypoint_sha256": entry_sha, "component_source_sha256": comp_sha,
                  "full_commit_sha": "f" * 40, "skill_root_sha256": "r" * 64,
                  "runtime_manifest_sha256": "m" * 64}
    good = {"official_gzh_call": True,
            "render_entry_path": str(entry), "entry_sha256": entry_sha,
            "component_source_path": str(comp),
            "installed_root_sha256": "r" * 64,
            "installed_runtime_manifest_sha256": "m" * 64,
            "install_receipt_root_sha256": "r" * 64,
            "install_receipt_manifest_sha256": "m" * 64,
            "install_source_commit": "f" * 40}
    code, rep = _theme(_pass_html(), tmp_path, exec_evidence=good,
                       network_mode="live", lock_entry=lock_entry)
    assert code == 0 and rep["THEME_IDENTITY"] == "PASS", rep
    assert rep["RENDER_ENTRY_HASH_MATCHES_LOCK"] and rep["COMPONENT_SOURCE_HASH_MATCHES_LOCK"]
    assert rep["INSTALLED_ROOT_MATCHES_LOCK"] and rep["INSTALL_SOURCE_COMMIT_MATCHES_LOCK"]
    assert rep["INSTALL_RECEIPT_PRESENT"] and rep["INSTALL_RECEIPT_ROOT_MATCHES"]
    # lock fields alone (no real files / wrong entry hash) => FAIL
    bad = dict(good, entry_sha256="0" * 64, render_entry_path=str(tmp_path / "nope.py"))
    code2, rep2 = _theme(_pass_html(), tmp_path, exec_evidence=bad,
                         network_mode="live", lock_entry=lock_entry)
    assert code2 == 1 and rep2["THEME_IDENTITY"] == "FAIL"
    assert rep2["RENDER_ENTRY_HASH_MATCHES_LOCK"] is False
    # P0#1: install receipt root that disagrees with lock/recomputed => FAIL
    # (recomputed==lock but receipt tampered — three-way compare catches it)
    tampered_receipt = dict(good, install_receipt_root_sha256="9" * 64)
    codeR, repR = _theme(_pass_html(), tmp_path, exec_evidence=tampered_receipt,
                         network_mode="live", lock_entry=lock_entry)
    assert codeR == 1 and repR["THEME_IDENTITY"] == "FAIL"
    assert repR["INSTALLED_ROOT_MATCHES_LOCK"] is False
    # tampered component source (real file hash != lock) => FAIL
    comp.write_text("# TAMPERED\n", encoding="utf-8")
    code3, rep3 = _theme(_pass_html(), tmp_path, exec_evidence=good,
                         network_mode="live", lock_entry=lock_entry)
    assert code3 == 1 and rep3["COMPONENT_SOURCE_HASH_MATCHES_LOCK"] is False


# ---- 16. gzh not actually called (no hammer structure at all) => fail ----
def test_16_gzh_not_called_fails(tmp_path):
    code, rep = _theme("<section><p>纯文本，未调用 gzh-design</p></section>", tmp_path)
    assert code == 1 and rep["HAMMER_COVER_BREAKING_COUNT"] == 0


# ---- 17. plain gray HTML masquerading as smartisan => fail ----
def test_17_gray_html_fails(tmp_path):
    gray = '<section style="background:#f7f7f7"><h2>01 标题</h2><p>正文</p></section>'
    code, rep = _theme(gray, tmp_path)
    assert code == 1 and rep["THEME_IDENTITY"] == "FAIL"


# ---- 18. cover-breaking missing => fail ----
def test_18_cover_missing_fails(tmp_path):
    html = _pass_html().replace("border-radius:20px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.06)", "border-radius:8px")
    code, rep = _theme(html, tmp_path)
    assert code == 1 and rep["HAMMER_COVER_BREAKING_COUNT"] == 0


# ---- 19. toc-scroll missing => fail ----
def test_19_toc_missing_fails(tmp_path):
    html = _pass_html().replace("overflow-x:scroll;-webkit-overflow-scrolling:touch;white-space:nowrap", "overflow:hidden")
    code, rep = _theme(html, tmp_path)
    assert code == 1 and rep["HAMMER_TOC_SCROLL_COUNT"] == 0


# ---- 20. chapter-title count mismatch => fail ----
def test_20_chapter_count_mismatch_fails(tmp_path):
    html = _pass_html()
    # drop one chapter-title fingerprint occurrence -> 5 chapters vs expected 6
    html = html.replace("font-size:28px;font-weight:900;color:#B3593B;line-height:1;letter-spacing:-2px", "font-size:20px;color:#B3593B", 1)
    code, rep = _theme(html, tmp_path, expected=6)
    assert code == 1 and rep["HAMMER_CHAPTER_TITLE_COUNT"] == 5


# ---- 21. component_usage_report is program-generated from HTML (not declarative) ----
def test_21_usage_report_from_html(tmp_path):
    import json
    code, rep = _theme(_pass_html(), tmp_path)
    usage = json.loads((tmp_path / "usage.json").read_text(encoding="utf-8"))
    assert usage["structural_components"]["chapter_title"] == rep["HAMMER_CHAPTER_TITLE_COUNT"]
    assert usage["source"].startswith("reverse-parsed")


# ---- 22. theme fallback (other theme colour present) => fail ----
def test_22_theme_fallback_fails(tmp_path):
    html = _pass_html().replace("#B3593B", "#059669")  # moyu-green primary => fallback
    code, rep = _theme(html, tmp_path)
    assert code == 1 and rep["THEME_FALLBACK_USED"] is True


# ---- 23. low-contrast strikethrough => fail (forbidden rgba as text colour) ----
def test_23_strikethrough_low_contrast_fails(tmp_path):
    html = _pass_html().replace("</section>", '<p style="color:rgba(202,202,199,0.35);text-decoration-line:line-through">旧</p></section>', 1)
    code, rep = _theme(html, tmp_path)
    assert code == 1 and rep["strikethrough_forbidden_rgba_present"] is True


# ---- 26. secrets scan: credential-form only; bare 'token' not a secret ----
def test_26_secrets_scan(tmp_path):
    (tmp_path / "a.txt").write_text("每百万 token 5 美元；100 万 token 上下文", encoding="utf-8")
    clean = SEC.scan_tree(tmp_path)
    assert clean["secrets_detected"] is False
    # build a credential-shaped string from fragments so THIS source file holds
    # no contiguous credential literal (bundle secrets scan stays clean).
    fake = "access_" + "token=" + ("a" * 32)
    (tmp_path / "b.txt").write_text(fake, encoding="utf-8")
    dirty = SEC.scan_tree(tmp_path)
    assert dirty["secrets_detected"] is True


# ---- 27. Windows-style path resolution ----
def test_27_windows_path(tmp_path):
    root = P.resolve_project_root(env={"WXGZH_PROJECT_ROOT": r"C:\proj\demo"})
    assert root == Path(r"C:\proj\demo").expanduser().resolve() or str(root).endswith("demo")
    rid = P.make_run_id("Claude Opus 5")
    assert re.match(r"^\d{8}T\d{6}-claude-opus-5-[a-z0-9]{6}$", rid)


# ---- 28. POSIX-style path resolution + AGENT_SKILLS_HOME ----
def test_28_posix_path():
    root = P.resolve_project_root(env={"AGENT_SKILLS_HOME": "/home/u/proj/.agents/skills"})
    assert root.as_posix().endswith("/home/u/proj") or str(root).endswith("proj")
    assert P.slugify("完全中文选题") == "topic"          # non-ascii collapses safely
    assert P.slugify("GPT-5 Turbo!") == "gpt-5-turbo"


# ---- 29. reproducible zip ----
def test_29_reproducible_zip(tmp_path):
    src = tmp_path / "src"; src.mkdir()
    (src / "a.txt").write_text("hello", encoding="utf-8")
    (src / "sub").mkdir(); (src / "sub" / "b.txt").write_text("world", encoding="utf-8")
    s1 = deterministic_zip(src, tmp_path / "1.zip", arc_prefix="pkg")
    s2 = deterministic_zip(src, tmp_path / "2.zip", arc_prefix="pkg")
    assert s1 == s2


# ---- 30. install (copy locked skills) then doctor passes ----
def test_30_install_then_doctor(tmp_path):
    from wxgzh_pipeline.orchestrator import Orchestrator
    lock = SD.load_lock(SKILL_ROOT)
    target = tmp_path / ".agents" / "skills"
    target.mkdir(parents=True)
    copy_tree(SKILL_ROOT, target / "wxgzh-pipeline")
    for name, meta in lock["skills"].items():
        if meta.get("kind") == "agent_invoked_skill":
            continue
        copy_tree(SKILLS_HOME / name, target / name)
    orch = Orchestrator(project_root=tmp_path, network_mode="offline_fixture", skills_home=target)
    ok, report = orch.doctor()
    assert ok and report["skills_locked_ok"] and report["FAIL_CLOSED"] is False
