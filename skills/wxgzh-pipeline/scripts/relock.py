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

--allow-required-files-removal (档33, default OFF):
  - when OFF, behavior is byte-identical to 档28/29 (required_files untouched)
  - when ON, --apply may REMOVE from a target skill's required_files exactly
    the entries that are (a) missing on the installed tree AND (b) not the
    skill's own lock-declared entry files (entrypoint/validator/render_entry/
    component_source). Nothing is ever ADDED to required_files; a lock-declared
    entry file that exists on the tree but is NOT covered by required_files is
    reported and requires human decision (--apply refused, exit 2).
  - ledger records always carry removed_required_files ([] when none removed);
    the field is audit-only and does NOT participate in receipt chain tracing
    (receipts.py chains on old_root_sha256 -> new_root_sha256 only).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wxgzh_pipeline import paths as P  # noqa: E402
from wxgzh_pipeline import secrets as SEC  # noqa: E402
from wxgzh_pipeline.skill_discovery import (  # noqa: E402
    _file_sha,
    _read_version,
    compute_root_sha,
    compute_runtime_manifest_sha,
)
from wxgzh_pipeline.zipping import (  # noqa: E402
    PIPELINE_RELEASE_EXCLUDES,
    PIPELINE_RELEASE_INCLUDES,
    copy_tree,
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
# 档44: fields that change with a real skill upgrade and are derived from the
# source tree / remote witness. _FILE_HASH_FIELDS are recomputed from the
# lock-declared file paths on the source tree; _SOURCE_FIELDS come from the
# remote witness (full_commit_sha/source_tree_sha) and the source checkout
# (branch). skill_version is deliberately NOT auto-derived (it is a declared
# release string; bump it in the skill docs and re-lock the 3 hash fields only).
_FILE_HASH_FIELDS = ("entrypoint_sha256", "validator_sha256",
                     "render_entry_sha256", "component_source_sha256")
_SOURCE_FIELDS = ("full_commit_sha", "source_tree_sha", "branch", "skill_version")
_ALL_FIELDS = _HASH_FIELDS + _FILE_HASH_FIELDS + _SOURCE_FIELDS


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
                  target_skills: set[str],
                  allow_required_files_removal: bool = False,
                  removable_req: dict[str, list[str]] | None = None,
                  ) -> tuple[bool, list[str]]:
    """Pre-apply doctor gate with reason classification (档28 Part 1 + 档33).

    doctor_passed=True                                   -> allowed
    Otherwise the ONLY allowed failure is the TARGET
    skill's hash_ok/version_ok mismatch (the state re-lock exists to fix):
      - environmental problems (missing skill dir, entrypoints_ok=false,
        missing required files, credentials missing, project not writable,
        AI HOT capability missing)                     -> REFUSE (exit 3)
      - any NON-target skill with hash/version mismatch -> REFUSE (exit 3)
    档33: with allow_required_files_removal=True, the TARGET's
    entrypoints_ok=false is allowed ONLY when every missing required file is
    one of the to-be-removed entries (removable_req[skill]); any other cause
    (missing file not scheduled for removal, missing protected entry/validator
    file, or any problem in a non-target skill) still refuses.
    Returns (allowed, reasons). reasons non-empty on refusal."""
    removable = {k: set(v) for k, v in (removable_req or {}).items()}
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
        removal_allowed_skill = False
        if entry.get("entrypoints_ok") is not True:
            missing = set(entry.get("missing_files") or [])
            if (allow_required_files_removal and name in target_skills
                    and missing and missing <= removable.get(name, set())):
                removal_allowed_skill = True
            else:
                reasons.append(f"{name}: entrypoints_ok=false")
                continue
        if entry.get("missing_files") and not removal_allowed_skill:
            reasons.append(f"{name}: missing required files {entry['missing_files']}")
            continue
        if name in target_skills:
            # re-lockable state: hash_ok=false and/or version_ok=false (档28 1b)
            if entry.get("hash_ok") is False or entry.get("version_ok") is False:
                target_mismatch_seen = True
            elif not removal_allowed_skill:
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


