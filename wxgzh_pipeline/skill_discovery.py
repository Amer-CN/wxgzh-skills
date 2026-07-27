"""Discover installed sub-skills and verify them against skills.lock.json.

Root-hash algorithm matches the inventory builder: sha256 over sorted
'relpath:sha256(content)' lines (excluding caches/vcs). Any mismatch =>
FAIL_CLOSED; the orchestrator refuses to run.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

EXCLUDE_DIRS = {"__pycache__", ".git", ".pytest_cache", ".github"}


def _file_sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def compute_root_sha(root: Path) -> tuple[str | None, int]:
    if not Path(root).is_dir():
        return None, 0
    entries = []
    for p in sorted(Path(root).rglob("*")):
        if p.is_file() and not any(part in EXCLUDE_DIRS for part in p.parts):
            entries.append(f"{p.relative_to(root).as_posix()}:{_file_sha(p)}")
    return hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest(), len(entries)


def load_lock(skill_root: Path) -> dict:
    return json.loads((Path(skill_root) / "skills.lock.json").read_text(encoding="utf-8"))


def discover(skills_home: Path, lock: dict) -> dict:
    """Return per-skill discovery/verification result."""
    result = {}
    for name, locked in lock.get("skills", {}).items():
        if locked.get("kind") == "agent_invoked_skill":
            # aihot: no local dir; presence is a registry concern, verified at run time
            result[name] = {"skill_name": name, "kind": "agent_invoked_skill",
                            "exists": True, "version_ok": True, "hash_ok": True,
                            "entrypoints_ok": True, "ok": True,
                            "note": "agent-invoked; output-hash locked at run time"}
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


def verify_all(skills_home: Path, lock: dict) -> tuple[bool, dict]:
    disc = discover(skills_home, lock)
    ok = all(v["ok"] for v in disc.values())
    return ok, disc
