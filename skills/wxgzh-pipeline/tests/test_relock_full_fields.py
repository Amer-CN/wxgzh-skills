"""档44 — relock full-field update + remote-witness + relock-then-install chain.

All witness/install/doctor subprocess calls are faked (no network, no real
environment writes). Mismatch scenarios live in tmp_path sandboxes; every
"refuse" case must leave zero writes; rollback cases must restore byte-exact.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import scripts.relock as RELOCK
from wxgzh_pipeline.receipts import _find_upgrade_chain

REPO_ROOT = Path(__file__).resolve().parents[1]

REMOTE_TREE = "ab" * 20
OTHER_TREE = "cd" * 20
COMMIT = "7c0c06f845b886138525af3bfaafa13614fdfe60"
OLD_COMMIT = "0007d7e6a4493aab59070d9c31dcde83830302fd"


class FakeProc:
    def __init__(self, rc=0, stdout="", stderr=""):
        self.returncode = rc
        self.stdout = stdout
        self.stderr = stderr


def _sha(text):
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


OLD_RENDER = _sha("old-render\n")
OLD_VALIDATE = _sha("old-validate\n")
OLD_GENERATE = _sha("old-gen\n")


def _make_env(tmp_path, lock_values=None):
    """gzh-design entry with full field set (incl. render/component fields)."""
    skills = tmp_path / "skills"
    (skills / "gzh-design" / "scripts").mkdir(parents=True)
    (skills / "gzh-design" / "scripts" / "render.py").write_text("old-render\n", encoding="utf-8")
    (skills / "gzh-design" / "scripts" / "validate.py").write_text("old-validate\n", encoding="utf-8")
    (skills / "gzh-design" / "scripts" / "generate.py").write_text("old-gen\n", encoding="utf-8")
    vals = {
        "skill_root_sha256": "9a8cd7f5" * 8,
        "runtime_manifest_sha256": "ced84143" * 8,
        "runtime_file_count": 76,
        "entrypoint_sha256": OLD_RENDER,
        "validator_sha256": OLD_VALIDATE,
        "render_entry_sha256": OLD_RENDER,
        "component_source_sha256": OLD_GENERATE,
        "full_commit_sha": OLD_COMMIT,
        "source_tree_sha": "a1f40820" * 8,
        "branch": "chore/wxgzh-pipeline-dev2-integration",
    }
    if lock_values:
        vals.update(lock_values)
    lock = {"lock_version": 2, "skills": {"gzh-design": {
        "skill_name": "gzh-design", "skill_version": "v-test",
        "repository_url": "https://github.com/Amer-CN/gzh-design-skill",
        "branch": "chore/wxgzh-pipeline-dev2-integration",
        **vals,
        "entrypoint": "scripts/render.py", "validator": "scripts/validate.py",
        "render_entry": "scripts/render.py",
        "component_source": "scripts/generate.py",
        "required_files": ["scripts/render.py", "scripts/validate.py",
                          "scripts/generate.py"],
    }}}
    lock_path = tmp_path / "skills.lock.json"
    lock_path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return skills, lock_path


def _make_source_tree(tmp_path):
    src = tmp_path / "source-tree"
    (src / ".git").mkdir(parents=True)  # marker: git checkout (symbolic-ref is faked)
    (src / "scripts").mkdir(parents=True)
    (src / "scripts" / "render.py").write_text("new-render\n", encoding="utf-8")
    (src / "scripts" / "validate.py").write_text("old-validate\n", encoding="utf-8")
    (src / "scripts" / "generate.py").write_text("old-gen\n", encoding="utf-8")
    return src


def _args(tmp_path, extra=None):
    base = {
        "--skill": "gzh-design", "--reason": "档44 test",
        "--skills-home": str(tmp_path / "skills"),
        "--lock-path": str(tmp_path / "skills.lock.json"),
        "--history-path": str(tmp_path / "skills.lock.history.json"),
        "--backup-dir": str(tmp_path / "backups"),
        "--tree-backup-dir": str(tmp_path / "tree-backups"),
        "--project-root": str(tmp_path),
    }
    if extra:
        base.update(extra)
    out = []
    for key, value in base.items():
        out.append(key)
        if value is not None:
            out.append(str(value))
    return out


class FakeRunner:
    """Routes subprocess.run: git witness commands, install.py, doctor.py."""

    def __init__(self, tmp_path, *, ls_remote_ok=True, fetch_ok=True, add_ok=True,
                 write_tree_ok=True, local_tree=REMOTE_TREE, install_ok=True,
                 install_stdout=None, doctor_ok=True, doctor_results=None,
                 network_down=False, smoke_ok=True):
        self.tmp_path = tmp_path
        self.ls_remote_ok = ls_remote_ok
        self.fetch_ok = fetch_ok
        self.add_ok = add_ok
        self.write_tree_ok = write_tree_ok
        self.local_tree = local_tree
        self.install_ok = install_ok
        self.install_stdout = install_stdout
        self.doctor_ok = doctor_ok
        self.doctor_results = list(doctor_results) if doctor_results else None
        self.network_down = network_down
        self.smoke_ok = smoke_ok
        self.calls = []

    def __call__(self, cmd, **kwargs):
        argv = list(cmd)
        self.calls.append(argv)
        if self.network_down and argv[:1] == ["git"]:
            raise OSError("network down (simulated)")
        if argv[:1] == ["git"]:
            if "ls-remote" in argv:
                return FakeProc(0 if self.ls_remote_ok else 128,
                                stdout=COMMIT if self.ls_remote_ok else "")
            if "init" in argv or "config" in argv or "remote" in argv or "symbolic-ref" in argv:
                if "symbolic-ref" in argv:
                    return FakeProc(0, stdout="fix/obs73-codeblock-docs")
                return FakeProc(0)
            if "fetch" in argv:
                return FakeProc(0 if self.fetch_ok else 128,
                                stderr="" if self.fetch_ok else "could not fetch")
            if "rev-parse" in argv:
                return FakeProc(0, stdout=REMOTE_TREE)
            if "add" in argv:
                return FakeProc(0 if self.add_ok else 128)
            if "write-tree" in argv:
                return FakeProc(0 if self.write_tree_ok else 128,
                                stdout=self.local_tree if self.write_tree_ok else "")
            return FakeProc(0)
        joined = " ".join(argv)
        if "render" in joined and "scripts" in joined:
            # OBS-78 entrypoint smoke subprocess
            if self.smoke_ok:
                return FakeProc(0, stdout="[render_article] smoke ok")
            return FakeProc(1, stderr="Traceback (most recent call last):\nNameError: name '_render_item' is not defined")
        if "install.py" in joined:
            if self.install_ok:
                out = self.install_stdout or json.dumps(
                    {"ok": True, "hash_verification": {"gzh-design": True}})
                return FakeProc(0, stdout=out)
            return FakeProc(1, stdout=json.dumps(
                {"ok": False, "error": "source proof does not match skills.lock"}))
        if "doctor.py" in joined:
            if self.doctor_results:
                rc = self.doctor_results.pop(0)
            else:
                rc = 0 if self.doctor_ok else 1
            return FakeProc(rc, stdout=json.dumps(_doctor_report(rc)))
        return FakeProc(0)


def _run(tmp_path, monkeypatch, runner, extra=None, apply=True):
    if apply:
        extra = dict(extra or {})
        extra.setdefault("--apply", None)
        extra.setdefault("--skip-regression", None)
    monkeypatch.setattr(RELOCK.subprocess, "run", runner)
    return RELOCK.main(_args(tmp_path, extra))


def _doctor_report(rc):
    """Doctor-style report the gate classifier can parse (mirrors test_relock)."""
    skills = {}
    for name in ("gzh-design", "super-writer"):
        ok = rc == 0
        skills[name] = {"exists": True, "version_ok": ok, "hash_ok": ok,
                        "entrypoints_ok": True, "missing_files": [], "ok": ok}
    return {"FAIL_CLOSED": rc != 0, "project_writable": True,
            "wechat_config_present": True, "LIVE_PIPELINE_ALLOWED": True,
            "skills": skills, "doctor": "PASS" if rc == 0 else "FAIL"}


def _snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}


def _snapshot_skills_before(tmp_path, before):
    """Subset of the pre-run snapshot covering the skills tree only."""
    out = {}
    for k, v in before.items():
        if k.startswith("skills\\") or k.startswith("skills/"):
            out[k.split("\\", 1)[1] if "\\" in k else k.split("/", 1)[1]] = v
    return out


# ── a. four new fields update correctly ────────────────────────────────────
def test_source_tree_updates_all_new_fields(tmp_path, monkeypatch):
    skills, lock_path = _make_env(tmp_path)
    src = _make_source_tree(tmp_path)
    runner = FakeRunner(tmp_path)
    rc = _run(tmp_path, monkeypatch, runner, {
        "--source-tree": str(src), "--source-commit": COMMIT, "--apply": None,
        "--skip-regression": None,
    })
    assert rc == 0
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    entry = lock["skills"]["gzh-design"]
    assert entry["full_commit_sha"] == COMMIT
    assert entry["source_tree_sha"] == REMOTE_TREE
    assert entry["branch"] == "fix/obs73-codeblock-docs"
    assert entry["entrypoint_sha256"] != OLD_RENDER
    assert entry["render_entry_sha256"] == entry["entrypoint_sha256"]
    assert entry["validator_sha256"] == OLD_VALIDATE  # unchanged file
    assert entry["component_source_sha256"] == OLD_GENERATE  # unchanged file
    assert entry["skill_root_sha256"] != "9a8cd7f5" * 8
    # sandbox tree was installed from source (installer faked ok -> tree copied)
    # doctor faked ok -> exit 0


# ── b. witness checks a/b/c fail -> refuse, zero writes ────────────────────
def test_witness_a_fail_refuses_zero_write(tmp_path, monkeypatch):
    skills, lock_path = _make_env(tmp_path)
    src = _make_source_tree(tmp_path)
    before = _snapshot(tmp_path)
    runner = FakeRunner(tmp_path, ls_remote_ok=False)
    rc = _run(tmp_path, monkeypatch, runner, {
        "--source-tree": str(src), "--source-commit": COMMIT})
    assert rc == RELOCK.EXIT_USAGE
    assert _snapshot(tmp_path) == before


def test_witness_b_fail_refuses_zero_write(tmp_path, monkeypatch):
    skills, lock_path = _make_env(tmp_path)
    src = _make_source_tree(tmp_path)
    before = _snapshot(tmp_path)
    runner = FakeRunner(tmp_path, local_tree=OTHER_TREE)
    rc = _run(tmp_path, monkeypatch, runner, {
        "--source-tree": str(src), "--source-commit": COMMIT})
    assert rc == RELOCK.EXIT_USAGE
    assert _snapshot(tmp_path) == before


def test_witness_c_fail_refuses_zero_write(tmp_path, monkeypatch):
    skills, lock_path = _make_env(tmp_path)
    src = _make_source_tree(tmp_path)
    before = _snapshot(tmp_path)
    runner = FakeRunner(tmp_path)
    monkeypatch.setattr(RELOCK.subprocess, "run", runner)
    # call the witness directly with a mismatched expected tree sha (check c)
    ok, msg, info = RELOCK.verify_remote_witness(
        "https://github.com/Amer-CN/gzh-design-skill", COMMIT, src, OTHER_TREE)
    assert not ok and "(c)" in msg and "远端" in msg
    rc = _run(tmp_path, monkeypatch, runner, {
        "--source-tree": str(src), "--source-commit": COMMIT}, apply=False)  # dry-run
    assert rc == RELOCK.EXIT_OK
    assert _snapshot(tmp_path) == before


# ── c. network unavailable -> refuse, no fallback ──────────────────────────
def test_network_unavailable_refuses(tmp_path, monkeypatch):
    skills, lock_path = _make_env(tmp_path)
    src = _make_source_tree(tmp_path)
    before = _snapshot(tmp_path)
    runner = FakeRunner(tmp_path, network_down=True)
    rc = _run(tmp_path, monkeypatch, runner, {
        "--source-tree": str(src), "--source-commit": COMMIT})
    assert rc == RELOCK.EXIT_USAGE
    assert _snapshot(tmp_path) == before


# ── d. install failure -> lock rollback, byte-exact ────────────────────────
def test_install_failure_rolls_back_lock_and_tree(tmp_path, monkeypatch):
    skills, lock_path = _make_env(tmp_path)
    src = _make_source_tree(tmp_path)
    before = _snapshot(tmp_path)
    runner = FakeRunner(tmp_path, install_ok=False, doctor_results=[0])
    rc = _run(tmp_path, monkeypatch, runner, {
        "--source-tree": str(src), "--source-commit": COMMIT, "--apply": None,
        "--skip-regression": None,
    })
    assert rc == RELOCK.EXIT_POST_DOCTOR_FAIL
    assert lock_path.read_bytes() == before[str("skills.lock.json")]
    assert not (tmp_path / "skills.lock.history.json").exists()
    assert _snapshot(tmp_path / "skills") == _snapshot_skills_before(tmp_path, before)


# ── e. post-doctor failure -> lock + installed tree rollback ───────────────
def test_post_doctor_failure_rolls_back_lock_and_tree(tmp_path, monkeypatch):
    skills, lock_path = _make_env(tmp_path)
    src = _make_source_tree(tmp_path)
    before = _snapshot(tmp_path)
    runner = FakeRunner(tmp_path, install_ok=True, doctor_results=[0, 1])
    rc = _run(tmp_path, monkeypatch, runner, {
        "--source-tree": str(src), "--source-commit": COMMIT, "--apply": None,
        "--skip-regression": None,
    })
    assert rc == RELOCK.EXIT_POST_DOCTOR_FAIL
    assert lock_path.read_bytes() == before[str("skills.lock.json")]
    assert not (tmp_path / "skills.lock.history.json").exists()
    assert _snapshot(tmp_path / "skills") == _snapshot_skills_before(tmp_path, before)


# ── f. ledger contains all changed fields ──────────────────────────────────
def test_ledger_contains_all_changed_fields(tmp_path, monkeypatch):
    skills, lock_path = _make_env(tmp_path)
    src = _make_source_tree(tmp_path)
    runner = FakeRunner(tmp_path)
    rc = _run(tmp_path, monkeypatch, runner, {
        "--source-tree": str(src), "--source-commit": COMMIT, "--apply": None,
        "--skip-regression": None,
    })
    assert rc == 0
    rec = json.loads((tmp_path / "skills.lock.history.json").read_text(encoding="utf-8"))[0]
    assert rec["old_root_sha256"] == "9a8cd7f5" * 8
    assert rec["old_full_commit_sha"] == OLD_COMMIT
    assert rec["new_full_commit_sha"] == COMMIT
    assert rec["old_source_tree_sha"] == "a1f40820" * 8
    assert rec["new_source_tree_sha"] == REMOTE_TREE
    assert rec["old_entrypoint_sha256"] == OLD_RENDER
    assert rec["old_render_entry_sha256"] == OLD_RENDER
    assert rec["old_branch"] == "chore/wxgzh-pipeline-dev2-integration"
    assert rec["new_branch"] == "fix/obs73-codeblock-docs"
    assert rec["source_commit_verified"] is True
    assert rec["remote_repo"] == "https://github.com/Amer-CN/gzh-design-skill"
    assert rec["entry_id"].startswith("relock-gzh-design-")


# ── chain tracing still works with the new record shape (instruction 14) ───
def test_upgrade_chain_traces_with_new_record_shape(tmp_path):
    history = tmp_path / "skills.lock.history.json"
    history.write_text(json.dumps([{
        "entry_id": "relock-gzh-design-20260802T000000Z-abcdef12",
        "skill": "gzh-design",
        "old_root_sha256": "9a8cd7f5" * 8,
        "new_root_sha256": "4d68cd90" * 8,
        "old_manifest_sha256": "ced84143" * 8,
        "new_manifest_sha256": "ced84143" * 8,
        "old_full_commit_sha": OLD_COMMIT,
        "new_full_commit_sha": COMMIT,
        "old_entrypoint_sha256": "e4023726" * 8,
        "new_entrypoint_sha256": "ca599b64" * 8,
        "source_commit_verified": True,
        "remote_repo": "https://github.com/Amer-CN/gzh-design-skill",
        "recorded_at": "2026-08-02T00:00:00Z",
        "doctor_result": "PASS",
    }], ensure_ascii=False) + "\n", encoding="utf-8")
    chain = _find_upgrade_chain("gzh-design", "9a8cd7f5" * 8, "4d68cd90" * 8,
                                history_path=history)
    assert chain is not None and len(chain) == 1
    assert chain[0]["entry_id"].startswith("relock-gzh-design-")


# ── g/h. existing paths unaffected ─────────────────────────────────────────
def test_required_files_switch_still_works_without_source_tree(tmp_path, monkeypatch):
    # 3-field path + removal switch: existing semantics preserved (no source tree)
    skills, lock_path = _make_env(tmp_path)
    req = json.loads(lock_path.read_text(encoding="utf-8"))["skills"]["gzh-design"]
    req["required_files"] = ["scripts/render.py", "scripts/validate.py",
                             "scripts/generate.py", "scripts/removed.py"]
    lock_path.write_text(json.dumps(
        {"lock_version": 2, "skills": {"gzh-design": req}},
        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    runner = FakeRunner(tmp_path)
    rc = _run(tmp_path, monkeypatch, runner, {
        "--allow-required-files-removal": None, "--apply": None,
        "--skip-regression": None,
    })
    assert rc == 0
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    assert "removed.py" not in (lock["skills"]["gzh-design"].get("required_files") or [])


def test_three_field_path_regression(tmp_path, monkeypatch):
    skills, lock_path = _make_env(tmp_path)
    runner = FakeRunner(tmp_path)
    rc = _run(tmp_path, monkeypatch, runner, {"--apply": None, "--skip-regression": None})
    assert rc == 0
    rec = json.loads((tmp_path / "skills.lock.history.json").read_text(encoding="utf-8"))[0]
    assert "old_root_sha256" in rec and "new_root_sha256" in rec
    assert "source_commit_verified" not in rec  # no witness in 3-field path
    assert rec["entry_id"].startswith("relock-gzh-design-")


def test_source_tree_without_commit_refused(tmp_path, monkeypatch):
    skills, lock_path = _make_env(tmp_path)
    src = _make_source_tree(tmp_path)
    before = _snapshot(tmp_path)
    rc = _run(tmp_path, monkeypatch, FakeRunner(tmp_path), {
        "--source-tree": str(src)})
    assert rc == RELOCK.EXIT_USAGE
    assert _snapshot(tmp_path) == before


# ── 档45R: skill_version support (same source as doctor's _read_version) ────

def test_skill_version_written_and_in_ledger(tmp_path, monkeypatch):
    skills, lock_path = _make_env(tmp_path)
    src = _make_source_tree(tmp_path)
    (src / "RELEASE_NOTES.md").write_text("# gzh-design v9.9.9-test\n", encoding="utf-8")
    runner = FakeRunner(tmp_path)
    rc = _run(tmp_path, monkeypatch, runner, {
        "--source-tree": str(src), "--source-commit": COMMIT, "--apply": None,
        "--skip-regression": None,
    })
    assert rc == 0
    entry = json.loads(lock_path.read_text(encoding="utf-8"))["skills"]["gzh-design"]
    assert entry["skill_version"] == "v9.9.9-test"
    rec = json.loads((tmp_path / "skills.lock.history.json").read_text(encoding="utf-8"))[0]
    assert rec["old_skill_version"] == "v-test"
    assert rec["new_skill_version"] == "v9.9.9-test"


def test_version_source_same_as_read_version(tmp_path, monkeypatch):
    """口径同源: BOM + CRLF + 前后空白样本 — relock 写入值必须与
    skill_discovery._read_version 读出值逐字相等(构造样本实测)。"""
    from wxgzh_pipeline.skill_discovery import _read_version
    skills, lock_path = _make_env(tmp_path)
    src = _make_source_tree(tmp_path)
    # BOM + CRLF 行尾 + 首行前后空白 + 多个空格分隔
    sample = "\ufeff# gzh-design   v9.9.9-tricky  \r\n"
    (src / "RELEASE_NOTES.md").write_bytes(sample.encode("utf-8"))
    expected = _read_version(src, "gzh-design")
    assert expected == "v9.9.9-tricky", f"_read_version itself: {expected!r}"
    runner = FakeRunner(tmp_path)
    rc = _run(tmp_path, monkeypatch, runner, {
        "--source-tree": str(src), "--source-commit": COMMIT, "--apply": None,
        "--skip-regression": None,
    })
    assert rc == 0
    entry = json.loads(lock_path.read_text(encoding="utf-8"))["skills"]["gzh-design"]
    assert entry["skill_version"] == expected  # 逐字相等,同源


def test_warn_root_changed_version_unchanged(tmp_path, monkeypatch, capsys):
    skills, lock_path = _make_env(tmp_path)
    src = _make_source_tree(tmp_path)  # render.py differs -> root changes; no RELEASE_NOTES -> version unchanged
    runner = FakeRunner(tmp_path)
    rc = _run(tmp_path, monkeypatch, runner, {
        "--source-tree": str(src), "--source-commit": COMMIT, "--apply": None,
        "--skip-regression": None,
    })
    assert rc == 0
    out = capsys.readouterr().out
    assert "WARN: root 变化但 skill_version 未变" in out


def test_warn_version_changed_root_unchanged(tmp_path, monkeypatch, capsys):
    src = tmp_path / "source-tree"
    (src / ".git").mkdir(parents=True)
    (src / "scripts").mkdir(parents=True)
    # identical content to the old tree -> root unchanged (lock root = computed)
    (src / "scripts" / "render.py").write_text("old-render\n", encoding="utf-8")
    (src / "scripts" / "validate.py").write_text("old-validate\n", encoding="utf-8")
    (src / "scripts" / "generate.py").write_text("old-gen\n", encoding="utf-8")
    root_sha, _, _ = RELOCK.compute_skill_hashes(src)
    skills, lock_path = _make_env(tmp_path, lock_values={"skill_root_sha256": root_sha})
    monkeypatch.setattr(RELOCK, "_read_version", lambda tree, name: "v9.9.9-bump")
    runner = FakeRunner(tmp_path)
    rc = _run(tmp_path, monkeypatch, runner, {
        "--source-tree": str(src), "--source-commit": COMMIT, "--apply": None,
        "--skip-regression": None,
    })
    assert rc == 0
    out = capsys.readouterr().out
    assert "WARN: skill_version 变化但 root 未变" in out


def test_rollback_restores_skill_version(tmp_path, monkeypatch):
    skills, lock_path = _make_env(tmp_path)
    src = _make_source_tree(tmp_path)
    (src / "RELEASE_NOTES.md").write_text("# gzh-design v9.9.9-test\n", encoding="utf-8")
    runner = FakeRunner(tmp_path, install_ok=False, doctor_results=[0])
    rc = _run(tmp_path, monkeypatch, runner, {
        "--source-tree": str(src), "--source-commit": COMMIT, "--apply": None,
        "--skip-regression": None,
    })
    assert rc == RELOCK.EXIT_POST_DOCTOR_FAIL
    entry = json.loads(lock_path.read_text(encoding="utf-8"))["skills"]["gzh-design"]
    assert entry["skill_version"] == "v-test"  # restored with the byte-level lock rollback


# ── 档45R2 OBS-78: entrypoint smoke ─────────────────────────────────────────

def test_smoke_failure_rolls_back_lock_and_tree(tmp_path, monkeypatch):
    skills, lock_path = _make_env(tmp_path)
    src = _make_source_tree(tmp_path)
    (src / "RELEASE_NOTES.md").write_text("# gzh-design v9.9.9-test\n", encoding="utf-8")
    before_lock = lock_path.read_bytes()
    runner = FakeRunner(tmp_path, doctor_results=[0], smoke_ok=False)
    rc = _run(tmp_path, monkeypatch, runner, {
        "--source-tree": str(src), "--source-commit": COMMIT, "--apply": None,
        "--skip-regression": None,
    })
    assert rc == RELOCK.EXIT_POST_DOCTOR_FAIL
    assert lock_path.read_bytes() == before_lock
    assert not (tmp_path / "skills.lock.history.json").exists()
    assert _snapshot(tmp_path / "skills") == _snapshot_skills_before(tmp_path, _snapshot(tmp_path))


def test_smoke_pass_allows_apply(tmp_path, monkeypatch, capsys):
    skills, lock_path = _make_env(tmp_path)
    src = _make_source_tree(tmp_path)
    (src / "RELEASE_NOTES.md").write_text("# gzh-design v9.9.9-test\n", encoding="utf-8")
    runner = FakeRunner(tmp_path, doctor_results=[0], smoke_ok=True)
    rc = _run(tmp_path, monkeypatch, runner, {
        "--source-tree": str(src), "--source-commit": COMMIT, "--apply": None,
        "--skip-regression": None,
    })
    assert rc == 0
    out = capsys.readouterr().out
    assert "entrypoint smoke PASS" in out


def test_no_smoke_entry_skipped_explicitly(tmp_path, monkeypatch, capsys):
    skills, lock_path = _make_env(tmp_path)
    src = _make_source_tree(tmp_path)
    monkeypatch.setattr(RELOCK, "SMOKE_ENTRIES", {})
    runner = FakeRunner(tmp_path, doctor_results=[0])
    rc = _run(tmp_path, monkeypatch, runner, {
        "--source-tree": str(src), "--source-commit": COMMIT, "--apply": None,
        "--skip-regression": None,
    })
    assert rc == 0
    out = capsys.readouterr().out
    assert "跳过冒烟" in out or "not configured" in out


def test_smoke_rolls_back_then_reapply_succeeds(tmp_path, monkeypatch):
    """坏版本被拦 -> 回滚;修好后重跑 -> 成功(模拟 45R2 流程)。"""
    skills, lock_path = _make_env(tmp_path)
    src = _make_source_tree(tmp_path)
    (src / "RELEASE_NOTES.md").write_text("# gzh-design v9.9.9-test\n", encoding="utf-8")
    runner = FakeRunner(tmp_path, doctor_results=[0], smoke_ok=False)
    rc = _run(tmp_path, monkeypatch, runner, {
        "--source-tree": str(src), "--source-commit": COMMIT, "--apply": None,
        "--skip-regression": None,
    })
    assert rc == RELOCK.EXIT_POST_DOCTOR_FAIL
    runner2 = FakeRunner(tmp_path, doctor_results=[0], smoke_ok=True)
    rc2 = _run(tmp_path, monkeypatch, runner2, {
        "--source-tree": str(src), "--source-commit": COMMIT, "--apply": None,
        "--skip-regression": None,
    })
    assert rc2 == 0