def _git_run(args, timeout=180):
    """Run git; returns subprocess.CompletedProcess. Raises on OSError/Timeout."""
    return subprocess.run(["git", *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def verify_remote_witness(repo_url: str, source_commit: str, source_tree: Path,
                          expected_tree_sha: str | None = None) -> tuple[bool, str, dict]:
    """OBS-74 remote-witness constraint (档44 Part 2 — the core safety design).

    来由 (OBS-74): 四轮本地热修(obs42/43、obs44-46、obs47、obs53)曾长期只存在
    于本地安装树、从未回流,skills.lock.json 的 root_sha256 长期指向无远端副本
    的本地树;lock 的 full_commit_sha 因此与真实代码不一致。为了杜绝再次出现
    「lock 指向无远端副本的树」,写 lock 之前必须完成三项远端见证:

      a. 该 commit 在远端仓库真实存在(不是只在本地)     — git ls-remote
      b. 远端该 commit 的树与 --source-tree 指向的本地树逐字一致
                                                          — git tree sha 相等
      c. 待写入 lock 的 source_tree_sha 等于远端实算值     — 显式断言

    没有任何跳过远端验证的开关/环境变量/参数:网络不可用一律拒绝执行,不允许
    降级为本地校验。错误信息明确指出哪一项未通过,并提示先 push 到远端。
    """
    def _fail(check, detail):
        return (False,
                f"远端见证 {check} 未通过: {detail}。升级前请先将改动 push 到远端。",
                {})

    # (a) remote existence — full ref listing (ls-remote treats a bare sha as a
    # ref-name pattern and returns nothing; the commit must be reachable from a
    # ref, i.e. actually pushed, not just present locally)
    try:
        ls = _git_run(["ls-remote", repo_url])
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"远端见证 (a) 失败: 网络不可用或无法访问远端 {repo_url}: {exc}", {}
    if ls.returncode != 0 or source_commit not in ls.stdout.split():
        return _fail("(a)", f"commit {source_commit} 在远端不存在 (ls-remote rc={ls.returncode})")

    # (b) remote tree == local tree
    try:
        with tempfile.TemporaryDirectory(prefix="relock-witness-") as td:
            td = Path(td)
            setup_steps = (["-C", str(td), "init", "-q"],
                           ["-C", str(td), "remote", "add", "origin", repo_url])
            for step in setup_steps:
                if _git_run(step).returncode != 0:
                    return _fail("(b)", f"temp repo setup failed: {step}")
            # mirror the SOURCE repo's core.autocrlf so CRLF/LF conversion on
            # `git add` matches the original commit's blobs (same for
            # .gitattributes below); otherwise a CRLF working tree would hash
            # differently and (b) would false-negative.
            autocrlf = ""
            src_cfg = _git_run(["-C", str(source_tree), "config", "core.autocrlf"])
            if src_cfg.returncode == 0:
                autocrlf = src_cfg.stdout.strip()
            if autocrlf:
                if _git_run(["-C", str(td), "config", "core.autocrlf", autocrlf]).returncode != 0:
                    return _fail("(b)", f"temp repo autocrlf mirror failed: {autocrlf}")
            fetch = _git_run(["-C", str(td), "fetch", "--depth", "1", "origin", source_commit])
            if fetch.returncode != 0:
                return _fail("(b)", f"远端无法取回该 commit 的树: {fetch.stderr.strip()[:200]}")
            rev = _git_run(["-C", str(td), "rev-parse", "FETCH_HEAD^{tree}"])  # temp repo itself
            if rev.returncode != 0:
                return _fail("(b)", f"无法解析远端树 sha: {rev.stderr.strip()[:200]}")
            remote_tree = rev.stdout.strip()
            # mirror the source repo's line-ending rules (if any) so CRLF/LF
            # normalization matches the ORIGINAL commit (OBS-74 witness must
            # compare like-for-like, not raw-platform bytes)
            src_attrs = Path(source_tree) / ".gitattributes"
            if src_attrs.is_file():
                shutil.copyfile(src_attrs, td / ".gitattributes")
            # Local tree = remote file set, content-compared via git tree sha.
            # add -A honors the source .gitignore (junk like __pycache__ stays
            # out); tracked-but-ignored commit files (e.g. *.png under a repo-
            # wide ignore rule) are force-added BY NAME from the remote file
            # list only, so the local tree can never silently miss them nor
            # pick up stray local files.
            remote_files = _git_run(
                ["-C", str(td), "ls-tree", "-r", "-z", "--name-only", remote_tree])
            if remote_files.returncode != 0:
                return _fail("(b)", "无法列出远端树文件")
            remote_set = {s for s in remote_files.stdout.split("\0") if s}
            add = _git_run(["--git-dir", str(td / ".git"),
                            "--work-tree", str(source_tree), "add", "-A"])
            if add.returncode != 0:
                return _fail("(b)", f"无法计算本地树: {add.stderr.strip()[:200]}")
            force_add = []
            for rel in sorted(remote_set):
                if not (Path(source_tree) / rel).is_file():
                    return _fail("(b)", f"本地 --source-tree 缺少远端树中的文件: {rel}")
                chk = _git_run(["-C", str(source_tree), "--git-dir", str(td / ".git"),
                                "ls-files", "--error-unmatch", "--", rel])
                if chk.returncode != 0:
                    force_add.append(rel)
            if force_add:
                fa = _git_run(["-C", str(source_tree), "--git-dir", str(td / ".git"),
                               "add", "-f", "--", *force_add])
                if fa.returncode != 0:
                    return _fail("(b)", f"force-add 失败: {fa.stderr.strip()[:200]}")
            local_set = {s for s in _git_run(
                ["-C", str(td), "ls-files", "-z"]).stdout.split("\0") if s}
            extra_local = sorted(local_set - remote_set)
            if extra_local:
                return _fail("(b)", f"本地树含远端没有的文件: {extra_local[:5]}")
            wt = _git_run(["--git-dir", str(td / ".git"), "write-tree"])
            if wt.returncode != 0:
                return _fail("(b)", f"本地 write-tree 失败: {wt.stderr.strip()[:200]}")
            local_tree = wt.stdout.strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"远端见证 (b) 失败: 网络/IO 错误: {exc}", {}
    if len(remote_tree) != 40 or len(local_tree) != 40:
        return _fail("(b)", f"树 sha 非法: remote={remote_tree!r} local={local_tree!r}")
    if local_tree != remote_tree:
        return _fail("(b)", f"远端树 {remote_tree} 与本地树 {local_tree} 不一致")

    # (c) the value to be written equals the remote-computed tree sha
    if expected_tree_sha is not None and expected_tree_sha != remote_tree:
        return _fail("(c)", f"待写入 source_tree_sha {expected_tree_sha} != 远端实算值 {remote_tree}")

    return True, ("远端见证 PASS (a/b/c)", ""), {"remote_tree_sha": remote_tree,
                                                  "remote_repo": repo_url}


def _source_branch_of(source_tree: Path) -> str | None:
    """Derive the branch name from a git checkout; None for non-git sources."""
    if not (Path(source_tree) / ".git").exists():
        return None
    try:
        proc = _git_run(["-C", str(source_tree), "symbolic-ref", "--short", "HEAD"])
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


# 档45R2 OBS-78: entrypoint smoke. After post-doctor, BEFORE declaring success,
# the locked skill's entrypoint must be run once via its PRODUCTION CLI path on
# the installed tree with the skill's own sample input. Non-zero exit or a
# python traceback in stderr => FAIL => full chain rollback (exit 4). No skip
# switch / parameter / env var exists for the smoke step. Skills without a
# configured smoke sample are SKIPPED EXPLICITLY with a printed notice.
SMOKE_ENTRIES = {
    "gzh-design": {
        "entry": "scripts/render_article.py",
        "args": ["--article", "{skill_dir}/assets/sample-article.md",
                 "--output-dir", "{smoke_dir}", "--theme", "smartisan"],
    },
    # 档56 OBS-80:样本优先引用 skill 侧现成样本({skill_dir});必须新造的样本
    # (super-writer ledger / media request+article+fixtures)放 Pipeline 侧
    # scripts/smoke-samples/ ({sample_dir}),不改被锁 skill 树。
    "super-writer": {
        "entry": "scripts/material_ingestion.py",
        "args": ["--ledger", "{sample_dir}/super-writer/material-ledger.smoke.yaml",
                 "--output", "{smoke_dir}/material-ingestion-report.json", "--json"],
    },
    "zh-human-writing": {
        "entry": "scripts/fidelity_guard.py",
        "args": ["--original", "{skill_dir}/examples/01-author-preserve/input.txt",
                 "--edited", "{skill_dir}/examples/01-author-preserve/input.txt",
                 "--output", "json"],
    },
    "media-enrichment": {
        "entry": "scripts/run_media_enrichment.py",
        "args": ["--request", "{sample_dir}/media-enrichment/media_enrichment_request.smoke.json",
                 "--output-dir", "{smoke_dir}",
                 "--fixture-dir", "{sample_dir}/media-enrichment/fixtures",
                 "--phase", "discover"],
    },
}
_SMOKE_TRACEBACK_MARKERS = ("Traceback", "NameError", "AttributeError", "KeyError")


def _run_entry_smoke(skills_home: Path, name: str, entry_cfg: dict,
                     sample_dir: Path | None = None) -> tuple[bool, str]:
    """Production-CLI smoke of a locked entrypoint (installed tree)."""
    skill_dir = Path(skills_home) / name
    entry = skill_dir / entry_cfg["entry"]
    if not entry.is_file():
        return False, f"{name}: entrypoint missing for smoke: {entry}"
    with tempfile.TemporaryDirectory(prefix="relock-smoke-") as td:
        args = [str(a).format(skill_dir=skill_dir, smoke_dir=td,
                             sample_dir=sample_dir)
                for a in entry_cfg["args"]]
        cmd = [sys.executable, "-X", "utf8", str(entry), *args]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True,
                                  encoding="utf-8", errors="replace", timeout=300)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return False, f"{name}: entrypoint smoke invocation failed: {exc}"
        stderr = proc.stderr or ""
        trace = any(m in stderr for m in _SMOKE_TRACEBACK_MARKERS)
        if proc.returncode != 0 or trace:
            return False, (f"{name}: entrypoint smoke FAILED rc={proc.returncode} "
                           f"traceback={trace}\n{stderr[-1500:]}")
    return True, f"{name}: entrypoint smoke PASS (CLI subprocess, production path)"


def _build_install_bundle(lock_path: Path, target_name: str, source_tree: Path,
                          skills_home: Path, project_root: Path) -> Path:
    """Build a minimal official bundle (installer-readable) reflecting the NEW
    lock: wxgzh-pipeline release tree + locked-skills (target = --source-tree,
    others = current installed trees) + source-proofs from the new lock values.

    Returns the bundle dir (caller owns cleanup)."""
    new_lock = json.loads(lock_path.read_text(encoding="utf-8"))
    expected = {n for n, m in new_lock["skills"].items()
                if m.get("kind") != "agent_invoked_skill"}
    if target_name not in expected:
        raise ValueError(f"target {target_name} not in lock")
    td = Path(tempfile.mkdtemp(prefix="relock-install-"))
    bundle = td / "portable-bundle"
    copy_tree(Path(__file__).resolve().parents[1], bundle / "wxgzh-pipeline",
              include_paths=PIPELINE_RELEASE_INCLUDES,
              exclude_paths=PIPELINE_RELEASE_EXCLUDES)
    # the installer reads the lock from its own pipeline tree: must be the NEW lock
    (bundle / "wxgzh-pipeline" / "skills.lock.json").write_bytes(lock_path.read_bytes())
    (bundle / "installer").mkdir()
    shutil.copyfile(Path(__file__).resolve().parents[1] / "scripts" / "install.py",
                    bundle / "installer" / "install.py")
    for name in sorted(expected):
        src = Path(source_tree) if name == target_name else Path(skills_home) / name
        copy_tree(src, bundle / "locked-skills" / name)
    shutil.copyfile(Path(__file__).resolve().parents[1] / "config.example.env",
                    bundle / "config.example.env")
    proofs = {}
    for name, meta in new_lock["skills"].items():
        if meta.get("kind") == "agent_invoked_skill":
            continue
        proofs[name] = {"repository_url": meta.get("repository_url"),
                        "full_commit_sha": meta.get("full_commit_sha"),
                        "source_tree_sha": meta.get("source_tree_sha")}
    (bundle / "source-proofs.json").write_text(json.dumps(
        {"generated_by": "relock.py 档44 (source-tree install)", "skills": proofs},
        ensure_ascii=False, indent=2), encoding="utf-8")
    scan = SEC.scan_tree(bundle, SEC.load_env_values(project_root / ".env"))
    if scan["secrets_detected"]:
        shutil.rmtree(td, ignore_errors=True)
        raise ValueError(f"secrets detected in install bundle: {scan['hits']}")
    files = []
    for fp in sorted(bundle.rglob("*")):
        if fp.is_file() and fp.name != "MANIFEST.json":
            b = fp.read_bytes()
            files.append({"path": fp.relative_to(bundle).as_posix(),
                          "size": len(b), "sha256": hashlib.sha256(b).hexdigest()})
    (bundle / "MANIFEST.json").write_text(json.dumps(
        {"artifact": "relock-档44 source-tree install", "file_count": len(files),
         "files": files}, ensure_ascii=False, indent=2), encoding="utf-8")
    return td


def _run_official_installer(bundle_td: Path, target_skills_home: Path) -> tuple[bool, str]:
    """Run the official transactional installer against the bundle."""
    cmd = [sys.executable,
           str(bundle_td / "portable-bundle" / "installer" / "install.py"),
           "--target", str(target_skills_home)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=900)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"installer invocation failed: {exc}"
    out = ((proc.stdout or "") + (proc.stderr or "")).strip()
    ok = proc.returncode == 0 and '"ok": true' in (proc.stdout or "")
    return ok, out


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


def build_rows(targets: list[str], lock_skills: dict, skills_home: Path,
               allow_required_files_removal: bool = False,
               source_tree: Path | None = None, source_commit: str | None = None,
               remote_tree_sha: str | None = None) -> list[dict]:
    rows = []
    for name in targets:
        entry = lock_skills[name]
        if source_tree is not None:
            # 档44 source-tree mode: all fields derived from the upgrade tree
            skill_dir = Path(source_tree)
            if not skill_dir.is_dir():
                raise ValueError(f"{name}: --source-tree dir missing: {skill_dir}")
            root_sha, man_sha, nfiles = compute_skill_hashes(skill_dir)
            if not root_sha or not man_sha:
                raise ValueError(f"{name}: hash computation returned empty for {skill_dir}")
            old = {f: entry.get(f) for f in _ALL_FIELDS}
            new = {
                "skill_root_sha256": root_sha,
                "runtime_manifest_sha256": man_sha,
                "runtime_file_count": nfiles,
                "full_commit_sha": source_commit,
                "source_tree_sha": remote_tree_sha,
                "branch": _source_branch_of(skill_dir) or entry.get("branch"),
                # 档45R: skill_version MUST come from the exact same source doctor
                # uses (skill_discovery._read_version L273-278 — for gzh-design that
                # is RELEASE_NOTES.md line 1). Any divergence would write A in the
                # lock while doctor reads B -> version_ok=false -> FAIL_CLOSED.
                "skill_version": _read_version(skill_dir, name) or entry.get("skill_version"),
            }
            for f in _FILE_HASH_FIELDS:
                rel = entry.get(f[:-7])  # e.g. entrypoint_sha256 -> entrypoint
                if not isinstance(rel, str) or not rel:
                    new[f] = entry.get(f)
                    continue
                fp = skill_dir / rel
                if not fp.is_file():
                    raise ValueError(
                        f"{name}: {f} source file missing on --source-tree: {rel}")
                new[f] = _file_sha(fp)
            changed = any(old.get(k) != new[k] for k in _ALL_FIELDS)
            row = {"skill": name, "skill_dir": str(skill_dir),
                   "old": old, "new": new, "changed": changed,
                   "remove_required_files": [], "uncovered_entries": []}
            if allow_required_files_removal:
                locked_req = entry.get("required_files")
                if isinstance(locked_req, list):
                    protected = {f for f in (entry.get("entrypoint"),
                                             entry.get("validator"),
                                             entry.get("render_entry"),
                                             entry.get("component_source"))
                                 if isinstance(f, str) and f}
                    missing = [rf for rf in locked_req
                               if not (skill_dir / rf).is_file()]
                    row["remove_required_files"] = [rf for rf in missing
                                                    if rf not in protected]
                    row["uncovered_entries"] = sorted(
                        f for f in protected
                        if (skill_dir / f).is_file() and f not in locked_req)
            rows.append(row)
            continue
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
        row = {"skill": name, "skill_dir": str(skill_dir),
               "old": old, "new": new, "changed": changed,
               "remove_required_files": [], "uncovered_entries": []}
        if allow_required_files_removal:
            locked_req = entry.get("required_files")
            if isinstance(locked_req, list):
                # Lock-declared operational entry files are never removable:
                # dropping them from required_files while absent would mask a
                # broken install (档33 guard).
                protected = {f for f in (entry.get("entrypoint"),
                                         entry.get("validator"),
                                         entry.get("render_entry"),
                                         entry.get("component_source"))
                             if isinstance(f, str) and f}
                missing = [rf for rf in locked_req
                           if not (skill_dir / rf).is_file()]
                row["remove_required_files"] = [rf for rf in missing
                                                if rf not in protected]
                row["uncovered_entries"] = sorted(
                    f for f in protected
                    if (skill_dir / f).is_file() and f not in locked_req)
        rows.append(row)
    return rows


def print_rows(rows: list[dict]) -> None:
    for row in rows:
        print(f"=== {row['skill']} ===")
        print(f"installed_dir: {row['skill_dir']}")
        for key in row["old"]:  # 档44: every managed field, none missed
            old, new = row["old"][key], row["new"][key]
            marker = "" if old == new else "  (CHANGED)"
            print(f"{key}: {old} -> {new}{marker}")
        if row.get("remove_required_files"):
            print(f"required_files removals: {row['remove_required_files']}")
        if row.get("uncovered_entries"):
            print(f"NOTE: required_files 未覆盖的新入口文件: "
                  f"{row['uncovered_entries']} — 需人工裁决 (不会自动新增)")
        print(f"status: {'CHANGED' if row['changed'] else '无变化'}")
        # 档45R WARN (output-only, never changes verdict/exit code):
        # version label vs actual content drift detection.
        if "skill_version" in row["old"]:
            root_changed = row["old"].get("skill_root_sha256") != row["new"].get("skill_root_sha256")
            ver_changed = row["old"].get("skill_version") != row["new"].get("skill_version")
            if root_changed and not ver_changed:
                print("WARN: root 变化但 skill_version 未变 — 代码已变但版本号未提升,"
                      "lock 的版本标签将与实际内容脱节 (建议提升版本后重跑)")
            elif ver_changed and not root_changed:
                print("WARN: skill_version 变化但 root 未变 — 版本标签已变但内容未变,"
                      "请核对是否仅为文档/版本声明变更")
        print()


_LEGACY_LEDGER_NAMES = {
    "skill_root_sha256": "root_sha256",
    "runtime_manifest_sha256": "manifest_sha256",
    "runtime_file_count": "file_count",
}


def append_history(history_path: Path, rows: list[dict], reason: str,
                   source_witness: dict | None = None) -> list[dict]:
    """Append one record per changed skill. Returns the appended records.

    档44: every CHANGED field is recorded old -> new (legacy short names for
    the three hash fields keep receipts.py chain tracing untouched). Records
    also carry source_commit_verified + remote_repo when a remote witness ran.
    """
    history = load_history(history_path)
    now = _utc_iso()
    appended = []
    for row in rows:
        rec = {
            "entry_id": f"relock-{row['skill']}-{_utc_compact()}-{uuid.uuid4().hex[:8]}",
            "skill": row["skill"],
            "reason": reason,
            "removed_required_files": list(row.get("remove_required_files") or []),
            "recorded_at": now,
            "doctor_result": "PASS",
        }
        for key in row["old"]:
            if row["old"][key] == row["new"][key]:
                continue
            stem = _LEGACY_LEDGER_NAMES.get(key, key)
            rec[f"old_{stem}"] = row["old"][key]
            rec[f"new_{stem}"] = row["new"][key]
        if source_witness:
            rec["source_commit_verified"] = True
            rec["remote_repo"] = source_witness.get("remote_repo")
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
    ap.add_argument("--allow-required-files-removal", action="store_true",
                    help="档33: allow REMOVING required_files entries that are "
                         "missing on the installed tree (removal ONLY — never "
                         "adds; lock-declared entry/validator files are protected)")
    # testability/override hooks (production defaults mirror doctor)
    ap.add_argument("--project-root", default=None)
    ap.add_argument("--skills-home", default=None)
    ap.add_argument("--lock-path", default=None)
    ap.add_argument("--history-path", default=None)
    ap.add_argument("--backup-dir", default=None)
    # OBS-79 (档45R2): preinstall TREE backups must live OUTSIDE the git repo
    # (same level as F:\AIXM\wxgzh-presnapshot-45\). Default =
    # <project-root parent>/wxgzh-relock-tree-backups. Tests inject tmp dirs.
    ap.add_argument("--tree-backup-dir", default=None)
    # 档44: full-field upgrade mode (single --skill target). The remote-witness
    # constraint (OBS-74) is mandatory when these are given — NO skip switch,
    # NO env override, NO local-only fallback exists by design.
    ap.add_argument("--source-tree", default=None,
                    help="upgrade source tree (new skill version); requires --source-commit")
    ap.add_argument("--source-commit", default=None,
                    help="40-hex commit sha that EXISTS on the remote repo and whose "
                         "tree is byte-identical to --source-tree (remote witness)")
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

    source_tree = Path(args.source_tree) if args.source_tree else None
    source_commit = (args.source_commit or "").strip().lower() if args.source_commit else None
    if (source_tree is None) != (source_commit is None):
        _err("--source-tree 与 --source-commit 必须同时提供")
        return EXIT_USAGE
    if source_commit is not None and not (
            len(source_commit) == 40 and all(c in "0123456789abcdef" for c in source_commit)):
        _err("--source-commit must be a 40-hex sha")
        return EXIT_USAGE
    if source_tree is not None and not source_tree.is_dir():
        _err(f"--source-tree is not a directory: {source_tree}")
        return EXIT_USAGE
    if source_tree is not None and args.all:
        _err("--source-tree/--source-commit 要求单个 --skill 目标(不支持 --all)")
        return EXIT_USAGE

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
        # 档44 OBS-74 remote witness — BEFORE any computation/write; failure = zero writes
        source_witness = None
        if source_tree is not None:
            repo_url = (lock_skills.get(args.skill) or {}).get("repository_url")
            if not repo_url:
                _err(f"{args.skill}: lock entry has no repository_url — remote witness impossible")
                return EXIT_USAGE
            ok_w, msg_w, info_w = verify_remote_witness(repo_url, source_commit, source_tree)
            print(msg_w)
            if not ok_w:
                _err(msg_w)
                return EXIT_USAGE
            source_witness = info_w
        rows = build_rows(targets, lock_skills, skills_home,
                          args.allow_required_files_removal,
                          source_tree=source_tree, source_commit=source_commit,
                          remote_tree_sha=(source_witness or {}).get("remote_tree_sha"))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        _err(str(exc))
        return EXIT_USAGE

    print_rows(rows)
    changed_rows = [r for r in rows if r["changed"]]
    uncovered = [r for r in rows if r.get("uncovered_entries")]
    for r in uncovered:
        print(f"NOTE: {r['skill']}: required_files 未覆盖的新入口文件 "
              f"{r['uncovered_entries']} — 需人工裁决 (relock 不会自动新增)")

    if not args.apply:
        n_changed = len(changed_rows)
        n_total = len(rows)
        if n_changed:
            print(f"dry-run: {n_total} skill(s) checked, {n_changed} CHANGED — "
                  f"run with --apply to write (none written)")
        else:
            print(f"dry-run: {n_total} skill(s) checked, 无变化 — nothing to write")
        return EXIT_OK

    if uncovered:
        _err("apply refused: required_files 未覆盖的新入口文件需人工裁决; nothing written")
        return EXIT_USAGE

    if not changed_rows:
        print("apply: 无变化 — no backup, no write, no ledger record")
        return EXIT_OK

    # ── --apply ─────────────────────────────────────────────────────────────
    passed, output = run_doctor(project_root, lock_path=lock_path,
                                skills_home=skills_home_override)
    allowed, reasons = classify_gate(
        passed, output, {r["skill"] for r in changed_rows},
        allow_required_files_removal=args.allow_required_files_removal,
        removable_req={r["skill"]: r["remove_required_files"] for r in rows})
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
            # 档44: write EVERY computed field (3 hash fields in the classic
            # path; + full_commit_sha/source_tree_sha/branch/entry/validator/
            # render-entry/component-source hashes in --source-tree mode).
            for key in row["new"]:
                lock["skills"][row["skill"]][key] = row["new"][key]
            if args.allow_required_files_removal and row["remove_required_files"]:
                req = lock["skills"][row["skill"]].get("required_files")
                if isinstance(req, list):
                    for rf in row["remove_required_files"]:
                        while rf in req:
                            req.remove(rf)
        # write_bytes (NOT write_text): Path.write_text translates "\n" to
        # "\r\n" on Windows, which would corrupt the CRLF template into
        # "\r\r\n" and break byte fidelity (档28 Part 2 test caught this).
        lock_path.write_bytes(_serialize_lock(lock, lock_bytes).encode("utf-8"))
        appended = append_history(history_path, changed_rows, reason, source_witness)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        _err(f"write failed — attempting rollback: {exc}")
        return _rollback(lock_path, lock_bytes, history_path,
                         hist_existed, hist_bytes, EXIT_ROLLBACK_FAILED)

    print(f"backup: {backup_path}")
    for row in changed_rows:
        if row["remove_required_files"]:
            print(f"required_files: {row['skill']}: removed {row['remove_required_files']}")
    for rec in appended:
        print(f"ledger: {rec['entry_id']} ({rec['skill']})")

    # 档44: 先 relock 后安装 (source-tree mode only). Between the lock write and
    # the install nothing else may run: the installer is invoked immediately, so
    # the intermediate "lock 已更新但代码未装" state is never visible.
    tree_backup = None
    receipts_bytes = None
    if source_tree is not None:
        target_name = targets[0]
        target_dir = Path(skills_home) / target_name
        tree_backup_dir = (Path(args.tree_backup_dir) if args.tree_backup_dir
                           else resolved_root.parent / "wxgzh-relock-tree-backups")
        tree_backup_dir.mkdir(parents=True, exist_ok=True)
        tree_backup = tree_backup_dir / f"skills-tree.{target_name}.preinstall"
        if tree_backup.exists():
            shutil.rmtree(tree_backup)
        shutil.copytree(target_dir, tree_backup)
        rf = Path(skills_home) / ".install-receipts" / f"{target_name}.json"
        receipts_bytes = rf.read_bytes() if rf.is_file() else None
        bundle_td = _build_install_bundle(lock_path, target_name, source_tree,
                                          Path(skills_home), project_root or resolved_root)
        try:
            ok_inst, inst_out = _run_official_installer(bundle_td, Path(skills_home))
        finally:
            shutil.rmtree(bundle_td, ignore_errors=True)
        if not ok_inst:
            _err("official installer FAILED after lock write — rolling back lock + ledger + tree")
            if inst_out:
                print(inst_out)
            return _rollback(lock_path, lock_bytes, history_path,
                             hist_existed, hist_bytes, EXIT_POST_DOCTOR_FAIL,
                             tree_backup=tree_backup, receipts_bytes=receipts_bytes,
                             skills_home=Path(skills_home))
        print("installer: PASS (source-tree install)")

    ok, output = run_doctor(project_root, lock_path=lock_path,
                           skills_home=skills_home_override)
    if not ok:
        _err("doctor FAIL after re-lock — rolling back")
        if output:
            print(output)
        return _rollback(lock_path, lock_bytes, history_path,
                         hist_existed, hist_bytes, EXIT_POST_DOCTOR_FAIL,
                         tree_backup=tree_backup, receipts_bytes=receipts_bytes,
                         skills_home=Path(skills_home))

    print("doctor: PASS (post-relock)")

    # 档45R2 OBS-78: entrypoint smoke BEFORE success is declared. Failure =>
    # identical rollback semantics as post-doctor (lock + ledger + installed
    # tree + receipts restored byte-exactly), exit code 4. No skip switch.
    if source_tree is not None:
        smoke_cfg = SMOKE_ENTRIES.get(targets[0])
        if smoke_cfg is None:
            print(f"smoke: {targets[0]} 无入口样本,跳过冒烟 "
                  f"(entrypoint smoke not configured for this skill)")
        else:
            # smoke runs THE LOCKED entrypoint (lock wins over the config default)
            smoke_cfg = dict(smoke_cfg)
            smoke_cfg["entry"] = ((lock_skills.get(targets[0]) or {}).get("entrypoint")
                                  or smoke_cfg.get("entry"))
            sample_dir = Path(__file__).resolve().parent / "smoke-samples"
            ok_smoke, smoke_out = _run_entry_smoke(Path(skills_home), targets[0], smoke_cfg,
                                                  sample_dir=sample_dir)
            print(smoke_out)
            if not ok_smoke:
                _err("entrypoint smoke FAILED after re-lock — rolling back")
                return _rollback(lock_path, lock_bytes, history_path,
                                 hist_existed, hist_bytes, EXIT_POST_DOCTOR_FAIL,
                                 tree_backup=tree_backup, receipts_bytes=receipts_bytes,
                                 skills_home=Path(skills_home))

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
              fail_code: int,
              tree_backup: Path | None = None,
              receipts_bytes: bytes | None = None,
              skills_home: Path | None = None) -> int:
    """Restore skills.lock.json, the ledger and (档44) the installed tree to
    their exact pre-run bytes. tree_backup is the pre-install copy of the
    target skill dir under backup_dir; receipts_bytes is the pre-install
    .install-receipts/<skill>.json content (None = file did not exist)."""
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
    if tree_backup is not None and tree_backup.is_dir():
        if skills_home is None:
            problems.append("tree restore failed: skills_home not provided")
        name = tree_backup.name[len("skills-tree."):-len(".preinstall")]
        dest = Path(skills_home) / name
        try:
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(tree_backup), str(dest))
        except OSError as exc:
            problems.append(f"installed tree restore failed: {exc}")
        rf = dest.parent / ".install-receipts" / dest.name
        try:
            if receipts_bytes is not None:
                rf.parent.mkdir(parents=True, exist_ok=True)
                rf.write_bytes(receipts_bytes)
            elif rf.is_file():
                rf.unlink()
        except OSError as exc:
            problems.append(f"install receipt restore failed: {exc}")
    if problems:
        for problem in problems:
            _err(problem)
        _err("rollback INCOMPLETE — state may be inconsistent; do NOT re-run blindly")
        return EXIT_ROLLBACK_FAILED
    print("rollback: skills.lock.json, ledger and installed tree restored byte-identically")
    return fail_code





if __name__ == "__main__":
    sys.exit(main())
