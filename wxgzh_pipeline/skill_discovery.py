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
from pathlib import Path

EXCLUDE_DIRS = {"__pycache__", ".git", ".pytest_cache", ".github", "tests",
                "node_modules", ".idea", ".vscode"}
EXCLUDE_FILES = {"WXGZH_PIPELINE_INTEGRATION.md", ".gitignore", ".gitattributes"}
EXCLUDE_SUFFIXES = {".pyc"}


def _file_sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _runtime_files(root: Path) -> list[Path]:
    out = []
    for p in sorted(Path(root).rglob("*")):
        if not p.is_file():
            continue
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        if p.name in EXCLUDE_FILES or p.suffix in EXCLUDE_SUFFIXES:
            continue
        out.append(p)
    return out


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


def check_aihot(skills_home: Path, env: dict | None = None) -> dict:
    """REAL existence check for the external agent-invoked AI HOT skill (P0#6).

    Never unconditionally True. If WXGZH_AIHOT_SKILL_DIR is set, ONLY that
    registration is accepted (deterministic for tests/doctor). Otherwise the
    known agent-skill registration locations are probed for aihot/SKILL.md.
    """
    import os
    e = env if env is not None else os.environ
    override = e.get("WXGZH_AIHOT_SKILL_DIR")
    if override:
        p = Path(override) / "SKILL.md"
        return {"exists": p.is_file(), "registration": str(p) if p.is_file() else None,
                "checked": [str(Path(override))]}
    candidates = [Path(skills_home) / "aihot",
                  Path.home() / ".agents" / "skills" / "aihot",
                  Path.home() / ".qoder" / "skills" / "aihot"]
    for c in candidates:
        if (c / "SKILL.md").is_file():
            return {"exists": True, "registration": str(c / "SKILL.md"),
                    "checked": [str(x) for x in candidates]}
    return {"exists": False, "registration": None,
            "checked": [str(x) for x in candidates]}


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
                            "EXTERNAL_DEPENDENCY_AIHOT":
                                "INSTALLED" if ai["exists"] else "NOT_INSTALLED",
                            "version_ok": ai["exists"], "hash_ok": ai["exists"],
                            "entrypoints_ok": ai["exists"], "ok": ai["exists"],
                            "note": "external dependency (卡兹克); registration checked for real; "
                                    "never copied/modified/republished"}
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
