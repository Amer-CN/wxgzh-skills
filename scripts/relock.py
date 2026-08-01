#!/usr/bin/env python3
"""scripts/relock.py — one-click re-lock tool (P0-1, 档27).

Usage:
    python scripts/relock.py --skill <name> --reason "<reason>" [--apply]
    python scripts/relock.py --all --reason "<reason>" [--apply]

Without --apply this is a DRY-RUN: it computes the installed skill's
root/manifest hashes, diffs them against skills.lock.json and prints the
result WITHOUT writing anything (default and safe behavior).

Hash computation reuses the Pipeline's existing functions:
  wxgzh_pipeline.skill_discovery.compute_root_sha /
  compute_runtime_manifest_sha / _file_sha (the latter is reused transitively
  inside compute_root_sha). Those functions are NOT modified.

--apply (only when the environment is healthy):
  1. refuses if doctor --require-wechat is FAIL_CLOSED (no writes)
  2. backs up skills.lock.json to
     audit/upgrade-capability/lock-backups/skills.lock.<UTC>.json
  3. writes new hash values into skills.lock.json
  4. appends one record per changed skill to skills.lock.history.json
  5. re-runs doctor --require-wechat; on FAIL restores skills.lock.json and
     the ledger to their exact pre-run bytes and exits non-zero.

Safety:
  - --reason is required and must not be empty (dry-run included)
  - only reads the installed skill dirs; only writes skills.lock.json, the
    ledger and the backup file; never writes inside any locked skill tree
  - the ledger is append-only; rollback deletes only the records appended
    by THIS run
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wxgzh_pipeline import paths as P  # noqa: E402
from wxgzh_pipeline.skill_discovery import (  # noqa: E402
    compute_root_sha,
    compute_runtime_manifest_sha,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = REPO_ROOT / "skills.lock.json"
DEFAULT_HISTORY = REPO_ROOT / "skills.lock.history.json"
DEFAULT_BACKUP_DIR = REPO_ROOT / "audit" / "upgrade-capability" / "lock-backups"
DEFAULT_DOCTOR = REPO_ROOT / "scripts" / "doctor.py"
DEFAULT_REGRESSION = REPO_ROOT / "scripts" / "upgrade_regression.py"

# Exit codes
EXIT_OK = 0
EXIT_USAGE = 2          # bad args / validation (reason, unknown skill, missing dir)
EXIT_PRE_DOCTOR_FAIL = 3   # --apply refused: doctor FAIL_CLOSED before any write
EXIT_POST_DOCTOR_FAIL = 4  # --apply rolled back: doctor FAIL after write
EXIT_ROLLBACK_FAILED = 5   # rollback itself failed (state may be inconsistent)
EXIT_REGRESSION_FAIL = 6  # lock updated OK but the upgrade regression did NOT pass

_HASH_FIELDS = ("skill_root_sha256", "runtime_manifest_sha256", "runtime_file_count")


def _utc_compact() -> str:
    """UTC timestamp for backup filenames, e.g. 20260801T123456Z."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _utc_iso() -> str:
    """UTC ISO-8601 timestamp for ledger records, e.g. 2026-08-01T12:34:56Z."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _err(msg: str) -> None:
    print(f"relock: ERROR: {msg}", file=sys.stderr)


def _serialize_lock(lock: dict, template_bytes: bytes) -> str:
    """Serialize the lock with the SAME newline style/trailing newline as the
    existing file so a real re-lock produces a minimal diff."""
    crlf = b"\r\n" in template_bytes
    text = json.dumps(lock, ensure_ascii=False, indent=2)
    if not text.endswith("\n"):
        text += "\n"
    if crlf:
        text = text.replace("\n", "\r\n")
    return text


def load_history(path: Path) -> list:
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"history file must be a JSON array: {path}")
    return data


def run_doctor(project_root: Path | None, lock_path: Path | None = None,
              skills_home: Path | None = None) -> tuple[bool, str]:
    """Run the real doctor with --require-wechat. Returns (passed, output).

    lock_path is forwarded to doctor --lock-path so a sandbox re-lock is
    verified against the SAME lock copy that was just written (档29);
    skills_home is forwarded to doctor --skills-home so the sandbox tree is
    verified against the sandbox lock (档29)."""
    cmd = [sys.executable, str(DEFAULT_DOCTOR)]
    if project_root is not None:
        cmd += ["--project-root", str(project_root)]
    if skills_home is not None:
        cmd += ["--skills-home", str(skills_home)]
    if lock_path is not None:
        cmd += ["--lock-path", str(lock_path)]
    cmd.append("--require-wechat")
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"doctor invocation failed: {exc}"
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return proc.returncode == 0, output


def run_regression() -> tuple[bool, str]:
    """Run the offline upgrade regression (scripts/upgrade_regression.py).

    Returns (passed, output). The regression checks the REAL environment:
    full pytest minus the explicit env-dependent exclusion list, relock
    dry-run x4 (all 无变化) and doctor --require-wechat PASS."""
    try:
        proc = subprocess.run(
            [sys.executable, str(DEFAULT_REGRESSION)],
            capture_output=True, text=True, timeout=900)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"upgrade regression invocation failed: {exc}"
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return proc.returncode == 0, output


def classify_gate(doctor_passed: bool, doctor_output: str,
                  target_skills: set[str]) -> tuple[bool, list[str]]:
    """Pre-apply doctor gate with reason classification (档28 Part 1).

    doctor_passed=True                                   -> allowed
    Otherwise the ONLY allowed failure is the TARGET
    skill's hash_ok/version_ok mismatch (the state re-lock exists to fix):
      - environmental problems (missing skill dir, entrypoints_ok=false,
        missing required files, credentials missing, project not writable,
        AI HOT capability missing)                     -> REFUSE (exit 3)
      - any NON-target skill with hash/version mismatch -> REFUSE (exit 3)
    Returns (allowed, reasons). reasons non-empty on refusal."""
    if doctor_passed:
        return True, []
    reasons: list[str] = []
    try:
        report = json.loads(doctor_output)
    except (ValueError, TypeError):
        return False, ["doctor output not parseable as JSON"]
    if not isinstance(report, dict):
        return False, ["doctor output is not a JSON object"]
    if report.get("FAIL_CLOSED") is not True:
        return False, ["doctor report FAIL_CLOSED != true while exit code non-zero"]
    if report.get("project_writable") is not True:
        reasons.append("project_writable=false")
    if report.get("wechat_config_present") is not True:
        reasons.append("wechat_config_present=false (credentials missing)")
    if report.get("LIVE_PIPELINE_ALLOWED") is not True:
        reasons.append("LIVE_PIPELINE_ALLOWED=false (AI HOT capability missing)")
    skills = report.get("skills")
    if not isinstance(skills, dict) or not skills:
        reasons.append("doctor report has no usable skills section")
    target_mismatch_seen = False
    for name, entry in (skills or {}).items():
        if name == "aihot" or not isinstance(entry, dict):
            continue
        if entry.get("exists") is not True:
            reasons.append(f"{name}: skill directory missing")
            continue
        if entry.get("entrypoints_ok") is not True:
            reasons.append(f"{name}: entrypoints_ok=false")
            continue
        if entry.get("missing_files"):
            reasons.append(f"{name}: missing required files {entry['missing_files']}")
            continue
        if name in target_skills:
            # re-lockable state: hash_ok=false and/or version_ok=false (档28 1b)
            if entry.get("hash_ok") is False or entry.get("version_ok") is False:
                target_mismatch_seen = True
            else:
                reasons.append(f"{name}: target is fully healthy — failure must be elsewhere")
        else:
            if entry.get("hash_ok") is not True:
                reasons.append(f"{name}: non-target skill hash_ok=false "
                               f"(only the named target may be re-locked)")
            if entry.get("version_ok") is not True:
                reasons.append(f"{name}: non-target skill version_ok=false")
    if reasons:
        return False, reasons
    if not target_mismatch_seen:
        return False, ["doctor failed for an unclassified reason "
                       "(no target hash/version mismatch to re-lock)"]
    return True, []


def compute_skill_hashes(skill_dir: Path) -> tuple[str | None, str | None, int]:
    """Reuse the Pipeline's own hash functions (no reimplementation)."""
    root_sha, nfiles = compute_root_sha(skill_dir)
    man_sha, _rels = compute_runtime_manifest_sha(skill_dir)
    return root_sha, man_sha, int(nfiles)


