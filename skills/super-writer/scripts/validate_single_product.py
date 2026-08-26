#!/usr/bin/env python3
"""76F/OBS-277:关键产物单文件预校验 —— agent 每写出一个产物即可自检,
失败立即返回可执行错误(缺哪个字段/期望形状),不必等阶段末 full-mode 一次性爆炸。

用法:
    python scripts/validate_single_product.py --product outline --file outline.md \
        [--target-visible-chars 3000]
    python scripts/validate_single_product.py --product core-card --file core-card.md
    python scripts/validate_single_product.py --product semantic-map --file semantic-map.yaml
    python scripts/validate_single_product.py --product handoff --file handoff.yaml
    python scripts/validate_single_product.py --product registry --file canonical_claim_registry.json

输出 JSON:{"product","file","valid","errors":[...],"checks":{...}};exit 0=通过,1=失败。
校验语义与生产校验器同源(import validate_article_length 的解析函数),不放宽任何质量门禁。
"""
from __future__ import annotations

import argparse
import json
import sys
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import yaml  # noqa: E402

from validate_article_length import parse_outline_budgets  # noqa: E402

# 76A/OBS-252:handoff full-mode 必填字段(与 validate_article_length 同源)
HANDOFF_REQUIRED_FIELDS = ["schema_version", "prose_craft_applied",
                           "prose_craft_version", "formatter.cover"]
# 76A/76B:标题与钩子字段(存在性 + 类型)
HANDOFF_TITLE_FIELDS = {"title_candidates": list, "hook_line": str,
                        "selected_title": str, "title_selection_reason": str}

CORE_CARD_FIELDS = ["Core Statement", "Reader Change", "Core Tension", "Value Carrier",
                   "Scope", "Result"]


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return raw.decode("utf-8")


def check_outline(path: Path, target_visible_chars: int | None = None) -> tuple[list, dict]:
    text = _read_text(path)
    sections, meta, errors = parse_outline_budgets(str(path))
    out_errors = [f"outline: {e}" for e in errors]
    if not sections:
        out_errors.append("outline: 无有效内容节(缺 ## 节或预算字段不全)")
    checks = {"sections": len(sections),
              "meta_target": meta.get("target_visible_chars")}
    if target_visible_chars is not None and sections:
        total_planned = sum(int(s.get("planned_chars", 0) or 0) for s in sections)
        if total_planned:
            deviation = abs(total_planned - target_visible_chars) / target_visible_chars
            checks["total_planned"] = total_planned
            checks["target_visible_chars"] = target_visible_chars
            checks["deviation"] = round(deviation, 4)
            if deviation > 0.05:
                out_errors.append(
                    f"outline: 总计划字数 {total_planned} 与目标 {target_visible_chars} "
                    f"偏差 {deviation:.1%} > 5% —— 先跑 align_outline_budget.py 对齐")
    return out_errors, checks


def check_core_card(path: Path) -> tuple[list, dict]:
    text = _read_text(path)
    out_errors = []
    # 77B/OBS-311(core-card 双格式):canonical = `字段: 内容` 同行一行式(与 full-mode
    # validate_article_length 同判);不再接受 `**字段**` 独占形态或只含标题。
    for field in CORE_CARD_FIELDS:
        m = re.search(rf'{re.escape(field)}[:：]\s*(.+)', text)
        if not m or not m.group(1).strip():
            out_errors.append(
                f"core-card: 缺 `{field}: 内容` 一行式字段(77B/OBS-311,对照 templates/core-card.md)")
    return out_errors, {"fields": CORE_CARD_FIELDS}


