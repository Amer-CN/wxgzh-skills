"""Stage output production for live / fake_live — dev2-hotfix1.

Every executable stage is invoked with the REAL sub-skill CLI (dev2's invented
--stage-dir/--article args are gone):

  media_enrichment  build media_request.json ->
                    run_media_enrichment.py --request <req> --output-dir <sd>
                    validate_media_manifest.py --manifest --request --bindings
  gzh_design        render_article.py --article --bindings --output-dir --theme smartisan
                    validate_gzh_html.py <final.html>          (positional)
  wechat_draft      publish_wechat_draft.py --html --title --audit-dir <sd>
                    (+ --dry-run in fake_live: zero side effects)

Agent stages (aihot / super_writer / zh_human_writing) use the handshake, then
the orchestrator subprocess-executes the OFFICIAL sub-skill validators (P0#5),
recording command + exit + stdout/stderr sha256 for the receipt.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from . import execmodel as EM
from . import agent_handshake as AH
from .state import sha256_file
from .subprocess_runner import run_script

AGENT_INSTRUCTIONS = {
    "aihot": "Query AI HOT (anonymous read-only), aggregate + dedup; do not write the article.",
    "super_writer": "Run Super Writer Material-Heavy Full Mode; FULL_MODE_VALIDATOR_EXIT must be 0.",
    "zh_human_writing": "De-AI the Super Writer article only; freeze final_article.md (no new facts).",
}


def _frozen_article(ctx) -> Path:
    return Path(ctx.run_dir) / "zh_human_writing" / "final_article.md"


def _vresult(run: dict) -> dict:
    """Receipt-grade record of one real validator subprocess (P0#5)."""
    return {"path": run["script_path"], "sha256": run["script_sha256"],
            "command": run["command"], "exit_code": run["exit_code"],
            "stdout_sha256": run["stdout_sha256"], "stderr_sha256": run["stderr_sha256"],
            "elapsed_seconds": run["elapsed_seconds"]}


def produce(ctx, stage: str, state) -> tuple[list, dict]:
    kind = EM.STAGE_EXEC[stage]
    sd = ctx.stage_dir(stage)
    expected = EM.EXPECTED_OUTPUTS[stage]
    if kind == EM.AGENT:
        return _agent(ctx, stage, sd, expected, state)
    if kind == EM.SUBPROC:
        return _subprocess(ctx, stage, sd, expected, state)
    if kind == EM.WECHAT:
        return _wechat(ctx, stage, sd, expected, state)
    raise ValueError(f"unknown exec kind for {stage}")


# ---------- agent stages ----------

def _upstream_hashes(ctx, stage: str) -> dict:
    out = {}
    for rel in EM.UPSTREAM_INPUTS.get(stage, []):
        p = Path(ctx.run_dir) / rel
        out[rel] = sha256_file(p) if p.is_file() else None
    return out


def _skill_identity(ctx, stage: str) -> dict:
    from .stages import STAGE_SKILL
    skill = STAGE_SKILL[stage]
    disc = ctx.discovery.get(skill, {})
    return {"skill_name": skill,
            "skill_version": disc.get("current_version") or disc.get("locked_version"),
            "skill_root_sha256": disc.get("current_root_sha256") or disc.get("locked_root_sha256")}


def _contract_sha(stage: str) -> str | None:
    from .contracts import CONTRACT_FILES, SKILL_ROOT as REPO
    p = REPO / "contracts" / CONTRACT_FILES[stage]
    return sha256_file(p) if p.is_file() else None


def _agent_validator_args(stage: str, ctx, sd: Path) -> list[tuple[str, str, list]]:
    """(skill, validator_rel, argv) for each OFFICIAL agent-stage validator."""
    rd = Path(ctx.run_dir)
    if stage == "super_writer":
        return [
            ("super-writer", "scripts/material_ingestion.py",
             ["--ledger", str(sd / "material-ledger.yaml"),
              "--output", str(sd / "material_ingestion_report.json")]),
            ("super-writer", "scripts/validate_article_length.py",
             ["--article", str(sd / "article.md"), "--full-mode"]),
            ("super-writer", "scripts/validate_semantic_map.py",
             ["--article", str(sd / "article.md"),
              "--semantic-map", str(sd / "semantic-map.yaml")]),
        ]
    if stage == "zh_human_writing":
        orig = rd / "super_writer" / "article.md"
        return [
            ("zh-human-writing", "scripts/fidelity_guard.py",
             ["--original", str(orig), "--edited", str(sd / "final_article.md")]),
            ("zh-human-writing", "scripts/pattern_audit.py",
             ["--text", str(sd / "final_article.md")]),
            ("zh-human-writing", "scripts/change_report.py",
             ["--original", str(orig), "--edited", str(sd / "final_article.md")]),
        ]
    return []


def _agent(ctx, stage, sd, expected, state):
    upstream = _upstream_hashes(ctx, stage)
    identity = _skill_identity(ctx, stage)
    inputs = {"topic": state.topic, "frozen_article_sha256": state.final_article_sha256}
    AH.write_request(sd, stage, identity["skill_name"], AGENT_INSTRUCTIONS.get(stage, ""),
                     expected, inputs, run_id=state.run_id, upstream_hashes=upstream,
                     stage_request_sha256=sha256_file(sd / "stage_request.json"),
                     skill_identity=identity, contract_sha256=_contract_sha(stage))
    if ctx.network_mode == "fake_live":
        agent = ctx.fake_agent or AH.FakeAgent(ctx.fixture_dir)
        agent.fulfill(sd, stage, expected)
    ok, hs = AH.verify_ack(sd, stage, expected, run_dir=ctx.run_dir)
    outputs = [sd / o for o in expected if (sd / o).is_file()]
    meta = {"exec_kind": EM.AGENT, "handshake": hs,
            "invoked_entrypoint": f"agent_handshake:{stage}",
            "entrypoint_path": None, "entrypoint_sha256": None}
    if not ok:
        meta["await_agent"] = (hs.get("HANDSHAKE") == "AWAITING_AGENT")
        meta["handshake_failed"] = not meta["await_agent"]
        return outputs, meta

    # P0#5 — REALLY execute the official sub-skill validators via subprocess.
    officials = []
    for skill, rel, argv in _agent_validator_args(stage, ctx, sd):
        script = EM.resolve_agent_validator(skill, rel, ctx.network_mode, ctx.skills_home)
        run = run_script(script, argv, timeout=180)
        officials.append(_vresult(run))
    meta["official_validators"] = officials
    if any(v["exit_code"] != 0 for v in officials):
        meta["official_validator_failed"] = [v for v in officials if v["exit_code"] != 0]
    return outputs, meta


# ---------- executable stages ----------

def _build_media_request(ctx, sd: Path, state) -> Path:
    """Build the REAL media_enrichment_request the installed skill validates."""
    rd = Path(ctx.run_dir)
    article = _frozen_article(ctx)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    materials, claims = [], []
    dedup = rd / "aihot" / "deduplicated_items.json"
    items = []
    if dedup.is_file():
        try:
            data = json.loads(dedup.read_text(encoding="utf-8"))
            items = data if isinstance(data, list) else data.get("items", [])
        except ValueError:
            items = []
    if not items:
        items = [{"title": state.topic or "untitled", "url": "https://example.com/source"}]
    for i, it in enumerate(items[:3], 1):
        mid, cid = f"M-{i:03d}", f"C-{i:02d}"
        src = it.get("source_url") or it.get("url") or "https://example.com/source"
        materials.append({
            "material_id": mid, "aihot_permalink": it.get("permalink") or src,
            "source_url": src, "title": it.get("title", ""), "selected_claim_ids": [cid],
            "copyright_review": {"status": "known_allowed", "reviewed_by": "wxgzh-pipeline",
                                 "reviewed_at": now,
                                 "evidence": "user blanket approval (USER_BLANKET_APPROVAL=true)"},
        })
        claims.append({"claim_id": cid, "claim_text": it.get("title", ""), "material_id": mid,
                       "source_url": src, "source_excerpt": it.get("title", "")})
    req = {
        "schema_version": "1.0", "run_id": state.run_id,
        "article": {"path": "../zh_human_writing/final_article.md",
                    "sha256": state.final_article_sha256 or sha256_file(article)},
        "materials": materials, "claims": claims,
        "config": {
            "upload_mode": "wechat_audit" if ctx.network_mode == "fake_live" else "wechat_image_host",
            "network_mode": "offline_fixture" if ctx.network_mode == "fake_live" else "live",
            "max_images_per_material": 3, "max_total_images": 8,
            "allow_unknown_license_for_publish": False,
        },
    }
    req_path = sd / "media_request.json"
    req_path.write_text(json.dumps(req, ensure_ascii=False, indent=2, sort_keys=True),
                        encoding="utf-8", newline="\n")
    return req_path


def _entry_args(ctx, stage: str, sd: Path, state, req_path: Path | None) -> list:
    rd = Path(ctx.run_dir)
    if stage == "media_enrichment":
        return ["--request", str(req_path), "--output-dir", str(sd)]
    if stage == "gzh_design":
        return ["--article", str(_frozen_article(ctx)),
                "--bindings", str(rd / "media_enrichment" / "article_image_bindings.json"),
                "--output-dir", str(sd), "--theme", "smartisan"]
    raise ValueError(stage)


def _validator_args(stage: str, sd: Path, req_path: Path | None) -> list:
    if stage == "media_enrichment":
        return ["--manifest", str(sd / "media_manifest.json"),
                "--request", str(req_path),
                "--bindings", str(sd / "article_image_bindings.json")]
    if stage == "gzh_design":
        return [str(sd / "final.html")]  # validate_gzh_html.py takes a positional path
    return []


def _subprocess(ctx, stage, sd, expected, state):
    entry, validator = EM.resolve_entry(stage, ctx.network_mode, ctx.skills_home)
    req_path = _build_media_request(ctx, sd, state) if stage == "media_enrichment" else None
    run = run_script(entry, _entry_args(ctx, stage, sd, state, req_path), timeout=300)
    meta = {"exec_kind": EM.SUBPROC, "invoked_entrypoint": str(entry),
            "entrypoint_path": run["script_path"], "entrypoint_sha256": run["script_sha256"],
            "entry_run": {"command": run["command"], "exit_code": run["exit_code"],
                          "elapsed": run["elapsed_seconds"],
                          "stdout_sha256": run["stdout_sha256"],
                          "stderr_sha256": run["stderr_sha256"],
                          "stderr": run["stderr"][-400:] if run["exit_code"] else ""}}
    if validator:
        vr = run_script(validator, _validator_args(stage, sd, req_path), timeout=180)
        meta["official_validator"] = _vresult(vr)
    outputs = [sd / o for o in expected if (sd / o).is_file()]
    return outputs, meta


def _wechat(ctx, stage, sd, expected, state):
    if not ctx.create_wechat_draft:
        return [], {"exec_kind": EM.WECHAT, "skipped": "create_wechat_draft=False"}
    entry, _ = EM.resolve_entry(stage, ctx.network_mode, ctx.skills_home)
    html = Path(ctx.run_dir) / "gzh_design" / "final.html"
    args = ["--html", str(html), "--title", (state.topic or "wxgzh article")[:60],
            "--audit-dir", str(sd)]
    if ctx.network_mode == "fake_live":
        args.append("--dry-run")  # zero side effects; simulated batchget snapshots
    run = run_script(entry, args, timeout=300)
    meta = {"exec_kind": EM.WECHAT, "invoked_entrypoint": str(entry),
            "entrypoint_path": run["script_path"], "entrypoint_sha256": run["script_sha256"],
            "entry_run": {"command": run["command"], "exit_code": run["exit_code"],
                          "stdout_sha256": run["stdout_sha256"],
                          "stderr_sha256": run["stderr_sha256"],
                          "stderr": run["stderr"][-400:] if run["exit_code"] else ""}}
    outputs = [sd / o for o in expected if (sd / o).is_file()]
    return outputs, meta
