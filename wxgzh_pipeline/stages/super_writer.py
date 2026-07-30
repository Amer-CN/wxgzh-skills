"""Stage 2 — Super Writer Material-Heavy Full Mode. Gate: FULL_MODE_VALIDATOR_EXIT=0."""
from __future__ import annotations

import json
from pathlib import Path

from . import subskill_validator_sha

STAGE = "super_writer"
STAGE_CONFIG = {"mode": "material_heavy_full_mode", "length": "auto_by_fact_density"}
_VALIDATOR_REL = "scripts/validate_article_length.py"


def stage_inputs(ctx, state):
    return {"deduplicated_items": "../aihot/deduplicated_items.json", "topic": state.topic}


def invoked_entrypoint(ctx):
    return "super-writer scripts/validate_article_length.py --full-mode (+ material_ingestion / validate_semantic_map)"


def side_effects(ctx, state):
    return []


def content_validate(ctx, sd: Path, state):
    vpath, vsha = subskill_validator_sha(ctx, "super-writer", _VALIDATOR_REL)
    rep = sd / "full_mode_validator_report.json"
    if not rep.is_file():
        return 1, {"reason": "full_mode_validator_report.json missing"}, vpath, vsha
    data = json.loads(rep.read_text(encoding="utf-8"))
    exit_code = 0 if data.get("passed") is True else 1
    length_mode = data.get("article_mode")
    target = data.get("target_visible_chars")
    fixed_medium = length_mode == "medium" and target == 3000 and data.get("policy_source") == "fixed_default"
    ok = exit_code == 0 and not fixed_medium
    return (0 if ok else 1), {
        "FULL_MODE_VALIDATOR_EXIT": exit_code,
        "length_mode": length_mode,
        "target_visible_chars": target,
        "fixed_medium_3000_forbidden": fixed_medium,
        "official_report_bound": True,
        "chapters": data.get("chapters"),
        "SUPER_WRITER": "PASS" if ok else "FAIL",
    }, vpath, vsha


def post(ctx, sd, state, exit_code, report):
    if exit_code == 0 and report.get("chapters"):
        state.output_hashes.setdefault("super_writer", {})["chapters"] = report["chapters"]


def run_live(ctx, state):
    from ..producers import produce
    return produce(ctx, STAGE, state)
