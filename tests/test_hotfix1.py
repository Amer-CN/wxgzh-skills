"""dev2-hotfix1 P0 tests:

- P0#3  resume MUST call verify_receipt: tamper media_manifest => media+后续失效，
        绝不 ALREADY_COMPLETE；tamper upstream final_article.md => media/gzh/wechat 全失效
- P0#1d CLI compatibility: the pipeline builds argv with the REAL sub-skill CLI
        flags, and the fake_live shims mirror those flags exactly
- P0#6  AI HOT existence is really checked (NOT_INSTALLED => live FAIL_CLOSED)
- P0#9  reinstall from the PR trees => live doctor skill verification PASS
"""
import json
import os
import shutil
from pathlib import Path

import pytest

from conftest import SKILL_ROOT
from wxgzh_pipeline import execmodel as EM
from wxgzh_pipeline import producers as PR
from wxgzh_pipeline import skill_discovery as SD


# ---------- P0#3: tamper + resume ----------

def test_resume_tamper_media_manifest_invalidates_media_and_later(orch):
    out = orch.run("t")
    assert out["status"] == "COMPLETE"
    rd = Path(out["run_dir"])
    man = rd / "media_enrichment" / "media_manifest.json"
    man.write_bytes(man.read_bytes() + b" ")  # tamper
    res = orch.resume(out["run_id"])
    assert res["status"] != "ALREADY_COMPLETE"
    rv = res["receipt_verification"]
    assert rv["media_enrichment"]["ok"] is False
    assert res["invalidated_from"] == "media_enrichment"
    # earlier stages stay valid; the run re-executes from media onward
    assert rv["aihot"]["ok"] and rv["super_writer"]["ok"] and rv["zh_human_writing"]["ok"]
    assert res["status"] == "COMPLETE"


def test_resume_tamper_upstream_article_invalidates_media_gzh_wechat(orch):
    out = orch.run("t")
    assert out["status"] == "COMPLETE"
    rd = Path(out["run_dir"])
    wechat_receipt = rd / "wechat_draft" / "stage_receipt.json"
    mtime_before = wechat_receipt.stat().st_mtime_ns
    fa = rd / "zh_human_writing" / "final_article.md"
    fa.write_text(fa.read_text(encoding="utf-8") + "\n篡改。\n", encoding="utf-8")
    res = orch.resume(out["run_id"])
    assert res["status"] != "ALREADY_COMPLETE"
    rv = res["receipt_verification"]
    # the tampered article is zh's OUTPUT and media/gzh's bound INPUT — all FAIL:
    for s in ("zh_human_writing", "media_enrichment", "gzh_design"):
        assert rv[s]["ok"] is False, s
    # cascade: everything from zh onward (incl. wechat_draft) is invalidated and
    # RE-EXECUTED — the wechat receipt file is freshly rewritten (outputs are
    # deterministic, so compare rewrite time, not bytes).
    assert res["invalidated_from"] == "zh_human_writing"
    assert res["status"] == "COMPLETE"
    assert wechat_receipt.stat().st_mtime_ns > mtime_before


# ---------- P0#1d: real-CLI compatibility ----------

REAL_CLI = {
    "media_entry": ("run_media_enrichment.py", ["--request", "--output-dir"]),
    "media_validator": ("validate_media_manifest.py", ["--manifest", "--request", "--bindings"]),
    "gzh_entry": ("render_article.py", ["--article", "--bindings", "--output-dir", "--theme"]),
    "wechat_entry": ("publish_wechat_draft.py", ["--html", "--title", "--audit-dir", "--dry-run"]),
}


class _Ctx:
    def __init__(self, run_dir, skills_home, network_mode="fake_live"):
        self.run_dir = run_dir
        self.skills_home = skills_home
        self.network_mode = network_mode


def test_pipeline_builds_real_media_cli(tmp_path):
    ctx = _Ctx(tmp_path, tmp_path)
    sd = tmp_path / "media_enrichment"; sd.mkdir()
    args = PR._entry_args(ctx, "media_enrichment", sd, None, sd / "media_request.json")
    assert args[0] == "--request" and args[2] == "--output-dir"
    v = PR._validator_args("media_enrichment", sd, sd / "media_request.json")
    assert v[0] == "--manifest" and v[2] == "--request" and v[4] == "--bindings"


def test_pipeline_builds_real_gzh_cli(tmp_path):
    ctx = _Ctx(tmp_path, tmp_path)
    sd = tmp_path / "gzh_design"; sd.mkdir()
    args = PR._entry_args(ctx, "gzh_design", sd, None, None)
    assert args[0] == "--article" and "--bindings" in args and "--output-dir" in args
    assert args[-2] == "--theme" and args[-1] == "smartisan"
    # gzh official validator takes a POSITIONAL html path (no --html flag)
    v = PR._validator_args("gzh_design", sd, None)
    assert len(v) == 1 and v[0].endswith("final.html")


def test_shims_mirror_real_cli_flags():
    home = EM.FAKE_LIVE_HOME
    shim_of = {
        "media_entry": home / "media-enrichment" / "run_media_enrichment.py",
        "media_validator": home / "media-enrichment" / "validate_media_manifest.py",
        "gzh_entry": home / "gzh-design" / "render_article.py",
        "wechat_entry": home / "gzh-design" / "publish_wechat_draft.py",
    }
    for key, (name, flags) in REAL_CLI.items():
        src = shim_of[key].read_text(encoding="utf-8")
        for flag in flags:
            assert f'"{flag}"' in src, f"shim {name} must accept {flag}"


