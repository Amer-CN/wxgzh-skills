#!/usr/bin/env python3
"""Transactional installer for wxgzh-pipeline and every locked file skill.

The installer is fail-closed and side-effect-free until every source, commit,
tree, repository, runtime hash, manifest member and staged receipt verifies.
It never runs an article, uploads an image, or touches WeChat drafts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_HERE = Path(__file__).resolve()


def _locate_skill_root() -> Path:
    for candidate in (
        _HERE.parents[1],
        _HERE.parents[1] / "wxgzh-pipeline",
        _HERE.parents[1].parent / "wxgzh-pipeline",
    ):
        if (candidate / "wxgzh_pipeline" / "__init__.py").is_file():
            return candidate
    return _HERE.parents[1]


SKILL_ROOT = _locate_skill_root()
sys.path.insert(0, str(SKILL_ROOT))
from wxgzh_pipeline import __version__  # noqa: E402
from wxgzh_pipeline import paths as P  # noqa: E402
from wxgzh_pipeline import skill_discovery as SD  # noqa: E402
from wxgzh_pipeline.skill_discovery import InstallReceiptError  # noqa: E402
from wxgzh_pipeline.zipping import copy_tree  # noqa: E402


def _find_source() -> tuple[Path, Path | None, Path | None]:
    for bundle in {SKILL_ROOT.parent, _HERE.parents[1].parent, _HERE.parents[1]}:
        if (bundle / "locked-skills").is_dir() and (bundle / "wxgzh-pipeline").is_dir():
            return bundle / "wxgzh-pipeline", bundle / "locked-skills", bundle
    return SKILL_ROOT, None, None


def _git(src: Path, *args: str) -> str | None:
    if not (Path(src) / ".git").exists():
        return None
    result = subprocess.run(
        ["git", "-C", str(src), *args], capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise InstallReceiptError(
            f"git {' '.join(args)} failed for {src}: "
            f"{(result.stderr or result.stdout).strip()}")
    value = result.stdout.strip()
    if not value:
        raise InstallReceiptError(
            f"git {' '.join(args)} returned no value for {src}")
    return value


def _norm_repo_url(url: str | None) -> str | None:
    if not url:
        return url
    normalized = url.strip()
    if normalized.endswith(".git"):
        normalized = normalized[:-4]
    if normalized.startswith("git@github.com:"):
        normalized = "https://github.com/" + normalized[len("git@github.com:"):]
    return normalized.rstrip("/")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_index(bundle: Path) -> dict[str, str]:
    manifest_path = bundle / "MANIFEST.json"
    if not manifest_path.is_file():
        raise InstallReceiptError("bundle MANIFEST.json missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return {item["path"]: item["sha256"] for item in manifest["files"]}
    except (ValueError, KeyError, TypeError) as exc:
        raise InstallReceiptError(f"invalid bundle MANIFEST.json: {exc}") from exc


def _validate_bundle_set(bundle: Path, expected_skills: set[str]) -> None:
    locked_dir = bundle / "locked-skills"
    actual_skills = {
        path.name for path in locked_dir.iterdir() if path.is_dir()
    } if locked_dir.is_dir() else set()
    if actual_skills != expected_skills:
        raise InstallReceiptError(
            f"bundle locked skill set mismatch: expected={sorted(expected_skills)} "
            f"actual={sorted(actual_skills)}")

    manifest_index = _manifest_index(bundle)
    proof_path = bundle / "source-proofs.json"
    recorded_proof_sha = manifest_index.get("source-proofs.json")
    if (not proof_path.is_file() or not recorded_proof_sha
            or _file_sha256(proof_path) != recorded_proof_sha):
        raise InstallReceiptError(
            "source-proofs.json missing or not hash-bound by bundle MANIFEST")
    try:
        proofs = json.loads(proof_path.read_text(encoding="utf-8"))
        proof_skills = set(proofs["skills"])
    except (ValueError, KeyError, TypeError) as exc:
        raise InstallReceiptError(f"invalid source-proofs.json: {exc}") from exc
    if proof_skills != expected_skills:
        raise InstallReceiptError(
            f"source proof skill set mismatch: expected={sorted(expected_skills)} "
            f"actual={sorted(proof_skills)}")

    for skill_name in sorted(expected_skills):
        prefix = f"locked-skills/{skill_name}/"
        listed = {path for path in manifest_index if path.startswith(prefix)}
        on_disk = {
            f"{prefix}{path.relative_to(locked_dir / skill_name).as_posix()}"
            for path in (locked_dir / skill_name).rglob("*") if path.is_file()
        }
        if not listed or listed != on_disk:
            raise InstallReceiptError(
                f"{skill_name}: MANIFEST file set mismatch; "
                f"missing={sorted(on_disk - listed)[:5]} extra={sorted(listed - on_disk)[:5]}")
        for relative_path in sorted(listed):
            path = bundle / relative_path
            if _file_sha256(path) != manifest_index[relative_path]:
                raise InstallReceiptError(
                    f"{skill_name}: {relative_path} does not match MANIFEST sha256")


def _bundle_source_proof(bundle: Path, skill_name: str, src: Path) -> dict:
    expected = {
        path.name for path in (bundle / "locked-skills").iterdir() if path.is_dir()
    }
    _validate_bundle_set(bundle, expected)
    proofs = json.loads((bundle / "source-proofs.json").read_text(encoding="utf-8"))
    proof = proofs["skills"].get(skill_name)
    if not isinstance(proof, dict):
        raise InstallReceiptError(f"{skill_name}: source proof missing")
    return proof


def _resolve_source_proof(
    bundle: Path | None, skill_name: str, src: Path, locked: dict,
) -> tuple[str, str, str]:
    if (Path(src) / ".git").exists():
        actual = _git(src, "rev-parse", "HEAD")
        tree = _git(src, "rev-parse", "HEAD^{tree}")
        remote = _norm_repo_url(_git(src, "config", "--get", "remote.origin.url"))
        if not remote:
            raise InstallReceiptError(
                f"{skill_name}: git remote.origin.url missing — FAIL_CLOSED")
        return remote, actual or "", tree or ""
    if bundle is not None:
        proof = _bundle_source_proof(bundle, skill_name, src)
        return (
            _norm_repo_url(proof.get("repository_url")) or "",
            proof.get("full_commit_sha") or "",
            proof.get("source_tree_sha") or "",
        )
    raise InstallReceiptError(
        f"{skill_name}: no verifiable source (git checkout or manifest-bound bundle)")


def _resolve_sources(
    src_pipeline: Path,
    locked_dir: Path | None,
    bundle: Path | None,
    lock_skills: dict[str, dict],
    skills_src: Path | None,
) -> list[tuple[str, Path, dict | None]]:
    expected_skills = set(lock_skills)
    if bundle is not None:
        _validate_bundle_set(bundle, expected_skills)
    sources: list[tuple[str, Path, dict | None]] = [
        ("wxgzh-pipeline", src_pipeline, None),
    ]
    if skills_src is not None:
        for name in sorted(expected_skills):
            meta = lock_skills[name]
            repo_name = (_norm_repo_url(meta.get("repository_url")) or "").rsplit("/", 1)[-1]
            candidates = [Path(skills_src) / name, Path(skills_src) / repo_name]
            source = next((path for path in candidates if path.is_dir()), None)
            if source is None:
                raise InstallReceiptError(f"{name}: source not found under {skills_src}")
            sources.append((name, source, meta))
    elif locked_dir is not None:
        actual = {path.name for path in locked_dir.iterdir() if path.is_dir()}
        if actual != expected_skills:
            raise InstallReceiptError(
                f"bundle locked skill set mismatch: expected={sorted(expected_skills)} "
                f"actual={sorted(actual)}")
        sources.extend((name, locked_dir / name, lock_skills[name])
                       for name in sorted(expected_skills))
    else:
        raise InstallReceiptError("locked skill sources unavailable")
    if {name for name, _, meta in sources if meta is not None} != expected_skills:
        raise InstallReceiptError("resolved source set does not equal skills.lock")
    return sources


def _rollback_switch(
    target: Path,
    switched: list[str],
    backups: dict[str, Path],
    receipts_backup: Path | None,
) -> None:
    # Restore both successfully switched destinations and the current destination
    # whose OLD directory was backed up but whose NEW move may have failed before
    # it could be appended to ``switched``.
    restore_names = list(dict.fromkeys([*reversed(switched), *reversed(backups)]))
    for name in restore_names:
        destination = target / name
        if destination.exists():
            shutil.rmtree(destination)
        backup = backups.get(name)
        if backup and backup.exists():
            shutil.move(str(backup), str(destination))
    receipt_dir = target / SD.INSTALL_RECEIPTS_DIRNAME
    if receipt_dir.exists():
        shutil.rmtree(receipt_dir)
    if receipts_backup and receipts_backup.exists():
        shutil.move(str(receipts_backup), str(receipt_dir))


def install(
    target_skills_home: Path,
    dry_run: bool = True,
    skills_src: Path | None = None,
) -> dict:
    src_pipeline, locked_dir, bundle = _find_source()
    target = Path(target_skills_home)
    lock = SD.load_lock(src_pipeline)
    lock_skills = {
        name: meta for name, meta in lock.get("skills", {}).items()
        if meta.get("kind") != "agent_invoked_skill"
    }
    expected_skills = set(lock_skills)
    plan: list[dict] = []
    try:
        sources = _resolve_sources(
            src_pipeline, locked_dir, bundle, lock_skills,
            Path(skills_src) if skills_src is not None else None,
        )
        source_proofs: dict[str, tuple[str, str, str]] = {}
        for name, source, meta in sources:
            action = {
                "skill": name, "src": str(source), "dst": str(target / name),
                "installed": False, "source_present": source.is_dir(),
                "commit_match": None, "source_tree_match": None,
                "repository_match": None, "runtime_root_match": None,
                "runtime_manifest_match": None, "receipt_written": False,
                "verify_all_ok": False, "install_receipt": None,
            }
            plan.append(action)
            if not source.is_dir():
                raise InstallReceiptError(f"{name}: source directory missing")
            if meta is not None:
                repository, commit, tree = _resolve_source_proof(bundle, name, source, meta)
                source_proofs[name] = (repository, commit, tree)
                action.update({
                    "commit_match": commit == meta.get("full_commit_sha"),
                    "source_tree_match": tree == meta.get("source_tree_sha"),
                    "repository_match": repository == _norm_repo_url(meta.get("repository_url")),
                })
                if not all((action["commit_match"], action["source_tree_match"],
                            action["repository_match"])):
                    raise InstallReceiptError(f"{name}: source proof does not match skills.lock")
        if dry_run:
            return {
                "ok": True, "dry_run": True, "target_skills_home": str(target),
                "env_untouched": True, "plan": plan,
                "hash_verification": "run without --dry-run to verify",
                "note": "installer never runs an article / uploads images / creates a draft",
            }

        transaction = target.parent / (
            f".{target.name}.hotfix5-install-{os.getpid()}-"
            f"{datetime.now().strftime('%Y%m%dT%H%M%S%f')}")
        staging_home = transaction / "staging"
        backups_dir = transaction / "backups"
        staging_home.mkdir(parents=True)
        backups_dir.mkdir(parents=True)
        try:
            for name, source, _ in sources:
                copy_tree(source, staging_home / name)

            for action in plan:
                name = action["skill"]
                meta = lock_skills.get(name)
                if meta is None:
                    action["installed"] = True
                    continue
                repository, commit, tree = source_proofs[name]
                SD.write_install_receipt(
                    staging_home, name,
                    repository_url=repository,
                    actual_commit=commit,
                    expected_commit=meta.get("full_commit_sha"),
                    expected_repository_url=_norm_repo_url(meta.get("repository_url")),
                    expected_root_sha256=meta.get("skill_root_sha256"),
                    expected_manifest_sha256=meta.get("runtime_manifest_sha256"),
                    source_tree_sha=tree,
                    expected_source_tree_sha=meta.get("source_tree_sha"),
                    installer_version=f"wxgzh-pipeline-installer/{__version__}",
                )
                action["runtime_root_match"] = True
                action["runtime_manifest_match"] = True
                action["receipt_written"] = True
                action["install_receipt"] = str(
                    SD.install_receipt_path(target, name))

            runtime_lock = {"lock_version": lock.get("lock_version"), "skills": lock_skills}
            verify_ok, verify = SD.verify_all(staging_home, runtime_lock)
            if set(verify) != expected_skills or not verify_ok or not all(
                verify[name].get("ok") for name in expected_skills
            ):
                raise InstallReceiptError(
                    f"staging verify_all failed for complete lock set: {verify}")

            target.mkdir(parents=True, exist_ok=True)
            switched: list[str] = []
            backups: dict[str, Path] = {}
            receipt_dir = target / SD.INSTALL_RECEIPTS_DIRNAME
            receipts_backup = None
            try:
                if receipt_dir.exists():
                    receipts_backup = backups_dir / SD.INSTALL_RECEIPTS_DIRNAME
                    shutil.move(str(receipt_dir), str(receipts_backup))
                for name, _, _ in sources:
                    destination = target / name
                    if destination.exists():
                        backup = backups_dir / name
                        shutil.move(str(destination), str(backup))
                        backups[name] = backup
                    shutil.move(str(staging_home / name), str(destination))
                    switched.append(name)
                shutil.move(
                    str(staging_home / SD.INSTALL_RECEIPTS_DIRNAME),
                    str(receipt_dir),
                )
            except Exception:
                _rollback_switch(target, switched, backups, receipts_backup)
                raise

            final_lock = {"lock_version": lock.get("lock_version"), "skills": lock_skills}
            final_ok, final_verify = SD.verify_all(target, final_lock)
            if not final_ok or set(final_verify) != expected_skills:
                _rollback_switch(target, switched, backups, receipts_backup)
                raise InstallReceiptError("post-switch verify_all failed; rolled back")
            required_action_gates = (
                "source_present", "commit_match", "source_tree_match",
                "repository_match", "runtime_root_match",
                "runtime_manifest_match", "receipt_written", "verify_all_ok",
            )
            for action in plan:
                if action["skill"] in expected_skills:
                    action["verify_all_ok"] = bool(
                        final_verify[action["skill"]].get("ok"))
                    action["installed"] = all(
                        action.get(field) is True for field in required_action_gates)
            complete_lock_ok = all(
                action.get("installed") is True
                for action in plan if action["skill"] in expected_skills
            )
            if not complete_lock_ok:
                _rollback_switch(target, switched, backups, receipts_backup)
                raise InstallReceiptError(
                    "post-switch complete lock action gates failed; rolled back")
            return {
                "ok": True, "dry_run": False, "target_skills_home": str(target),
                "env_untouched": True, "plan": plan,
                "hash_verification": {
                    name: final_verify[name].get("ok") for name in sorted(expected_skills)
                },
                "note": "installer never runs an article / uploads images / creates a draft",
            }
        finally:
            if transaction.exists():
                shutil.rmtree(transaction)
    except (InstallReceiptError, OSError, ValueError, KeyError, TypeError) as exc:
        if not plan:
            plan = [{
                "skill": name, "installed": False, "receipt_written": False,
                "error": str(exc),
            } for name in sorted(expected_skills)]
        for action in plan:
            if not action.get("installed"):
                action.setdefault("error", str(exc))
        return {
            "ok": False, "dry_run": dry_run, "target_skills_home": str(target),
            "env_untouched": True, "plan": plan, "error": str(exc),
            "hash_verification": {},
            "note": "installer never runs an article / uploads images / creates a draft",
        }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", default=None)
    parser.add_argument("--project-root", default=None)
    parser.add_argument("--skills-src", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.target:
        target = Path(args.target)
    else:
        project_root = P.resolve_project_root(args.project_root)
        target = P.skills_home(project_root)
    report = install(
        target, dry_run=args.dry_run,
        skills_src=Path(args.skills_src) if args.skills_src else None,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
