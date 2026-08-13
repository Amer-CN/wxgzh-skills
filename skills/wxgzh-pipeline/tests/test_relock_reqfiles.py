"""档33: relock --allow-required-files-removal (P2 prerequisite).

Covers: switch-off behavior unchanged (refusal), removal-only semantics,
protected entry/validator files never removable, uncovered entry files are
reported and refuse --apply, ledger removed_required_files field format, and
byte-identical rollback (required_files restored with the lock).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from conftest import SKILL_ROOT
from wxgzh_pipeline.skill_discovery import compute_root_sha, compute_runtime_manifest_sha


def _load_relock():
    path = SKILL_ROOT / "scripts" / "relock.py"
    spec = importlib.util.spec_from_file_location("relock_reqfiles", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


RELOCK = _load_relock()


class FakeProc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _tree(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def _make_env(tmp_path, *, missing_on_disk=(), uncovered_entrypoint=False):
    """gzh-design fixture. required_files = render.py (+ publish.py unless the
    caller marks it missing). entrypoint=render.py (protected)."""
    skills_home = tmp_path / "skills"
    files = {
        "SKILL.md": "---\nname: gzh-design\n---\n",
        "scripts/render.py": "print('render')\n",
        "scripts/publish.py": "print('publish')\n",
    }
    if uncovered_entrypoint:
        files["scripts/extra_entry.py"] = "print('entry')\n"
    _tree(skills_home / "gzh-design", files)
    for rel in missing_on_disk:
        p = skills_home / "gzh-design" / rel
        if p.is_file():
            p.unlink()

    required_files = ["scripts/render.py"]
    entrypoint = "scripts/render.py"
    if uncovered_entrypoint:
        entrypoint = "scripts/extra_entry.py"  # exists on tree, NOT in required_files
    for rel in missing_on_disk:
        if rel not in required_files:
            required_files.append(rel)

    root_sha, nfiles = compute_root_sha(skills_home / "gzh-design")
    man_sha, _ = compute_runtime_manifest_sha(skills_home / "gzh-design")
    lock = {"lock_version": 2, "skills": {"gzh-design": {
        "skill_name": "gzh-design",
        "skill_version": "v-test",
        "skill_root_sha256": "old" * 32,          # stale -> row CHANGED
        "runtime_manifest_sha256": "old" * 32,
        "runtime_file_count": 999,
        "entrypoint": entrypoint,
        "validator": None,
        "required_files": required_files,
    }}}
    lock_path = tmp_path / "skills.lock.json"
    lock_path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")
    return skills_home, lock_path, {"root_sha": root_sha, "man_sha": man_sha,
                                    "nfiles": nfiles}


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


def _doctor_report(rc, *, target="gzh-design", target_hash_bad=False,
                   target_version_bad=False, entrypoints_bad=False, missing=None,
                   non_target_bad=False, env_bad=False) -> dict:
    skills = {}
    for name in ("gzh-design", "super-writer"):
        if name != target:
            bad = non_target_bad
            skills[name] = {"exists": True, "version_ok": not bad, "hash_ok": not bad,
                            "entrypoints_ok": not bad, "missing_files": [], "ok": not bad}
        else:
            skills[name] = {"exists": True,
                            "version_ok": not target_version_bad,
                            "hash_ok": not target_hash_bad,
                            "entrypoints_ok": not entrypoints_bad,
                            "missing_files": list(missing or []) if entrypoints_bad else [],
                            "ok": not (target_hash_bad or target_version_bad or entrypoints_bad)}
    return {
        "FAIL_CLOSED": rc != 0,
        "project_writable": not env_bad,
        "wechat_config_present": not env_bad,
        "LIVE_PIPELINE_ALLOWED": True,
        "skills": skills,
        "doctor": "PASS" if rc == 0 else "FAIL",
    }


def _monkey_doctor(monkeypatch, results):
    """results: list of (rc, kwargs-for-_doctor_report); int allowed as plain rc."""
    calls = {"n": 0}

    def fake_run(cmd, **kwargs):
        item = results[min(calls["n"], len(results) - 1)]
        rc, kw = (item, {}) if isinstance(item, int) else item
        calls["n"] += 1
        return FakeProc(returncode=rc, stdout=json.dumps(_doctor_report(rc, **kw)))

    monkeypatch.setattr(RELOCK.subprocess, "run", fake_run)
    return calls


# ── 1. switch OFF (default): entrypoints_ok=false still refuses ─────────────
def test_switch_off_refuses_entrypoints_missing(tmp_path, monkeypatch):
    skills_home, lock_path, _ = _make_env(tmp_path, missing_on_disk=["scripts/publish.py"])
    before = _snapshot(tmp_path)
    _monkey_doctor(monkeypatch, [(1, {"target_hash_bad": True,
                                      "entrypoints_bad": True,
                                      "missing": ["scripts/publish.py"]})])
    rc = RELOCK.main(_args(tmp_path, {"--skill": "gzh-design", "--reason": "x",
                                      "--apply": None}))
    assert rc == RELOCK.EXIT_PRE_DOCTOR_FAIL == 3
    assert _snapshot(tmp_path) == before  # zero writes


# ── 2. switch ON: allowed; ONLY the missing entries are removed ─────────────
def test_switch_on_removes_only_missing_entries(tmp_path, monkeypatch):
    skills_home, lock_path, computed = _make_env(
        tmp_path, missing_on_disk=["scripts/publish.py"])
    _monkey_doctor(monkeypatch, [(1, {"target_hash_bad": True,
                                      "entrypoints_bad": True,
                                      "missing": ["scripts/publish.py"]}),
                                 0])  # pre allowed, post PASS
    rc = RELOCK.main(_args(tmp_path, {"--skill": "gzh-design", "--reason": "migrate",
                                      "--apply": None,
                                      "--allow-required-files-removal": None}))
    assert rc == RELOCK.EXIT_OK
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    gzh = lock["skills"]["gzh-design"]
    assert gzh["required_files"] == ["scripts/render.py"]      # only the missing one
    assert gzh["skill_root_sha256"] == computed["root_sha"]
    assert gzh["runtime_manifest_sha256"] == computed["man_sha"]
    assert gzh["runtime_file_count"] == computed["nfiles"]
    # no additions, no protected entry removed
    assert "scripts/publish.py" not in gzh["required_files"]
    assert "scripts/render.py" in gzh["required_files"]
    history = json.loads((tmp_path / "skills.lock.history.json").read_text(encoding="utf-8"))
    assert len(history) == 1
    assert history[0]["removed_required_files"] == ["scripts/publish.py"]
    # second dry-run with the switch: 无变化
    rc = RELOCK.main(_args(tmp_path, {"--skill": "gzh-design", "--reason": "x",
                                      "--allow-required-files-removal": None}))
    assert rc == RELOCK.EXIT_OK


# ── 3. switch ON but other cause (protected entry missing) -> refuse ────────
def test_switch_on_refuses_protected_entry_missing(tmp_path, monkeypatch):
    skills_home, lock_path, _ = _make_env(tmp_path, missing_on_disk=["scripts/render.py"])
    before = _snapshot(tmp_path)
    _monkey_doctor(monkeypatch, [(1, {"target_hash_bad": True,
                                      "entrypoints_bad": True,
                                      "missing": ["scripts/render.py"]})])
    rc = RELOCK.main(_args(tmp_path, {"--skill": "gzh-design", "--reason": "x",
                                      "--apply": None,
                                      "--allow-required-files-removal": None}))
    assert rc == RELOCK.EXIT_PRE_DOCTOR_FAIL
    assert _snapshot(tmp_path) == before
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    assert lock["skills"]["gzh-design"]["required_files"] == ["scripts/render.py"]


# ── 4. uncovered entry file: report only; --apply refused ───────────────────
def test_uncovered_entry_reports_and_refuses_apply(tmp_path, monkeypatch):
    skills_home, lock_path, _ = _make_env(tmp_path, uncovered_entrypoint=True)
    rc = RELOCK.main(_args(tmp_path, {"--skill": "gzh-design", "--reason": "x",
                                      "--allow-required-files-removal": None}))
    assert rc == RELOCK.EXIT_OK  # dry-run reports, writes nothing
    before = _snapshot(tmp_path)
    _monkey_doctor(monkeypatch, [(1, {"target_hash_bad": True}), 0])
    rc = RELOCK.main(_args(tmp_path, {"--skill": "gzh-design", "--reason": "x",
                                      "--apply": None,
                                      "--allow-required-files-removal": None}))
    assert rc == RELOCK.EXIT_USAGE == 2
    assert _snapshot(tmp_path) == before  # refused BEFORE any write
    assert not (tmp_path / "skills.lock.history.json").exists()


# ── 5. ledger field is [] when nothing is removed ───────────────────────────
def test_ledger_field_empty_when_no_removal(tmp_path, monkeypatch):
    skills_home, lock_path, _ = _make_env(tmp_path)
    (skills_home / "gzh-design" / "scripts" / "extra.py").write_text("x\n", encoding="utf-8")
    _monkey_doctor(monkeypatch, [0, 0])
    rc = RELOCK.main(_args(tmp_path, {"--skill": "gzh-design", "--reason": "hash only",
                                      "--apply": None,
                                      "--allow-required-files-removal": None}))
    assert rc == RELOCK.EXIT_OK
    history = json.loads((tmp_path / "skills.lock.history.json").read_text(encoding="utf-8"))
    assert len(history) == 1
    assert history[0]["removed_required_files"] == []
    # required_files untouched by a hash-only re-lock
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    assert lock["skills"]["gzh-design"]["required_files"] == ["scripts/render.py"]


# ── 6. post-write doctor FAIL -> lock (incl. required_files) restored ───────
def test_rollback_restores_required_files(tmp_path, monkeypatch):
    skills_home, lock_path, _ = _make_env(tmp_path, missing_on_disk=["scripts/publish.py"])
    lock_before = lock_path.read_bytes()
    _monkey_doctor(monkeypatch, [(1, {"target_hash_bad": True,
                                      "entrypoints_bad": True,
                                      "missing": ["scripts/publish.py"]}),
                                 (1, {"target_hash_bad": True})])  # post FAIL
    rc = RELOCK.main(_args(tmp_path, {"--skill": "gzh-design", "--reason": "rollback",
                                      "--apply": None,
                                      "--allow-required-files-removal": None}))
    assert rc == RELOCK.EXIT_POST_DOCTOR_FAIL == 4
    assert lock_path.read_bytes() == lock_before              # required_files restored
    assert not (tmp_path / "skills.lock.history.json").exists()
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    assert lock["skills"]["gzh-design"]["required_files"] == ["scripts/render.py",
                                                              "scripts/publish.py"]