def check_semantic_map(path: Path) -> tuple[list, dict]:
    try:
        data = yaml.safe_load(_read_text(path))
    except yaml.YAMLError as exc:
        return [f"semantic-map: YAML 解析失败: {exc}"], {}
    out_errors = []
    if not isinstance(data, dict):
        out_errors.append("semantic-map: 顶层必须是映射")
        return out_errors, {}
    for key in ("schema_version", "article", "blocks"):
        if key not in data:
            out_errors.append(f"semantic-map: 缺顶层键 `{key}`")
    if isinstance(data.get("article"), dict) and not data["article"].get("title"):
        out_errors.append("semantic-map: article.title 为空")
    # 77F/OBS-315: semantic-map 清单缺口 — 未注册 role/payload 缺口直接拒并附合法清单指路
    # 单一真源：validate_semantic_map.py:ALLOWED_ROLES / ROLE_REQUIRED_FIELDS
    try:
        import importlib.util
        sm_path = Path(__file__).resolve().parent / "validate_semantic_map.py"
        spec = importlib.util.spec_from_file_location("vsm", str(sm_path.resolve()))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        allowed = set(mod.ALLOWED_ROLES)
        required = dict(mod.ROLE_REQUIRED_FIELDS)
        for idx, blk in enumerate(data.get("blocks") or []):
            if not isinstance(blk, dict):
                continue
            role = blk.get("role") or blk.get("type")
            if role and role not in allowed:
                out_errors.append(f"semantic-map: blocks[{idx}].role '{role}' 未注册；合法清单见 references/component-catalog.md（单一真源 validate_semantic_map.py:ALLOWED_ROLES，77F/OBS-315）")
                continue
            if role in required:
                payload = blk.get("payload") or {}
                for fld in (required.get(role) or []):
                    if not payload.get(fld):
                        out_errors.append(f"semantic-map: blocks[{idx}] role={role} 缺必填 payload 字段 '{fld}'（清单见 references/component-catalog.md，77F/OBS-315）")
    except Exception as exc:
        out_errors.append(f"semantic-map: 清单校验异常: {exc}（77F/OBS-315）")
    return out_errors, {"top_keys": sorted(data.keys())}


def check_handoff(path: Path) -> tuple[list, dict]:
    try:
        data = yaml.safe_load(_read_text(path))
    except yaml.YAMLError as exc:
        return [f"handoff: YAML 解析失败: {exc}"], {}
    out_errors = []
    if not isinstance(data, dict):
        out_errors.append("handoff: 顶层必须是映射")
        return out_errors, {}
    # 76Q/OBS-285:与 full-mode 校验器同构——顶层必须是 {handoff: {...}} 双层包裹。
    # (76F 首版误按顶层平铺实现,与 validate_article_length.py --full-mode 的
    # 嵌套期望冲突,agent 被迫手工嵌套;现以 full-mode 为准绳,两工具同判。)
    if not isinstance(data.get("handoff"), dict):
        out_errors.append("handoff: 顶层必须是 {handoff: {...}}(双层包裹,与 full-mode "
                          "校验器同构);请把全部字段包进 handoff: 键下")
        return out_errors, {}
    h = data["handoff"]
    for field in HANDOFF_REQUIRED_FIELDS:
        # formatter.cover 为嵌套路径
        if "." in field:
            head, tail = field.split(".", 1)
            cover = h.get(head)
            if not isinstance(cover, dict) or not isinstance(cover.get(tail), dict) \
                    or not cover[tail]:
                out_errors.append(f"handoff: 缺必填字段 `handoff.{field}`(非空 dict)")
        elif h.get(field) in (None, ""):
            out_errors.append(f"handoff: 缺必填字段 `handoff.{field}`")
    for field, ftype in HANDOFF_TITLE_FIELDS.items():
        if field not in h:
            out_errors.append(f"handoff: 缺标题字段 `handoff.{field}`(76A/76B)")
        elif not isinstance(h.get(field), ftype):
            out_errors.append(f"handoff: `handoff.{field}` 类型应为 {ftype.__name__}")
    # 76T/OBS-293:strike_assumption(可选,advisory)——存在时校验类型与长度(≤40 字),
    # 缺失不 FAIL;超长/非字符串仅记 checks 提示(不阻断交付,渲染端缺失整行不渲染)。
    checks = {"schema_version": h.get("schema_version")}
    cover = h.get("formatter", {}).get("cover") if isinstance(h.get("formatter"), dict) else None
    sa = cover.get("strike_assumption") if isinstance(cover, dict) else None
    checks["strike_assumption"] = sa
    if sa is not None and sa != "":
        # advisory:仅记入 checks,不阻断交付(缺失/超长都不 FAIL,渲染端自行降级)
        if not isinstance(sa, str):
            checks["strike_assumption_warnings"] = "类型应为 str(76T/OBS-293,advisory)"
        elif len(sa) > 40:
            checks["strike_assumption_warnings"] = (
                f"长度 {len(sa)} > 40 字(76T/OBS-293,advisory)")
    # 77I/OBS-322:title playbook adoption is advisory only; handoff schema unchanged.
    candidates = h.get("title_candidates")
    reason = h.get("title_selection_reason")
    title_warnings = []
    if not isinstance(candidates, list) or not (3 <= len(candidates) <= 5):
        title_warnings.append(f"title_candidates 数量 {len(candidates) if isinstance(candidates, list) else '非数组'} 不在 3–5")
    groups = ("稳健准确", "网感点击", "专业权威", "长期价值")
    present_groups = [group for group in groups if group in str(reason)]
    if len(present_groups) < 3:
        title_warnings.append("分组覆盖不足 3 组(稳健准确/网感点击/专业权威/长期价值)")
    dimensions = ("点击欲望", "事实匹配", "人群匹配", "差异化", "长期价值")
    missing_dimensions = [dimension for dimension in dimensions if dimension not in str(reason)]
    if missing_dimensions:
        title_warnings.append("缺五维评分:" + "/".join(missing_dimensions))
    risk_markers = ("标题党", "堆砌", "无据", "时效", "风险标记")
    if not any(marker in str(reason) for marker in risk_markers):
        title_warnings.append("缺风险标记(标题党/堆砌/无据/时效)")
    if title_warnings:
        checks["title_playbook_warnings"] = (
            "对照 references/title-playbook.md: " + "; ".join(title_warnings))
    return out_errors, checks