def select_targets(args, lock_skills: dict) -> list[str]:
    """Validate the target set. aihot (agent-invoked) is never re-lockable."""
    if args.all:
        targets = [name for name, entry in lock_skills.items()
                   if entry.get("kind") != "agent_invoked_skill"]
        skipped = [name for name, entry in lock_skills.items()
                   if entry.get("kind") == "agent_invoked_skill"]
        for name in skipped:
            print(f"relock: note: skipping {name} (agent-invoked skill, no tree hashes)")
        return targets
    name = args.skill
    entry = lock_skills.get(name)
    if entry is None:
        raise ValueError(f"unknown skill in skills.lock.json: {name}")
    if entry.get("kind") == "agent_invoked_skill":
        raise ValueError(f"{name} is an agent-invoked skill; it has no tree hashes to re-lock")
    return [name]


def build_rows(targets: list[str], lock_skills: dict, skills_home: Path) -> list[dict]:
    rows = []
    for name in targets:
        entry = lock_skills[name]
        skill_dir = Path(skills_home) / name
        if not skill_dir.is_dir():
            raise ValueError(f"{name}: installed skill dir missing: {skill_dir}")
        root_sha, man_sha, nfiles = compute_skill_hashes(skill_dir)
        if not root_sha or not man_sha:
            raise ValueError(f"{name}: hash computation returned empty for {skill_dir}")
        old = {
            "skill_root_sha256": entry.get("skill_root_sha256"),
            "runtime_manifest_sha256": entry.get("runtime_manifest_sha256"),
            "runtime_file_count": entry.get("runtime_file_count"),
        }
        new = {
            "skill_root_sha256": root_sha,
            "runtime_manifest_sha256": man_sha,
            "runtime_file_count": nfiles,
        }
        changed = any(old[k] != new[k] for k in _HASH_FIELDS)
        rows.append({"skill": name, "skill_dir": str(skill_dir),
                     "old": old, "new": new, "changed": changed})
    return rows


