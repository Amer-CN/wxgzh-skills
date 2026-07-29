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
from wxgzh_pipeline.orchestrator import Orchestrator  # noqa: E402
from wxgzh_pipeline.receipts import verify_receipt  # noqa: E402

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


def _single_asset_e2e(skills_home: Path, staging: Path) -> dict:
    """Run the REAL two-phase media CLI with stable single-asset approval.

    Discovery and continuation both use offline fixtures. Discovery must emit a
    frozen manifest without any upload event. The continuation approval is built
    from A-001's complete frozen identity and may upload only that asset through
    the deterministic wechat_audit uploader. No network or real WeChat effects.
    """
    media = skills_home / "media-enrichment"
    sa = staging / "single_asset_e2e"
    sa.mkdir(parents=True, exist_ok=True)
    article = sa / "final_article.md"
    article.write_text("# 标题\n\n示例论点一。\n\n正文说明两张图。\n", encoding="utf-8")
    src_url = "https://www.example-source.test/single-asset-e2e"
    req = {
        "schema_version": "1.0", "run_id": "integ-single-asset",
        "article": {"path": "final_article.md",
                    "sha256": hashlib.sha256(article.read_bytes()).hexdigest()},
        "materials": [{"material_id": "M-001",
                       "aihot_permalink": "https://aihot.virxact.com/items/single-asset-e2e",
                       "source_url": src_url, "title": "示例素材",
                       "selected_claim_ids": ["C-01"],
                       "copyright_review": {"status": "unknown"}}],
        "claims": [{"claim_id": "C-01", "claim_text": "示例论点一",
                    "material_id": "M-001", "source_url": src_url,
                    "source_excerpt": "原文摘录"}],
        "asset_approvals": [],
        "config": {"network_mode": "offline_fixture", "upload_mode": "wechat_audit",
                   "max_images_per_material": 3, "max_total_images": 8,
                   "allow_unknown_license_for_publish": False},
    }
    request_path = sa / "media_request.json"
    request_path.write_text(json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
    cli = media / "scripts" / "run_media_enrichment.py"
    fixture_dir = media / "fixtures" / "html"
    discover_out = sa / "discover-out"
    discover = _run([
        sys.executable, "-X", "utf8", str(cli),
        "--request", str(request_path), "--output-dir", str(discover_out),
        "--fixture-dir", str(fixture_dir), "--phase", "discover",
    ])
    res = {"discover_exit_code": discover.returncode}
    try:
        frozen_path = discover_out / "asset_discovery_manifest.json"
        frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
        discover_events = json.loads(
            (discover_out / "upload_events.json").read_text(encoding="utf-8"))
        target = next(
            asset for asset in frozen.get("assets", [])
            if asset.get("asset_id") == "A-001"
        )
    except (OSError, ValueError, StopIteration) as e:
        res["ok"] = False
        res["error"] = f"discovery outputs invalid: {e}; stderr={discover.stderr[-300:]}"
        return res

    approval = dict(target)
    approval.update({
        "discovery_manifest_sha256": frozen.get("discovery_manifest_sha256"),
        "approval_id": "AP-A-001", "approved_scope": "single_asset",
        "approved_by": "integration-user", "approved_at": "2026-07-29T00:00:00Z",
        "approval_evidence_sha256": "e" * 64,
    })
    stable_fields = (
        "asset_id", "material_id", "source_page_url", "resolved_original_url",
        "asset_sha256", "asset_identity_sha256", "discovery_manifest_sha256",
    )
    missing_fields = [field for field in stable_fields if not approval.get(field)]
    digest_fields = (
        "asset_sha256", "asset_identity_sha256", "discovery_manifest_sha256",
        "approval_evidence_sha256",
    )
    invalid_digests = [
        field for field in digest_fields
        if len(str(approval.get(field, ""))) != 64
        or any(ch not in "0123456789abcdef" for ch in str(approval.get(field, "")))
    ]
    if missing_fields or invalid_digests:
        res["ok"] = False
        res["error"] = (f"frozen approval identity invalid: missing={missing_fields} "
                        f"invalid_digests={invalid_digests}")
        return res
    req["asset_approvals"] = [approval]
    request_path.write_text(json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
    continue_out = sa / "continue-out"
    continued = _run([
        sys.executable, "-X", "utf8", str(cli),
        "--request", str(request_path), "--output-dir", str(continue_out),
        "--fixture-dir", str(fixture_dir), "--phase", "continue",
        "--discovery-manifest", str(frozen_path),
    ])
    res["continue_exit_code"] = continued.returncode
    try:
        manifest = json.loads(
            (continue_out / "media_manifest.json").read_text(encoding="utf-8"))
        events = json.loads(
            (continue_out / "upload_events.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        res["ok"] = False
        res["error"] = f"continuation outputs invalid: {e}; stderr={continued.stderr[-300:]}"
        return res

    assets = {asset["asset_id"]: asset for asset in manifest.get("assets", [])}
    a1, a2 = assets.get("A-001") or {}, assets.get("A-002") or {}
    discover_ev_ids = [event["asset_id"] for event in discover_events.get("events", [])]
    ev_ids = [event["asset_id"] for event in events.get("events", [])]
    res.update({
        "discovery_manifest_sha256": frozen.get("discovery_manifest_sha256"),
        "approved_asset_identity_sha256": approval.get("asset_identity_sha256"),
        "discovery_upload_event_asset_ids": discover_ev_ids,
        "A-001_copyright": a1.get("copyright_status"),
        "A-001_upload": (a1.get("upload") or {}).get("status"),
        "A-001_consumed": a1.get("asset_approval_consumed"),
        "A-001_identity_mismatch": a1.get("approval_identity_mismatch"),
        "A-002_copyright": a2.get("copyright_status"),
        "A-002_upload": (a2.get("upload") or {}).get("status"),
        "upload_event_asset_ids": ev_ids,
    })
    res["ok"] = (discover.returncode == 0
                 and continued.returncode == 0
                 and discover_ev_ids == []
                 and a1.get("copyright_status") == "known_allowed"
                 and (a1.get("upload") or {}).get("status") == "success"
                 and a1.get("asset_approval_consumed") is True
                 and a1.get("approval_identity_mismatch") == []
                 and a2.get("copyright_status") == "unknown"
                 and (a2.get("upload") or {}).get("status") != "success"
                 and ev_ids == ["A-001"])
    return res


def _pipeline_media_state_machine_e2e(skills_home: Path, staging: Path) -> dict:
    """Run the real Pipeline entry across discover/pause/continue/gzh/dry-run draft."""
    from PIL import Image, ImageDraw

    fixture_root = staging / "pipeline-media-fixture"
    html_dir = fixture_root / "html"
    image_dir = fixture_root / "images"
    html_dir.mkdir(parents=True)
    image_dir.mkdir(parents=True)
    parts = ["<!doctype html><html><body><article><p>RX 580 integration.</p>"]
    for i in range(1, 8):
        name = f"rx580-{i}.png"
        image = Image.new("RGB", (1000, 700), (245, 245, 245))
        draw = ImageDraw.Draw(image)
        draw.rectangle((30 * i, 40, 30 * i + 220, 660),
                       fill=((35 * i) % 255, (70 * i) % 255, (110 * i) % 255))
        draw.ellipse((350, 55 * i, 950, 55 * i + 140),
                     fill=((150 + 10 * i) % 255, (40 * i) % 255,
                           (220 - 15 * i) % 255))
        draw.text((400, 300), f"RX580-{i}", fill=(0, 0, 0))
        image.save(image_dir / name, "PNG")
        parts.append(
            f'<img src="https://img.example-source.test/{name}" '
            f'alt="rx580 figure {i}">')
    parts.append("</article></body></html>")
    (html_dir / "rx580-local-ai.html").write_text(
        "".join(parts), encoding="utf-8")

    env = dict(os.environ)
    env.update({
        "WXGZH_AIHOT_SKILL_DIR": str(skills_home / "aihot"),
        "WXGZH_INTEGRATION_MATERIAL_ID": "M-001",
        "WXGZH_MEDIA_FIXTURE_DIR": str(html_dir),
        "WXGZH_MEDIA_MAX_PER_MATERIAL": "8",
        "WXGZH_MEDIA_MAX_TOTAL": "8",
    })
    project = staging / "pipeline-state-machine"
    orch = Orchestrator(
        project_root=project, network_mode="integration",
        skills_home=skills_home,
        fixture_dir=REPO / "fixtures" / "fake_live_fixture",
        env=env,
    )
    first = orch.run("integration media state machine")
    result = {"first_status": first.get("status")}
    if first.get("status") != "AWAITING_MEDIA_ASSET_APPROVAL":
        result.update({"ok": False, "error": first})
        return result
    run_dir = Path(first["discovery_manifest"]).parents[2]
    frozen_path = Path(first["discovery_manifest"])
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    assets = frozen.get("assets", [])
    if len(assets) < 7:
        result.update({"ok": False, "error": f"expected >=7 assets, got {len(assets)}"})
        return result
    approvals = []
    for target in assets[:6]:
        approval = dict(target)
        approval.update({
            "discovery_manifest_sha256": frozen["discovery_manifest_sha256"],
            "approval_id": f"AP-{target['asset_id']}",
            "approved_scope": "single_asset",
            "approved_by": "integration-user",
            "approved_at": "2026-07-29T00:00:00Z",
            "approval_evidence_sha256": "e" * 64,
        })
        approvals.append(approval)
    approval_path = Path(first["approval_file"])
    approval_path.write_text(
        json.dumps({"approvals": approvals}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    resumed = orch.resume(first["run_id"])
    events = json.loads(
        (run_dir / "media_enrichment" / "upload_events.json").read_text(encoding="utf-8"))
    uploaded_ids = [item["asset_id"] for item in events.get("events", [])
                      if item.get("status") == "success"]
    manifest = json.loads(
        (run_dir / "media_enrichment" / "media_manifest.json").read_text(encoding="utf-8"))
    unapproved = {asset["asset_id"]: asset for asset in manifest["assets"]
                  if asset["asset_id"] not in {a["asset_id"] for a in approvals}}
    receipts = {}
    for stage in ("media_enrichment", "gzh_design", "wechat_draft"):
        ok, mismatches = verify_receipt(
            run_dir, stage, skills_home=skills_home, network_mode="integration")
        receipts[stage] = {"ok": ok, "mismatches": mismatches}
    draft = json.loads(
        (run_dir / "wechat_draft" / "draft_creation_result.json").read_text(encoding="utf-8"))
    theme = json.loads(
        (run_dir / "gzh_design" / "theme_identity_report.json").read_text(encoding="utf-8"))
    result.update({
        "run_id": first["run_id"],
        "paused_before_gzh": first.get("gzh_design_executed") is False,
        "paused_before_draft": first.get("wechat_draft_executed") is False,
        "resume_status": resumed.get("status"),
        "uploaded_asset_ids": uploaded_ids,
        "unapproved_assets_not_uploaded": all(
            (asset.get("upload") or {}).get("status") != "success"
            for asset in unapproved.values()),
        "uploaded_image_count": resumed.get("uploaded_image_count"),
        "theme_identity": theme.get("THEME_IDENTITY"),
        "draft_created": resumed.get("draft_created"),
        "real_api_call": draft.get("real_api_call"),
        "formally_published": draft.get("formally_published"),
        "receipts": receipts,
    })
    result["ok"] = (
        result["paused_before_gzh"] and result["paused_before_draft"]
        and resumed.get("status") == "COMPLETE"
        and len(uploaded_ids) == 6
        and result["unapproved_assets_not_uploaded"]
        and resumed.get("uploaded_image_count") == 6
        and theme.get("THEME_IDENTITY") == "PASS"
        and resumed.get("draft_created") is True
        and draft.get("real_api_call") is False
        and draft.get("formally_published") is False
        and all(item["ok"] for item in receipts.values())
    )
    return result


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

    # ── P0#1: FORMAL installer (scripts/install.py) installs the locked trees AND
    # generates the external install receipts. The integration must NOT copy the
    # directories itself and bypass the formal installer. ──
    inst = _run([sys.executable, "-X", "utf8", str(REPO / "scripts" / "install.py"),
                 "--target", str(skills_home), "--skills-src", str(clones)])
    record("formal_install_py", inst.returncode == 0,
           (inst.stdout + inst.stderr)[-400:] if inst.returncode else "")
    receipts = {}
    for skill_name in CLONE_TO_SKILL.values():
        rec = SD.read_install_receipt(skills_home, skill_name)
        receipts[skill_name] = rec
        le = lock_skills.get(skill_name) or {}
        ok_rec = bool(rec
                      and rec.get("full_commit_sha") == le.get("full_commit_sha")
                      and rec.get("installed_runtime_root_sha256") == le.get("skill_root_sha256")
                      and rec.get("installed_runtime_manifest_sha256") == le.get("runtime_manifest_sha256"))
        record(f"install_receipt:{skill_name}", ok_rec,
               "" if ok_rec else f"receipt={rec}")
    details["install_receipts"] = receipts

    # a verifiable AI HOT registration (external agent-invoked dependency)
    aihot = skills_home / "aihot"
    aihot.mkdir(exist_ok=True)
    (aihot / "SKILL.md").write_text("---\nname: aihot\n---\n", encoding="utf-8")
    (aihot / "registration.json").write_text(json.dumps(
        {"name": "aihot", "identifier": "aihot", "discoverable": True,
         "output_contract": {"items": "array of AI HOT entries"}}), encoding="utf-8")
    env = dict(os.environ)
    env["WXGZH_AIHOT_SKILL_DIR"] = str(aihot)

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

    # ── P0#3: stable single_asset approval via the REAL two-phase media CLI ──
    sa = _single_asset_e2e(skills_home, staging)
    details["single_asset_e2e"] = sa
    record("single_asset_media_cli_e2e", sa.get("ok", False),
           json.dumps({k: v for k, v in sa.items() if k != "ok"}, ensure_ascii=False)[:300])

    # ── hotfix6: real Pipeline media discover/pause/approve/resume E2E ──
    pipeline_e2e = _pipeline_media_state_machine_e2e(skills_home, staging)
    details["pipeline_media_state_machine_e2e"] = pipeline_e2e
    record("pipeline_media_state_machine_e2e", pipeline_e2e.get("ok", False),
           json.dumps({k: v for k, v in pipeline_e2e.items() if k != "ok"},
                      ensure_ascii=False)[:500])

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
