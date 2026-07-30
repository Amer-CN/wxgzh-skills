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

import hashlib
import importlib.util
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import execmodel as EM
from . import agent_handshake as AH
from .state import sha256_file
from .subprocess_runner import run_script

AGENT_INSTRUCTIONS = {
    "aihot": "Query AI HOT (anonymous read-only), aggregate + dedup; do not write the article.",
    "super_writer": "Run Super Writer Material-Heavy Full Mode. Generate every requested product, then run the locked official validate_article_length.py with --full-mode --json and save its exact JSON stdout as full_mode_validator_report.json before ACK.",
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
        agent_expected = EM.AGENT_EXPECTED_OUTPUTS[stage]
        return _agent(ctx, stage, sd, expected, agent_expected, state)
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


def _super_writer_policy(sd: Path) -> dict:
    """Load the declared length policy; never derive it from article length."""
    profile = sd / "generation-profile.yaml"
    try:
        data = yaml.safe_load(profile.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ValueError(f"invalid generation-profile.yaml: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("generation-profile.yaml top-level must be an object")
    fields = ("article_mode", "target_visible_chars", "acceptable_min", "acceptable_max")
    missing = [name for name in fields if data.get(name) in (None, "")]
    if missing:
        raise ValueError(f"generation-profile.yaml missing length policy: {missing}")
    mode = data["article_mode"]
    if not isinstance(mode, str):
        raise ValueError("generation-profile.yaml article_mode must be a string")
    values = {}
    for name in fields[1:]:
        value = data[name]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"generation-profile.yaml {name} must be a positive integer")
        values[name] = value
    if not values["acceptable_min"] <= values["target_visible_chars"] <= values["acceptable_max"]:
        raise ValueError("generation-profile.yaml requires min <= target <= max")
    return {"article_mode": mode, **values}


def _agent_validator_args(stage: str, ctx, sd: Path) -> list[tuple[str, str, list]]:
    """(skill, validator_rel, argv) for each OFFICIAL agent-stage validator."""
    rd = Path(ctx.run_dir)
    if stage == "super_writer":
        policy = _super_writer_policy(sd)
        length_args = [
            "--article", str(sd / "article.md"),
            "--outline", str(sd / "outline.md"),
            "--full-mode",
            "--generation-profile", str(sd / "generation-profile.yaml"),
            "--brief", str(sd / "writing-brief.md"),
            "--material-readiness", str(sd / "material-readiness.yaml"),
            "--material-ledger", str(sd / "material-ledger.yaml"),
            "--material-report", str(sd / "material-ingestion-report.json"),
            "--evidence-map", str(sd / "evidence-map.md"),
            "--core-card", str(sd / "core-card.md"),
            "--semantic-map", str(sd / "semantic-map.yaml"),
            "--editor-report", str(sd / "editor-report.md"),
            "--article-mode", policy["article_mode"],
            "--target-visible-chars", str(policy["target_visible_chars"]),
            "--acceptable-min", str(policy["acceptable_min"]),
            "--acceptable-max", str(policy["acceptable_max"]),
            "--json",
        ]
        return [
            ("super-writer", "scripts/material_ingestion.py",
             ["--ledger", str(sd / "material-ledger.yaml"),
              "--output", str(sd / "material_ingestion_verification.json")]),
            ("super-writer", "scripts/validate_article_length.py", length_args),
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


def _agent(ctx, stage, sd, expected, agent_expected, state):
    upstream = _upstream_hashes(ctx, stage)
    identity = _skill_identity(ctx, stage)
    inputs = {"topic": state.topic, "frozen_article_sha256": state.final_article_sha256}
    AH.write_request(sd, stage, identity["skill_name"], AGENT_INSTRUCTIONS.get(stage, ""),
                     agent_expected, inputs, run_id=state.run_id, upstream_hashes=upstream,
                     stage_request_sha256=sha256_file(sd / "stage_request.json"),
                     skill_identity=identity, contract_sha256=_contract_sha(stage))
    if ctx.network_mode in ("fake_live", "integration"):
        agent = ctx.fake_agent or AH.FakeAgent(ctx.fixture_dir)
        try:
            agent.fulfill(sd, stage, agent_expected)
        except (OSError, ValueError, TypeError) as exc:
            outputs = [sd / o for o in expected if (sd / o).is_file()]
            return outputs, {"exec_kind": EM.AGENT,
                             "handshake": {"HANDSHAKE": "FAIL", "reason": str(exc)},
                             "handshake_failed": True,
                             "invoked_entrypoint": f"agent_handshake:{stage}",
                             "entrypoint_path": None, "entrypoint_sha256": None}
    ok, hs = AH.verify_ack(sd, stage, agent_expected, run_dir=ctx.run_dir)
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
    try:
        validators = _agent_validator_args(stage, ctx, sd)
    except ValueError as exc:
        validators = []
        if stage == "super_writer":
            validators = [
                ("super-writer", "scripts/material_ingestion.py",
                 ["--ledger", str(sd / "material-ledger.yaml"),
                  "--output", str(sd / "material_ingestion_verification.json")]),
                ("super-writer", "scripts/validate_semantic_map.py",
                 ["--article", str(sd / "article.md"),
                  "--semantic-map", str(sd / "semantic-map.yaml")]),
            ]
        officials.append({"path": None, "sha256": None, "command": [], "exit_code": 2,
                          "stdout_sha256": hashlib.sha256(b"").hexdigest(),
                          "stderr_sha256": hashlib.sha256(str(exc).encode("utf-8")).hexdigest(),
                          "elapsed_seconds": 0.0, "error": str(exc)})
    for skill, rel, argv in validators:
        script = EM.resolve_agent_validator(skill, rel, ctx.network_mode, ctx.skills_home)
        run = run_script(script, argv, timeout=180)
        officials.append(_vresult(run))
        if stage == "super_writer" and rel == "scripts/validate_article_length.py":
            try:
                official_report = json.loads(run.get("stdout") or "{}")
                agent_report = json.loads((sd / "full_mode_validator_report.json").read_text(encoding="utf-8"))
                report_matches = agent_report == official_report
            except (OSError, UnicodeError, json.JSONDecodeError):
                report_matches = False
            if not report_matches:
                run["exit_code"] = run["exit_code"] or 3
                run["stderr"] = (run.get("stderr") or "") + "\nagent report != official validator JSON"
                run["stderr_sha256"] = hashlib.sha256(run["stderr"].encode("utf-8")).hexdigest()
                officials[-1] = _vresult(run)
    outputs = [sd / o for o in expected if (sd / o).is_file()]
    meta["official_validators"] = officials
    if any(v["exit_code"] != 0 for v in officials):
        meta["official_validator_failed"] = [v for v in officials if v["exit_code"] != 0]
    return outputs, meta


# ---------- executable stages ----------

class MediaRequestError(Exception):
    """Fail-closed: canonical registry missing / malformed / unmappable."""


_HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
_APPROVAL_BASE = {"approval_id", "approved_scope", "approved_at", "approved_by",
                  "approval_evidence_sha256"}
_STABLE_SINGLE_ASSET_FIELDS = {
    "asset_id", "material_id", "source_page_url", "resolved_original_url",
    "asset_sha256", "asset_identity_sha256", "discovery_manifest_sha256",
    "approval_id", "approved_scope", "approved_by", "approved_at",
    "approval_evidence_sha256",
}
VALID_APPROVAL_SCOPES = ("material", "source_url", "single_asset")


def _canonical_discovery_sha(manifest: dict) -> str:
    unsigned = dict(manifest)
    unsigned.pop("discovery_manifest_sha256", None)
    payload = (json.dumps(
        unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _stable_asset_identity(record: dict) -> str:
    payload = "\n".join((
        str(record.get("material_id", "")),
        str(record.get("source_page_url", "")),
        str(record.get("resolved_original_url", "")),
        str(record.get("asset_sha256", "")),
    )).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_copyright_approvals(rd: Path) -> dict:
    """P0#2: scope-aware copyright approvals. known_allowed can ONLY come from a
    real approval record whose approved_scope is one of material/source_url/
    single_asset, whose scope-specific binding field is present, and whose
    approval_evidence_sha256 is a well-formed 64-hex digest. Returns:

      {"material": {material_id: rec}, "source_url": {source_url: rec},
       "single_asset": {asset_id: rec}, "count": int}

    - material     -> requires material_id; approves ONLY that material.
    - source_url   -> requires source_url;  approves ONLY that exact URL.
    - single_asset -> requires asset_id;    NEVER marks the whole material
                      known_allowed (applied per-asset downstream, AFTER the
                      asset_id is produced from image extraction).
    Unknown scope / scope-binding mismatch / malformed evidence hash => ignored.
    """
    out = {"material": {}, "source_url": {}, "single_asset": {}, "count": 0}
    p = rd / "media_enrichment" / "copyright_approval.json"
    if not p.is_file():
        return out
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return out
    for rec in data.get("approvals", []):
        if not isinstance(rec, dict) or not _APPROVAL_BASE.issubset(rec):
            if isinstance(rec, dict) and rec.get("approved_scope") == "single_asset":
                raise MediaRequestError(
                    "old/malformed single_asset approval rejected: full stable fields required")
            continue
        ev = rec.get("approval_evidence_sha256", "")
        if not isinstance(ev, str) or not _HEX64.match(ev):
            continue  # evidence hash format error => FAIL_CLOSED (ignore record)
        scope = rec.get("approved_scope")
        if scope == "material" and rec.get("material_id"):
            out["material"][rec["material_id"]] = rec
        elif scope == "source_url" and rec.get("source_url"):
            out["source_url"][rec["source_url"]] = rec
        elif scope == "single_asset":
            if not _STABLE_SINGLE_ASSET_FIELDS.issubset(rec):
                raise MediaRequestError(
                    "old single_asset approval rejected: full stable fields required")
            if any(not rec.get(field) for field in _STABLE_SINGLE_ASSET_FIELDS):
                raise MediaRequestError(
                    "single_asset approval rejected: stable fields cannot be empty")
            if any(not _HEX64.fullmatch(str(rec.get(field, ""))) for field in (
                "asset_sha256", "asset_identity_sha256",
                "discovery_manifest_sha256", "approval_evidence_sha256",
            )):
                raise MediaRequestError(
                    "single_asset approval rejected: invalid sha256 field")
            if rec["asset_identity_sha256"] != _stable_asset_identity(rec):
                raise MediaRequestError(
                    "single_asset approval rejected: asset_identity_sha256 mismatch")
            out["single_asset"][rec["asset_id"]] = rec
        else:
            continue  # unknown scope OR missing required binding field => ignore
        out["count"] += 1
    return out


def _load_dedup_index(rd: Path) -> tuple[Path, dict]:
    """P0#3 (strict): load aihot/deduplicated_items.json into a deterministic index
    used to cross-verify the canonical registry (tolerant of id/url key aliases).
    Raises MediaRequestError on missing/malformed dedup, on ANY duplicated dedup id
    (even with an identical URL), or when one source_url is mapped by multiple
    different ids (ambiguous)."""
    p = rd / "aihot" / "deduplicated_items.json"
    if not p.is_file():
        raise MediaRequestError("aihot/deduplicated_items.json missing (FAIL_CLOSED)")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        raise MediaRequestError(f"deduplicated_items malformed: {e}")
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list) or not items:
        raise MediaRequestError("deduplicated_items empty/invalid (FAIL_CLOSED)")
    by_id, by_url = {}, {}
    for it in items:
        if not isinstance(it, dict):
            continue
        iid = it.get("id", it.get("material_id", it.get("item_id")))
        iid = str(iid) if iid is not None else None
        url = it.get("source_url") or it.get("url")
        permalink = it.get("aihot_permalink") or it.get("permalink") or url
        norm = {"id": iid, "source_url": url, "aihot_permalink": permalink,
                "title": it.get("title", "")}
        if iid is not None:
            if iid in by_id:
                raise MediaRequestError(
                    f"dedup id {iid} appears more than once (FAIL_CLOSED)")
            by_id[iid] = norm
        if url:
            prev = by_url.get(url)
            if prev is not None and prev["id"] != iid:
                raise MediaRequestError(
                    f"dedup source_url {url} is mapped by multiple different ids "
                    "(ambiguous, FAIL_CLOSED)")
            by_url[url] = norm
    return p, {"by_id": by_id, "by_url": by_url}


def _validate_with_fixed_media(ctx, request_path: Path) -> dict:
    """Run the installed/fixed media Commit's real validate_request in-process.

    This is deliberately independent from Pipeline's own field checks. Every
    generated media_request.json must pass the exact media runtime that will be
    invoked next; otherwise Pipeline fails closed before media execution.
    """
    ctx_env = getattr(ctx, "env", {}) or {}
    media_root = Path(
        ctx_env.get("WXGZH_FIXED_MEDIA_ROOT")
        or os.environ.get("WXGZH_FIXED_MEDIA_ROOT")
        or (Path(getattr(ctx, "skills_home", Path(__file__).resolve().parents[2]))
            / "media-enrichment")
    )
    contract_path = media_root / "src" / "media_enrichment" / "input_contract.py"
    package_root = media_root / "src"
    if not contract_path.is_file():
        raise MediaRequestError(
            f"fixed media validate_request unavailable: {contract_path}")
    inserted = False
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))
        inserted = True
    try:
        module_name = f"_wxgzh_fixed_media_contract_{hashlib.sha256(str(contract_path).encode()).hexdigest()[:12]}"
        spec = importlib.util.spec_from_file_location(module_name, contract_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
            validation = module.validate_request(request_path)
        finally:
            sys.modules.pop(module_name, None)
    finally:
        if inserted:
            sys.path.remove(str(package_root))
    if not validation.valid:
        raise MediaRequestError(
            "fixed media validate_request rejected Pipeline request: "
            + "; ".join(validation.errors))
    return {
        "validator": str(contract_path),
        "validator_sha256": sha256_file(contract_path),
        "request_sha256": validation.request_sha256,
        "valid": True,
    }


def _build_media_request(ctx, sd: Path, state, *, phase: str = "discover") -> Path:
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

    if phase not in ("discover", "continue"):
        raise MediaRequestError(f"invalid media phase: {phase}")
    dedup_p, dedup = _load_dedup_index(rd)           # P0#3 (raises on missing/bad)
    approvals = _load_copyright_approvals(rd)         # P0#2 scope-aware
    if phase == "discover":
        # Discovery must never carry an old, forged, or even valid single-asset
        # approval. Stable approval can only be created from its frozen output.
        approvals["single_asset"] = {}
    materials, claims = [], []
    mat_ids = set()
    verified_material_count = 0
    for m in reg_materials:
        mid = m.get("material_id")
        src = m.get("source_url")
        if not mid or not src:
            raise MediaRequestError(f"registry material missing id/source_url: {m}")
        mat_ids.add(mid)
        # ── P0#3 STRICT dedup mapping (hotfix4): the canonical material must map
        #    by its FORMAL upstream/dedup ID ONLY. A URL can NEVER be used to find
        #    a substitute item for a wrong/missing ID (no by_url fallback). ──
        explicit = m.get("dedup_id") or m.get("upstream_id") or m.get("aihot_id")
        dkey = str(explicit) if explicit is not None else str(mid)
        di = dedup["by_id"].get(dkey)
        if di is None:
            raise MediaRequestError(
                f"material {mid}: canonical/upstream id {dkey} not found in dedup "
                "(URL fallback is FORBIDDEN) (FAIL_CLOSED)")
        if explicit is not None:
            also = dedup["by_id"].get(str(mid))
            if also is not None and also != di:
                raise MediaRequestError(
                    f"material {mid}: dedup_id {dkey} conflicts with the "
                    "material_id mapping (FAIL_CLOSED)")
        if di["source_url"] != src:
            raise MediaRequestError(
                f"material {mid} source_url disagrees with dedup (FAIL_CLOSED)")
        permalink = m.get("aihot_permalink") or src
        if di.get("aihot_permalink") and di["aihot_permalink"] != permalink:
            raise MediaRequestError(
                f"material {mid} aihot_permalink disagrees with dedup (FAIL_CLOSED)")
        verified_material_count += 1
        # ── P0#2 approval: ONLY material/source_url scope marks the material;
        #    single_asset NEVER marks the whole material known_allowed. ──
        appr = approvals["material"].get(mid) or approvals["source_url"].get(src)
        cr = ({"status": "known_allowed", "reviewed_by": appr["approved_by"],
               "reviewed_at": appr["approved_at"],
               "evidence": appr["approval_evidence_sha256"],
               "approval_id": appr["approval_id"], "approved_scope": appr["approved_scope"]}
              if appr else {"status": "unknown"})
        materials.append({
            "material_id": mid,
            "aihot_permalink": permalink,
            "source_url": src, "title": m.get("title", ""),
            "selected_claim_ids": list(m.get("selected_claim_ids", [])),
            "dedup_id": di["id"],
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
    # Integration uses the real media CLI with frozen local HTML/image fixtures.
    # Those fixtures contain one material; keep the Pipeline path authentic while
    # avoiding unrelated fixture coverage gaps for the second canonical material.
    ctx_env = getattr(ctx, "env", {}) or {}
    if ctx.network_mode == "integration" and ctx_env.get("WXGZH_INTEGRATION_MATERIAL_ID"):
        only_mid = ctx_env["WXGZH_INTEGRATION_MATERIAL_ID"]
        materials = [m for m in materials if m["material_id"] == only_mid]
        claims = [c for c in claims if c["material_id"] == only_mid]
        if not materials or not claims:
            raise MediaRequestError(
                f"integration material {only_mid} missing from canonical registry")
    req = {
        "schema_version": "1.0", "run_id": state.run_id,
        "article": {"path": "../zh_human_writing/final_article.md",
                    "sha256": state.final_article_sha256 or sha256_file(article)},
        "materials": materials, "claims": claims,
        "asset_approvals": [
            {field: rec[field] for field in sorted(_STABLE_SINGLE_ASSET_FIELDS)}
            for _, rec in sorted(approvals["single_asset"].items())],
        "config": {
            "upload_mode": (
                "wechat_audit" if ctx.network_mode in ("fake_live", "integration")
                else "wechat_image_host"
            ),
            "network_mode": (
                "offline_fixture" if ctx.network_mode in ("fake_live", "integration")
                else "live"
            ),
            "max_images_per_material": int(ctx_env.get("WXGZH_MEDIA_MAX_PER_MATERIAL", 8)),
            "max_total_images": int(ctx_env.get("WXGZH_MEDIA_MAX_TOTAL", 8)),
            "allow_unknown_license_for_publish": False,
        },
        "provenance": {"canonical_registry_sha256": sha256_file(reg_p),
                       "deduplicated_items_sha256": sha256_file(dedup_p),
                       "material_mapping_verified": True,
                       "verified_material_count": verified_material_count,
                       "copyright_approvals_bound": approvals["count"]},
    }
    req_path = sd / (
        "media_discovery_request.json" if phase == "discover"
        else "media_continuation_request.json"
    )
    req_path.write_text(json.dumps(req, ensure_ascii=False, indent=2, sort_keys=True),
                        encoding="utf-8", newline="\n")
    if getattr(ctx, "skills_home", None) or (getattr(ctx, "env", {}) or {}).get(
            "WXGZH_FIXED_MEDIA_ROOT"):
        validation = _validate_with_fixed_media(ctx, req_path)
        (sd / f"{phase}_request_validation.json").write_text(
            json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8", newline="\n",
        )
    return req_path


def _entry_args(
    ctx, stage: str, sd: Path, state, req_path: Path | None, *,
    media_phase: str = "discover", discovery_manifest: Path | None = None,
) -> list:
    rd = Path(ctx.run_dir)
    if stage == "media_enrichment":
        phase_dir = sd / media_phase
        args = ["--phase", media_phase, "--request", str(req_path),
                "--output-dir", str(phase_dir)]
        fixture_html = (getattr(ctx, "env", {}) or {}).get("WXGZH_MEDIA_FIXTURE_DIR")
        if fixture_html:
            args.extend(["--fixture-dir", fixture_html])
        if media_phase == "continue":
            args.extend(["--discovery-manifest", str(discovery_manifest)])
        return args
    if stage == "gzh_design":
        return ["--article", str(_frozen_article(ctx)),
                "--bindings", str(rd / "media_enrichment" / "article_image_bindings.json"),
                "--output-dir", str(sd), "--theme", "smartisan"]
    raise ValueError(stage)


def _validator_args(stage: str, sd: Path, req_path: Path | None) -> list:
    if stage == "media_enrichment":
        continue_dir = sd / "continue"
        return ["--manifest", str(continue_dir / "media_manifest.json"),
                "--request", str(req_path),
                "--bindings", str(continue_dir / "article_image_bindings.json")]
    if stage == "gzh_design":
        return [str(sd / "final.html")]  # validate_gzh_html.py takes a positional path
    return []


def _subprocess(ctx, stage, sd, expected, state):
    entry, validator = EM.resolve_entry(stage, ctx.network_mode, ctx.skills_home)
    req_path = None
    if stage == "media_enrichment":
        if ctx.network_mode == "fake_live":
            return _media_fake_live(ctx, sd, expected, state, entry, validator)
        return _media_two_phase(ctx, sd, expected, state, entry, validator)
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


def _media_fake_live(ctx, sd, expected, state, entry, validator):
    """Compatibility fake-live path; request still uses the fixed media contract."""
    try:
        request_path = _build_media_request(ctx, sd, state, phase="discover")
    except MediaRequestError as exc:
        return [], {
            "exec_kind": EM.SUBPROC, "invoked_entrypoint": str(entry),
            "entrypoint_path": str(entry),
            "entrypoint_sha256": sha256_file(entry) if Path(entry).is_file() else None,
            "media_request_failed": str(exc),
            "entry_run": {"exit_code": 2, "stderr": f"FAIL_CLOSED: {exc}"},
        }
    run = run_script(
        entry, ["--request", str(request_path), "--output-dir", str(sd)], timeout=300)
    meta = {
        "exec_kind": EM.SUBPROC, "invoked_entrypoint": str(entry),
        "entrypoint_path": run["script_path"], "entrypoint_sha256": run["script_sha256"],
        "entry_run": {"command": run["command"], "exit_code": run["exit_code"],
                      "elapsed": run["elapsed_seconds"],
                      "stdout_sha256": run["stdout_sha256"],
                      "stderr_sha256": run["stderr_sha256"],
                      "stderr": run["stderr"][-400:] if run["exit_code"] else ""},
    }
    if run["exit_code"] == 0 and validator:
        vr = run_script(
            validator,
            ["--manifest", str(sd / "media_manifest.json"),
             "--request", str(request_path),
             "--bindings", str(sd / "article_image_bindings.json")],
            timeout=180,
        )
        meta["official_validator"] = _vresult(vr)
    return [sd / name for name in expected if (sd / name).is_file()], meta


def _media_two_phase(ctx, sd, expected, state, entry, validator):
    """State-machine-owned media discover/continue execution.

    First invocation runs discover and returns an explicit clean pause. Resume
    requires a stable approval file bound to the frozen discovery manifest,
    rebuilds and independently validates the continuation request, then invokes
    continue and the official media validator. Final outputs are copied only
    after both processes succeed.
    """
    discover_dir = sd / "discover"
    continue_dir = sd / "continue"
    frozen = discover_dir / "asset_discovery_manifest.json"
    approval_file = sd / "copyright_approval.json"

    try:
        if not frozen.is_file():
            request_path = _build_media_request(ctx, sd, state, phase="discover")
            run = run_script(
                entry,
                _entry_args(ctx, "media_enrichment", sd, state, request_path,
                            media_phase="discover"),
                timeout=300,
            )
            events_path = discover_dir / "upload_events.json"
            zero_upload = False
            if events_path.is_file():
                try:
                    zero_upload = not json.loads(
                        events_path.read_text(encoding="utf-8")).get("events", [])
                except ValueError:
                    zero_upload = False
            meta = {
                "exec_kind": EM.SUBPROC,
                "invoked_entrypoint": str(entry),
                "entrypoint_path": run["script_path"],
                "entrypoint_sha256": run["script_sha256"],
                "entry_run": {"command": run["command"], "exit_code": run["exit_code"],
                              "elapsed": run["elapsed_seconds"],
                              "stdout_sha256": run["stdout_sha256"],
                              "stderr_sha256": run["stderr_sha256"],
                              "stderr": run["stderr"][-400:] if run["exit_code"] else ""},
                "media_phase": "discover",
                "discovery_zero_upload_events": zero_upload,
            }
            if run["exit_code"] != 0:
                return [], meta
            if not frozen.is_file() or not zero_upload:
                meta["entry_run"]["exit_code"] = 2
                meta["entry_run"]["stderr"] = (
                    "FAIL_CLOSED: discovery manifest missing or upload events not empty")
                return [], meta
            meta["await_media_approval"] = True
            meta["discovery_manifest"] = str(frozen)
            meta["approval_file"] = str(approval_file)
            return [], meta

        if not approval_file.is_file():
            return [], {
                "exec_kind": EM.SUBPROC,
                "invoked_entrypoint": str(entry),
                "entrypoint_path": str(entry),
                "entrypoint_sha256": sha256_file(entry),
                "entry_run": {"exit_code": None, "stderr": ""},
                "media_phase": "awaiting_approval",
                "await_media_approval": True,
                "discovery_manifest": str(frozen),
                "approval_file": str(approval_file),
            }

        discovery = json.loads(frozen.read_text(encoding="utf-8"))
        if discovery.get("discovery_manifest_sha256") != _canonical_discovery_sha(discovery):
            raise MediaRequestError("frozen discovery manifest sha256 invalid")
        approval_data = json.loads(approval_file.read_text(encoding="utf-8"))
        stable = [a for a in approval_data.get("approvals", [])
                  if a.get("approved_scope") == "single_asset"]
        frozen_by_id = {a["asset_id"]: a for a in discovery.get("assets", [])}
        for approval in stable:
            if not _STABLE_SINGLE_ASSET_FIELDS.issubset(approval):
                raise MediaRequestError("old single_asset approval rejected")
            frozen_asset = frozen_by_id.get(approval.get("asset_id"))
            if frozen_asset is None:
                raise MediaRequestError("single_asset approval target missing from frozen manifest")
            checks = {
                **frozen_asset,
                "discovery_manifest_sha256": discovery["discovery_manifest_sha256"],
            }
            for field in (
                "asset_id", "material_id", "source_page_url", "resolved_original_url",
                "asset_sha256", "asset_identity_sha256", "discovery_manifest_sha256",
            ):
                if approval.get(field) != checks.get(field):
                    raise MediaRequestError(
                        f"single_asset approval does not match frozen manifest: {field}")

        request_path = _build_media_request(ctx, sd, state, phase="continue")
        run = run_script(
            entry,
            _entry_args(ctx, "media_enrichment", sd, state, request_path,
                        media_phase="continue", discovery_manifest=frozen),
            timeout=300,
        )
        meta = {
            "exec_kind": EM.SUBPROC,
            "invoked_entrypoint": str(entry),
            "entrypoint_path": run["script_path"],
            "entrypoint_sha256": run["script_sha256"],
            "entry_run": {"command": run["command"], "exit_code": run["exit_code"],
                          "elapsed": run["elapsed_seconds"],
                          "stdout_sha256": run["stdout_sha256"],
                          "stderr_sha256": run["stderr_sha256"],
                          "stderr": run["stderr"][-400:] if run["exit_code"] else ""},
            "media_phase": "continue",
        }
        if run["exit_code"] == 0 and validator:
            vr = run_script(
                validator,
                _validator_args("media_enrichment", sd, request_path),
                timeout=180,
            )
            meta["official_validator"] = _vresult(vr)
            if vr["exit_code"] == 0:
                for name in expected:
                    source = continue_dir / name
                    if source.is_file():
                        (sd / name).write_bytes(source.read_bytes())
        outputs = [sd / name for name in expected if (sd / name).is_file()]
        return outputs, meta
    except (OSError, ValueError, KeyError, TypeError, MediaRequestError) as exc:
        return [], {
            "exec_kind": EM.SUBPROC,
            "invoked_entrypoint": str(entry),
            "entrypoint_path": str(entry),
            "entrypoint_sha256": sha256_file(entry),
            "media_request_failed": str(exc),
            "entry_run": {"exit_code": 2, "stderr": f"FAIL_CLOSED: {exc}"},
        }


def _wechat(ctx, stage, sd, expected, state):
    if not ctx.create_wechat_draft:
        return [], {"exec_kind": EM.WECHAT, "skipped": "create_wechat_draft=False"}
    entry, _ = EM.resolve_entry(stage, ctx.network_mode, ctx.skills_home)
    html = Path(ctx.run_dir) / "gzh_design" / "final.html"
    args = ["--html", str(html), "--title", (state.topic or "wxgzh article")[:60],
            "--audit-dir", str(sd)]
    if ctx.network_mode in ("fake_live", "integration"):
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
