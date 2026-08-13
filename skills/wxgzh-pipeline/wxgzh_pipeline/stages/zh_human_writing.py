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
# 76Q/OBS-284:FT-001(zh 词表禁用词 Agent/智能体助手)以 pattern_audit 分组输出
# (pattern_audit.stdout.json)为真源——strong 段命中=普通命中(阻断);advisory 段
# 命中=疑似专名降级(豁免,仅留痕)。这两词不再参与 text.count 一刀切,
# 避免「Luma Agents」等产品名被逼改写(词表 saga 第六次根因)。
_FT001_TERMS = ("Agent", "智能体助手")


def _ft_hits(pa_data):
    """从 pattern_audit 输出取 FT-001 分组命中:(strong_findings, advisory_findings)。"""
    strong, advisory = [], []
    sc = (pa_data or {}).get("strong_contextual", {}) or {}
    for bucket in ("high_confidence", "low_confidence"):
        for f in sc.get(bucket, []) or []:
            if f.get("rule_id") == "FT-001":
                strong.append(f)
    for f in ((pa_data or {}).get("advisory_only", {}) or {}).get("items", []) or []:
        if f.get("rule_id") == "FT-001":
            advisory.append(f)
    return strong, advisory


def _ft_word(finding):
    """从 finding 摘录还原命中词(span_text 自命中位置起摘录,必含命中词)。"""
    st = finding.get("span_text") or ""
    for w in _FT001_TERMS:
        if w in st:
            return w
    return "FT-001"


def _count_hits(findings):
    counts = {}
    for f in findings:
        w = _ft_word(f)
        counts[w] = counts.get(w, 0) + 1
    return counts


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
    # 76Q/OBS-284:FT-001 advisory 豁免——读 pattern_audit 分组输出。
    # 文件缺失/解析失败 → 回退旧 text.count(fail-closed,不因本改动放行)。
    pa_status = "missing"
    strong_ft, advisory_ft = [], []
    pa = sd / "pattern_audit.stdout.json"
    if pa.is_file():
        try:
            strong_ft, advisory_ft = _ft_hits(json.loads(pa.read_text(encoding="utf-8")))
            pa_status = "ok"
        except (OSError, ValueError):
            pa_status = "unparseable"
    term_hits = {t: text.count(t) for t in _FORBIDDEN_TERMS
                 if t not in _FT001_TERMS and t in text}
    if pa_status == "ok":
        term_hits.update(_count_hits(strong_ft))
    else:
        # 回退:FT-001 词回到 text.count 一刀切(与旧行为逐字一致)。
        for t in _FT001_TERMS:
            if t in text:
                term_hits[t] = text.count(t)
    ok = gates_ok and not term_hits
    report = {"gates": gate_vals, "forbidden_term_hits": term_hits,
              "pattern_audit_report": pa_status,
              "ZH_HUMAN": "PASS" if ok else "FAIL"}
    if pa_status == "ok":
        # 留痕不阻断:疑似专名降级命中(76Q/OBS-284)。
        report["forbidden_term_advisory"] = _count_hits(advisory_ft)
    return (0 if ok else 1), report, vpath, vsha


def post(ctx, sd, state, exit_code, report):
    fa = sd / "final_article.md"
    if exit_code == 0 and fa.is_file():
        state.final_article_sha256 = hashlib.sha256(fa.read_bytes()).hexdigest()
        state.output_hashes["final_article_sha256"] = state.final_article_sha256


def run_live(ctx, state):
    from ..producers import produce
    return produce(ctx, STAGE, state)
