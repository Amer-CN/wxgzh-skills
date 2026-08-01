"""档27 P0-1: one-click re-lock tool (scripts/relock.py).

All tests run against tmp_path fixtures with path overrides — the real repo
skills.lock.json / ledger are never touched. Doctor subprocess is monkeypatched.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from conftest import SKILL_ROOT
from wxgzh_pipeline.skill_discovery import compute_root_sha, compute_runtime_manifest_sha


def _load_relock():
    path = SKILL_ROOT / "scripts" / "relock.py"
    spec = importlib.util.spec_from_file_location("relock", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RELOCK = _load_relock()


class FakeProc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _fake_tree(skills_home: Path, name: str, files: dict[str, str]) -> None:
    root = skills_home / name
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def _make_env(tmp_path: Path, lock_values: dict | None = None):
    """Fake skills home + lock; lock_values override the three hash fields."""
    skills_home = tmp_path / "skills"
    _fake_tree(skills_home, "gzh-design", {
        "SKILL.md": "---\nname: gzh-design\n---\n",
        "scripts/render.py": "print('render')\n",
        "scripts/publish.py": "print('publish')\n",
    })
    root_sha, nfiles = compute_root_sha(skills_home / "gzh-design")
    man_sha, _ = compute_runtime_manifest_sha(skills_home / "gzh-design")
    computed = {
        "skill_root_sha256": root_sha,
        "runtime_manifest_sha256": man_sha,
        "runtime_file_count": nfiles,
    }
    lock_vals = dict(computed)
    if lock_values:
        lock_vals.update(lock_values)
    lock = {"lock_version": 2, "skills": {"gzh-design": {
        "skill_name": "gzh-design",
        "skill_version": "v-test",
        **lock_vals,
        "entrypoint": "scripts/render.py",
        "validator": None,
        "required_files": ["scripts/render.py"],
    }}}
    lock_path = tmp_path / "skills.lock.json"
    lock_path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    return skills_home, lock_path, computed


def _snapshot(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}


def _args(tmp_path, extra: dict | None = None) -> list[str]:
    base = {
        "--skills-home": str(tmp_path / "skills"),
        "--lock-path": str(tmp_path / "skills.lock.json"),
        "--history-path": str(tmp_path / "skills.lock.history.json"),
        "--backup-dir": str(tmp_path / "backups"),
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


def _monkey_doctor(monkeypatch, results):
    calls = {"n": 0}

    def fake_run(cmd, **kwargs):
        rc = results[min(calls["n"], len(results) - 1)]
        calls["n"] += 1
        return FakeProc(returncode=rc, stdout='{"doctor": "PASS" if rc == 0 else "FAIL"}')

    monkeypatch.setattr(RELOCK.subprocess, "run", fake_run)
    return calls


# ── a. dry-run produces no file writes ──────────────────────────────────────
def test_dry_run_writes_nothing(tmp_path):
    skills_home, lock_path, _ = _make_env(tmp_path)
    before = _snapshot(tmp_path)
    rc = RELOCK.main(_args(tmp_path, {"--skill": "gzh-design", "--reason": "survey"}))
    assert rc == RELOCK.EXIT_OK
    assert _snapshot(tmp_path) == before
    assert not (tmp_path / "skills.lock.history.json").exists()
    assert not (tmp_path / "backups").exists()


# ── b. --apply + doctor FAIL -> byte-identical rollback ─────────────────────
def test_apply_doctor_fail_rolls_back(tmp_path, monkeypatch):
    skills_home, lock_path, base = _make_env(
        tmp_path, lock_values={"skill_root_sha256": "old" * 32,
                               "runtime_manifest_sha256": "old" * 32,
                               "runtime_file_count": 999})
    history = tmp_path / "skills.lock.history.json"
    history.write_text(json.dumps([{"entry_id": "pre-existing"}], ensure_ascii=False) + "\n",
                       encoding="utf-8")
    lock_before = lock_path.read_bytes()
    hist_before = history.read_bytes()
    _monkey_doctor(monkeypatch, [0, 1])  # pre-gate PASS, post FAIL
    rc = RELOCK.main(_args(tmp_path, {"--skill": "gzh-design",
                                      "--reason": "test rollback", "--apply": None}))
    assert rc == RELOCK.EXIT_POST_DOCTOR_FAIL
    assert lock_path.read_bytes() == lock_before
    assert history.read_bytes() == hist_before
    # ledger not modified, pre-existing record untouched
    assert json.loads(history.read_text(encoding="utf-8"))[0]["entry_id"] == "pre-existing"


def test_apply_doctor_fail_rolls_back_created_history(tmp_path, monkeypatch):
    """History file created by this run must be deleted on rollback."""
    skills_home, lock_path, base = _make_env(
        tmp_path, lock_values={"skill_root_sha256": "old" * 32,
                               "runtime_manifest_sha256": "old" * 32,
                               "runtime_file_count": 999})
    _monkey_doctor(monkeypatch, [0, 1])
    rc = RELOCK.main(_args(tmp_path, {"--skill": "gzh-design",
                                      "--reason": "test rollback", "--apply": None}))
    assert rc == RELOCK.EXIT_POST_DOCTOR_FAIL
    assert not (tmp_path / "skills.lock.history.json").exists()


# ── c. --reason missing/empty refused ───────────────────────────────────────
def test_reason_missing_refused(tmp_path):
    _make_env(tmp_path)
    with pytest.raises(SystemExit) as exc:
        RELOCK.main(_args(tmp_path, {"--skill": "gzh-design", "--apply": None}))
    assert exc.value.code == 2  # argparse


def test_reason_empty_refused(tmp_path):
    skills_home, lock_path, _ = _make_env(tmp_path)
    before = _snapshot(tmp_path)
    rc = RELOCK.main(_args(tmp_path, {"--skill": "gzh-design", "--reason": "   "}))
    assert rc == RELOCK.EXIT_USAGE
    assert _snapshot(tmp_path) == before


# ── d. ledger append format ─────────────────────────────────────────────────
def test_apply_ledger_format(tmp_path, monkeypatch):
    skills_home, lock_path, base = _make_env(
        tmp_path, lock_values={"skill_root_sha256": "old" * 32,
                               "runtime_manifest_sha256": "old" * 32,
                               "runtime_file_count": 999})
    _monkey_doctor(monkeypatch, [0, 0])  # pre + post PASS
    rc = RELOCK.main(_args(tmp_path, {"--skill": "gzh-design",
                                      "--reason": "first relock", "--apply": None}))
    assert rc == RELOCK.EXIT_OK
    history = json.loads((tmp_path / "skills.lock.history.json").read_text(encoding="utf-8"))
    assert len(history) == 1
    rec = history[0]
    assert rec["skill"] == "gzh-design"
    assert rec["old_root_sha256"] == "old" * 32
    assert rec["new_root_sha256"] == base["skill_root_sha256"]
    assert rec["old_manifest_sha256"] == "old" * 32
    assert rec["new_manifest_sha256"] == base["runtime_manifest_sha256"]
    assert rec["old_file_count"] == 999
    assert rec["new_file_count"] == base["runtime_file_count"]
    assert rec["reason"] == "first relock"
    assert rec["recorded_at"].endswith("Z")
    assert rec["doctor_result"] == "PASS"
    assert rec["entry_id"].startswith("relock-gzh-design-")
    # second apply on an UNCHANGED tree is a no-op (nothing appended)
    rc = RELOCK.main(_args(tmp_path, {"--skill": "gzh-design",
                                      "--reason": "second relock", "--apply": None}))
    assert rc == RELOCK.EXIT_OK
    history2 = json.loads((tmp_path / "skills.lock.history.json").read_text(encoding="utf-8"))
    assert len(history2) == 1
    # change the installed tree -> second apply appends and never rewrites #1
    (skills_home / "gzh-design" / "scripts" / "extra.py").write_text("x\n", encoding="utf-8")
    _monkey_doctor(monkeypatch, [0, 0])
    rc = RELOCK.main(_args(tmp_path, {"--skill": "gzh-design",
                                      "--reason": "second relock", "--apply": None}))
    assert rc == RELOCK.EXIT_OK
    history3 = json.loads((tmp_path / "skills.lock.history.json").read_text(encoding="utf-8"))
    assert len(history3) == 2
    assert history3[0] == rec
    assert history3[1]["new_file_count"] == rec["new_file_count"] + 1


# ── extra safety gates ──────────────────────────────────────────────────────
def test_apply_refused_when_doctor_fail_closed(tmp_path, monkeypatch):
    skills_home, lock_path, _ = _make_env(
        tmp_path, lock_values={"skill_root_sha256": "old" * 32,
                               "runtime_manifest_sha256": "old" * 32,
                               "runtime_file_count": 999})
    before = _snapshot(tmp_path)
    _monkey_doctor(monkeypatch, [1])  # pre-gate FAIL
    rc = RELOCK.main(_args(tmp_path, {"--skill": "gzh-design",
                                      "--reason": "gate test", "--apply": None}))
    assert rc == RELOCK.EXIT_PRE_DOCTOR_FAIL
    assert _snapshot(tmp_path) == before


def test_apply_no_change_is_noop(tmp_path, monkeypatch):
    skills_home, lock_path, base = _make_env(tmp_path)  # lock == installed
    before = _snapshot(tmp_path)
    rc = RELOCK.main(_args(tmp_path, {"--skill": "gzh-design",
                                      "--reason": "noop", "--apply": None}))
    assert rc == RELOCK.EXIT_OK
    assert _snapshot(tmp_path) == before
    assert not (tmp_path / "backups").exists()


def test_unknown_skill_refused(tmp_path):
    skills_home, lock_path, _ = _make_env(tmp_path)
    rc = RELOCK.main(_args(tmp_path, {"--skill": "nope", "--reason": "x"}))
    assert rc == RELOCK.EXIT_USAGE


def test_aihot_refused(tmp_path):
    skills_home, lock_path, base = _make_env(tmp_path)
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["skills"]["aihot"] = {"skill_name": "aihot", "kind": "agent_invoked_skill",
                               "skill_root_sha256": None}
    lock_path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    rc = RELOCK.main(_args(tmp_path, {"--skill": "aihot", "--reason": "x"}))
    assert rc == RELOCK.EXIT_USAGE


def test_all_dry_run_skips_aihot(tmp_path):
    skills_home, lock_path, base = _make_env(tmp_path)
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    lock["skills"]["aihot"] = {"skill_name": "aihot", "kind": "agent_invoked_skill",
                               "skill_root_sha256": None}
    lock_path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    before = _snapshot(tmp_path)
    rc = RELOCK.main(_args(tmp_path, {"--all": None, "--reason": "x"}))
    assert rc == RELOCK.EXIT_OK
    assert _snapshot(tmp_path) == before
