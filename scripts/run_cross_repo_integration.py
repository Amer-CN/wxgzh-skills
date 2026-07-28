#!/usr/bin/env python3
"""Cross-repo integration runner (P0#4 + P0#7 + P0#1 live-proof).

Installs the four sub-skill trees (checked out at their EXACT locked commits)
into a temporary skills_home, then:
  - P0#4: verifies each clone's HEAD == skills.lock full_commit_sha
          (records repository / expected_commit / actual_commit / match);
  - P0#1: generates EXTERNAL install receipts from the real checkout
          (<skills_home>/.install-receipts/<skill>.json), fail-closed on mismatch;
  - verify_all + doctor against the freshly "installed" skills (P0#7);
  - the real sub-skill CLI --help (argv compatibility);
  - P0#1 live-proof: a REAL render_article + REAL validate_theme_identity that
          MUST return THEME_IDENTITY=PASS (official gzh call, hash-anchored).

NO real network, NO WeChat side effects. Writes an integration result JSON.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
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
                          errors="replace", timeout=180, **kw)


def _git(clone: Path, *args) -> str | None:
    if not (clone / ".git").exists():
        return None
    r = subprocess.run(["git", "-C", str(clone), *args], capture_output=True, text=True)
    return r.stdout.strip() or None


def _nsha(p: Path) -> str:
    d = p.read_bytes()
    if b"\x00" not in d:
        d = d.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(d).hexdigest()


def _load_validator(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "validators" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _live_proof_theme(skills_home: Path, gzh_lock: dict, staging: Path) -> dict:
    """P0#1: run the REAL gzh render_article on a full 6-chapter article + image
    bindings, then run the REAL validate_theme_identity in live mode. Requires an
    official, hash-anchored PASS (never a copied-HTML or lock-fields-only pass)."""
    fx = REPO / "fixtures" / "offline_pipeline_fixture"
    article = fx / "zh_human_writing" / "outputs" / "final_article.md"
    bindings = fx / "media_enrichment" / "outputs" / "article_image_bindings.json"
    gdir = skills_home / "gzh-design"
    render = gdir / "scripts" / "render_article.py"
    comp = gdir / "scripts" / "generate_hammer_upgrade_samples.py"
    out = staging / "liveproof"
    r = _run([sys.executable, "-X", "utf8", str(render), "--article", str(article),
              "--bindings", str(bindings), "--output-dir", str(out), "--theme", "smartisan"])
    final_html = out / "final.html"
    if r.returncode != 0 or not final_html.is_file():
        return {"THEME_IDENTITY": "FAIL", "reason": f"render failed: {r.stderr[:200]}"}
    root_sha, _ = SD.compute_root_sha(gdir)
    man_sha, _ = SD.compute_runtime_manifest_sha(gdir)
    receipt = SD.read_install_receipt(skills_home, "gzh-design") or {}
    ev = {"official_gzh_call": True,
          "render_entry_path": str(render), "entry_path": str(render),
          "entry_sha256": _nsha(render),
          "component_source_path": str(comp),
          "installed_root_sha256": root_sha,
          "installed_runtime_manifest_sha256": man_sha,
          "install_receipt_root_sha256": receipt.get("installed_runtime_root_sha256"),
          "install_receipt_manifest_sha256": receipt.get("installed_runtime_manifest_sha256"),
          "install_source_commit": receipt.get("full_commit_sha")}
    chapters = sum(1 for ln in article.read_text(encoding="utf-8").splitlines()
                   if ln.startswith("## "))
    vti = _load_validator("validate_theme_identity")
    code, rep = vti.validate(final_html, expected_chapters=chapters, exec_evidence=ev,
                             lock_entry=gzh_lock, network_mode="live",
                             usage_out=out / "component_usage_report.json")
    keys = ("THEME_IDENTITY", "structure_ok", "OFFICIAL_GZH_CALL",
            "RENDER_ENTRY_HASH_MATCHES_LOCK", "COMPONENT_SOURCE_HASH_MATCHES_LOCK",
            "INSTALLED_ROOT_MATCHES_LOCK", "RUNTIME_MANIFEST_MATCHES_LOCK",
            "INSTALL_SOURCE_COMMIT_MATCHES_LOCK", "INSTALL_RECEIPT_PRESENT",
            "INSTALL_RECEIPT_ROOT_MATCHES", "HAMMER_CHAPTER_TITLE_COUNT")
    return {k: rep.get(k) for k in keys}


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
    lock = SD.load_lock(REPO)
    lock_skills = lock.get("skills", {})
    staging = Path(tempfile.mkdtemp(prefix="wxgzh-integ-"))
    skills_home = staging / "skills"
    skills_home.mkdir(parents=True)

    # ── P0#4: pin + VERIFY each clone is at the EXACT locked full commit ──
    commit_checks = []
    for clone_name, skill_name in CLONE_TO_SKILL.items():
        clone = clones / clone_name
        locked = (lock_skills.get(skill_name) or {}).get("full_commit_sha")
        actual = _git(clone, "rev-parse", "HEAD")
        match = bool(locked and actual and actual == locked)
        commit_checks.append({"repository": skill_name, "clone": clone_name,
                              "expected_commit": locked, "actual_commit": actual,
                              "match": match})
        record(f"commit_match:{skill_name}", match, f"expected={locked} actual={actual}")
    details["commit_verification"] = commit_checks

    # install the (verified) trees + a verifiable AI HOT registration
    for clone_name, skill_name in CLONE_TO_SKILL.items():
        src = clones / clone_name
        if not src.is_dir():
            record(f"clone_present:{clone_name}", False, "missing")
            continue
        shutil.copytree(src, skills_home / skill_name,
                        ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache"))
        record(f"installed:{skill_name}", True)
    aihot = skills_home / "aihot"
    aihot.mkdir(exist_ok=True)
    (aihot / "SKILL.md").write_text("---\nname: aihot\n---\n", encoding="utf-8")
    (aihot / "registration.json").write_text(json.dumps(
        {"name": "aihot", "identifier": "aihot", "discoverable": True,
         "output_contract": {"items": "array of AI HOT entries"}}), encoding="utf-8")
    env = dict(os.environ)
    env["WXGZH_AIHOT_SKILL_DIR"] = str(aihot)

    # ── P0#1: EXTERNAL install receipts generated from the real checkout ──
    for clone_name, skill_name in CLONE_TO_SKILL.items():
        clone = clones / clone_name
        le = lock_skills.get(skill_name) or {}
        actual = _git(clone, "rev-parse", "HEAD")
        tree = _git(clone, "rev-parse", "HEAD^{tree}")
        try:
            SD.write_install_receipt(
                skills_home, skill_name, repository_url=le.get("repository_url", ""),
                actual_commit=actual or "", expected_commit=le.get("full_commit_sha"),
                source_tree_sha=tree, installer_version="wxgzh-integration/0.1.0-dev2-hotfix3")
            record(f"install_receipt:{skill_name}", True)
        except SD.InstallReceiptError as e:
            record(f"install_receipt:{skill_name}", False, str(e))

    # verify_all against the freshly installed trees (uses the shipped lock)
    vok, disc = SD.verify_all(skills_home, lock, env=env)
    bad = {k: v for k, v in disc.items() if not v.get("ok")}
    record("verify_all", vok, json.dumps(bad, ensure_ascii=False)[:400])
    if not vok:
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

    # ── P0#1 live-proof: real render + real theme identity => must PASS ──
    theme = _live_proof_theme(skills_home, lock_skills.get("gzh-design", {}), staging)
    details["theme_identity"] = theme
    record("live_proof_theme_identity", theme.get("THEME_IDENTITY") == "PASS",
           str(theme.get("THEME_IDENTITY")))

    result = {"ran": True, "exit_code": 0 if ok else 1, **details}
    _write(a.result, result)
    print(f"[cross-repo-integration] ok={ok} checks={len(details['checks'])} "
          f"theme={theme.get('THEME_IDENTITY')}")
    return 0 if ok else 1


def _write(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