def test_real_skills_accept_same_flags_when_available():
    """When the real sub-skills are installed locally, their sources must accept
    the exact flags the pipeline passes (skipped hermetically in CI)."""
    homes = [Path(os.environ.get("WXGZH_REAL_SKILLS_HOME", "")),
             SKILL_ROOT.parent]
    real = {
        "media_entry": "media-enrichment/scripts/run_media_enrichment.py",
        "media_validator": "media-enrichment/scripts/validate_media_manifest.py",
        "gzh_entry": "gzh-design/scripts/render_article.py",
        "wechat_entry": "gzh-design/scripts/publish_wechat_draft.py",
    }
    checked = 0
    for key, rel in real.items():
        for home in homes:
            p = home / rel if str(home) else None
            if p and p.is_file():
                src = p.read_text(encoding="utf-8", errors="replace")
                for flag in REAL_CLI[key][1]:
                    assert f'"{flag}"' in src or f"'{flag}'" in src, f"{rel} missing {flag}"
                checked += 1
                break
    if checked == 0:
        pytest.skip("no real sub-skills available in this environment")


# ---------- P0#6/#8: AI HOT real CAPABILITY check ----------

def test_aihot_bare_skill_md_is_unverified_and_fails_live(tmp_path):
    """hotfix2: a bare SKILL.md is NOT a verified capability."""
    from wxgzh_pipeline.orchestrator import Orchestrator
    reg = tmp_path / "aihot"; reg.mkdir()
    (reg / "SKILL.md").write_text("---\nname: aihot\n---\n", encoding="utf-8")  # SKILL.md only
    o = Orchestrator(project_root=tmp_path, network_mode="live", skills_home=tmp_path,
                     env={"WXGZH_AIHOT_SKILL_DIR": str(reg),
                          "WECHAT_APP_ID": "wx123456", "WECHAT_APP_SECRET": "abcdef123456"})
    ok, rep = o.doctor()
    assert rep["EXTERNAL_DEPENDENCY_AIHOT"] == "UNVERIFIED"
    assert rep["LIVE_PIPELINE_ALLOWED"] is False
    assert ok is False and rep["FAIL_CLOSED"] is True


def test_aihot_not_installed_fails_closed_in_live(tmp_path):
    from wxgzh_pipeline.orchestrator import Orchestrator
    empty = tmp_path / "no-aihot-here"; empty.mkdir()
    o = Orchestrator(project_root=tmp_path, network_mode="live", skills_home=tmp_path,
                     env={"WXGZH_AIHOT_SKILL_DIR": str(empty),
                          "WECHAT_APP_ID": "wx123456", "WECHAT_APP_SECRET": "abcdef123456"})
    ok, rep = o.doctor()
    assert rep["EXTERNAL_DEPENDENCY_AIHOT"] == "UNVERIFIED"
    assert ok is False and rep["FAIL_CLOSED"] is True


def test_aihot_valid_registration_detected(tmp_path):
    """A real registration manifest (name + output_contract + discoverable) verifies."""
    from wxgzh_pipeline.skill_discovery import check_aihot
    manifest = tmp_path / "aihot_reg.json"
    manifest.write_text(json.dumps({"name": "aihot", "identifier": "aihot",
                                    "discoverable": True,
                                    "output_contract": {"items": "array"}}), encoding="utf-8")
    res = check_aihot(tmp_path, env={"WXGZH_AIHOT_REGISTRATION": str(manifest)})
    assert res["exists"] is True and res["status"] == "INSTALLED"
    assert res["live_pipeline_allowed"] is True
    # missing output_contract => UNVERIFIED
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"name": "aihot", "discoverable": True}), encoding="utf-8")
    res2 = check_aihot(tmp_path, env={"WXGZH_AIHOT_REGISTRATION": str(bad)})
    assert res2["exists"] is False and res2["status"] == "UNVERIFIED"


# ---------- P0#9: reinstall from PR trees => doctor skill verification PASS ----------

def test_reinstall_from_pr_trees_doctor_pass(tmp_path):
    clones_dir = os.environ.get("WXGZH_SUBSKILL_CLONES", "")
    if not clones_dir or not Path(clones_dir).is_dir():
        pytest.skip("WXGZH_SUBSKILL_CLONES not set (PR trees unavailable here)")
    clones = Path(clones_dir)
    mapping = {"super-writer": "super-writer", "zh-human-writing": "zh-human-writing",
               "media-enrichment": "media-enrichment", "gzh-design-skill": "gzh-design"}
    staging = tmp_path / "skills"; staging.mkdir()
    for src_name, dst_name in mapping.items():
        shutil.copytree(clones / src_name, staging / dst_name,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
    lock = SD.load_lock(SKILL_ROOT)
    aihot_dir = staging / "aihot"; aihot_dir.mkdir()
    (aihot_dir / "SKILL.md").write_text("---\nname: aihot\n---\n", encoding="utf-8")
    (aihot_dir / "registration.json").write_text(json.dumps(
        {"name": "aihot", "identifier": "aihot", "discoverable": True,
         "output_contract": {"items": "array"}}), encoding="utf-8")
    ok, disc = SD.verify_all(staging, lock, env={"WXGZH_AIHOT_SKILL_DIR": str(aihot_dir)})
    problems = {k: v for k, v in disc.items() if not v["ok"]}
    assert ok, f"reinstalled PR trees must verify against the lock: {problems}"
