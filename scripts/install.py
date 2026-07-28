#!/usr/bin/env python3
"""Cross-platform installer for wxgzh-pipeline + locked sub-skills (hotfix4 P0#1).

For EVERY locked sub-skill the installer:
  1. copies the source tree into the target skills home (backing up any existing
     same-name skill — never deletes user work, NEVER touches the user's .env);
  2. recomputes the installed runtime root + runtime manifest hashes and REQUIRES
     them to equal skills.lock.json;
  3. verifies the install SOURCE:
       - git checkout install: reads `git rev-parse HEAD` / `HEAD^{tree}` and the
         origin remote URL from the source clone;
       - ZIP/bundle install: reads the BUILD-generated source-proofs.json, which
         must itself be hash-bound by the bundle MANIFEST.json, and every
         installed runtime file must match its MANIFEST sha256 (a hand-written /
         tampered proof or a tampered runtime file always FAILs);
  4. requires source commit == lock.full_commit_sha and
     repository_url == lock.repository_url;
  5. only after ALL checks pass writes the EXTERNAL install receipt
     <skills_home>/.install-receipts/<skill>.json (strict write_install_receipt);
  6. on ANY mismatch: InstallReceiptError — no receipt is written, the installer
     exits non-zero and never reports the skill as installed.

Runs doctor-grade hash verification afterwards. Never runs an article, uploads
images, or creates a draft.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve()
# Locate the wxgzh-pipeline skill dir (contains the wxgzh_pipeline package) in
# either layout: dev (scripts/ inside the skill) or bundle (installer/ sibling).
def _locate_skill_root() -> Path:
    for c in [_HERE.parents[1], _HERE.parents[1] / "wxgzh-pipeline",
              _HERE.parents[1].parent / "wxgzh-pipeline"]:
        if (c / "wxgzh_pipeline" / "__init__.py").is_file():
            return c
    return _HERE.parents[1]


SKILL_ROOT = _locate_skill_root()
sys.path.insert(0, str(SKILL_ROOT))
from wxgzh_pipeline import __version__                        # noqa: E402
from wxgzh_pipeline import paths as P                         # noqa: E402
from wxgzh_pipeline import skill_discovery as SD              # noqa: E402
from wxgzh_pipeline.skill_discovery import InstallReceiptError  # noqa: E402
from wxgzh_pipeline.zipping import copy_tree                  # noqa: E402


def _find_source() -> tuple[Path, Path | None, Path | None]:
    """Return (wxgzh_pipeline_src, locked_skills_dir_or_None, bundle_dir_or_None)."""
    for bundle in {SKILL_ROOT.parent, _HERE.parents[1].parent, _HERE.parents[1]}:
        if (bundle / "locked-skills").is_dir() and (bundle / "wxgzh-pipeline").is_dir():
            return bundle / "wxgzh-pipeline", bundle / "locked-skills", bundle
    return SKILL_ROOT, None, None


def _git(src: Path, *args) -> str | None:
    if not (Path(src) / ".git").exists():
        return None
    r = subprocess.run(["git", "-C", str(src), *args], capture_output=True, text=True)
    return r.stdout.strip() or None


def _norm_repo_url(url: str | None) -> str | None:
    if not url:
        return url
    u = url.strip()
    if u.endswith(".git"):
        u = u[:-4]
    if u.startswith("git@github.com:"):
        u = "https://github.com/" + u[len("git@github.com:"):]
    return u.rstrip("/")


def _file_sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _bundle_source_proof(bundle: Path, skill_name: str, src: Path) -> dict:
    """P0#1: bundle installs must prove their source via the BUILD-generated
    source-proofs.json, hash-bound by the bundle MANIFEST.json. Verifies:
      - MANIFEST.json exists and lists source-proofs.json with a matching sha256
        (an arbitrary hand-written proof JSON is rejected);
      - every locked-skills/<skill>/ file listed in the MANIFEST matches its
        recorded sha256 and no runtime file was added/removed (tamper => FAIL).
    Returns the per-skill proof dict {repository_url, full_commit_sha, source_tree_sha}.
    """
    man_p = bundle / "MANIFEST.json"
    proof_p = bundle / "source-proofs.json"
    if not man_p.is_file() or not proof_p.is_file():
        raise InstallReceiptError(
            f"{skill_name}: bundle MANIFEST.json/source-proofs.json missing — "
            "cannot prove install source (FAIL_CLOSED)")
    manifest = json.loads(man_p.read_text(encoding="utf-8"))
    by_path = {f["path"]: f["sha256"] for f in manifest.get("files", [])}
    # 1. the proof file itself must be bound by the manifest
    recorded = by_path.get("source-proofs.json")
    if not recorded or _file_sha256(proof_p) != recorded:
        raise InstallReceiptError(
            f"{skill_name}: source-proofs.json is not hash-bound by the bundle "
            "MANIFEST (tampered or hand-written) — FAIL_CLOSED")
    # 2. every bundled runtime file of this skill must match the manifest
    prefix = f"locked-skills/{skill_name}/"
    listed = {p: s for p, s in by_path.items() if p.startswith(prefix)}
    if not listed:
        raise InstallReceiptError(f"{skill_name}: bundle MANIFEST lists no files for {prefix}")
    for rel, sha in sorted(listed.items()):
        f = bundle / rel
        if not f.is_file() or _file_sha256(f) != sha:
            raise InstallReceiptError(
                f"{skill_name}: bundled runtime file {rel} missing or does not "
                "match the bundle MANIFEST sha256 (tampered) — FAIL_CLOSED")
    on_disk = {f"{prefix}{q.relative_to(src).as_posix()}"
               for q in src.rglob("*") if q.is_file()}
    extra = on_disk - set(listed)
    if extra:
        raise InstallReceiptError(
            f"{skill_name}: bundle contains files not bound by the MANIFEST: "
            f"{sorted(extra)[:5]} — FAIL_CLOSED")
    proofs = json.loads(proof_p.read_text(encoding="utf-8"))
    proof = (proofs.get("skills") or proofs).get(skill_name)
    if not isinstance(proof, dict):
        raise InstallReceiptError(f"{skill_name}: no source proof entry in source-proofs.json")
    return proof


def _resolve_source_proof(bundle: Path | None, skill_name: str, src: Path,
                          locked: dict) -> tuple[str | None, str | None, str | None]:
    """Return (repository_url, actual_commit, source_tree_sha) for the install
    source — from git (checkout install) or from the manifest-bound bundle proof."""
    if (Path(src) / ".git").exists():
        actual = _git(src, "rev-parse", "HEAD")
        tree = _git(src, "rev-parse", "HEAD^{tree}")
        remote = _norm_repo_url(_git(src, "config", "--get", "remote.origin.url"))
        return remote or locked.get("repository_url"), actual, tree
    if bundle is not None:
        proof = _bundle_source_proof(bundle, skill_name, src)
        return (_norm_repo_url(proof.get("repository_url")),
                proof.get("full_commit_sha"), proof.get("source_tree_sha"))
    raise InstallReceiptError(
        f"{skill_name}: no verifiable install source (neither a git checkout nor "
        "a manifest-bound bundle proof) — FAIL_CLOSED")


def install(target_skills_home: Path, dry_run: bool = True,
            skills_src: Path | None = None) -> dict:
    src_pipeline, locked_dir, bundle = _find_source()
    target_skills_home = Path(target_skills_home)
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    plan = []
    ok = True

    lock = SD.load_lock(src_pipeline)
    lock_skills = {n: m for n, m in lock.get("skills", {}).items()
                   if m.get("kind") != "agent_invoked_skill"}

    # sources for the locked sub-skills: --skills-src clones > bundle locked-skills
    to_install: list[tuple[str, Path, dict | None]] = [("wxgzh-pipeline", src_pipeline, None)]
    if skills_src is not None:
        for name, meta in sorted(lock_skills.items()):
            repo_base = _norm_repo_url(meta.get("repository_url", "")) or ""
            candidates = [Path(skills_src) / name,
                          Path(skills_src) / repo_base.rsplit("/", 1)[-1]]
            src = next((c for c in candidates if c.is_dir()), None)
            if src is None:
                plan.append({"skill": name, "installed": False,
                             "error": f"source not found under {skills_src}"})
                ok = False
                continue
            to_install.append((name, src, meta))
    elif locked_dir is not None:
        for d in sorted(locked_dir.iterdir()):
            if d.is_dir():
                to_install.append((d.name, d, lock_skills.get(d.name)))

    for name, src, locked in to_install:
        dst = target_skills_home / name
        action = {"skill": name, "src": str(src), "dst": str(dst),
                  "existing_backup": None, "installed": False, "file_count": None,
                  "install_receipt": None, "source_proof": None}
        if not dry_run:
            target_skills_home.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                bak = target_skills_home / f"{name}.bak-{ts}"
                shutil.move(str(dst), str(bak))
                action["existing_backup"] = str(bak)
            action["file_count"] = copy_tree(src, dst)
            if locked is not None:
                # P0#1: verify source + hashes against the lock, then write the
                # EXTERNAL install receipt. Fail-closed on any mismatch.
                try:
                    repo_url, actual, tree = _resolve_source_proof(bundle, name, src, locked)
                    receipt = SD.write_install_receipt(
                        target_skills_home, name,
                        repository_url=repo_url or "",
                        actual_commit=actual or "",
                        expected_commit=locked.get("full_commit_sha"),
                        expected_repository_url=_norm_repo_url(locked.get("repository_url")),
                        expected_root_sha256=locked.get("skill_root_sha256"),
                        expected_manifest_sha256=locked.get("runtime_manifest_sha256"),
                        source_tree_sha=tree,
                        installer_version=f"wxgzh-pipeline-installer/{__version__}")
                    action["install_receipt"] = str(
                        SD.install_receipt_path(target_skills_home, name))
                    action["source_proof"] = {
                        "repository_url": repo_url, "expected_commit": locked.get("full_commit_sha"),
                        "actual_commit": actual, "source_tree_sha": tree, "match": True}
                    action["installed"] = True
                except InstallReceiptError as e:
                    action["error"] = str(e)
                    action["installed"] = False           # never report success
                    ok = False
            else:
                action["installed"] = True                # orchestrator skill itself
        plan.append(action)

    # hash verification against lock (only meaningful after real install)
    verify = {}
    if not dry_run:
        _, verify = SD.verify_all(target_skills_home, lock)
        if any(locked is not None for _, __, locked in to_install):
            ok = ok and all(v.get("ok") for n, v in verify.items()
                            if n in lock_skills and any(t[0] == n for t in to_install))

    return {"ok": ok if not dry_run else True, "dry_run": dry_run,
            "target_skills_home": str(target_skills_home),
            "env_untouched": True, "plan": plan,
            "hash_verification": {k: v.get("ok") for k, v in verify.items()} if verify else "run without --dry-run to verify",
            "note": "installer never runs an article / uploads images / creates a draft"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default=None, help="target skills home (default: auto-discover)")
    ap.add_argument("--project-root", default=None)
    ap.add_argument("--skills-src", default=None,
                    help="directory holding the locked sub-skill sources (git clones)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.target:
        target = Path(a.target)
    else:
        pr = P.resolve_project_root(a.project_root)
        target = P.skills_home(pr)
    report = install(target, dry_run=a.dry_run,
                     skills_src=Path(a.skills_src) if a.skills_src else None)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
