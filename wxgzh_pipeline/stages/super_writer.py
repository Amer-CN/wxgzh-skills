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
    report = {
        "FULL_MODE_VALIDATOR_EXIT": exit_code,
        "length_mode": length_mode,
        "target_visible_chars": target,
        "fixed_medium_3000_forbidden": fixed_medium,
        "official_report_bound": True,
        "chapters": data.get("chapters"),
        "SUPER_WRITER": "PASS" if ok else "FAIL",
    }
    # OBS-88(档66):注入路径强制写作合同——数字结构化登记 + 代码块保真。
    # 仅 items_file 注入路径启用;正常 aihot 检索路径不强制(避免影响资讯类 RUN)。
    if ok and getattr(state, "items_file", None):
        from ..writing_contract import validate_registry_numbers, validate_codeblock_fidelity
        rd = Path(ctx.run_dir)
        items_p = rd / "aihot" / "deduplicated_items.json"
        reg_p = sd / "canonical_claim_registry.json"
        art_p = sd / "article.md"
        if not (items_p.is_file() and reg_p.is_file() and art_p.is_file()):
            ok = False
            report["reason"] = "OBS-88 FAIL: aihot items / registry / article missing"
        else:
            n_ok, n_rep = validate_registry_numbers(art_p, reg_p)
            c_ok, c_rep = validate_codeblock_fidelity(art_p, items_p)
            report["OBS88_NUMBERS"] = n_rep["OBS88_NUMBERS"]
            report["OBS88_CODEBLOCK"] = c_rep["OBS88_CODEBLOCK"]
            report["number_pairs"] = n_rep["pairs_in_article"]
            report["registered_groups"] = len(n_rep["registered"])
            report["deny_ask_covered"] = c_rep["covered_in_codeblocks"]
            if not n_ok:
                ok = False
                report["reason"] = ("OBS-88 FAIL: registry numbers missing for "
                                    + str(n_rep["missing"]))
            elif not c_ok:
                ok = False
                report["reason"] = ("OBS-88 FAIL: deny/ask codeblock coverage "
                                    f"{c_rep['covered_in_codeblocks']}/{c_rep['deny_ask_total']} "
                                    f"(min {c_rep['min_coverage']}) or prefixes missing")
        report["SUPER_WRITER"] = "PASS" if ok else "FAIL"
    return (0 if ok else 1), report, vpath, vsha


def post(ctx, sd, state, exit_code, report):
    if exit_code == 0 and report.get("chapters"):
        state.output_hashes.setdefault("super_writer", {})["chapters"] = report["chapters"]


def run_live(ctx, state):
    from ..producers import produce
    return produce(ctx, STAGE, state)
