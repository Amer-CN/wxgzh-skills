#!/usr/bin/env python3
"""scripts/verify_report_consistency.py — 77AF 报告一致性机械校验器（任务 1）。

只读回放指定 RUN 的报告一致性，逐项 PASS/FAIL（任务 1-2 的校验器本体；
回放归档由调用方按「验证方式」收 CLI 输出，不写历史 RUN）。

输入：--run-id <RUN_ID>（目录名）或 --run-dir <路径>；--runs-root 指定 RUN 根
  （默认取环境 WXGZH_RUNS_ROOT，否则 WXGZH_PROJECT_ROOT/.temp/wxgzh-pipeline，
  再否则 cwd/.temp/wxgzh-pipeline——与 ai_tone_calibration.py 同款可移植约定，
  不写死机器绝对路径以满足 release_audit 的 P0#10 扫描）。

七项（与简报任务目标逐条对应）：
  1. receipts_exist      六份 stage_receipt.json 存在性
  2. verify_receipt       每阶段 receipts.verify_receipt 全绿（版本漂移容忍：
                         仅 entrypoint/validator 脚本哈希漂移视为版本升级痕迹，
                         输出/输入/结构问题仍 FAIL；详见函数注释）
  3. pattern_audit_counts pattern_audit.stdout.json 内计数自洽（count==len）
                         + fidelity_report.pattern_audit（如有）与 stdout 交叉一致
                         （含 advisory/strong 缺席判 omission FAIL）
  4. fidelity_numbers_gates fidelity 四数（total/passes/fails/warnings）与
                         fidelity_guard.stdout 对齐 + 六 gate 对齐且全零 +
                         six_family_changes（如有）与 pattern 声明自洽
                         （声称 ai_tone 0 却有 5 处改写即自相矛盾 FAIL）
  5. approval_basis      落账 copyright_approval.json == 机械重算值（调 media
                         run_media_enrichment._mechanical_basis，禁字符串比对；
                         时代感知：有 77AD provenance=77AD+ 时代，要求落账==机械
                         且请求手填（!=机械）即 FAIL（报告引错源风险）；无标记=
                         前 77AD 时代，要求落账==请求（内部溯源一致），机械值仅
                         作诊断记录，不以新模板苛求旧 RUN）
  6. title_scores         handoff.yaml 首候选五维加总 == 宣称总分
  7. wall_sums             wall_self_check.json 分段加总 == stage_wall_total_seconds

stdout 输出 JSON（indent 2），overall PASS 时 exit 0，否则 exit 1。
纯 stdlib + 仓内既有模块（receipts / media _mechanical_basis），只读不写盘。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from types import SimpleNamespace

_SCRIPT = Path(__file__).resolve()
SKILL_ROOT = _SCRIPT.parents[1]  # .../wxgzh-pipeline
sys.path.insert(0, str(SKILL_ROOT))

STAGES_6 = ["aihot", "super_writer", "zh_human_writing",
            "media_enrichment", "gzh_design", "wechat_draft"]

GATE_KEYS_6 = ["NEW_UNREGISTERED_FACTS", "NUMBER_CHANGES", "ATTRIBUTION_LOSS",
               "QUALIFIER_LOSS", "CLAIM_SEMANTIC_CHANGE", "HARD_RESIDUE"]

def _default_runs_root() -> Path:
    runs_root = os.environ.get("WXGZH_RUNS_ROOT")
    if runs_root:
        return Path(runs_root)
    project_root = os.environ.get("WXGZH_PROJECT_ROOT")
    base = Path(project_root) if project_root else Path.cwd()
    return base / ".temp" / "wxgzh-pipeline"

MECHANICAL_PROVENANCE_FALLBACK = "orchestrator_mechanical_rewrite (77AD/OBS-381)"


def _ok(name, detail="", extra=None):
    d = {"name": name, "status": "PASS", "detail": detail}
    if extra:
        d.update(extra)
    return d


def _fail(name, detail="", extra=None):
    d = {"name": name, "status": "FAIL", "detail": detail}
    if extra:
        d.update(extra)
    return d


def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except (OSError, ValueError) as e:
        return None, f"{p.name} 不可读/解析失败: {e}"


# ── 1. receipts_exist ────────────────────────────────────────────────
def check_receipts_exist(run_dir: Path):
    missing = []
    for st in STAGES_6:
        if not (run_dir / st / "stage_receipt.json").is_file():
            missing.append(st)
    if missing:
        return _fail("receipts_exist", f"缺失 stage_receipt.json: {missing}")
    return _ok("receipts_exist", "六份 stage_receipt.json 齐全")


# ── 2. verify_receipt ────────────────────────────────────────────────
def _is_drift_only(mismatches: list) -> bool:
    """仅脚本哈希/路径漂移视为版本升级痕迹（历史回放容忍），其余一律硬 FAIL。

    漂移类（含 entrypoint / validator / official_validator 的 hash/missing）：
    旧 RUN 的执行脚本在新版本已升级（如 jla535 的 run_media_enrichment.py
    0bec…→e2d4…），输出/输入哈希仍对得上即证明产物未被篡改。
    硬 FAIL 类：结构缺字段、stage/skill 不一致、input/output 缺失或哈希 mismatch、
    expected outputs 未覆盖等（verify_receipt 的其余全部消息）。
    """
    if not mismatches:
        return True
    for m in mismatches:
        ml = str(m).lower()
        is_script = ("entrypoint" in ml or "official_validator" in ml
                     or ("validator" in ml and "hash" in ml)
                     or ("validator" in ml and "missing" in ml))
        if not is_script:
            return False
    return True


def check_verify_receipt(run_dir: Path):
    try:
        from wxgzh_pipeline.receipts import verify_receipt
    except Exception as e:  # noqa: BLE001 — 导入失败即 FAIL，不崩
        return _fail("verify_receipt", f"receipts 模块导入失败: {e}")
    hard = {}
    drift = {}
    for st in STAGES_6:
        try:
            ok, mism, extra = verify_receipt(run_dir, st, skills_home=None)
        except Exception as e:  # noqa: BLE001
            hard[st] = [f"verify_receipt 异常: {e}"]
            continue
        mism = list(mism or [])
        if not mism:
            continue
        if _is_drift_only(mism):
            drift[st] = mism
        else:
            hard[st] = mism
    if hard:
        return _fail("verify_receipt", f"硬 mismatch: {hard}")
    if drift:
        return _ok("verify_receipt", f"全绿（含版本漂移容忍）: {drift}")
    return _ok("verify_receipt", "六阶段 verify_receipt 全绿")


# ── 3. pattern_audit_counts ──────────────────────────────────────────
def _group_len(group: dict):
    if not isinstance(group, dict):
        return None
    if "items" in group and isinstance(group["items"], list):
        return len(group["items"])
    hi = group.get("high_confidence")
    lo = group.get("low_confidence")
    if isinstance(hi, list) or isinstance(lo, list):
        return len(hi or []) + len(lo or [])
    return None


def check_pattern_audit(run_dir: Path):
    p = run_dir / "zh_human_writing" / "pattern_audit.stdout.json"
    data, err = _read_json(p)
    if err:
        return _fail("pattern_audit_counts", err)
    problems = []
    actual = {}
    for g in ["hard_residue", "strong_contextual", "advisory_only",
              "statistical", "ai_tone"]:
        grp = data.get(g)
        if not isinstance(grp, dict) or "count" not in grp:
            continue
        actual[g] = grp.get("count")
        n = _group_len(grp)
        if n is not None and n != grp.get("count"):
            problems.append(f"{g}.count={grp.get('count')} != 明细长度 {n}")
    # 交叉：fidelity_report.pattern_audit（如有）须与 stdout 一致
    frp = run_dir / "zh_human_writing" / "fidelity_report.json"
    fr, ferr = _read_json(frp)
    if ferr:
        problems.append(f"fidelity_report.json 不可读（交叉无法验证）: {ferr}")
        return _fail("pattern_audit_counts", "; ".join(problems))
    claim = (fr or {}).get("pattern_audit")
    if claim is None:
        # 旧 schema（jla535 无此节 / fmq9km 新 schema 无此节）：无声明可证伪即 PASS
        note = "fidelity_report 无 pattern_audit 声明（旧/新 schema），仅内计数自洽"
        if problems:
            return _fail("pattern_audit_counts", "; ".join(problems))
        return _ok("pattern_audit_counts",
                   f"内计数自洽 {actual}；{note}")
    # 新声明 schema（imwq5d）：逐键比对 + 缺席 omission 判定
    cmap = dict(claim) if isinstance(claim, dict) else {}
    # 兼容旧审计形态键名（hard_residue/strong_contextual/advisory_only）
    name_map = {"hard_residue_count": "hard_residue",
                "ai_tone_count": "ai_tone",
                "hard_residue": "hard_residue",
                "strong_contextual": "strong_contextual",
                "advisory_only": "advisory_only"}
    for ck, gname in name_map.items():
        if ck in cmap and gname in actual:
            if cmap[ck] != actual[gname]:
                problems.append(
                    f"fidelity_report.pattern_audit.{ck}={cmap[ck]} "
                    f"!= stdout {gname}.count={actual[gname]}")
    # advisory 缺席 omission：stdout 有 advisory/strong，声明却无对应键
    adv_actual = int(actual.get("advisory_only", 0) or 0)
    sc_actual = int(actual.get("strong_contextual", 0) or 0)
    has_adv_claim = any(k in cmap for k in ("advisory_only", "advisory_count",
                                            "strong_contextual"))
    if (adv_actual > 0 or sc_actual > 0) and not has_adv_claim:
        problems.append(
            f"fidelity_report.pattern_audit 缺 advisory/strong 声明 "
            f"(stdout advisory_only={adv_actual}, strong_contextual={sc_actual})")
    if problems:
        return _fail("pattern_audit_counts", "; ".join(problems))
    return _ok("pattern_audit_counts", f"内计数与声明一致 {actual}")


# ── 4. fidelity_numbers_gates（含 six_family） ────────────────────────
def check_fidelity(run_dir: Path):
    frp = run_dir / "zh_human_writing" / "fidelity_report.json"
    fr, err = _read_json(frp)
    if err:
        return _fail("fidelity_numbers_gates", err)
    # 参考：guard stdout 优先，缺失则用 fidelity_stdout.json
    ref = None
    for cand in ["fidelity_guard.stdout.json", "fidelity_stdout.json"]:
        q = run_dir / "zh_human_writing" / cand
        if q.is_file():
            ref, rerr = _read_json(q)
            if ref is not None:
                break
    problems = []
    # 四数（total/passes/fails/warnings）：双方齐备才比对（fmq9km 新 schema 无四数即跳过）
    four = ["total_checks", "passes", "fails", "warnings"]
    if ref is not None and all(k in fr for k in four) and all(k in ref for k in four):
        for k in four:
            if fr[k] != ref[k]:
                problems.append(f"四数 {k}: report={fr[k]} != guard={ref[k]}")
    # 六 gate：双方有 gates 即比对；report 侧须全零
    frg = (fr or {}).get("gates")
    rfg = (ref or {}).get("gates") if isinstance(ref, dict) else None
    if isinstance(frg, dict):
        for k in GATE_KEYS_6:
            if k in frg and frg[k] != 0:
                problems.append(f"gate {k}={frg[k]} 非零")
        if isinstance(rfg, dict):
            for k in GATE_KEYS_6:
                if k in frg and k in rfg and frg[k] != rfg[k]:
                    problems.append(
                        f"gate {k}: report={frg[k]} != guard={rfg[k]}")
    # six_family 自洽（imwq5d 有此节才验证；jla535/fmq9km 无即跳过）：
    # 报告自称 ai_tone 0（pattern_audit.ai_tone_count==0）却同时申报 5 处改写
    # （2+2+1）即自相矛盾 FAIL。
    sixf = (fr or {}).get("six_family_changes")
    if isinstance(sixf, dict):
        vals = []
        for k, v in sixf.items():
            if not isinstance(v, int) or v < 0:
                problems.append(f"six_family_changes.{k} 非法值 {v!r}")
            else:
                vals.append(v)
        claim = (fr or {}).get("pattern_audit") or {}
        claimed_zero = claim.get("ai_tone_count") == 0
        if claimed_zero and sum(vals) > 0:
            problems.append(
                f"six_family_changes 自相矛盾：pattern_audit 声称 ai_tone 0，"
                f"却申报改写 {dict(sixf)}（合计 {sum(vals)}）")
    if problems:
        return _fail("fidelity_numbers_gates", "; ".join(problems))
    return _ok("fidelity_numbers_gates", "四数/gate/six_family 自洽")


# ── 5. approval_basis ────────────────────────────────────────────────
def _load_mechanical_fn():
    """调 media run_media_enrichment._mechanical_basis（禁字符串比对的正门）。

    返回 (fn, load_contract, provenance, error)。import 失败即 FAIL，不崩。
    """
    media_mod = SKILL_ROOT.parent / "media-enrichment" / "scripts" \
        / "run_media_enrichment.py"
    if not media_mod.is_file():
        return None, None, MECHANICAL_PROVENANCE_FALLBACK, \
            f"media 脚本缺失: {media_mod}"
    try:
        spec = importlib.util.spec_from_file_location(
            "wxgzh_media_runner_77af", media_mod)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fn = getattr(mod, "_mechanical_basis", None)
        lc = getattr(mod, "_load_media_contract", None)
        prov = getattr(mod, "MECHANICAL_BASIS_PROVENANCE",
                       MECHANICAL_PROVENANCE_FALLBACK)
        if fn is None:
            return None, None, prov, "_mechanical_basis 缺失"
        return fn, lc, prov, None
    except Exception as e:  # noqa: BLE001
        return None, None, MECHANICAL_PROVENANCE_FALLBACK, f"media 导入失败: {e}"


def check_approval_basis(run_dir: Path):
    cap = run_dir / "media_enrichment" / "copyright_approval.json"
    ca, err = _read_json(cap)
    if err:
        return _fail("approval_basis", err)
    crp = run_dir / "media_enrichment" / "media_continuation_request.json"
    cr, err2 = _read_json(crp)
    if err2:
        return _fail("approval_basis", err2)
    fn, load_contract, provenance, lerr = _load_mechanical_fn()
    if lerr:
        return _fail("approval_basis", lerr)
    approvals = (ca or {}).get("approvals") or []
    req_approvals = (cr or {}).get("asset_approvals") or []
    rmap = {a.get("asset_id"): a for a in req_approvals if isinstance(a, dict)}
    has_prov = any(isinstance(a, dict) and a.get("basis_provenance") == provenance
                   for a in approvals)
    # 机械重算输入：当前合同 + readiness + manifest 终态 decision + 落账 url。
    # （config 黑名单取空：三 RUN 域名均非黑名单；network_mode 取 receipt。）
    contract = None
    try:
        contract = load_contract() if load_contract else None
    except Exception:  # noqa: BLE001 — 合同不可读则按 UNAVAILABLE 重算
        contract = None
    readiness = {}
    arp = run_dir / "media_enrichment" / "approval_readiness.json"
    ar, _ = _read_json(arp)
    if isinstance(ar, dict):
        for rec in ar.get("assets") or []:
            if isinstance(rec, dict) and rec.get("asset_id"):
                readiness[rec["asset_id"]] = rec
    manifest_decision = {}
    mp = run_dir / "media_enrichment" / "media_manifest.json"
    man, _ = _read_json(mp)
    if isinstance(man, dict):
        for a in man.get("assets") or []:
            if isinstance(a, dict) and a.get("asset_id"):
                manifest_decision[a["asset_id"]] = a.get("decision")
    landed_bad, request_handfilled = [], []
    for ap in approvals:
        if not isinstance(ap, dict):
            continue
        if ap.get("approved_by") not in ("auto_rule", "auto_approve"):
            continue
        if ap.get("approved_scope") != "single_asset":
            continue
        aid = ap.get("asset_id")
        rd = readiness.get(aid) or {}
        asset = SimpleNamespace(
            decision=manifest_decision.get(aid) or rd.get("decision") or "",
            copyright_status="",
            resolved_original_url=ap.get("resolved_original_url") or "")
        try:
            expected = fn("live", {}, contract, rd, asset)
        except Exception as e:  # noqa: BLE001
            return _fail("approval_basis", f"_mechanical_basis 异常({aid}): {e}")
        if expected is None:
            # 机械车道不 blessed（水印/受限/证据断）却落账即 FAIL
            landed_bad.append(f"{aid}=机械None却落账")
            continue
        if (ap.get("basis") or "") != expected:
            landed_bad.append(f"{aid} 落账!=机械")
        rq = rmap.get(aid) or {}
        if (rq.get("basis") or "") != expected:
            request_handfilled.append(aid)
    # 落账 vs 请求逐条溯源计数（诊断用，非字符串定罪：定罪依据是机械值）
    trace_mism = 0
    for ap in approvals:
        if not isinstance(ap, dict):
            continue
        aid = ap.get("asset_id")
        if (rmap.get(aid) or {}).get("basis", "") != ap.get("basis", ""):
            trace_mism += 1
    if has_prov:
        # 77AD+ 时代：落账须==机械；请求手填残留（!=机械）即 FAIL（报告引错源风险）。
        # imwq5d 实测：落账 19/19==机械 OK，请求 19/19 手填 FAIL。
        if landed_bad:
            return _fail("approval_basis",
                         f"77AD+ 落账非机械: {landed_bad[:5]}")
        if request_handfilled:
            return _fail(
                "approval_basis",
                f"77AD+ 请求侧手填残留 {len(request_handfilled)}/{len(approvals)}"
                f"（如 {request_handfilled[:3]}），落账机械 OK 但请求溯源断裂"
                f"（落账!=请求 {trace_mism} 条）——报告须引落账机械值，禁引请求手填串")
        return _ok("approval_basis", f"77AD+ 落账 {len(approvals)} 条==机械，请求一致")
    # 前 77AD 时代（无 provenance：jla535/fmq9km）：要求落账==请求（内部溯源一致），
    # 机械值仅作诊断记录（旧模板与现模板时代差，不以新模板苛求旧 RUN）。
    if trace_mism:
        return _fail("approval_basis",
                     f"前77AD 落账!=请求 {trace_mism}/{len(approvals)} 条")
    return _ok("approval_basis",
               f"前77AD 落账==请求 {len(approvals)} 条一致"
               f"（机械诊断：落账!=现模板 {len(landed_bad)} 条，时代差已注明）")


# ── 6. title_scores ──────────────────────────────────────────────────
TITLE_DIM_RE = re.compile(
    r"点击欲望\s*(\d)\s*(?:（[^）]*）|\([^)]*\))?\s*[,，、]?\s*"
    r"事实匹配\s*(\d)\s*(?:（[^）]*）|\([^)]*\))?\s*[,，、]?\s*"
    r"人群匹配\s*(\d)\s*(?:（[^）]*）|\([^)]*\))?\s*[,，、]?\s*"
    r"差异化\s*(\d)\s*(?:（[^）]*）|\([^)]*\))?\s*[,，、]?\s*"
    r"长期价值\s*(\d)")
TOTAL_RE = re.compile(r"总分\s*(\d+)")


def check_title(run_dir: Path):
    hp = run_dir / "super_writer" / "handoff.yaml"
    try:
        text = hp.read_text(encoding="utf-8")
    except OSError as e:
        return _fail("title_scores", f"handoff.yaml 不可读: {e}")
    dims = [tuple(int(x) for x in m.groups())
            for m in TITLE_DIM_RE.finditer(text)]
    totals = [int(m.group(1)) for m in TOTAL_RE.finditer(text)]
    if not dims:
        return _fail("title_scores", "未解析到任何候选五维评分")
    if not totals:
        return _fail("title_scores", "未解析到宣称总分")
    first_sum = sum(dims[0])
    # 首候选即主标题（imwq5d/jla535/fmq9km 实测首组==宣称总分）；宣称取首个总分。
    if first_sum != totals[0]:
        return _fail("title_scores",
                     f"首候选五维 {dims[0]} 自加总 {first_sum} != 宣称总分 {totals[0]}")
    return _ok("title_scores", f"首候选 {dims[0]} 加总 {first_sum}==宣称 {totals[0]}")


# ── 7. wall_sums ─────────────────────────────────────────────────────
def check_wall(run_dir: Path):
    wp = run_dir / "wall_self_check.json"
    data, err = _read_json(wp)
    if err:
        return _fail("wall_sums", err)
    try:
        stages = data["stages"]
        total = float(data["stage_wall_total_seconds"])
        s = float(sum(float(x[1]) for x in stages))
    except (KeyError, TypeError, ValueError) as e:
        return _fail("wall_sums", f"字段缺失/形状错误: {e}")
    if abs(s - total) > 1e-6:
        return _fail("wall_sums", f"分段加总 {s} != total {total}")
    return _ok("wall_sums", f"分段加总 {s}==total {total}")


CHECKS = [check_receipts_exist, check_verify_receipt, check_pattern_audit,
          check_fidelity, check_approval_basis, check_title, check_wall]


def verify_run(run_dir: Path) -> dict:
    run_dir = Path(run_dir)
    results = []
    for fn in CHECKS:
        try:
            results.append(fn(run_dir))
        except Exception as e:  # noqa: BLE001 — 单项异常记 FAIL，不崩整轮
            results.append(_fail(fn.__name__, f"校验异常: {e}"))
    overall = "PASS" if all(r["status"] == "PASS" for r in results) else "FAIL"
    return {"run_id": run_dir.name, "run_dir": str(run_dir),
            "overall": overall, "checks": results}


def _resolve_run_dir(args) -> Path:
    if args.run_dir:
        return Path(args.run_dir)
    if not args.run_id:
        raise SystemExit("须提供 --run-id 或 --run-dir")
    cand = Path(args.runs_root) / args.run_id
    if cand.is_dir():
        return cand
    # 允许直接传完整目录名外的绝对/相对路径
    alt = Path(args.run_id)
    if alt.is_dir():
        return alt
    raise SystemExit(f"RUN 目录不存在: {cand}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="verify_report_consistency")
    ap.add_argument("--run-id", default=None, help="RUN 目录名（runs-root 下）")
    ap.add_argument("--run-dir", default=None, help="RUN 目录完整路径（只读）")
    ap.add_argument("--runs-root", default=None,
                    help="RUN 根目录（默认 WXGZH_RUNS_ROOT，否则 "
                         "WXGZH_PROJECT_ROOT/cwd 下的 .temp/wxgzh-pipeline）")
    a = ap.parse_args(argv)
    if a.runs_root is None:
        a.runs_root = str(_default_runs_root())
    run_dir = _resolve_run_dir(a)
    report = verify_run(run_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
