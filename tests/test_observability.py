"""档42 OBS-68/69 — detection-only doctor observability tests.

Safety boundary (explicitly asserted): neither check may change doctor's
exit code. All mismatch scenarios are built inside pytest tmp_path sandboxes;
the real environment is never modified here.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from wxgzh_pipeline import observability as OBS

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCTOR = REPO_ROOT / "scripts" / "doctor.py"


def _sha(p: Path) -> str:
    return OBS._sha256_file(p)


def _make_pipeline_tree(root: Path, files: dict[str, str]) -> None:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


# ---------- OBS-69 lock consistency ----------

def test_lock_check_match(tmp_path):
    lock = tmp_path / "skills.lock.json"
    lock.write_bytes((REPO_ROOT / "skills.lock.json").read_bytes())
    report = OBS.check_lock_consistency(lock)
    assert report["status"] == "MATCH"
    assert report["installed_sha256"] == OBS.REPO_LOCK_SHA256


def test_lock_check_mismatch_reports_both_shas_and_field_diff(tmp_path):
    repo_lock = tmp_path / "repo" / "skills.lock.json"
    repo_lock.parent.mkdir(parents=True)
    shutil.copyfile(REPO_ROOT / "skills.lock.json", repo_lock)
    installed = tmp_path / "installed" / "skills.lock.json"
    installed.parent.mkdir(parents=True)
    data = json.loads(repo_lock.read_text(encoding="utf-8"))
    data["skills"]["media-enrichment"]["skill_root_sha256"] = "0" * 64
    installed.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    report = OBS.check_lock_consistency(installed, repo_lock)
    assert report["status"] == "MISMATCH"
    assert report["installed_sha256"] == _sha(installed)
    assert report["baseline_sha256"] == OBS.REPO_LOCK_SHA256
    assert report["installed_sha256"] != report["baseline_sha256"]
    assert any("media-enrichment.skill_root_sha256" in line for line in report["diff_summary"])


def test_lock_check_no_baseline(monkeypatch, tmp_path):
    lock = tmp_path / "skills.lock.json"
    lock.write_bytes((REPO_ROOT / "skills.lock.json").read_bytes())
    monkeypatch.setattr(OBS, "REPO_LOCK_SHA256", "not-a-sha")
    report = OBS.check_lock_consistency(lock)
    assert report["status"] == "NO_BASELINE"


def test_embedded_baseline_pins_repo_lock():
    """The embedded OBS-69 baseline must equal the repo-side lock sha; update
    them together in the same commit (the constant's own integrity guard)."""
    assert OBS.REPO_LOCK_SHA256 == _sha(REPO_ROOT / "skills.lock.json")


# ---------- OBS-68 pipeline consistency ----------

def test_pipeline_check_match(tmp_path):
    repo = tmp_path / "repo"
    inst = tmp_path / "installed"
    files = {"wxgzh_pipeline/__init__.py": "a\n", "scripts/doctor.py": "b\n",
             "skills.lock.json": "c\n", "config.example.env": "d\n"}
    _make_pipeline_tree(repo, files)
    _make_pipeline_tree(inst, files)
    report = OBS.check_pipeline_consistency(inst, repo)
    assert report["status"] == "MATCH"
    assert report["repo_file_count"] == report["installed_file_count"] == len(files)


def test_pipeline_check_mismatch_lists_diff_missing_extra(tmp_path):
    repo = tmp_path / "repo"
    inst = tmp_path / "installed"
    _make_pipeline_tree(repo, {"a.py": "same\n", "b.py": "orig\n", "c.py": "gone\n"})
    _make_pipeline_tree(inst, {"a.py": "same\n", "b.py": "CHANGED\n", "d.py": "new\n"})
    report = OBS.check_pipeline_consistency(inst, repo)
    assert report["status"] == "DIFF"
    assert report["diff_files"] == ["b.py"]
    assert report["missing_files"] == ["c.py"]
    assert report["extra_files"] == ["d.py"]
    assert report["diff_total"] == 1 and report["missing_total"] == 1 and report["extra_total"] == 1


def test_pipeline_check_skipped_no_repo(tmp_path):
    inst = tmp_path / "installed"
    inst.mkdir()
    report = OBS.check_pipeline_consistency(inst, None)
    assert report["status"] == "SKIPPED_NO_REPO"


# ---------- doctor exit-code safety boundary ----------

def _run_doctor_offline(project_root: Path, skills_home: Path, repo_root: Path | None):
    cmd = [sys.executable, str(DOCTOR), "--offline", "--project-root", str(project_root),
           "--skills-home", str(skills_home)]
    if repo_root is not None:
        cmd += ["--repo-root", str(repo_root)]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=300)


def test_doctor_exit_code_unchanged_with_mismatches(tmp_path):
    """【重要】构造 OBS-69 MISMATCH + OBS-68 DIFF 时,doctor 退出码必须仍为 0。"""
    project = tmp_path / "project"
    project.mkdir()
    skills = tmp_path / "skills"
    repo = tmp_path / "repo"
    _make_pipeline_tree(repo, {"wxgzh_pipeline/__init__.py": "repo\n", "a.py": "x\n"})
    _make_pipeline_tree(skills / "wxgzh-pipeline", {"wxgzh_pipeline/__init__.py": "installed\n",
                                                    "a.py": "y\n"})
    bad_lock = json.loads((REPO_ROOT / "skills.lock.json").read_text(encoding="utf-8"))
    bad_lock["skills"]["gzh-design"]["skill_root_sha256"] = "1" * 64
    (skills / "wxgzh-pipeline" / "skills.lock.json").write_text(
        json.dumps(bad_lock, ensure_ascii=False, indent=2), encoding="utf-8")
    proc = _run_doctor_offline(project, skills, repo)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    report = json.loads(proc.stdout)
    assert report["doctor"] == "PASS"
    assert report["observability"]["OBS_69_LOCK_MATCH"]["status"] == "MISMATCH"
    assert report["observability"]["OBS_68_PIPELINE_MATCH"]["status"] == "DIFF"


def test_doctor_observability_skipped_without_repo_root(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    skills = tmp_path / "skills"
    _make_pipeline_tree(skills / "wxgzh-pipeline", {"wxgzh_pipeline/__init__.py": "x\n",
                                                    "skills.lock.json": "y\n"})
    proc = _run_doctor_offline(project, skills, None)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    report = json.loads(proc.stdout)
    assert report["observability"]["OBS_68_PIPELINE_MATCH"]["status"] == "SKIPPED_NO_REPO"
