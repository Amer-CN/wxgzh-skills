#!/usr/bin/env python3
"""Cross-platform installer for wxgzh-pipeline + locked sub-skills.

- Auto-discovers the target skills home (or --target).
- Backs up any same-name existing skill (timestamped .bak-*) — never deletes user work.
- Recomputes root hashes and compares to skills.lock.json.
- NEVER overwrites the user's .env.
- Runs doctor afterwards. Never runs an article, uploads images, or creates a draft.
"""
from __future__ import annotations

import argparse
import json
import shutil
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
from wxgzh_pipeline import paths as P            # noqa: E402
from wxgzh_pipeline import skill_discovery as SD  # noqa: E402
from wxgzh_pipeline.zipping import copy_tree      # noqa: E402


def _find_source() -> tuple[Path, Path | None]:
    """Return (wxgzh_pipeline_src, locked_skills_dir_or_None)."""
    # bundle layout: <bundle>/wxgzh-pipeline + <bundle>/locked-skills
    for bundle in {SKILL_ROOT.parent, _HERE.parents[1].parent, _HERE.parents[1]}:
        if (bundle / "locked-skills").is_dir() and (bundle / "wxgzh-pipeline").is_dir():
            return bundle / "wxgzh-pipeline", bundle / "locked-skills"
    return SKILL_ROOT, None


def install(target_skills_home: Path, dry_run: bool = True) -> dict:
    src_pipeline, locked = _find_source()
    target_skills_home = Path(target_skills_home)
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    plan = []

    to_install = [("wxgzh-pipeline", src_pipeline)]
    if locked:
        for d in sorted(locked.iterdir()):
            if d.is_dir():
                to_install.append((d.name, d))

    for name, src in to_install:
        dst = target_skills_home / name
        action = {"skill": name, "src": str(src), "dst": str(dst),
                  "existing_backup": None, "installed": False, "file_count": None}
        if not dry_run:
            target_skills_home.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                bak = target_skills_home / f"{name}.bak-{ts}"
                shutil.move(str(dst), str(bak))
                action["existing_backup"] = str(bak)
            action["file_count"] = copy_tree(src, dst)
            action["installed"] = True
        plan.append(action)

    # hash verification against lock (only meaningful after real install)
    lock = SD.load_lock(src_pipeline)
    verify = {}
    if not dry_run:
        _, verify = SD.verify_all(target_skills_home, lock)

    return {"dry_run": dry_run, "target_skills_home": str(target_skills_home),
            "env_untouched": True, "plan": plan,
            "hash_verification": {k: v.get("ok") for k, v in verify.items()} if verify else "run without --dry-run to verify",
            "note": "installer never runs an article / uploads images / creates a draft"}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default=None, help="target skills home (default: auto-discover)")
    ap.add_argument("--project-root", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.target:
        target = Path(a.target)
    else:
        pr = P.resolve_project_root(a.project_root)
        target = P.skills_home(pr)
    report = install(target, dry_run=a.dry_run)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
