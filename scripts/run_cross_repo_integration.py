#!/usr/bin/env python3
"""Cross-repo integration runner (P0#7).

Installs the four sub-skill PR trees into a temporary skills_home, registers a
verifiable AI HOT registration manifest, then:
  - verify_all + doctor against the freshly "installed" skills;
  - the real sub-skill CLI --help (proves the pipeline's argv is compatible);
  - a minimal offline fixture render (render_article on a tiny article);
Writes an integration result JSON (ran / exit_code / details) to --result.

NO real network, NO WeChat side effects. Intended for the CI integration job
(WXGZH_SUBSKILL_CLONES points at the checked-out PR trees).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from wxgzh_pipeline import skill_discovery as SD  # noqa: E402

CLONE_TO_SKILL = {"super-writer": "super-writer", "zh-human-writing": "zh-human-writing",
                  "media-enrichment": "media-enrichment", "gzh-design-skill": "gzh-design"}

CLI_HELP = {
    "media-enrichment": ["scripts/run_media_enrichment.py", "scripts/validate_media_manifest.py"],
    "gzh-design": ["scripts/render_article.py", "scripts/validate_gzh_html.py",
                   "scripts/publish_wechat_draft.py"],
    "super-writer": ["scripts/material_ingestion.py", "scripts/validate_article_length.py",
                     "scripts/validate_semantic_map.py"],
    "zh-human-writing": ["scripts/fidelity_guard.py", "scripts/pattern_audit.py",
                         "scripts/change_report.py"],
}


def _run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=120, **kw)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--clones", default=os.environ.get("WXGZH_SUBSKILL_CLONES"))
    ap.add_argument("--result", required=True)
    a = ap.parse_args(argv)
    details: dict = {"checks": {}}
    ok = True

    def record(name, passed, info=""):
        nonlocal ok
        details["checks"][name] = {"ok": bool(passed), "info": info}
        ok = ok and bool(passed)

    if not a.clones or not Path(a.clones).is_dir():
        details["error"] = "WXGZH_SUBSKILL_CLONES not set / not a dir"
        _write(a.result, {"ran": False, "exit_code": None, **details})
        return 2

    clones = Path(a.clones)
    staging = Path(tempfile.mkdtemp(prefix="wxgzh-integ-"))
    skills_home = staging / "skills"
    skills_home.mkdir(parents=True)
    for clone_name, skill_name in CLONE_TO_SKILL.items():
        src = clones / clone_name
        if not src.is_dir():
            record(f"clone_present:{clone_name}", False, "missing")
            continue
        shutil.copytree(src, skills_home / skill_name,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
        record(f"installed:{skill_name}", True)

    # verifiable AI HOT registration (declares name + output contract + discoverable)
    aihot = skills_home / "aihot"
    aihot.mkdir(exist_ok=True)
    (aihot / "SKILL.md").write_text("---\nname: aihot\n---\n", encoding="utf-8")
    (aihot / "registration.json").write_text(json.dumps(
        {"name": "aihot", "identifier": "aihot", "discoverable": True,
         "output_contract": {"items": "array of AI HOT entries"}}), encoding="utf-8")
    env = dict(os.environ)
    env["WXGZH_AIHOT_SKILL_DIR"] = str(aihot)

    # verify_all against the freshly installed PR trees (uses the shipped lock)
    lock = SD.load_lock(REPO)
    vok, disc = SD.verify_all(skills_home, lock, env=env)
    bad = {k: v for k, v in disc.items() if not v.get("ok")}
    record("verify_all", vok, json.dumps(bad, ensure_ascii=False)[:400])
    if not vok:
        # dump per-file runtime hashes for the failing skills (cross-platform debug)
        dbg = {}
        for k in bad:
            sk = skills_home / k
            files = SD._runtime_files(sk)
            dbg[k] = {"root": SD.compute_root_sha(sk)[0],
                      "files": {p.relative_to(sk).as_posix(): SD._file_sha(p) for p in files}}
        details["hash_debug"] = dbg

    # real CLI --help for every entry the pipeline invokes
    for skill, scripts in CLI_HELP.items():
        for rel in scripts:
            p = skills_home / skill / rel
            if not p.is_file():
                record(f"help:{skill}/{Path(rel).name}", False, "missing")
                continue
            r = _run([sys.executable, "-X", "utf8", str(p), "--help"])
            record(f"help:{skill}/{Path(rel).name}", r.returncode == 0, r.stderr[:200])

    # minimal offline render via the REAL gzh render_article
    render = skills_home / "gzh-design" / "scripts" / "render_article.py"
    if render.is_file():
        art = staging / "a.md"
        art.write_text("# 标题\n\n## 一\n\n正文一。\n\n## 二\n\n正文二。\n", encoding="utf-8")
        out = staging / "gzh"
        r = _run([sys.executable, "-X", "utf8", str(render), "--article", str(art),
                  "--output-dir", str(out), "--theme", "smartisan"])
        record("render_article_offline", r.returncode == 0 and (out / "final.html").is_file(),
               r.stderr[:200])

    result = {"ran": True, "exit_code": 0 if ok else 1, **details}
    _write(a.result, result)
    print(f"[cross-repo-integration] ok={ok} checks={len(details['checks'])}")
    return 0 if ok else 1


def _write(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
