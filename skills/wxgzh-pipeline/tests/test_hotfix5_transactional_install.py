"""hotfix5: complete lock-set, source-tree, and transactional rollback gates."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

from conftest import SKILL_ROOT
from wxgzh_pipeline import skill_discovery as SD
from wxgzh_pipeline.skill_discovery import InstallReceiptError

SKILLS = {"super-writer", "zh-human-writing", "media-enrichment", "gzh-design"}
HEX40 = "1" * 40


def _load_module(name: str, relative_path: str):
    path = SKILL_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_installer():
    return _load_module("hotfix5_installer", "scripts/install.py")


def _manifest(bundle: Path):
    files = []
    for path in sorted(bundle.rglob("*")):
        if path.is_file() and path.name != "MANIFEST.json":
            data = path.read_bytes()
            files.append({"path": path.relative_to(bundle).as_posix(),
                          "size": len(data),
                          "sha256": hashlib.sha256(data).hexdigest()})
    (bundle / "MANIFEST.json").write_text(
        json.dumps({"artifact": "test", "files": files}), encoding="utf-8")


def _bundle(tmp_path: Path):
    bundle = tmp_path / "bundle"
    pipeline = bundle / "wxgzh-pipeline"
    pipeline.mkdir(parents=True)
    (pipeline / "SKILL.md").write_text("pipeline", encoding="utf-8")
    workflow = pipeline / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_bytes((SKILL_ROOT / ".github" / "workflows" / "ci.yml").read_bytes())
    proofs = {}
    lock_skills = {}
    for index, name in enumerate(sorted(SKILLS), 1):
        root = bundle / "locked-skills" / name
        root.mkdir(parents=True)
        (root / "SKILL.md").write_text(f"{name}\n", encoding="utf-8")
        root_sha, _ = SD.compute_root_sha(root)
        man_sha, rels = SD.compute_runtime_manifest_sha(root)
        commit = str(index) * 40
        tree = format(index, "x") * 40
        repo = f"https://github.com/Amer-CN/{name}"
        proofs[name] = {"repository_url": repo, "full_commit_sha": commit,
                        "source_tree_sha": tree}
        lock_skills[name] = {
            "skill_name": name, "repository_url": repo,
            "full_commit_sha": commit, "source_tree_sha": tree,
            "skill_root_sha256": root_sha,
            "runtime_manifest_sha256": man_sha,
            "runtime_file_count": len(rels), "required_files": ["SKILL.md"],
        }
    (bundle / "source-proofs.json").write_text(
        json.dumps({"generated_by": "test", "skills": proofs}), encoding="utf-8")
    _manifest(bundle)
    return bundle, {"lock_version": 2, "skills": lock_skills}


def _install(tmp_path, monkeypatch, mutate=None, receipt_writer=None):
    bundle, lock = _bundle(tmp_path)
    if mutate:
        mutate(bundle, lock)
    installer = _load_installer()
    monkeypatch.setattr(installer, "_find_source", lambda: (
        bundle / "wxgzh-pipeline", bundle / "locked-skills", bundle))
    monkeypatch.setattr(installer.SD, "load_lock", lambda _: lock)
    if receipt_writer:
        monkeypatch.setattr(installer.SD, "write_install_receipt", receipt_writer)
    target = tmp_path / "target"
    return installer.install(target, dry_run=False), target, lock, installer


@pytest.mark.parametrize("missing", ["media-enrichment", "gzh-design"])
def test_bundle_builder_missing_locked_skill_creates_no_outputs(
    tmp_path, monkeypatch, missing,
):
    builder = _load_module(
        "hotfix5_bundle_builder", "scripts/build_portable_bundle.py",
    )
    skills_home = tmp_path / "sources"
    for name in sorted(SKILLS - {missing}):
        (skills_home / name).mkdir(parents=True)
    out = tmp_path / "out"
    staging = tmp_path / "staging"
    lock = {
        "skills": {
            name: {"kind": "file_skill"} for name in sorted(SKILLS)
        },
    }
    monkeypatch.setattr(builder.SD, "load_lock", lambda _: lock)

    with pytest.raises(SystemExit, match="source directories missing"):
        builder.build(out, skills_home, staging)

    assert not out.exists()
    assert not staging.exists()
    assert not list(tmp_path.rglob("MANIFEST.json"))
    assert not list(tmp_path.rglob("*.zip"))


@pytest.mark.parametrize("missing", ["media-enrichment", "gzh-design"])
def test_bundle_missing_locked_skill_fails_before_copy(tmp_path, monkeypatch, missing):
    def mutate(bundle, _):
        shutil.rmtree(bundle / "locked-skills" / missing)
        _manifest(bundle)
    report, target, _, _ = _install(tmp_path, monkeypatch, mutate)
    assert report["ok"] is False
    assert not target.exists()


def test_bundle_unknown_skill_fails_before_copy(tmp_path, monkeypatch):
    def mutate(bundle, _):
        extra = bundle / "locked-skills" / "unknown-skill"
        extra.mkdir(parents=True)
        (extra / "SKILL.md").write_text("unknown", encoding="utf-8")
        _manifest(bundle)
    report, target, _, _ = _install(tmp_path, monkeypatch, mutate)
    assert report["ok"] is False and not target.exists()


def test_source_proof_missing_locked_skill_fails(tmp_path, monkeypatch):
    def mutate(bundle, _):
        path = bundle / "source-proofs.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        del data["skills"]["media-enrichment"]
        path.write_text(json.dumps(data), encoding="utf-8")
        _manifest(bundle)
    report, target, _, _ = _install(tmp_path, monkeypatch, mutate)
    assert report["ok"] is False and not target.exists()


def test_manifest_missing_one_locked_skill_file_fails(tmp_path, monkeypatch):
    def mutate(bundle, _):
        manifest = json.loads((bundle / "MANIFEST.json").read_text(encoding="utf-8"))
        manifest["files"] = [item for item in manifest["files"]
                             if item["path"] != "locked-skills/gzh-design/SKILL.md"]
        (bundle / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    report, target, _, _ = _install(tmp_path, monkeypatch, mutate)
    assert report["ok"] is False and not target.exists()


def test_receipt_failure_for_any_skill_keeps_all_old_state(tmp_path, monkeypatch):
    installer = _load_installer()
    original_writer = installer.SD.write_install_receipt

    def fail_media(*args, **kwargs):
        skill_name = args[1]
        if skill_name == "media-enrichment":
            raise InstallReceiptError("simulated receipt failure")
        return original_writer(*args, **kwargs)

    bundle, lock = _bundle(tmp_path)
    monkeypatch.setattr(installer, "_find_source", lambda: (
        bundle / "wxgzh-pipeline", bundle / "locked-skills", bundle))
    monkeypatch.setattr(installer.SD, "load_lock", lambda _: lock)
    monkeypatch.setattr(installer.SD, "write_install_receipt", fail_media)
    target = tmp_path / "target"
    old_media = target / "media-enrichment"
    old_media.mkdir(parents=True)
    (old_media / "old.txt").write_text("OLD MEDIA", encoding="utf-8")
    old_receipt = target / ".install-receipts" / "media-enrichment.json"
    old_receipt.parent.mkdir(parents=True)
    old_receipt.write_text("OLD RECEIPT", encoding="utf-8")
    before_media = (old_media / "old.txt").read_bytes()
    before_receipt = old_receipt.read_bytes()

    report = installer.install(target, dry_run=False)
    assert report["ok"] is False
    assert (old_media / "old.txt").read_bytes() == before_media
    assert old_receipt.read_bytes() == before_receipt
    assert not any((target / name).exists() for name in SKILLS - {"media-enrichment"})


def test_bad_new_media_hash_keeps_old_media_and_receipt(tmp_path, monkeypatch):
    installer = _load_installer()
    bundle, lock = _bundle(tmp_path)
    # Rebuild the outer MANIFEST after tampering so only the immutable runtime
    # lock catches the bad new media tree during staging validation.
    (bundle / "locked-skills" / "media-enrichment" / "SKILL.md").write_text(
        "TAMPERED MEDIA\n", encoding="utf-8",
    )
    _manifest(bundle)
    monkeypatch.setattr(installer, "_find_source", lambda: (
        bundle / "wxgzh-pipeline", bundle / "locked-skills", bundle))
    monkeypatch.setattr(installer.SD, "load_lock", lambda _: lock)
    target = tmp_path / "target"
    old_media = target / "media-enrichment"
    old_media.mkdir(parents=True)
    old_content = b"KNOWN GOOD OLD MEDIA"
    (old_media / "old.bin").write_bytes(old_content)
    receipt = target / ".install-receipts" / "media-enrichment.json"
    receipt.parent.mkdir(parents=True)
    old_receipt = b"KNOWN GOOD OLD RECEIPT"
    receipt.write_bytes(old_receipt)

    report = installer.install(target, dry_run=False)

    assert report["ok"] is False
    assert "installed root" in report["error"]
    assert (old_media / "old.bin").read_bytes() == old_content
    assert receipt.read_bytes() == old_receipt
    assert not any((target / name).exists() for name in SKILLS - {"media-enrichment"})


def test_success_requires_all_eight_gates_for_every_locked_skill(tmp_path, monkeypatch):
    report, _, _, _ = _install(tmp_path, monkeypatch)
    assert report["ok"] is True
    locked_actions = {
        action["skill"]: action for action in report["plan"]
        if action["skill"] in SKILLS
    }
    assert set(locked_actions) == SKILLS
    gates = {
        "source_present", "commit_match", "source_tree_match",
        "repository_match", "runtime_root_match", "runtime_manifest_match",
        "receipt_written", "verify_all_ok",
    }
    for action in locked_actions.values():
        assert all(action[field] is True for field in gates)
        assert action["installed"] is True


def test_switch_failure_restores_all_old_skills_and_receipts(tmp_path, monkeypatch):
    installer = _load_installer()
    bundle, lock = _bundle(tmp_path)
    monkeypatch.setattr(installer, "_find_source", lambda: (
        bundle / "wxgzh-pipeline", bundle / "locked-skills", bundle))
    monkeypatch.setattr(installer.SD, "load_lock", lambda _: lock)
    target = tmp_path / "target"
    old_bytes = {}
    for name in ["wxgzh-pipeline", *sorted(SKILLS)]:
        old_file = target / name / "old.bin"
        old_file.parent.mkdir(parents=True)
        payload = f"OLD:{name}".encode("utf-8")
        old_file.write_bytes(payload)
        old_bytes[name] = payload
    receipt_dir = target / ".install-receipts"
    receipt_dir.mkdir(parents=True)
    old_receipts = {}
    for name in sorted(SKILLS):
        payload = f"OLD RECEIPT:{name}".encode("utf-8")
        (receipt_dir / f"{name}.json").write_bytes(payload)
        old_receipts[name] = payload

    real_move = installer.shutil.move
    failed = False

    def fail_during_new_skill_move(src, dst, *args, **kwargs):
        nonlocal failed
        src_path = Path(src)
        dst_path = Path(dst)
        if (not failed and "staging" in src_path.parts
                and dst_path.parent == target and dst_path.name == "media-enrichment"):
            failed = True
            raise OSError("simulated switch failure")
        return real_move(src, dst, *args, **kwargs)

    monkeypatch.setattr(installer.shutil, "move", fail_during_new_skill_move)
    report = installer.install(target, dry_run=False)

    assert report["ok"] is False
    assert "simulated switch failure" in report["error"]
    for name, payload in old_bytes.items():
        assert (target / name / "old.bin").read_bytes() == payload
    for name, payload in old_receipts.items():
        assert (receipt_dir / f"{name}.json").read_bytes() == payload


def test_source_tree_tamper_with_rebuilt_manifest_fails(tmp_path, monkeypatch):
    def mutate(bundle, lock):
        proof_path = bundle / "source-proofs.json"
        proofs = json.loads(proof_path.read_text(encoding="utf-8"))
        proofs["skills"]["media-enrichment"]["source_tree_sha"] = "f" * 40
        proof_path.write_text(json.dumps(proofs), encoding="utf-8")
        _manifest(bundle)
    report, target, _, _ = _install(tmp_path, monkeypatch, mutate)
    assert report["ok"] is False and not target.exists()
    assert "source proof does not match" in report["error"]


def test_git_tree_different_from_lock_fails_before_staging(monkeypatch, tmp_path):
    bundle, lock = _bundle(tmp_path)
    media = bundle / "locked-skills" / "media-enrichment"
    (media / ".git").mkdir()
    installer = _load_installer()
    monkeypatch.setattr(installer, "_find_source", lambda: (
        bundle / "wxgzh-pipeline", bundle / "locked-skills", bundle))
    monkeypatch.setattr(installer.SD, "load_lock", lambda _: lock)

    def fake_git(src, *args):
        meta = lock["skills"]["media-enrichment"]
        assert Path(src) == media
        if args == ("rev-parse", "HEAD"):
            return meta["full_commit_sha"]
        if args == ("rev-parse", "HEAD^{tree}"):
            return "f" * 40
        if args == ("config", "--get", "remote.origin.url"):
            return meta["repository_url"]
        raise AssertionError(args)

    monkeypatch.setattr(installer, "_git", fake_git)
    target = tmp_path / "target"
    report = installer.install(target, dry_run=False)
    assert report["ok"] is False
    assert "source proof does not match" in report["error"]
    assert not target.exists()


def test_git_remote_missing_fails(monkeypatch, tmp_path):
    installer = _load_installer()
    src = tmp_path / "repo"
    (src / ".git").mkdir(parents=True)

    def fake_git(_src, *args):
        if args == ("config", "--get", "remote.origin.url"):
            raise InstallReceiptError("git config failed")
        return HEX40

    monkeypatch.setattr(installer, "_git", fake_git)
    with pytest.raises(InstallReceiptError):
        installer._resolve_source_proof(None, "media-enrichment", src, {})


def test_write_receipt_rejects_tree_mismatch(tmp_path):
    home = tmp_path / "skills"
    (home / "media-enrichment").mkdir(parents=True)
    with pytest.raises(InstallReceiptError):
        SD.write_install_receipt(
            home, "media-enrichment", repository_url="repo",
            actual_commit=HEX40, expected_commit=HEX40,
            source_tree_sha="2" * 40, expected_source_tree_sha="3" * 40,
        )
    assert SD.read_install_receipt(home, "media-enrichment") is None
