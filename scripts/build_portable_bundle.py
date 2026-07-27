#!/usr/bin/env python3
"""Build the two deliverable ZIPs (reproducible):
  1. wxgzh-pipeline-v0.1.0-dev1.zip                 (orchestrator skill only)
  2. wxgzh-pipeline-portable-bundle-v0.1.0-dev1.zip (installer + skill + locked sub-skills)

The bundle excludes .env / secrets / *.zip / caches. A secrets scan runs before
zipping and fails the build on any credential-form hit.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))
from wxgzh_pipeline import __version__            # noqa: E402
from wxgzh_pipeline import paths as P             # noqa: E402
from wxgzh_pipeline import skill_discovery as SD  # noqa: E402
from wxgzh_pipeline import secrets as SEC         # noqa: E402
from wxgzh_pipeline.zipping import copy_tree, deterministic_zip  # noqa: E402

INSTALL_MD = {
    "INSTALL_WINDOWS.md": "# 安装（Windows）\n\n```powershell\npython installer\\install.py --dry-run\npython installer\\install.py   # 实际安装\npython .agents\\skills\\wxgzh-pipeline\\scripts\\doctor.py --offline\n```\n\n复制 config.example.env 为项目根 .env 填入 WECHAT_APP_ID/WECHAT_APP_SECRET。\n日常：`发文：<选题>`。\n",
    "INSTALL_MACOS.md": "# 安装（macOS）\n\n```bash\npython3 installer/install.py --dry-run\npython3 installer/install.py\npython3 .agents/skills/wxgzh-pipeline/scripts/doctor.py --offline\n```\n\ncp config.example.env <项目根>/.env 并填入凭据。日常：`发文：<选题>`。\n",
    "INSTALL_LINUX.md": "# 安装（Linux）\n\n```bash\npython3 installer/install.py --dry-run\npython3 installer/install.py\npython3 .agents/skills/wxgzh-pipeline/scripts/doctor.py --offline\n```\n\ncp config.example.env <项目根>/.env 并填入凭据。日常：`发文：<选题>`。\n",
}


def build(out_dir: Path, skills_home: Path, staging: Path) -> dict:
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    if staging.exists():
        shutil.rmtree(staging)
    bundle = staging / "portable-bundle"
    bundle.mkdir(parents=True)

    # 1. orchestrator skill
    copy_tree(SKILL_ROOT, bundle / "wxgzh-pipeline")
    # 2. installer
    (bundle / "installer").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SKILL_ROOT / "scripts" / "install.py", bundle / "installer" / "install.py")
    # 3. locked sub-skills (file skills only; aihot is agent-invoked)
    lock = SD.load_lock(SKILL_ROOT)
    locked_counts = {}
    for name, meta in lock["skills"].items():
        if meta.get("kind") == "agent_invoked_skill":
            continue
        src = Path(skills_home) / name
        if src.is_dir():
            locked_counts[name] = copy_tree(src, bundle / "locked-skills" / name)
    # 4. lock + config + install docs
    shutil.copyfile(SKILL_ROOT / "skills.lock.json", bundle / "skills.lock.json")
    shutil.copyfile(SKILL_ROOT / "config.example.env", bundle / "config.example.env")
    for name, text in INSTALL_MD.items():
        (bundle / name).write_text(text, encoding="utf-8")

    # 5. secrets scan (must be clean) — bundle must not contain .env / real creds
    scan = SEC.scan_tree(bundle, SEC.load_env_values(P.resolve_project_root() / ".env"))
    if scan["secrets_detected"]:
        raise SystemExit(f"secrets detected in bundle: {scan['hits']}")

    # 6. bundle MANIFEST
    import hashlib
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
    skill_sha = deterministic_zip(SKILL_ROOT, skill_zip, arc_prefix="wxgzh-pipeline")
    bundle_sha = deterministic_zip(bundle, bundle_zip, arc_prefix="portable-bundle")
    return {"skill_zip": str(skill_zip), "skill_zip_sha256": skill_sha,
            "bundle_zip": str(bundle_zip), "bundle_zip_sha256": bundle_sha,
            "locked_skill_file_counts": locked_counts, "secrets_detected": False}


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
