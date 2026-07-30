#!/usr/bin/env python3
"""Build the two deliverable ZIPs (reproducible):
  1. wxgzh-pipeline-v0.1.0-dev1.zip                 (orchestrator skill only)
  2. wxgzh-pipeline-portable-bundle-v0.1.0-dev1.zip (installer + skill + locked sub-skills)

The bundle excludes .env / secrets / *.zip / caches. A secrets scan runs before
zipping and fails the build on any credential-form hit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))
from wxgzh_pipeline import __version__            # noqa: E402
from wxgzh_pipeline import paths as P             # noqa: E402
from wxgzh_pipeline import skill_discovery as SD  # noqa: E402
from wxgzh_pipeline import secrets as SEC         # noqa: E402
from wxgzh_pipeline.zipping import (  # noqa: E402
    PIPELINE_RELEASE_EXCLUDES, PIPELINE_RELEASE_INCLUDES,
    copy_tree, deterministic_zip)

EXPECTED_PIPELINE_FILE_COUNT = 130
EXPECTED_MANIFEST_FILE_COUNT = 665
EXPECTED_BUNDLE_ZIP_FILE_COUNT = 666

INSTALL_MD = {
    "INSTALL_WINDOWS.md": "# 安装（Windows）\n\n```powershell\npython installer\\install.py --dry-run\npython installer\\install.py   # 实际安装\npython .agents\\skills\\wxgzh-pipeline\\scripts\\doctor.py --offline\n```\n\n复制 config.example.env 为项目根 .env 填入 WECHAT_APP_ID/WECHAT_APP_SECRET。\n日常：`发文：<选题>`。\n",
    "INSTALL_MACOS.md": "# 安装（macOS）\n\n```bash\npython3 installer/install.py --dry-run\npython3 installer/install.py\npython3 .agents/skills/wxgzh-pipeline/scripts/doctor.py --offline\n```\n\ncp config.example.env <项目根>/.env 并填入凭据。日常：`发文：<选题>`。\n",
    "INSTALL_LINUX.md": "# 安装（Linux）\n\n```bash\npython3 installer/install.py --dry-run\npython3 installer/install.py\npython3 .agents/skills/wxgzh-pipeline/scripts/doctor.py --offline\n```\n\ncp config.example.env <项目根>/.env 并填入凭据。日常：`发文：<选题>`。\n",
}


def _zip_file_map(z: zipfile.ZipFile, prefix: str) -> dict:
    result = {}
    for info in z.infolist():
        if info.is_dir() or not info.filename.startswith(prefix):
            continue
        rel = info.filename[len(prefix):]
        data = z.read(info.filename)
        result[rel] = {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    return result


def _run_shipped_workflow_test(root: Path) -> dict:
    command = [sys.executable, "-m", "pytest",
               "tests/test_hotfix7_live_handshake.py::test_integration_workflow_fails_closed_after_tee",
               "-q", "-o", "addopts="]
    proc = subprocess.run(command, cwd=root, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise SystemExit(f"shipped workflow test failed in {root}:\n{proc.stdout}\n{proc.stderr}")
    return {"command": command, "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}


def verify_release_artifacts(skill_zip: Path, bundle_zip: Path, extract_root: Path) -> dict:
    """Fail closed unless both release archives are self-consistent."""
    workflow_rel = ".github/workflows/ci.yml"
    skill_prefix = "wxgzh-pipeline/"
    bundle_pipeline_prefix = "portable-bundle/wxgzh-pipeline/"
    with zipfile.ZipFile(skill_zip) as skill_z, zipfile.ZipFile(bundle_zip) as bundle_z:
        skill_tree = _zip_file_map(skill_z, skill_prefix)
        bundle_tree = _zip_file_map(bundle_z, bundle_pipeline_prefix)
        if skill_tree != bundle_tree:
            raise SystemExit("pipeline ZIP tree differs from portable bundle pipeline tree")
        if len(skill_tree) != EXPECTED_PIPELINE_FILE_COUNT:
            raise SystemExit(f"unexpected pipeline file count: {len(skill_tree)}")
        sw = skill_z.read(skill_prefix + workflow_rel)
        bw = bundle_z.read(bundle_pipeline_prefix + workflow_rel)
        source = (SKILL_ROOT / workflow_rel).read_bytes()
        if not (sw == bw == source):
            raise SystemExit("CI workflow bytes differ between source and release archives")
        manifest = json.loads(bundle_z.read("portable-bundle/MANIFEST.json"))
        if manifest.get("file_count") != EXPECTED_MANIFEST_FILE_COUNT:
            raise SystemExit(f"unexpected manifest file_count: {manifest.get('file_count')}")
        bundle_files = [i for i in bundle_z.infolist() if not i.is_dir()]
        if len(bundle_files) != EXPECTED_BUNDLE_ZIP_FILE_COUNT:
            raise SystemExit(f"unexpected bundle ZIP file count: {len(bundle_files)}")
        manifest_paths = {item["path"] for item in manifest.get("files", [])}
        workflow_manifest_path = "wxgzh-pipeline/" + workflow_rel
        if workflow_manifest_path not in manifest_paths:
            raise SystemExit("portable MANIFEST does not cover CI workflow")
        manifest_errors = []
        for item in manifest["files"]:
            data = bundle_z.read("portable-bundle/" + item["path"])
            if len(data) != item["size"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
                manifest_errors.append(item["path"])
        if manifest_errors:
            raise SystemExit(f"portable MANIFEST mismatch: {manifest_errors}")
        skill_z.extractall(extract_root / "skill")
        bundle_z.extractall(extract_root / "bundle")
    skill_test = _run_shipped_workflow_test(extract_root / "skill" / "wxgzh-pipeline")
    bundle_test = _run_shipped_workflow_test(
        extract_root / "bundle" / "portable-bundle" / "wxgzh-pipeline")
    return {
        "pipeline_file_count": len(skill_tree),
        "manifest_file_count": manifest["file_count"],
        "bundle_zip_file_count": len(bundle_files),
        "workflow_size": len(source),
        "workflow_sha256": hashlib.sha256(source).hexdigest(),
        "pipeline_trees_equal": True,
        "manifest_verified": True,
        "skill_zip_test": skill_test,
        "bundle_zip_test": bundle_test,
    }


def build(out_dir: Path, skills_home: Path, staging: Path) -> dict:
    # Validate the complete lock set before creating output/staging or copying a
    # single byte. A missing locked Skill must leave no partial bundle, MANIFEST,
    # or ZIP behind.
    lock = SD.load_lock(SKILL_ROOT)
    expected_skills = {
        name for name, meta in lock["skills"].items()
        if meta.get("kind") != "agent_invoked_skill"
    }
    missing_sources = sorted(
        name for name in expected_skills if not (Path(skills_home) / name).is_dir())
    if missing_sources:
        raise SystemExit(
            f"locked skill source directories missing: {missing_sources} — bundle not generated")

    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    if staging.exists():
        shutil.rmtree(staging)
    bundle = staging / "portable-bundle"
    bundle.mkdir(parents=True)

    # 1. orchestrator skill. Include the exact CI workflow because a shipped
    # regression test reads it; all other .github content remains excluded.
    copy_tree(SKILL_ROOT, bundle / "wxgzh-pipeline",
              include_paths=PIPELINE_RELEASE_INCLUDES,
              exclude_paths=PIPELINE_RELEASE_EXCLUDES)
    # 2. installer
    (bundle / "installer").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SKILL_ROOT / "scripts" / "install.py", bundle / "installer" / "install.py")
    # 3. locked sub-skills (file skills only; aihot is agent-invoked)
    locked_counts = {}
    for name in sorted(expected_skills):
        locked_counts[name] = copy_tree(
            Path(skills_home) / name, bundle / "locked-skills" / name)
    actual_skills = {
        path.name for path in (bundle / "locked-skills").iterdir() if path.is_dir()
    }
    if actual_skills != expected_skills:
        raise SystemExit(
            f"locked-skills set mismatch: expected={sorted(expected_skills)} "
            f"actual={sorted(actual_skills)}")
    # 4. lock + config + install docs
    shutil.copyfile(SKILL_ROOT / "skills.lock.json", bundle / "skills.lock.json")
    shutil.copyfile(SKILL_ROOT / "config.example.env", bundle / "config.example.env")
    for name, text in INSTALL_MD.items():
        (bundle / name).write_text(text, encoding="utf-8")

    # 4b. P0#1 (hotfix4): BUILD-generated per-skill source proofs. The file is a
    # regular bundle member, so the bundle MANIFEST (step 6) hash-binds it — the
    # installer rejects any hand-written / tampered proof.
    proofs = {name: {"repository_url": meta.get("repository_url"),
                     "full_commit_sha": meta.get("full_commit_sha"),
                     "source_tree_sha": meta.get("source_tree_sha")}
              for name, meta in lock["skills"].items()
              if meta.get("kind") != "agent_invoked_skill"}
    (bundle / "source-proofs.json").write_text(json.dumps(
        {"generated_by": f"build_portable_bundle/{__version__}", "skills": proofs},
        ensure_ascii=False, indent=2), encoding="utf-8")

    # 5. secrets scan (must be clean) — bundle must not contain .env / real creds
    scan = SEC.scan_tree(bundle, SEC.load_env_values(P.resolve_project_root() / ".env"))
    if scan["secrets_detected"]:
        raise SystemExit(f"secrets detected in bundle: {scan['hits']}")

    # 6. bundle MANIFEST
    files = []
    for p in sorted(bundle.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.json":
            b = p.read_bytes()
            files.append({"path": p.relative_to(bundle).as_posix(), "size": len(b),
                          "sha256": hashlib.sha256(b).hexdigest()})
    (bundle / "MANIFEST.json").write_text(json.dumps(
        {"artifact": f"wxgzh-pipeline-portable-bundle-v{__version__}", "file_count": len(files),
         "locked_skill_file_counts": locked_counts, "files": files},
        ensure_ascii=False, indent=2), encoding="utf-8")

    # 7. zips (reproducible)
    skill_zip = out_dir / f"wxgzh-pipeline-v{__version__}.zip"
    bundle_zip = out_dir / f"wxgzh-pipeline-portable-bundle-v{__version__}.zip"
    skill_sha = deterministic_zip(
        SKILL_ROOT, skill_zip, arc_prefix="wxgzh-pipeline",
        include_paths=PIPELINE_RELEASE_INCLUDES,
        exclude_paths=PIPELINE_RELEASE_EXCLUDES)
    bundle_sha = deterministic_zip(
        bundle, bundle_zip, arc_prefix="portable-bundle",
        include_paths=("wxgzh-pipeline/.github/workflows/ci.yml",))
    artifact_check = verify_release_artifacts(skill_zip, bundle_zip, staging / "artifact-check")
    return {"skill_zip": str(skill_zip), "skill_zip_sha256": skill_sha,
            "bundle_zip": str(bundle_zip), "bundle_zip_sha256": bundle_sha,
            "locked_skill_file_counts": locked_counts, "secrets_detected": False,
            "artifact_check": artifact_check}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--skills-home", default=None)
    ap.add_argument("--staging", default=None)
    a = ap.parse_args(argv)
    pr = P.resolve_project_root()
    out = Path(a.out) if a.out else pr
    sh = Path(a.skills_home) if a.skills_home else P.skills_home(pr)
    staging = Path(a.staging) if a.staging else (pr / ".temp" / "wxgzh-pipeline-build" / "bundle-staging")
    report = build(out, sh, staging)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
