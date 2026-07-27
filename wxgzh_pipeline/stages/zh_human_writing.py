"""Stage 3 — zh-human-writing. De-AI only; freeze final_article.md + sha256.
Gates: all fact-preservation counters == 0, no reader-facing internal terms.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import subskill_validator_sha

STAGE = "zh_human_writing"
STAGE_CONFIG = {"responsibility": "de-AI only; no new facts; freeze article"}
_VALIDATOR_REL = "scripts/fidelity_guard.py"
_ZERO_GATES = ["NEW_UNREGISTERED_FACTS", "NUMBER_CHANGES", "ATTRIBUTION_LOSS",
               "QUALIFIER_LOSS", "CLAIM_SEMANTIC_CHANGE", "HARD_RESIDUE"]
_FORBIDDEN_TERMS = ["本次抓取", "这次检索", "输入材料", "素材库", "Material", "Claim",
                    "Validator", "Agent", "流水线", "系统没有找到", "根据提供的材料"]


def stage_inputs(ctx, state):
    return {"super_writer_article": "../super_writer/article.md"}


def invoked_entrypoint(ctx):
    return "zh-human-writing scripts/fidelity_guard.py (+ pattern_audit / change_report)"


def side_effects(ctx, state):
    return []


def content_validate(ctx, sd: Path, state):
    vpath, vsha = subskill_validator_sha(ctx, "zh-human-writing", _VALIDATOR_REL)
    fa = sd / "final_article.md"
    rep = sd / "fidelity_report.json"
    if not fa.is_file() or not rep.is_file():
        return 1, {"reason": "final_article.md or fidelity_report.json missing"}, vpath, vsha
    data = json.loads(rep.read_text(encoding="utf-8"))
    gate_vals = {g: data.get(g, 1) for g in _ZERO_GATES}
    gates_ok = all(v == 0 for v in gate_vals.values())
    text = fa.read_text(encoding="utf-8")
    term_hits = {t: text.count(t) for t in _FORBIDDEN_TERMS if t in text}
    ok = gates_ok and not term_hits
    return (0 if ok else 1), {"gates": gate_vals, "forbidden_term_hits": term_hits,
                              "ZH_HUMAN": "PASS" if ok else "FAIL"}, vpath, vsha


def post(ctx, sd, state, exit_code, report):
    fa = sd / "final_article.md"
    if exit_code == 0 and fa.is_file():
        state.final_article_sha256 = hashlib.sha256(fa.read_bytes()).hexdigest()
        state.output_hashes["final_article_sha256"] = state.final_article_sha256


def run_live(ctx, state):
    raise NotImplementedError("zh-human-writing is agent-driven; run under the agent, not dev/tests")
