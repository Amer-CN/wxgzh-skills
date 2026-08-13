#!/usr/bin/env python3
"""72E-1/Batch 3:材料门按 article_mode 分档校验(确定性)。

分档表(任务书摘要逐字):
- short:     无下限
- medium:    独立素材 >=3
- long:      独立素材 >=5
- deep:      每 core claim >=2 件独立材料,且覆盖率 100%
- digest:    单一来源占比 <=40%(daily_digest 与 weekly_roundup 同属聚合体裁,归 digest 档)
- synthesis: 输入覆盖率 100%(material_synthesis)

判定字段来源:
- material-ledger.yaml: 独立素材(状态非 deduplicated)、来源分布、claims(supporting_events)、events(materials)
- material-ingestion-report.json: claim_coverage / source_coverage / event_coverage

任一档无法用上述字段确定性评估 → 判定不通过并给出明确 reason,不降格为概率判断。

退出码:0=通过,1=未通过。--output 指定时写 JSON 判定结果。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

ALLOWED_MODES = {
    "short", "medium", "long", "deep",
    "daily_digest", "weekly_roundup", "material_synthesis",
}
# 聚合体裁归 digest 档(72E-1 审核方重建裁决,用户可否决)
DIGEST_MODES = {"daily_digest", "weekly_roundup"}


def _independent_materials(ledger: dict) -> list[dict]:
    """独立素材 = material_ledger.materials 中状态非 deduplicated 的条目。"""
    ml = ledger.get("material_ledger", {}) if isinstance(ledger, dict) else {}
    mats = ml.get("materials", []) if isinstance(ml, dict) else []
    return [m for m in mats if isinstance(m, dict) and m.get("status") != "deduplicated"]


def _single_source_ratio(materials: list[dict]) -> float:
    """单一来源占比 = 最大同源素材数 / 素材总数(source_url 归一后计数)。"""
    if not materials:
        return 0.0
    counts: dict[str, int] = {}
    for m in materials:
        url = (m.get("source_url") or "").strip().lower().rstrip("/")
        counts[url] = counts.get(url, 0) + 1
    return max(counts.values()) / len(materials)


def _claim_material_counts(ledger: dict, materials: list[dict]) -> list[int]:
    """每个 claim 的独立支撑材料数。

    claim.supporting_events -> events.materials -> 状态非 deduplicated 的素材 id 去重。
    ledger 无 claims 段或结构不完整 -> 返回 []。
    """
    ml = ledger.get("material_ledger", {}) if isinstance(ledger, dict) else {}
    claims = ml.get("claims", []) if isinstance(ml, dict) else []
    events = ml.get("events", []) if isinstance(ml, dict) else []
    if not isinstance(claims, list) or not claims:
        return []
    evt_map: dict[str, list] = {}
    for e in events if isinstance(events, list) else []:
        if isinstance(e, dict):
            evt_map[e.get("id", "")] = e.get("materials", []) or []
    active_ids = {m.get("id") for m in materials}
    counts = []
    for c in claims:
        if not isinstance(c, dict):
            counts.append(0)
            continue
        sup = c.get("supporting_events", []) or []
        ids = set()
        for eid in sup:
            ids.update(mid for mid in evt_map.get(eid, []) if mid in active_ids)
        counts.append(len(ids))
    return counts


def evaluate(mode: str, ledger: dict, report: dict) -> dict:
    """逐档判定。返回 {mode, passed, reason, stats}。"""
    materials = _independent_materials(ledger)
    stats = {"independent_materials": len(materials),
             "single_source_ratio": round(_single_source_ratio(materials), 4)}
    if mode not in ALLOWED_MODES:
        return {"mode": mode, "passed": False,
                "reason": f"unknown article_mode '{mode}'", "stats": stats}

    if mode == "short":
        return {"mode": mode, "passed": True,
                "reason": "short:无下限", "stats": stats}

    if mode == "medium":
        ok = len(materials) >= 3
        return {"mode": mode, "passed": ok,
                "reason": f"medium:独立素材 {len(materials)} >= 3" if ok
                          else f"medium:独立素材 {len(materials)} < 3", "stats": stats}

    if mode == "long":
        ok = len(materials) >= 5
        return {"mode": mode, "passed": ok,
                "reason": f"long:独立素材 {len(materials)} >= 5" if ok
                          else f"long:独立素材 {len(materials)} < 5", "stats": stats}

    if mode == "deep":
        counts = _claim_material_counts(ledger, materials)
        claim_cov = report.get("claim_coverage")
        if not counts:
            return {"mode": mode, "passed": False,
                    "reason": "deep:ledger 无 claims 结构,无法确定性评估每 core claim 材料数",
                    "stats": stats}
        min_support = min(counts)
        cov_ok = claim_cov is not None and claim_cov >= 1.0
        ok = min_support >= 2 and cov_ok
        return {"mode": mode, "passed": ok,
                "reason": f"deep:每 claim 最少支撑 {min_support} >= 2 且 claim_coverage={claim_cov}"
                          if ok else
                          f"deep:每 claim 最少支撑 {min_support}(需 >=2)或 claim_coverage={claim_cov}(需 1.0)",
                "stats": stats}

    if mode in DIGEST_MODES:
        ratio = _single_source_ratio(materials)
        ok = ratio <= 0.4
        return {"mode": mode, "passed": ok,
                "reason": f"digest({mode}):单一来源占比 {ratio:.2%} <= 40%" if ok
                          else f"digest({mode}):单一来源占比 {ratio:.2%} > 40%", "stats": stats}

    if mode == "material_synthesis":
        claim_cov = report.get("claim_coverage")
        if claim_cov is None:
            return {"mode": mode, "passed": False,
                    "reason": "synthesis:ingestion report 无 claim_coverage,无法评估输入覆盖率",
                    "stats": stats}
        ok = claim_cov >= 1.0
        return {"mode": mode, "passed": ok,
                "reason": f"synthesis:输入覆盖率 claim_coverage={claim_cov} == 100%" if ok
                          else f"synthesis:输入覆盖率 claim_coverage={claim_cov} < 100%",
                "stats": stats}

    return {"mode": mode, "passed": False, "reason": f"unhandled mode '{mode}'", "stats": stats}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="材料门按 article_mode 分档校验")
    ap.add_argument("--ledger", required=True, help="material-ledger.yaml")
    ap.add_argument("--report", required=True, help="material-ingestion-report.json")
    ap.add_argument("--mode", required=True, help="article_mode(short/medium/long/deep/daily_digest/weekly_roundup/material_synthesis)")
    ap.add_argument("--output", default=None, help="判定 JSON 输出路径(可选)")
    a = ap.parse_args(argv)

    try:
        ledger = yaml.safe_load(Path(a.ledger).read_text(encoding="utf-8")) or {}
        report = json.loads(Path(a.report).read_text(encoding="utf-8")) or {}
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: cannot read ledger/report: {exc}", file=sys.stderr)
        return 1
    if not isinstance(ledger, dict) or not isinstance(report, dict):
        print("ERROR: ledger 与 report 顶层必须是对象", file=sys.stderr)
        return 1

    result = evaluate(a.mode, ledger, report)
    if a.output:
        Path(a.output).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(f"material_gate: mode={result['mode']} passed={result['passed']} "
          f"reason={result['reason']}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
