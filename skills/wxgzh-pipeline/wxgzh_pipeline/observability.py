"""OBS-68 / OBS-69 detection-only observability for doctor (档42).

WARN-LEVEL ONLY: nothing in this module may change doctor's PASS/FAIL verdict
or exit code. These checks make two trust-chain inconsistencies VISIBLE; they
do not block. Blocking, if ever wanted, requires a separate authorized
decision (the 档42 design boundary states: 只做检测,不做阻断).

OBS-69 — installed-side skills.lock.json vs repo-side baseline:
    The baseline below is the sha256 of the REPO-side skills.lock.json,
    embedded in Pipeline source. doctor compares the INSTALLED-side lock sha
    against it and reports MATCH / MISMATCH / NO_BASELINE.

    UPDATE TIMING: this constant MUST be updated in the same commit that
    changes the repo-side skills.lock.json. tests/test_observability.py has an
    assertion pinning it to the repo lock (the check's own integrity guard).

    HONEST LIMITATION (must not be overstated): the embedded constant itself
    lives in modifiable Pipeline source, so editing code + lock together can
    still bypass this check. Its value is making drift VISIBLE, not preventing
    tampering.

OBS-68 — installed wxgzh-pipeline vs repo worktree:
    doctor compares the installed wxgzh-pipeline runtime file set (same
    release-include rules as scripts/install.py / zipping.copy_tree) against
    the repo worktree given via --repo-root / WXGZH_REPO_ROOT, and reports
    file counts + per-file sha diffs + missing + extra. Repo unavailable ->
    SKIPPED_NO_REPO (never an error).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import zipping

# OBS-69 baseline: sha256 of the REPO-side skills.lock.json
# (dev/0.1.0-dev2, 76I relock #42(d3e20fb). Update together with any lock change.
# 上一处基线对应 77E relock #70(cf5caa5)。R93:relock 后同次操作同步。
# 上一处基线对应 77F relock #72/#73(2735887)。R93:relock 后同次操作同步。
# 上一处基线对应 77G relock #74/#75。R93:relock 后同次操作同步。
# 上一处基线对应 77H relock #76(887ae6b)。R93:relock 后同次操作同步。
# 上一处基线对应 77I relock #77/#78(sw/zh)。R93:relock 后同次操作同步。
# 上一处基线对应 77J relock #79/#80(sw/media)。R93:relock 后同次操作同步。
# 上一处基线对应 77K relock #81/#82/#83(zh/sw/gzh)。R93:relock 后同次操作同步。
REPO_LOCK_SHA256 = "916422e9379a2f370e996209ca6a3d62b83194d059e91529b6d112de0534f8f6"

_HEX64 = frozenset("0123456789abcdef")


def _sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _lock_skill_diff_summary(installed_lock: Path, repo_lock: Path | None) -> list[str]:
    """Per-skill field diff summary (root/version/entrypoint) between the
    installed lock and the repo lock. Empty list when repo lock unavailable."""
    if repo_lock is None or not Path(repo_lock).is_file():
        return []
    try:
        inst = json.loads(Path(installed_lock).read_text(encoding="utf-8")).get("skills", {})
        repo = json.loads(Path(repo_lock).read_text(encoding="utf-8")).get("skills", {})
    except (OSError, ValueError, TypeError):
        return ["<lock files unreadable; field diff skipped>"]
    out: list[str] = []
    fields = ("skill_version", "skill_root_sha256", "runtime_manifest_sha256",
              "full_commit_sha", "entrypoint_sha256")
    for name in sorted(set(inst) | set(repo)):
        if name not in inst:
            out.append(f"{name}: present in repo lock, absent in installed lock")
            continue
        if name not in repo:
            out.append(f"{name}: present in installed lock, absent in repo lock")
            continue
        for f in fields:
            if inst[name].get(f) != repo[name].get(f):
                out.append(f"{name}.{f}: installed={inst[name].get(f)} repo={repo[name].get(f)}")
    return out


def check_lock_consistency(installed_lock: Path, repo_lock: Path | None = None) -> dict:
    """OBS-69: installed-side skills.lock.json sha vs embedded repo baseline."""
    baseline = REPO_LOCK_SHA256
    if (not isinstance(baseline, str) or len(baseline) != 64
            or any(c not in _HEX64 for c in baseline.lower())):
        return {"status": "NO_BASELINE", "baseline": baseline,
                "note": "embedded REPO_LOCK_SHA256 missing or malformed (see observability.py)"}
    inst_path = Path(installed_lock)
    if not inst_path.is_file():
        return {"status": "MISMATCH", "baseline_sha256": baseline,
                "installed_sha256": None,
                "reason": f"installed lock not found at {inst_path}",
                "diff_summary": []}
    actual = _sha256_file(inst_path)
    if actual == baseline:
        return {"status": "MATCH", "baseline_sha256": baseline,
                "installed_sha256": actual}
    return {"status": "MISMATCH",
            "baseline_sha256": baseline, "installed_sha256": actual,
            "diff_summary": _lock_skill_diff_summary(inst_path, repo_lock)}


# OBS-107(档71B):报告类文件永不在自身核验范围内。
# 报告是审计产物、不是运行资产;「核验先跑、报告后写」是必然时序,不排除就会形成
# 「同步 -> 产生新报告 -> 又不一致」的无限递归,靠调整顺序不可能消除。
# 排除范围仅限 audit/quality/**/*.md;audit/runs/ 是 RUN 证据,严禁排除。
# 显式常量 + 显式前缀判定,不得写成正则通配 audit/ 全目录。
REPORT_DOC_EXCLUDE_PREFIX = ("audit", "quality")


def _is_report_doc(rel: str) -> bool:
    parts = rel.split("/")
    return (len(parts) >= 3 and parts[0] == REPORT_DOC_EXCLUDE_PREFIX[0]
            and parts[1] == REPORT_DOC_EXCLUDE_PREFIX[1]
            and rel.endswith(".md"))


def _runtime_files(root: Path) -> list[Path]:
    return sorted(
        p for p in Path(root).rglob("*") if p.is_file()
        and not _is_report_doc(p.relative_to(root).as_posix())
        and not zipping._skip(p.relative_to(root),
                              zipping.PIPELINE_RELEASE_INCLUDES,
                              zipping.PIPELINE_RELEASE_EXCLUDES))


def check_pipeline_consistency(installed_pipeline: Path, repo_pipeline: Path | None) -> dict:
    """OBS-68: installed wxgzh-pipeline runtime files vs repo worktree.

    Uses the same release-include rules as the official installer
    (zipping.copy_tree). 计数基线 = runtime 文件集合减去 audit/quality/**/*.md
    (OBS-107/档71B);具体数值随仓库演进,不写死(写死数字曾导致注释与实现脱节)。
    """
    if repo_pipeline is None or not Path(repo_pipeline).is_dir():
        return {"status": "SKIPPED_NO_REPO",
                "note": "--repo-root / WXGZH_REPO_ROOT not provided; cannot compare"}
    repo_root = Path(repo_pipeline)
    inst_root = Path(installed_pipeline)
    if not inst_root.is_dir():
        return {"status": "DIFF", "repo_file_count": 0,
                "installed_file_count": 0, "reason": f"installed pipeline dir missing: {inst_root}",
                "diff_files": [], "missing_files": [], "extra_files": [],
                "diff_total": 0, "missing_total": 0, "extra_total": 0}
    repo_files = _runtime_files(repo_root)
    inst_files = _runtime_files(inst_root)
    repo_rel = {p.relative_to(repo_root).as_posix() for p in repo_files}
    inst_rel = {p.relative_to(inst_root).as_posix() for p in inst_files}
    by_rel = {p.relative_to(inst_root).as_posix(): p for p in inst_files}
    diffs = sorted(rel for rel in repo_rel & inst_rel
                   if _sha256_file(repo_root / rel) != _sha256_file(by_rel[rel]))
    missing = sorted(repo_rel - inst_rel)
    extra = sorted(inst_rel - repo_rel)
    ok = not diffs and not missing and not extra
    return {"status": "MATCH" if ok else "DIFF",
            "repo_file_count": len(repo_rel), "installed_file_count": len(inst_rel),
            "diff_files": diffs, "missing_files": missing, "extra_files": extra,
            "diff_total": len(diffs), "missing_total": len(missing),
            "extra_total": len(extra)}
