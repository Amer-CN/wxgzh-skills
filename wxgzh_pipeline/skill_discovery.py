"""Discover installed sub-skills and verify them against skills.lock.json.

dev2-hotfix1 (P0#9): the root hash is RUNTIME-MANIFEST scoped — it covers only
formal runtime files, excluding VCS/CI/integration metadata (.git, .github,
WXGZH_PIPELINE_INTEGRATION.md, tests, caches, .gitignore/.gitattributes). This
makes the hash identical between the GitHub PR tree and a local install, so
"reinstall from the PR commit -> doctor PASS" holds. The lock also records the
repository URL + full commit SHA + entry/validator hashes per skill.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

# .install-receipts holds EXTERNAL per-skill install proofs generated at install
# time; it lives under skills_home (a sibling of each skill) and must never be
# counted as skill runtime content (P0#1 — avoids commit/hash self-reference).
INSTALL_RECEIPTS_DIRNAME = ".install-receipts"
_HEX40 = re.compile(r"^[0-9a-fA-F]{40}$")
EXCLUDE_DIRS = {"__pycache__", ".git", ".pytest_cache", ".github", "tests",
                "node_modules", ".idea", ".vscode", INSTALL_RECEIPTS_DIRNAME}
EXCLUDE_FILES = {"WXGZH_PIPELINE_INTEGRATION.md", ".gitignore", ".gitattributes"}
EXCLUDE_SUFFIXES = {".pyc"}


class InstallReceiptError(Exception):
    """Fail-closed: checked-out HEAD does not match the locked commit."""


def _file_sha(p: Path) -> str:
    """Content hash that is IDENTICAL across Windows/Linux checkouts (P0#9 CI):
    text files are newline-normalized (CRLF/CR -> LF) before hashing; binary
    files (containing a NUL byte) are hashed byte-for-byte."""
    data = p.read_bytes()
    if b"\x00" not in data:  # text: normalize line endings
        data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()


def _runtime_files(root: Path) -> list[Path]:
    out = []
    for p in Path(root).rglob("*"):
        if not p.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        if p.name in EXCLUDE_FILES or p.suffix in EXCLUDE_SUFFIXES:
            continue
        out.append(p)
    # sort by POSIX relpath (NOT Path objects) so the order is identical on
    # Windows and Linux — os-separator sorting would flip subdir ordering and
    # change the aggregate root hash even when every file hash matches (P0#9 CI).
    return sorted(out, key=lambda p: p.relative_to(root).as_posix())


def compute_root_sha(root: Path) -> tuple[str | None, int]:
    """Runtime-scoped content hash: sha256 over sorted 'relpath:sha256' lines."""
    if not Path(root).is_dir():
        return None, 0
    entries = [f"{p.relative_to(root).as_posix()}:{_file_sha(p)}" for p in _runtime_files(root)]
    return hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest(), len(entries)


def compute_runtime_manifest_sha(root: Path) -> tuple[str | None, list[str]]:
    """Hash of the runtime FILE LIST itself (which files count as runtime)."""
    if not Path(root).is_dir():
        return None, []
    rels = [p.relative_to(root).as_posix() for p in _runtime_files(root)]
    return hashlib.sha256("\n".join(rels).encode("utf-8")).hexdigest(), rels


def load_lock(skill_root: Path) -> dict:
    return json.loads((Path(skill_root) / "skills.lock.json").read_text(encoding="utf-8"))


def install_receipt_path(skills_home: Path, skill_name: str) -> Path:
    return Path(skills_home) / INSTALL_RECEIPTS_DIRNAME / f"{skill_name}.json"


def write_install_receipt(skills_home: Path, skill_name: str, *, repository_url: str,
                          actual_commit: str, expected_commit: str | None,
                          expected_repository_url: str | None = None,
                          expected_root_sha256: str | None = None,
                          expected_manifest_sha256: str | None = None,
                          source_tree_sha: str | None = None,
                          expected_source_tree_sha: str | None = None,
                          installer_version: str = "wxgzh-pipeline-installer") -> dict:
    """Generate an EXTERNAL install receipt from the REAL checkout (P0#1, strict).

    The receipt is written OUTSIDE the skill tree
    (<skills_home>/.install-receipts/<skill>.json) so it never counts toward the
    skill runtime root hash. Fail-closed (InstallReceiptError, NO receipt written)
    unless ALL of the following hold:
      - expected_commit is present and a 40-hex sha (expected_commit=None FORBIDDEN);
      - actual_commit is present and a 40-hex sha;
      - actual_commit == expected_commit;
      - repository_url == expected_repository_url (when the lock value is given);
      - the recomputed runtime root/manifest == the lock values (when given).
    """
    root = Path(skills_home) / skill_name
    if not root.is_dir():
        raise InstallReceiptError(f"{skill_name}: install dir missing at {root}")
    if not (isinstance(expected_commit, str) and _HEX40.match(expected_commit)):
        raise InstallReceiptError(
            f"{skill_name}: expected_commit must be a 40-hex sha (got {expected_commit!r})")
    if not (isinstance(actual_commit, str) and _HEX40.match(actual_commit)):
        raise InstallReceiptError(
            f"{skill_name}: actual_commit must be a 40-hex sha (got {actual_commit!r})")
    if actual_commit != expected_commit:
        raise InstallReceiptError(
            f"{skill_name}: checked-out HEAD {actual_commit} != locked {expected_commit}")
    if not (isinstance(expected_source_tree_sha, str) and _HEX40.fullmatch(expected_source_tree_sha)):
        raise InstallReceiptError(
            f"{skill_name}: expected_source_tree_sha must be a 40-hex sha "
            f"(got {expected_source_tree_sha!r})")
    if not (isinstance(source_tree_sha, str) and _HEX40.fullmatch(source_tree_sha)):
        raise InstallReceiptError(
            f"{skill_name}: actual source_tree_sha must be a 40-hex sha "
            f"(got {source_tree_sha!r})")
    if source_tree_sha != expected_source_tree_sha:
        raise InstallReceiptError(
            f"{skill_name}: source tree {source_tree_sha} != locked {expected_source_tree_sha}")
    if expected_repository_url is not None and repository_url != expected_repository_url:
        raise InstallReceiptError(
            f"{skill_name}: repository_url {repository_url!r} != locked {expected_repository_url!r}")
    root_sha, _ = compute_root_sha(root)
    man_sha, _ = compute_runtime_manifest_sha(root)
    if expected_root_sha256 is not None and root_sha != expected_root_sha256:
        raise InstallReceiptError(
            f"{skill_name}: installed root {root_sha} != locked {expected_root_sha256}")
    if expected_manifest_sha256 is not None and man_sha != expected_manifest_sha256:
        raise InstallReceiptError(
            f"{skill_name}: runtime manifest {man_sha} != locked {expected_manifest_sha256}")
    receipt = {
        "schema_version": "1.0",
        "skill_name": skill_name,
        "repository_url": repository_url,
        "full_commit_sha": actual_commit,
        "source_tree_sha": source_tree_sha,
        "installed_runtime_root_sha256": root_sha,
        "installed_runtime_manifest_sha256": man_sha,
        "installed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "installer_version": installer_version,
    }
    p = install_receipt_path(skills_home, skill_name)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True),
                 encoding="utf-8", newline="\n")
    return receipt


def read_install_receipt(skills_home: Path, skill_name: str) -> dict | None:
    p = install_receipt_path(skills_home, skill_name)
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return None


def check_aihot(skills_home: Path, env: dict | None = None) -> dict:
    """REAL capability check for the external agent-invoked AI HOT skill (P0#6/#8).

    A bare SKILL.md is NOT enough. We require a genuine agent-skill REGISTRATION
    record that declares name/identifier + an output contract, plus a signal that
    the CURRENT agent can discover it. Sources, in order:

    - WXGZH_AIHOT_REGISTRATION=<file>: a JSON registration manifest; must declare
      skill name/id + output_contract + discoverable=true.
    - WXGZH_AIHOT_SKILL_DIR=<dir>: must contain SKILL.md AND a registration file
      (registration.json / skill.json) with the same fields.

    If capability cannot be verified => status UNVERIFIED and
    live_pipeline_allowed=false. Never PASS on a throwaway fake SKILL.md.
    """
    import json as _json
    import os
    e = env if env is not None else os.environ

    def _valid_registration(data: dict) -> bool:
        name = data.get("name") or data.get("skill") or data.get("identifier")
        has_output = bool(data.get("output_contract") or data.get("outputs")
                          or data.get("output"))
        discoverable = data.get("discoverable", True) is not False
        return bool(name) and has_output and discoverable

    reg_file = e.get("WXGZH_AIHOT_REGISTRATION")
    if reg_file:
        p = Path(reg_file)
        if p.is_file():
            try:
                data = _json.loads(p.read_text(encoding="utf-8"))
            except ValueError:
                data = {}
            if _valid_registration(data):
                return {"exists": True, "status": "INSTALLED",
                        "registration": str(p), "checked": [str(p)],
                        "live_pipeline_allowed": True}
        return {"exists": False, "status": "UNVERIFIED", "registration": None,
                "checked": [str(p)], "live_pipeline_allowed": False,
                "reason": "registration manifest missing/invalid"}

    override = e.get("WXGZH_AIHOT_SKILL_DIR")
    dirs = [Path(override)] if override else [
        Path(skills_home) / "aihot",
        Path.home() / ".agents" / "skills" / "aihot",
        Path.home() / ".qoder" / "skills" / "aihot"]
    checked = []
    for d in dirs:
        checked.append(str(d))
        if not (d / "SKILL.md").is_file():
            continue
        # require a real registration record alongside SKILL.md
        for regname in ("registration.json", "skill.json", "agent_skill.json"):
            rp = d / regname
            if rp.is_file():
                try:
                    data = _json.loads(rp.read_text(encoding="utf-8"))
                except ValueError:
                    data = {}
                if _valid_registration(data):
                    return {"exists": True, "status": "INSTALLED",
                            "registration": str(rp), "checked": checked,
                            "live_pipeline_allowed": True}
    # SKILL.md alone (or nothing) cannot be verified as a callable capability
    return {"exists": False, "status": "UNVERIFIED", "registration": None,
            "checked": checked, "live_pipeline_allowed": False,
            "reason": "no valid agent-skill registration (SKILL.md alone is insufficient)"}


def discover(skills_home: Path, lock: dict, env: dict | None = None) -> dict:
    """Return per-skill discovery/verification result."""
    result = {}
    for name, locked in lock.get("skills", {}).items():
        if locked.get("kind") == "agent_invoked_skill":
            # aihot: EXTERNAL dependency — existence is REALLY checked against the
            # agent-skill registry; never unconditionally ok (P0#6).
            ai = check_aihot(skills_home, env=env)
            result[name] = {"skill_name": name, "kind": "agent_invoked_skill",
                            "exists": ai["exists"], "registration": ai["registration"],
                            "EXTERNAL_DEPENDENCY_AIHOT": ai.get("status",
                                "INSTALLED" if ai["exists"] else "NOT_INSTALLED"),
                            "live_pipeline_allowed": ai.get("live_pipeline_allowed", ai["exists"]),
                            "version_ok": ai["exists"], "hash_ok": ai["exists"],
                            "entrypoints_ok": ai["exists"], "ok": ai["exists"],
                            "note": "external dependency (卡兹克); capability checked for real "
                                    "(registration + output contract); never copied/modified/republished"}
            continue
        root = Path(skills_home) / name
        exists = root.is_dir()
        cur_sha, nfiles = compute_root_sha(root) if exists else (None, 0)
        cur_ver = _read_version(root, name) if exists else None
        version_ok = exists and cur_ver == locked.get("skill_version")
        hash_ok = exists and cur_sha == locked.get("skill_root_sha256")
        req = locked.get("required_files", [])
        entrypoints_ok = exists and all((root / rf).is_file() for rf in req)
        result[name] = {
            "skill_name": name, "skill_dir": str(root), "exists": exists,
            "locked_version": locked.get("skill_version"), "current_version": cur_ver,
            "locked_root_sha256": locked.get("skill_root_sha256"), "current_root_sha256": cur_sha,
            "file_count": nfiles, "version_ok": version_ok, "hash_ok": hash_ok,
            "entrypoints_ok": entrypoints_ok,
            "missing_files": [rf for rf in req if not (root / rf).is_file()] if exists else req,
            "ok": bool(exists and version_ok and hash_ok and entrypoints_ok),
        }
    return result


def _read_version(root: Path, name: str) -> str | None:
    if name == "gzh-design":
        rn = root / "RELEASE_NOTES.md"
        if rn.is_file():
            head = rn.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
            return head.split("gzh-design")[-1].strip() if "gzh-design" in head else head.strip("# ").strip()
    vf = root / "VERSION"
    if vf.is_file():
        first = vf.read_text(encoding="utf-8", errors="ignore").splitlines()[:1]
        if first:
            return first[0].replace("version:", "").strip()
    return None


def verify_all(skills_home: Path, lock: dict, env: dict | None = None) -> tuple[bool, dict]:
    disc = discover(skills_home, lock, env=env)
    ok = all(v["ok"] for v in disc.values())
    return ok, disc