def check_registry(path: Path, dedup: Path | None = None,
                  ledger: Path | None = None) -> tuple[list, dict]:
    raw = _read_text(path)
    try:
        data = json.loads(raw)
    except ValueError as exc:
        return [f"registry: JSON 解析失败: {exc}"], {}
    out_errors = []
    # 76Q/OBS-287:registry 真实形状 = dict {claims: [...], materials: [...]}
    # (76F 首版误按顶层数组实现,与生产产物不符,agent 被迫返工)。
    if not isinstance(data, dict):
        out_errors.append("registry: 顶层必须是对象 {claims: [...], materials: [...]}")
        return out_errors, {}
    claims = data.get("claims")
    materials = data.get("materials")
    if not isinstance(claims, list):
        out_errors.append("registry: 缺 claims 数组(76Q/OBS-287)")
    if not isinstance(materials, list):
        out_errors.append("registry: 缺 materials 数组(76Q/OBS-287)")
    if not isinstance(claims, list) or not isinstance(materials, list):
        return out_errors, {"claims": type(claims).__name__,
                            "materials": type(materials).__name__}
    for i, row in enumerate(claims):
        if not isinstance(row, dict):
            out_errors.append(f"registry.claims[{i}]: 条目必须是对象")
            continue
        for field in ("claim_id", "claim_text", "material_id", "source_url",
                      "source_excerpt"):
            if not row.get(field):
                out_errors.append(f"registry.claims[{i}]: 缺必填字段 `{field}`(76G-R)")
    # 77B/OBS-310(numbers schema 税):chart 字段归属 claim 级,禁止进 numbers 数组;
    # numbers.value 仅 number,日期/时间一律走 claim.time_value(ISO 字符串)。
    _CHART_KEYS = ("chart_group", "metric_name", "series_label")
    for i, row in enumerate(claims):
        if not isinstance(row, dict):
            continue
        nums = row.get("numbers")
        if nums is not None:
            if not isinstance(nums, list):
                out_errors.append(f"registry.claims[{i}]: `numbers` 必须是数组(77B/OBS-310)")
            else:
                for j, it in enumerate(nums):
                    if isinstance(it, str):
                        continue
                    if not isinstance(it, dict):
                        out_errors.append(
                            f"registry.claims[{i}].numbers[{j}]: 元素只能是 string 或 "
                            f"{{value, unit}}(77B/OBS-310)")
                        continue
                    bad = [k for k in _CHART_KEYS + ("time_value",) if k in it]
                    if bad:
                        out_errors.append(
                            f"registry.claims[{i}].numbers[{j}]: 含 chart 字段 {bad}——"
                            f"chart_group/metric_name/series_label/time_value 归属 claim 级,"
                            f"禁止进 numbers 数组(77B/OBS-310,对照 media schema)")
                    unknown = set(it) - {"value", "unit"}
                    if unknown:
                        out_errors.append(
                            f"registry.claims[{i}].numbers[{j}]: 未知键 {sorted(unknown)}——"
                            f"numbers 元素仅 value/unit(77B/OBS-310)")
                    v = it.get("value")
                    if isinstance(v, bool) or not isinstance(v, (int, float)):
                        out_errors.append(
                            f"registry.claims[{i}].numbers[{j}]: `value` 仅接受 number;"
                            f"日期/时间走 claim.time_value,禁止进 value(77B/OBS-310)")
                    if "unit" in it and not isinstance(it["unit"], str):
                        out_errors.append(
                            f"registry.claims[{i}].numbers[{j}]: `unit` 必须是 string(77B/OBS-310)")
        for k in _CHART_KEYS:
            if k in row and not isinstance(row.get(k), str):
                out_errors.append(f"registry.claims[{i}].{k}: 必须是 string(77B/OBS-310)")
        if "time_value" in row and not isinstance(row.get("time_value"), str):
            out_errors.append(f"registry.claims[{i}].time_value: 必须是 ISO 字符串(77B/OBS-310)")
    material_ids = {}
    for i, row in enumerate(materials):
        if not isinstance(row, dict):
            out_errors.append(f"registry.materials[{i}]: 条目必须是对象")
            continue
        for field in ("material_id", "dedup_id", "source_url"):
            if not row.get(field):
                out_errors.append(f"registry.materials[{i}]: 缺必填字段 `{field}`(76Q/OBS-287)")
        # 77I/OBS-320: align with media request required fields before media stage.
        for field in ("title", "aihot_permalink"):
            if not row.get(field):
                out_errors.append(f"registry.materials[{i}]: 缺必填字段 `{field}`(77I/OBS-320,对照 media schema)")
        # 77J/OBS-324: scalar shape matters; lists/dicts pass truthiness but fail media schema.
        for field in ("material_id", "dedup_id", "source_url", "title", "aihot_permalink"):
            value = row.get(field)
            if value is not None and not isinstance(value, str):
                out_errors.append(f"registry.materials[{i}].{field}: 必须是 string(77J/OBS-324,对照 media schema)")
        mid = row.get("material_id")
        if isinstance(mid, str) and mid:
            material_ids[mid] = row
    for i, row in enumerate(claims):
        mid = row.get("material_id")
        if isinstance(mid, str) and mid and mid not in material_ids:
            out_errors.append(
                f"registry.claims[{i}]: material_id `{mid}` 在 materials 中不存在"
                f"(dedup-id ↔ material_id 映射,76Q/OBS-287)")
        mat = material_ids.get(mid) if isinstance(mid, str) else None
        if mat and row.get("source_url") and mat.get("source_url"):
            # 逐字一致含锚点:两边必须原样相等,不得一边带 #anchor 一边不带。
            if row["source_url"] != mat["source_url"]:
                out_errors.append(
                    f"registry.claims[{i}]: source_url 与 materials[{mid}].source_url "
                    f"逐字不一致(含锚点原样一致,76Q/OBS-287)")
    # 77E/OBS-313(media 一致性税):同 URL 双 ID / links.original / 双通道唯一性机械校验。
    # R1: registry materials 内同 source_url 双 ID 直接拒。
    urls = {}
    for i, row in enumerate(materials):
        if not isinstance(row, dict):
            continue
        u = row.get("source_url")
        if not u:
            continue
        if u in urls:
            out_errors.append(
                f"registry.materials: source_url 重复({u})——{urls[u]} 与 {row.get('material_id')} "
                f"同 URL 双 ID,禁止;同一素材只允许一个 material 登记(77E/OBS-313)")
        else:
            urls[u] = row.get("material_id")
    # R2/R3/R4: dedup 侧(optional --dedup)。
    dedup_items = []
    if dedup is not None:
        if not dedup.is_file():
            out_errors.append(f"registry: --dedup 文件不存在: {dedup}(77E/OBS-313)")
        else:
            try:
                ddata = json.loads(dedup.read_text(encoding="utf-8"))
            except ValueError as exc:
                out_errors.append(f"registry: dedup 解析失败: {exc}(77E/OBS-313)")
                ddata = None
            if isinstance(ddata, list):
                dedup_items = ddata
            else:
                out_errors.append("registry: deduplicated_items.json 顶层必须是数组(77E/OBS-313)")
    d_urls = {}
    d_meta = {}
    for i, it in enumerate(dedup_items):
        if not isinstance(it, dict):
            continue
        u = it.get("source_url")
        if u:
            if u in d_urls:
                out_errors.append(
                    f"dedup[{i}]: source_url 重复({u})——{d_urls[u]} 与 {it.get('id')} "
                    f"同 URL 双 ID,禁止(77E/OBS-313)")
            else:
                d_urls[u] = it.get("id")
        links = it.get("links")
        did = it.get("id")
        if did is not None:
            d_meta[str(did)] = {"source_url": u,
                                "aihot_permalink": it.get("aihot_permalink") or it.get("permalink") or u}
        orig = links.get("original") if isinstance(links, dict) else None
        if not orig:
            out_errors.append(
                f"dedup[{i}]({it.get('id')}): links.original 为空/缺失——必须有原始链接,"
                f"禁止 null(77E/OBS-313)")
    # R3: registry↔dedup 同 URL 的 id 必须一一对应(dedup_id 对齐)。
    if dedup_items:
        for mrow in materials:
            if not isinstance(mrow, dict):
                continue
            u = mrow.get("source_url")
            did = mrow.get("dedup_id")
            if u and did and u in d_urls and d_urls[u] != did:
                out_errors.append(
                    f"registry.materials({mrow.get('material_id')}): source_url {u} 在 dedup 中"
                    f"对应 id={d_urls[u]},与 dedup_id={did} 不一致——同 URL 双 ID 冲突(77E/OBS-313)")
            ditem = d_meta.get(str(did)) if did is not None else None
            registry_permalink = mrow.get("aihot_permalink")
            if ditem and registry_permalink and ditem["aihot_permalink"] != registry_permalink:
                out_errors.append(
                    f"registry.materials({mrow.get('material_id')}): aihot_permalink 与 dedup 不一致——先回填 registry 再进 media(77I/OBS-320)")
    # R5: ledger 双通道(optional --ledger):双方 source_url 集合必须一一对齐。
    if ledger is not None:
        if not ledger.is_file():
            out_errors.append(f"registry: --ledger 文件不存在: {ledger}(77E/OBS-313)")
        else:
            try:
                ldata = yaml.safe_load(ledger.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                out_errors.append(f"registry: ledger 解析失败: {exc}(77E/OBS-313)")
                ldata = None
            if isinstance(ldata, dict):
                lmats = (ldata.get("material_ledger") or {}).get("materials") or []
                ledger_urls = {str(m.get("source_url")): m.get("id")
                               for m in lmats if isinstance(m, dict) and m.get("source_url")}
                if ledger_urls:
                    reg_urls = {u: (m.get("material_id"), m.get("dedup_id"))
                                for m in materials if isinstance(m, dict) and m.get("source_url")
                                for u in [m["source_url"]]}
                    only_ledger = set(ledger_urls) - set(reg_urls)
                    only_reg = set(reg_urls) - set(ledger_urls)
                    if only_ledger or only_reg:
                        out_errors.append(
                            f"registry: ledger↔registry 双通道 URL 不齐——仅 ledger:{sorted(only_ledger)[:3]}"
                            f" 仅 registry:{sorted(only_reg)[:3]};同一素材两个登记通道必须一一对齐,"
                            f"禁止 mat-xxx/M-xx 双 ID 双通道重复(77E/OBS-313)")
    return out_errors, {"claims": len(claims), "materials": len(materials)}


CHECKERS = {
    "outline": check_outline,
    "core-card": check_core_card,
    "semantic-map": check_semantic_map,
    "handoff": check_handoff,
    "registry": check_registry,
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="单产物最小预校验(76F/OBS-277)")
    ap.add_argument("--product", required=True,
                    choices=sorted(CHECKERS))
    ap.add_argument("--file", required=True)
    ap.add_argument("--target-visible-chars", type=int, default=None,
                    help="outline 专用:目标字数,偏差 >5% 即报错")
    ap.add_argument("--dedup", default=None, help="registry 专用(77E/OBS-313):deduplicated_items.json 路径,做同 URL 双 ID/links.original 校验")
    ap.add_argument("--ledger", default=None, help="registry 专用(77E/OBS-313):material-ledger.yaml 路径,做双通道 URL 一一对齐校验")
    a = ap.parse_args(argv)
    path = Path(a.file)
    if not path.is_file():
        result = {"product": a.product, "file": str(path), "valid": False,
                  "errors": [f"{a.product}: 文件不存在: {path}"], "checks": {}}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    checker = CHECKERS[a.product]
    if a.product == "outline":
        errors, checks = checker(path, a.target_visible_chars)
    elif a.product == "registry":
        errors, checks = checker(path, dedup=Path(a.dedup) if a.dedup else None,
                                  ledger=Path(a.ledger) if a.ledger else None)
    else:
        errors, checks = checker(path)
    result = {"product": a.product, "file": str(path),
              "valid": not errors, "errors": errors, "checks": checks}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
