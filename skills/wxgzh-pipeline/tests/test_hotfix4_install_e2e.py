"""hotfix4 P0#1 e2e: the FORMAL installer (scripts/install.py) generates the
EXTERNAL install receipt — and fail-closes on any tampered bundle source proof.

Spec cases:
  a. real install => receipt exists at <skills_home>/.install-receipts/<skill>.json
  b. receipt commit/root/manifest/repository ALL match skills.lock
  c. after install, the theme validator (live-proof, receipt-based) => PASS
  d. bundle commit tampered              => install FAILs, no receipt
  e. bundle repository_url tampered      => install FAILs, no receipt
  f. bundle runtime file tampered        => install FAILs, no receipt
  g. receipt missing / corrupt           => live theme identity FAILs
"""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from conftest import load_validator, SKILL_ROOT
from wxgzh_pipeline import skill_discovery as SD

COMMIT = "5ed758cf0487ac88090efed24bfe02e21d8edd45"
TREE = "7b35ad2030209a78624226b5de14a9c713761455"
REPO_URL = "https://github.com/Amer-CN/gzh-design-skill"


def _load_installer():
    p = SKILL_ROOT / "scripts" / "install.py"
    spec = importlib.util.spec_from_file_location("wxgzh_install_mod", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _nsha(p: Path) -> str:
    d = p.read_bytes()
    if b"\x00" not in d:
        d = d.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(d).hexdigest()


def _rebuild_manifest(bundle: Path) -> None:
    files = []
    for p in sorted(bundle.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.json":
            b = p.read_bytes()
            files.append({"path": p.relative_to(bundle).as_posix(), "size": len(b),
                          "sha256": hashlib.sha256(b).hexdigest()})
    (bundle / "MANIFEST.json").write_text(
        json.dumps({"artifact": "test-bundle", "file_count": len(files), "files": files}),
        encoding="utf-8")


def _mk_bundle(tmp_path: Path) -> tuple[Path, dict]:
    """Synthetic portable bundle: pipeline stub + one locked skill (gzh-design) +
    build-generated source proof, all hash-bound by MANIFEST.json."""
    bundle = tmp_path / "bundle"
    (bundle / "wxgzh-pipeline").mkdir(parents=True)
    (bundle / "wxgzh-pipeline" / "SKILL.md").write_text("# stub\n", encoding="utf-8")
    workflow = bundle / "wxgzh-pipeline" / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_bytes((SKILL_ROOT / ".github" / "workflows" / "ci.yml").read_bytes())
    g = bundle / "locked-skills" / "gzh-design"
    (g / "scripts").mkdir(parents=True)
    (g / "VERSION").write_text("version: v-test\n", encoding="utf-8")
    (g / "scripts" / "render_article.py").write_text("# render entry\n", encoding="utf-8")
    (g / "scripts" / "generate_hammer_upgrade_samples.py").write_text(
        "# components\n", encoding="utf-8")
    (bundle / "source-proofs.json").write_text(json.dumps(
        {"generated_by": "build_portable_bundle/test",
         "skills": {"gzh-design": {"repository_url": REPO_URL,
                                   "full_commit_sha": COMMIT,
                                   "source_tree_sha": TREE}}}), encoding="utf-8")
    _rebuild_manifest(bundle)
    root_sha, _ = SD.compute_root_sha(g)
    man_sha, _ = SD.compute_runtime_manifest_sha(g)
    lock = {"lock_version": 2, "skills": {"gzh-design": {
        "skill_name": "gzh-design", "repository_url": REPO_URL,
        "full_commit_sha": COMMIT, "source_tree_sha": TREE,
        "skill_version": "v-test", "skill_root_sha256": root_sha,
        "runtime_manifest_sha256": man_sha,
        "entrypoint_sha256": _nsha(g / "scripts" / "render_article.py"),
        "component_source_sha256": _nsha(g / "scripts" / "generate_hammer_upgrade_samples.py"),
        "required_files": ["scripts/render_article.py"]}}}
    return bundle, lock


def _install(tmp_path: Path, monkeypatch, mutate=None):
    bundle, lock = _mk_bundle(tmp_path)
    if mutate:
        mutate(bundle)
    inst = _load_installer()
    monkeypatch.setattr(inst, "_find_source",
                        lambda: (bundle / "wxgzh-pipeline", bundle / "locked-skills", bundle))
    monkeypatch.setattr(inst.SD, "load_lock", lambda root: lock)
    target = tmp_path / "skills"
    report = inst.install(target, dry_run=False)
    return report, target, lock


# ---------------- a + b: formal install writes a lock-matching receipt ----------------

def test_a_install_writes_receipt(tmp_path, monkeypatch):
    report, target, lock = _install(tmp_path, monkeypatch)
    assert report["ok"] is True, report
    p = SD.install_receipt_path(target, "gzh-design")
    assert p.is_file(), "formal install.py must generate the external receipt"
    gzh_action = next(a for a in report["plan"] if a["skill"] == "gzh-design")
    assert gzh_action["installed"] is True and gzh_action["install_receipt"]


def test_b_receipt_matches_lock(tmp_path, monkeypatch):
    report, target, lock = _install(tmp_path, monkeypatch)
    rec = SD.read_install_receipt(target, "gzh-design")
    le = lock["skills"]["gzh-design"]
    assert rec["full_commit_sha"] == le["full_commit_sha"]
    assert rec["repository_url"] == le["repository_url"]
    assert rec["installed_runtime_root_sha256"] == le["skill_root_sha256"]
    assert rec["installed_runtime_manifest_sha256"] == le["runtime_manifest_sha256"]
    assert rec["source_tree_sha"] == le["source_tree_sha"]


# ---------------- c: live-proof theme PASS built on the formal receipt ----------------

def test_c_live_proof_theme_pass_after_install(tmp_path, monkeypatch):
    report, target, lock = _install(tmp_path, monkeypatch)
    le = lock["skills"]["gzh-design"]
    rec = SD.read_install_receipt(target, "gzh-design")
    g = target / "gzh-design"
    root_sha, _ = SD.compute_root_sha(g)
    man_sha, _ = SD.compute_runtime_manifest_sha(g)
    html = (SKILL_ROOT / "fixtures" / "offline_pipeline_fixture" / "gzh_design" /
            "outputs" / "final.html")
    ev = {"official_gzh_call": True,
          "render_entry_path": str(g / "scripts" / "render_article.py"),
          "entry_sha256": _nsha(g / "scripts" / "render_article.py"),
          "component_source_path": str(g / "scripts" / "generate_hammer_upgrade_samples.py"),
          "installed_root_sha256": root_sha,
          "installed_runtime_manifest_sha256": man_sha,
          "install_receipt_root_sha256": rec["installed_runtime_root_sha256"],
          "install_receipt_manifest_sha256": rec["installed_runtime_manifest_sha256"],
          "install_source_commit": rec["full_commit_sha"]}
    v = load_validator("validate_theme_identity")
    code, rep = v.validate(html, expected_chapters=6, usage_out=tmp_path / "u.json",
                           exec_evidence=ev, lock_entry=le, network_mode="live")
    assert code == 0 and rep["THEME_IDENTITY"] == "PASS", rep


# ---------------- d/e/f: tampered bundle => install FAILs, no receipt ----------------

def _assert_failed(report, target):
    assert report["ok"] is False
    gzh = next(a for a in report["plan"] if a["skill"] == "gzh-design")
    assert gzh["installed"] is False and gzh.get("error")
    assert SD.read_install_receipt(target, "gzh-design") is None


def test_d_tampered_bundle_commit_fails(tmp_path, monkeypatch):
    def tamper(bundle):  # hand-edited proof WITHOUT manifest rebuild
        p = bundle / "source-proofs.json"
        p.write_text(p.read_text(encoding="utf-8").replace(COMMIT, "f" * 40),
                     encoding="utf-8")
    report, target, _ = _install(tmp_path, monkeypatch, mutate=tamper)
    _assert_failed(report, target)


def test_d2_tampered_commit_with_rebuilt_manifest_still_fails(tmp_path, monkeypatch):
    def tamper(bundle):  # consistently rebuilt manifest — still != lock commit
        p = bundle / "source-proofs.json"
        p.write_text(p.read_text(encoding="utf-8").replace(COMMIT, "f" * 40),
                     encoding="utf-8")
        _rebuild_manifest(bundle)
    report, target, _ = _install(tmp_path, monkeypatch, mutate=tamper)
    _assert_failed(report, target)


def test_e_tampered_repository_url_fails(tmp_path, monkeypatch):
    def tamper(bundle):
        p = bundle / "source-proofs.json"
        p.write_text(p.read_text(encoding="utf-8").replace(
            REPO_URL, "https://evil.example/clone"), encoding="utf-8")
        _rebuild_manifest(bundle)
    report, target, _ = _install(tmp_path, monkeypatch, mutate=tamper)
    _assert_failed(report, target)


def test_f_tampered_runtime_file_fails(tmp_path, monkeypatch):
    def tamper(bundle):  # runtime bytes differ from the manifest-bound sha
        f = bundle / "locked-skills" / "gzh-design" / "scripts" / "render_article.py"
        f.write_text("# TAMPERED entry\n", encoding="utf-8")
    report, target, _ = _install(tmp_path, monkeypatch, mutate=tamper)
    _assert_failed(report, target)


def test_f2_tampered_runtime_file_with_rebuilt_manifest_still_fails(tmp_path, monkeypatch):
    def tamper(bundle):  # even a consistent manifest cannot beat the LOCK hashes
        f = bundle / "locked-skills" / "gzh-design" / "scripts" / "render_article.py"
        f.write_text("# TAMPERED entry\n", encoding="utf-8")
        _rebuild_manifest(bundle)
    report, target, _ = _install(tmp_path, monkeypatch, mutate=tamper)
    _assert_failed(report, target)


# ---------------- g: missing / corrupt receipt => live theme FAILs ----------------

def test_g_missing_or_corrupt_receipt_live_theme_fails(tmp_path, monkeypatch):
    report, target, lock = _install(tmp_path, monkeypatch)
    le = lock["skills"]["gzh-design"]
    g = target / "gzh-design"
    root_sha, _ = SD.compute_root_sha(g)
    man_sha, _ = SD.compute_runtime_manifest_sha(g)
    html = (SKILL_ROOT / "fixtures" / "offline_pipeline_fixture" / "gzh_design" /
            "outputs" / "final.html")
    v = load_validator("validate_theme_identity")

    def _ev(rec):
        return {"official_gzh_call": True,
                "render_entry_path": str(g / "scripts" / "render_article.py"),
                "entry_sha256": _nsha(g / "scripts" / "render_article.py"),
                "component_source_path": str(g / "scripts" / "generate_hammer_upgrade_samples.py"),
                "installed_root_sha256": root_sha,
                "installed_runtime_manifest_sha256": man_sha,
                "install_receipt_root_sha256": (rec or {}).get("installed_runtime_root_sha256"),
                "install_receipt_manifest_sha256": (rec or {}).get("installed_runtime_manifest_sha256"),
                "install_source_commit": (rec or {}).get("full_commit_sha")}

    # receipt MISSING -> FAIL
    SD.install_receipt_path(target, "gzh-design").unlink()
    code1, rep1 = v.validate(html, expected_chapters=6, usage_out=tmp_path / "u1.json",
                             exec_evidence=_ev(SD.read_install_receipt(target, "gzh-design")),
                             lock_entry=le, network_mode="live")
    assert code1 == 1 and rep1["THEME_IDENTITY"] == "FAIL"
    # receipt CORRUPT (tampered root) -> FAIL
    p = SD.install_receipt_path(target, "gzh-design")
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps({"full_commit_sha": le["full_commit_sha"],
                             "installed_runtime_root_sha256": "9" * 64,
                             "installed_runtime_manifest_sha256": "9" * 64}),
                 encoding="utf-8")
    code2, rep2 = v.validate(html, expected_chapters=6, usage_out=tmp_path / "u2.json",
                             exec_evidence=_ev(SD.read_install_receipt(target, "gzh-design")),
                             lock_entry=le, network_mode="live")
    assert code2 == 1 and rep2["THEME_IDENTITY"] == "FAIL"
