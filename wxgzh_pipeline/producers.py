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

class MediaRequestError(Exception):
    """Fail-closed: canonical registry missing / malformed / unmappable."""


def _load_copyright_approvals(rd: Path) -> dict:
    """P0#3: known_allowed can ONLY come from a real approval record on disk.
    Returns {material_id or source_url: approval_record}. Absent file => {}.
    Each record must bind approval_id/approved_scope/scope-ref/approved_at/
    approved_by/approval_evidence_sha256; incomplete records are ignored."""
    p = rd / "media_enrichment" / "copyright_approval.json"
    if not p.is_file():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return {}
    req_fields = {"approval_id", "approved_scope", "approved_at", "approved_by",
                  "approval_evidence_sha256"}
    out = {}
    for rec in data.get("approvals", []):
        if not req_fields.issubset(rec):
            continue
        for key in (rec.get("material_id"), rec.get("source_url"), rec.get("asset_id")):
            if key:
                out[key] = rec
    return out


def _build_media_request(ctx, sd: Path, state) -> Path:
    """Build the REAL media request bound to the CANONICAL registry (P0#2/#3).

    Reads super_writer/canonical_claim_registry.json + aihot/deduplicated_items
    + the frozen article, and copies claim_id/material_id/claim_text/source_url/
    source_excerpt/selected_claim_ids/numbers/chart_group VERBATIM. NEVER invents
    IDs, NEVER uses material titles as claims, NEVER uses example.com fallback,
    and NEVER self-approves copyright. Missing/malformed registry => FAIL_CLOSED.
    """
    rd = Path(ctx.run_dir)
    reg_p = rd / "super_writer" / "canonical_claim_registry.json"
    if not reg_p.is_file():
        raise MediaRequestError("canonical_claim_registry.json missing (FAIL_CLOSED)")
    try:
        reg = json.loads(reg_p.read_text(encoding="utf-8"))
    except ValueError as e:
        raise MediaRequestError(f"canonical registry malformed: {e}")
    reg_claims = reg.get("claims") or reg.get("canonical_claims") or []
    reg_materials = reg.get("materials") or []
    if not reg_claims or not reg_materials:
        raise MediaRequestError("canonical registry has no claims/materials (FAIL_CLOSED)")

    approvals = _load_copyright_approvals(rd)
    materials, claims = [], []
    mat_ids = set()
    for m in reg_materials:
        mid = m.get("material_id")
        src = m.get("source_url")
        if not mid or not src:
            raise MediaRequestError(f"registry material missing id/source_url: {m}")
        mat_ids.add(mid)
        # P0#3: approval ONLY from a real record; else pipeline does not approve.
        appr = approvals.get(mid) or approvals.get(src)
        cr = ({"status": "known_allowed", "reviewed_by": appr["approved_by"],
               "reviewed_at": appr["approved_at"],
               "evidence": appr["approval_evidence_sha256"],
               "approval_id": appr["approval_id"], "approved_scope": appr["approved_scope"]}
              if appr else {"status": "unknown"})
        materials.append({
            "material_id": mid,
            "aihot_permalink": m.get("aihot_permalink") or src,
            "source_url": src, "title": m.get("title", ""),
            "selected_claim_ids": list(m.get("selected_claim_ids", [])),
            "copyright_review": cr,
        })
    for c in reg_claims:
        cid, mid = c.get("claim_id"), c.get("material_id")
        if not cid or not mid:
            raise MediaRequestError(f"registry claim missing claim_id/material_id: {c}")
        if mid not in mat_ids:
            raise MediaRequestError(f"claim {cid} references unknown material {mid} (FAIL_CLOSED)")
        claim = {"claim_id": cid, "claim_text": c.get("claim_text", ""),
                 "material_id": mid, "source_url": c.get("source_url", ""),
                 "source_excerpt": c.get("source_excerpt", "")}
        for opt in ("numbers", "chart_group", "metric_name", "series_label"):
            if opt in c:
                claim[opt] = c[opt]
        claims.append(claim)

    article = _frozen_article(ctx)
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
        "provenance": {"canonical_registry_sha256": sha256_file(reg_p),
                       "copyright_approvals_bound": len(approvals)},
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
    req_path = None
    if stage == "media_enrichment":
        try:
            req_path = _build_media_request(ctx, sd, state)
        except MediaRequestError as e:
            return [], {"exec_kind": EM.SUBPROC, "invoked_entrypoint": str(entry),
                        "entrypoint_path": None, "entrypoint_sha256": None,
                        "media_request_failed": str(e),
                        "entry_run": {"exit_code": 2, "stderr": f"FAIL_CLOSED: {e}"}}
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