def print_rows(rows: list[dict]) -> None:
    for row in rows:
        print(f"=== {row['skill']} ===")
        print(f"installed_dir: {row['skill_dir']}")
        for key in _HASH_FIELDS:
            label = key
            old, new = row["old"][key], row["new"][key]
            marker = "" if old == new else "  (CHANGED)"
            print(f"{label}: {old} -> {new}{marker}")
        print(f"status: {'CHANGED' if row['changed'] else '无变化'}")
        print()


def append_history(history_path: Path, rows: list[dict], reason: str) -> list[dict]:
    """Append one record per changed skill. Returns the appended records."""
    history = load_history(history_path)
    now = _utc_iso()
    appended = []
    for row in rows:
        rec = {
            "entry_id": f"relock-{row['skill']}-{_utc_compact()}-{uuid.uuid4().hex[:8]}",
            "skill": row["skill"],
            "old_root_sha256": row["old"]["skill_root_sha256"],
            "new_root_sha256": row["new"]["skill_root_sha256"],
            "old_manifest_sha256": row["old"]["runtime_manifest_sha256"],
            "new_manifest_sha256": row["new"]["runtime_manifest_sha256"],
            "old_file_count": row["old"]["runtime_file_count"],
            "new_file_count": row["new"]["runtime_file_count"],
            "reason": reason,
            "recorded_at": now,
            "doctor_result": "PASS",
        }
        history.append(rec)
        appended.append(rec)
    history_path.write_bytes(
        (json.dumps(history, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return appended


def parse_args(argv):
    ap = argparse.ArgumentParser(description="One-click re-lock tool (dry-run by default)")
    target = ap.add_mutually_exclusive_group(required=True)
    target.add_argument("--skill", help="lock skill name (e.g. gzh-design)")
    target.add_argument("--all", action="store_true", help="all lockable skills")
    ap.add_argument("--reason", required=True,
                    help="change reason (required, must not be empty)")
    ap.add_argument("--apply", action="store_true",
                    help="write lock + ledger + doctor gate (default: dry-run)")
    ap.add_argument("--skip-regression", action="store_true",
                    help="skip the automatic upgrade regression after --apply "
                         "(sandbox/debug scenarios)")
    # testability/override hooks (production defaults mirror doctor)
    ap.add_argument("--project-root", default=None)
    ap.add_argument("--skills-home", default=None)
    ap.add_argument("--lock-path", default=None)
    ap.add_argument("--history-path", default=None)
    ap.add_argument("--backup-dir", default=None)
    return ap.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    reason = (args.reason or "").strip()
    if not reason:
        _err("--reason is required and must not be empty (dry-run included)")
        return EXIT_USAGE

    project_root = P.resolve_project_root(args.project_root) if args.project_root else None
    resolved_root = project_root if project_root is not None else P.resolve_project_root(None)
    skills_home_override = Path(args.skills_home) if args.skills_home else None
    skills_home = skills_home_override or P.skills_home(resolved_root)
    lock_path = Path(args.lock_path) if args.lock_path else DEFAULT_LOCK
    history_path = Path(args.history_path) if args.history_path else DEFAULT_HISTORY
    backup_dir = Path(args.backup_dir) if args.backup_dir else DEFAULT_BACKUP_DIR

    if not lock_path.is_file():
        _err(f"skills.lock.json not found: {lock_path}")
        return EXIT_USAGE
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        lock_skills = lock.get("skills") or {}
        if not isinstance(lock_skills, dict) or not lock_skills:
            _err(f"skills.lock.json has no usable 'skills' object: {lock_path}")
            return EXIT_USAGE
        targets = select_targets(args, lock_skills)
        if not targets:
            _err("no lockable skills (all lock entries are agent-invoked)")
            return EXIT_USAGE
        rows = build_rows(targets, lock_skills, skills_home)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        _err(str(exc))
        return EXIT_USAGE

    print_rows(rows)
    changed_rows = [r for r in rows if r["changed"]]

    if not args.apply:
        n_changed = len(changed_rows)
        n_total = len(rows)
        if n_changed:
            print(f"dry-run: {n_total} skill(s) checked, {n_changed} CHANGED — "
                  f"run with --apply to write (none written)")
        else:
            print(f"dry-run: {n_total} skill(s) checked, 无变化 — nothing to write")
        return EXIT_OK

    if not changed_rows:
        print("apply: 无变化 — no backup, no write, no ledger record")
        return EXIT_OK

    # ── --apply ─────────────────────────────────────────────────────────────
    passed, output = run_doctor(project_root, lock_path=lock_path,
                                skills_home=skills_home_override)
    allowed, reasons = classify_gate(passed, output, {r["skill"] for r in changed_rows})
    if not allowed:
        _err("doctor gate refused --apply: " + "; ".join(reasons))
        if output:
            print(output)
        return EXIT_PRE_DOCTOR_FAIL
    if passed:
        print("doctor gate: PASS (pre-write)")
    else:
        print("doctor gate: allowed — target hash/version mismatch only (re-lockable state)")

    lock_bytes = lock_path.read_bytes()
    hist_existed = history_path.is_file()
    hist_bytes = history_path.read_bytes() if hist_existed else None

    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"skills.lock.{_utc_compact()}.json"
        backup_path.write_bytes(lock_bytes)
    except OSError as exc:
        _err(f"backup failed — nothing written: {exc}")
        return EXIT_USAGE

    try:
        for row in changed_rows:
            for key in _HASH_FIELDS:
                lock["skills"][row["skill"]][key] = row["new"][key]
        # write_bytes (NOT write_text): Path.write_text translates "\n" to
        # "\r\n" on Windows, which would corrupt the CRLF template into
        # "\r\r\n" and break byte fidelity (档28 Part 2 test caught this).
        lock_path.write_bytes(_serialize_lock(lock, lock_bytes).encode("utf-8"))
        appended = append_history(history_path, changed_rows, reason)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        _err(f"write failed — attempting rollback: {exc}")
        return _rollback(lock_path, lock_bytes, history_path,
                         hist_existed, hist_bytes, EXIT_ROLLBACK_FAILED)

    print(f"backup: {backup_path}")
    for rec in appended:
        print(f"ledger: {rec['entry_id']} ({rec['skill']})")

    ok, output = run_doctor(project_root, lock_path=lock_path,
                           skills_home=skills_home_override)
    if not ok:
        _err("doctor FAIL after re-lock — rolling back")
        if output:
            print(output)
        return _rollback(lock_path, lock_bytes, history_path,
                         hist_existed, hist_bytes, EXIT_POST_DOCTOR_FAIL)

    print("doctor: PASS (post-relock)")
    if not args.skip_regression:
        reg_ok, reg_output = run_regression()
        if not reg_ok:
            _err("lock 已更新但回归未通过,需人工裁决 (lock was NOT rolled back)")
            if reg_output:
                print(reg_output)
            return EXIT_REGRESSION_FAIL
        print("regression: PASS (upgrade_regression.py)")
    else:
        print("regression: skipped (--skip-regression)")
    print("relock: OK")
    return EXIT_OK


def _rollback(lock_path: Path, lock_bytes: bytes,
              history_path: Path, hist_existed: bool, hist_bytes: bytes | None,
              fail_code: int) -> int:
    """Restore skills.lock.json and the ledger to their exact pre-run bytes."""
    problems = []
    try:
        lock_path.write_bytes(lock_bytes)
    except OSError as exc:
        problems.append(f"lock restore failed: {exc}")
    try:
        if hist_existed:
            history_path.write_bytes(hist_bytes)
        elif history_path.is_file():
            history_path.unlink()  # file created by THIS run only
    except OSError as exc:
        problems.append(f"history restore failed: {exc}")
    if problems:
        for problem in problems:
            _err(problem)
        _err("rollback INCOMPLETE — state may be inconsistent; do NOT re-run blindly")
        return EXIT_ROLLBACK_FAILED
    print("rollback: skills.lock.json and ledger restored byte-identically")
    return fail_code


if __name__ == "__main__":
    sys.exit(main())
