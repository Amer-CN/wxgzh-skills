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

# OBS-65(档71B'-C):文件计数常量过时(130 vs 实算 660)且与仓库演进脱节。
# 改为动态实算:EXPECTED_* 由构建时实际产物推导,不再写死(写死数字曾导致
# 「报错却继续」——校验失败仍产出 staging,安装器照常运行)。
# 8c 悖论检查:先「实算 + 打印」,在档 71B'-C 第 10 步 bundle 重建实测一致后,
# 再启用 fail-closed(见 _enforce_expected_counts)。

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


# OBS-65(档71B'-C):动态实算 + 可选 fail-closed。
# 8c 悖论检查:实算值来自构建产物自身(同一 zip 解出的文件集合),若与磁盘
# 集合不一致,说明拷贝/打包环节有真实偏差 —— 这正是要拦截的「报错却继续」。
# 8c/8d:第 10 步 bundle 重建实测一致(660/1228/1230),启用 fail-closed。
# 若未来产物自洽性被破坏(计数失配),构建将非 0 退出,不再「报错却继续」。
_EXPECTED_ENFORCE = True


def _mode_enforce() -> bool:
    return _EXPECTED_ENFORCE


def _enforce_expected_counts(pipeline_count: int, manifest_count: int,
                             bundle_count: int, enforce: bool,
                             skip_count: int = 0,
                             skip_names: list[str] | None = None) -> None:
    """动态实算校验:以构建产物自身计数为基线,拒绝写死常量。"""
    print(f"[build] 实算计数: pipeline={pipeline_count} manifest={manifest_count} "
          f"bundle_zip={bundle_count} enforce={enforce}")
    if not enforce:
        return
    # fail-closed 语义(OBS-116):manifest 记录文件数 == bundle zip 实际文件数
    # − skip_count。skip_count = bundle 中名为 MANIFEST.json 的条目数(同名文件
    # 可能有多个,如顶层与 audit/runs/*/ 内嵌),随仓库演进动态统计,禁止写死。
    if manifest_count != bundle_count - skip_count:
        raise SystemExit(
            f"manifest count mismatch: manifest={manifest_count} "
            f"bundle_zip={bundle_count} skip_count={skip_count} "
            f"skip_names={skip_names or []}")
    # OBS-117(档71C-2):由「比 count」升级为「比 set」——磁盘独立枚举集合与
    # zip 内条目集合的双向差集校验在 verify_release_artifacts 内执行
    # (only_in_disk / only_in_zip 全清单,任一非空即 SystemExit)。


def _disk_enum_set() -> set[str]:
    """OBS-117(档71C-2):按 PIPELINE_RELEASE_INCLUDES/EXCLUDES 独立枚举磁盘
    release 文件相对路径集合。

    与 zipping._skip 的排除语义保持一致但不复用其函数(独立实现,防「同一份
    代码两个副本」与「校验与被校验同源」)。"""
    from wxgzh_pipeline import zipping as _zip_mod
    src = SKILL_ROOT
    result = set()
    for p in sorted(src.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(src)
        posix = rel.as_posix()
        if posix in {Path(x).as_posix() for x in _zip_mod.PIPELINE_RELEASE_EXCLUDES}:
            continue
        if posix in {Path(x).as_posix() for x in _zip_mod.PIPELINE_RELEASE_INCLUDES}:
            result.add(posix)
            continue
        if any(part in _zip_mod.EXCLUDE_DIRS for part in p.parts):
            continue
        if p.suffix.lower() in _zip_mod.EXCLUDE_SUFFIXES or p.name in _zip_mod.FORBIDDEN_NAMES:
            continue
        result.add(posix)
    return result


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
        sw = skill_z.read(skill_prefix + workflow_rel)
        bw = bundle_z.read(bundle_pipeline_prefix + workflow_rel)
        source = (SKILL_ROOT / workflow_rel).read_bytes()
        if not (sw == bw == source):
            raise SystemExit("CI workflow bytes differ between source and release archives")
        manifest = json.loads(bundle_z.read("portable-bundle/MANIFEST.json"))
        bundle_files = [i for i in bundle_z.infolist() if not i.is_dir()]
        # OBS-65:动态实算校验(见 _enforce_expected_counts;常量已废除)
        # 5a(OBS-116):失败信息补全 —— 记录 skip_names 全清单,失配时逐条打印。
        skip_names = sorted({
            Path(i.filename).as_posix()
            for i in bundle_z.infolist()
            if not i.is_dir() and Path(i.filename).name == "MANIFEST.json"
        })
        skip_count = len(skip_names)
        _enforce_expected_counts(len(skill_tree), len(manifest.get("files", [])),
                                 len(bundle_files), _mode_enforce(), skip_count,
                                 skip_names)
        # 5b(OBS-117):磁盘独立枚举集合 vs zip 条目集合,双向差集任一非空即失败。
        disk_set = _disk_enum_set()
        zip_set = set(skill_tree)
        only_in_disk = sorted(disk_set - zip_set)
        only_in_zip = sorted(zip_set - disk_set)
        if only_in_disk or only_in_zip:
            raise SystemExit(
                f"pipeline/disk set mismatch: only_in_disk={only_in_disk} "
                f"only_in_zip={only_in_zip}")
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
