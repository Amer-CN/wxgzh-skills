"""Stage 1 — AI HOT (agent-invoked). Fetch / aggregate / dedup only.
Live mode is agent-driven; dev/tests use offline fixtures.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import subskill_validator_sha, SKILL_ROOT

STAGE = "aihot"
STAGE_CONFIG = {"responsibility": "fetch/aggregate/dedup; no article; no image inventory"}


def stage_inputs(ctx, state):
    return {"topic": state.topic}


def invoked_entrypoint(ctx):
    return "aihot (agent-invoked skill; queries aihot.virxact.com anonymous API)"


def side_effects(ctx, state):
    return [{"type": "network_read", "detail": "anonymous read-only AI HOT API"}]


def content_validate(ctx, sd: Path, state):
    dedup = sd / "deduplicated_items.json"
    vpath = str(SKILL_ROOT / "validators" / "validate_stage_receipt.py")
    import hashlib
    vsha = hashlib.sha256(Path(vpath).read_bytes()).hexdigest() if Path(vpath).is_file() else None
    if not dedup.is_file():
        return 1, {"reason": "deduplicated_items.json missing"}, vpath, vsha
    try:
        n = len(json.loads(dedup.read_text(encoding="utf-8")))
    except Exception as e:
        return 1, {"reason": f"dedup unreadable: {e}"}, vpath, vsha
    ok = n >= 1
    return (0 if ok else 1), {"deduplicated_count": n, "AIHOT": "PASS" if ok else "FAIL"}, vpath, vsha


def post(ctx, sd, state, exit_code, report):
    if exit_code == 0:
        state.output_hashes.setdefault("aihot", {})["deduplicated_count"] = report.get("deduplicated_count")


def run_live(ctx, state):
    from ..producers import produce
    return produce(ctx, STAGE, state)
