#!/usr/bin/env python3
"""scripts/upgrade_regression.py — offline upgrade regression self-check (档29).

Runs automatically after a successful `relock --apply` (or standalone):
  1. full pytest MINUS an explicit environment-dependent exclusion list
  2. relock dry-run x4 — every locked skill must report 无变化
  3. doctor --require-wechat must PASS
No external side effects. Exit 0 = all pass; any failure = exit 1.

The exclusion list is EXPLICIT and names the missing environment per entry.
It exists because this dev box has no sibling checkouts / live handshake env;
it must NEVER be grown to mask a real regression.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCTOR = REPO_ROOT / "scripts" / "doctor.py"
RELOCK = REPO_ROOT / "scripts" / "relock.py"
LOCKED_SKILLS = ["super-writer", "zh-human-writing", "media-enrichment", "gzh-design"]

# ── explicit env-dependent exclusion list (档29 Part 2) ─────────────────────
# Every entry: exact node id + the missing environment it depends on.
EXCLUDED_TESTS = [
    # fake_live full-run / receipt-tamper / chapter-gate tests: need a
    # media-enrichment checkout at <repo>/../media-enrichment
    # (fixed media root with src/media_enrichment/input_contract.py)
    "tests/test_dev2_fake_live.py::test_fake_live_six_stages",
    "tests/test_dev2_fake_live.py::test_receipt_tamper",
    "tests/test_dev2_fake_live.py::test_dynamic_chapter_gate",
    "tests/test_hotfix1.py::test_resume_tamper_media_manifest_invalidates_media_and_later",
    "tests/test_hotfix1.py::test_resume_tamper_upstream_article_invalidates_media_gzh_wechat",
    "tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[a_empty_object]",
    "tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[b_del_input_hash]",
    "tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[c_del_output_hash]",
    "tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[d_del_entrypoint_sha]",
    "tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[e_del_official_validators]",
    "tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[f_validator_exit_1]",
    "tests/test_hotfix2_receipt_tamper.py::test_receipt_tamper_fails_verify_and_resume[g_official_exit_1]",
    "tests/test_hotfix2_receipt_tamper.py::test_wechat_gate_blocks_on_tampered_prior_receipt",
    "tests/test_hotfix3_approved_scope.py::test_c_material_scope_only_that_material",
    "tests/test_hotfix3_approved_scope.py::test_d_source_url_scope_no_inheritance",
    "tests/test_hotfix3_approved_scope.py::test_e_unknown_scope_not_known_allowed",
    "tests/test_hotfix3_approved_scope.py::test_bad_evidence_hash_ignored",
    "tests/test_hotfix3_approved_scope.py::test_material_scope_missing_binding_ignored",
    "tests/test_hotfix3_approved_scope.py::test_source_url_for_unknown_url_approves_nobody",
    # portable installer: needs a git checkout context for the bundle build
    "tests/test_hotfix1.py::test_portable_installer_preserves_pipeline_release_include",
    # live cross-repo handshake: need WXGZH_REAL_SUPER_WRITER_ROOT /
    # WXGZH_REAL_SKILLS_HOME pointing at real skill checkouts
    "tests/test_hotfix7_live_handshake.py::test_cross_repo_real_full_mode_long_pass",
    "tests/test_hotfix7_live_handshake.py::test_cross_repo_medium_overlong_uses_declared_policy",
    "tests/test_hotfix7_live_handshake.py::test_cross_repo_missing_full_mode_artifact_fails",
    # full LIVE 6-stage pipeline runs (real agents + WeChat draft): never in
    # an offline regression
    "tests/test_pipeline.py::test_02_03_defaults_and_draft",
    "tests/test_pipeline.py::test_08_no_stage_skip",
    "tests/test_pipeline.py::test_10_resume_no_rerun",
    "tests/test_pipeline.py::test_full_run_delivery",
]


def _child_env() -> dict:
    sys.path.insert(0, str(REPO_ROOT))
    from wxgzh_pipeline import paths as P
    project_root = P.resolve_project_root(os.environ.get("WXGZH_PROJECT_ROOT"))
    env = dict(os.environ)
    env.pop("AGENT_SKILLS_HOME", None)  # canonical project layout only
    env["WXGZH_PROJECT_ROOT"] = str(project_root)
    return env, project_root


def _run(cmd, env=None, timeout=900) -> tuple[bool, str]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              timeout=timeout, cwd=str(REPO_ROOT), env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"invocation failed: {exc}"
    return proc.returncode == 0, ((proc.stdout or "") + (proc.stderr or "")).strip()


def step_pytest() -> tuple[bool, str]:
    cmd = [sys.executable, "-m", "pytest", str(REPO_ROOT / "tests"),
           "-q", "-p", "no:cacheprovider"]
    for node in EXCLUDED_TESTS:
        cmd += ["--deselect", node]
    ok, out = _run(cmd, env=dict(os.environ), timeout=900)
    tail = "\n".join(out.splitlines()[-6:])
    return ok, f"pytest: {'PASS' if ok else 'FAIL'} " \
               f"({len(EXCLUDED_TESTS)} explicit deselects)\n{tail}"


def step_relock_dryruns(env, project_root) -> tuple[bool, str]:
    lines = []
    all_ok = True
    for name in LOCKED_SKILLS:
        ok, out = _run([sys.executable, str(RELOCK), "--skill", name,
                        "--project-root", str(project_root),
                        "--reason", "upgrade-regression dry-run"], env=env)
        no_change = ("status: 无变化" in out) and ("CHANGED" not in out)
        status_line = next((ln for ln in out.splitlines()
                            if ln.startswith("status:")), "status: <missing>")
        lines.append(f"  {name}: {status_line} {'OK' if ok and no_change else 'FAIL'}")
        all_ok = all_ok and ok and no_change
    return all_ok, "relock dry-run x4: " + ("PASS" if all_ok else "FAIL") + "\n" + "\n".join(lines)


def step_doctor(env, project_root) -> tuple[bool, str]:
    ok, out = _run([sys.executable, str(DOCTOR), "--project-root",
                    str(project_root), "--require-wechat"], env=env)
    verdict = "PASS" if ok else "FAIL"
    return ok, f"doctor --require-wechat: {verdict}"


def main() -> int:
    env, project_root = _child_env()
    print(f"upgrade_regression: project_root={project_root}")
    ok = True
    for name, fn in (("pytest", step_pytest),
                     ("relock_dryruns", lambda: step_relock_dryruns(env, project_root)),
                     ("doctor", lambda: step_doctor(env, project_root))):
        step_ok, text = fn()
        print(text)
        ok = ok and step_ok
    print("upgrade_regression: " + ("ALL PASS" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
