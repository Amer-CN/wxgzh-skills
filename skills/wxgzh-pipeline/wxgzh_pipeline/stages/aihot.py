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
    # OBS-64(档64):注入路径不调用 AI HOT API,副作用如实声明为 none
    if getattr(state, "items_file", None):
        return [{"type": "none",
                 "detail": "自有素材注入(--items-file),无 AI HOT API 调用(注入事实见 fetch_log)"}]
    return [{"type": "network_read", "detail": "anonymous read-only AI HOT API"}]


def content_validate(ctx, sd: Path, state):
    dedup = sd / "deduplicated_items.json"
    vpath = str(SKILL_ROOT / "validators" / "validate_stage_receipt.py")
    import hashlib
    vsha = hashlib.sha256(Path(vpath).read_bytes()).hexdigest() if Path(vpath).is_file() else None
    if not dedup.is_file():
        return 1, {"reason": "deduplicated_items.json missing"}, vpath, vsha
    try:
        items = json.loads(dedup.read_text(encoding="utf-8"))
    except Exception as e:
        return 1, {"reason": f"dedup unreadable: {e}"}, vpath, vsha
    n = len(items) if isinstance(items, list) else 0
    ok = n >= 1
    report = {"deduplicated_count": n, "AIHOT": "PASS" if ok else "FAIL"}
    # OBS-64(档64):素材注入正门——旧的非正式通道(user_materials_override)
    # 一律 FAIL_CLOSED;正式注入(items_file_injection)必须与注入块一致。
    fetch_log_p = sd / "fetch_log.json"
    if fetch_log_p.is_file():
        try:
            fetch_log = json.loads(fetch_log_p.read_text(encoding="utf-8"))
        except Exception as e:
            return 1, {"reason": f"fetch_log unreadable: {e}"}, vpath, vsha
        mode = fetch_log.get("mode")
        if mode == "user_materials_override":
            return 1, {"reason": "user_materials_override 非正式通道已关闭(档64)",
                       "AIHOT": "FAIL"}, vpath, vsha
        if mode == "items_file_injection":
            inj = fetch_log.get("injection")
            problems = []
            if not isinstance(inj, dict):
                problems.append("injection block missing")
            else:
                if inj.get("item_count") != n:
                    problems.append("item_count mismatch")
                prov = inj.get("provenance")
                if not isinstance(prov, list) or len(prov) != n:
                    problems.append("provenance incomplete")
                else:
                    ids = {p.get("id") for p in prov}
                    if ids != {it.get("id") for it in items}:
                        problems.append("provenance id mismatch")
            if problems:
                return 1, {"reason": f"material injection inconsistent: {problems}",
                           "AIHOT": "FAIL"}, vpath, vsha
            report["injection"] = {"mode": "items_file_injection",
                                   "items_file_sha256": inj.get("items_file_sha256"),
                                   "item_count": n}
            report["AIHOT"] = "PASS(INJECTED)" if ok else "FAIL"
    return (0 if ok else 1), report, vpath, vsha


def post(ctx, sd, state, exit_code, report):
    if exit_code == 0:
        state.output_hashes.setdefault("aihot", {})["deduplicated_count"] = report.get("deduplicated_count")


def run_live(ctx, state):
    from ..producers import produce
    return produce(ctx, STAGE, state)
