#!/usr/bin/env python3
"""76F/OBS-278:大纲预算自动对齐 —— 按目标字数 ±5% 调整各节预算数值字段。

只重写每节的 `- planned_chars:` / `- minimum_chars:` / `- maximum_chars:` 行,
按「原 planned 比例」缩放(保持各节相对结构与包络);weight_percent 不动;
evidence_ids / event_ids / unique_information_goal 与正文数字/产品名一律不动
(保护域)。文章配置节(target_visible_chars 等)不动。

用法:
    python scripts/align_outline_budget.py --outline outline.md \
        [--target-visible-chars 3000]

输出 JSON:{"ok","target","sections":[{title,old_planned,new_planned}],
           "total_old","total_new","deviation","errors"};exit 0=已对齐,1=失败。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

# 77Y/OBS-370:可见字符计数与官方 validate_article_length.count_visible_chars
# 同口径(import 单一真源;该脚本 stdlib 导入+main guard,模块导入无副作用)。
from validate_article_length import count_visible_chars  # noqa: E402

INTRO_SECTION_TITLE = "（导语）"

NON_SECTION_HEADINGS = {"文章配置", "权重校验", "语义规划校验", "篇幅校验"}
BUDGET_FIELDS = ("planned_chars", "minimum_chars", "maximum_chars")


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return raw.decode("utf-8")


def parse_sections(text: str) -> list[dict]:
    """按 ## 分节,返回非配置节的 {title, start, end, planned, min_c, max_c}。"""
    heading_re = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    heads = list(heading_re.finditer(text))
    sections = []
    for idx, hm in enumerate(heads):
        title = hm.group(1).strip()
        if title in NON_SECTION_HEADINGS:
            continue
        start = hm.end()
        end = heads[idx + 1].start() if idx + 1 < len(heads) else len(text)
        body = text[start:end]
        planned = min_c = max_c = None
        for field in BUDGET_FIELDS:
            m = re.search(rf"-\s*{field}[\uff1a:]\s*(\d+)", body)
            val = int(m.group(1)) if m else None
            if field == "planned_chars":
                planned = val
            elif field == "minimum_chars":
                min_c = val
            else:
                max_c = val
        if planned is None:
            continue
        # 76V/OBS-297:提取各节 evidence_ids(素材密度代理)——用于分节加权预算。
        ev_m = re.search(r"-\s*evidence_ids[\uff1a:]\s*\[([^\]]*)\]", body)
        ev_count = 0
        if ev_m:
            ev_count = len([x for x in re.split(r"[,\s]+", ev_m.group(1).strip()) if x])
        sections.append({"title": title,
                         "start": text[:start].count("\n"),
                         "end": text[:end].count("\n"),
                         "planned": planned, "min_c": min_c, "max_c": max_c,
                         "evidence_count": ev_count})
    return sections


def align_outline(text: str, target: int,
                  actual: dict[str, int] | None = None) -> tuple[str, dict, list[str]]:
    sections = parse_sections(text)
    errors = []
    if not sections:
        return text, {}, ["outline: 无有效内容节(缺 ## 节或 planned_chars)"]
    total_old = sum(s["planned"] for s in sections)
    if total_old <= 0:
        return text, {}, ["outline: 各节 planned_chars 合计为 0,无法对齐"]
    # 77Y/OBS-370:导语节(actual 传入的「（导语）」)参与预算分配——导语在大纲中
    # 无 planned_chars/evidence 行,按简单上限处理:仅参与加权切分与整数分配、
    # 进入输出清单(new),不写回任何大纲行(无预算字段可写,重写循环跳过)。
    if actual and int(actual.get(INTRO_SECTION_TITLE) or 0) > 0:
        sections = [{"title": INTRO_SECTION_TITLE, "start": None, "end": None,
                     "planned": 0, "min_c": None, "max_c": None,
                     "evidence_count": 0}] + sections
    # 76V/OBS-297:分节加权预算——按各节 evidence_ids 数量(素材密度)分配权重,
    # 不再均分/原比例;无任何 evidence 时回退原 planned 比例(与 76F 行为一致)。
    # 77A/OBS-306:actual 映射存在时按各节实测可见字数重排,不再只按 planned 估计。
    total_ev = sum(s["evidence_count"] for s in sections)
    if actual is not None and any(actual.get(s["title"], 0) > 0 for s in sections):
        total_act = sum(max(actual.get(x["title"], 0), 1) for x in sections)
        weights = {s["title"]: max(actual.get(s["title"], 0), 1) / total_act for s in sections}
        alloc_mode = "actual_weighted"
    elif total_ev > 0:
        weights = {s["title"]: s["evidence_count"] / total_ev for s in sections}
        alloc_mode = "evidence_weighted"
    else:
        weights = {s["title"]: s["planned"] / total_old for s in sections}
        alloc_mode = "original_proportional"
    # 整数分配(target 按权重切分,最大余数法保证合计=target)
    alloc = {s["title"]: int(target * weights[s["title"]]) for s in sections}
    rem = target - sum(alloc.values())
    for s in sorted(sections, key=lambda x: target * weights[x["title"]] - alloc[x["title"]], reverse=True)[:rem]:
        alloc[s["title"]] += 1
    new_sections = []
    for s in sections:
        planned = max(1, alloc[s["title"]])
        # ±5% 容差区间
        min_c = max(1, round(planned * 0.95)) if s["min_c"] is not None else None
        max_c = round(planned * 1.05) if s["max_c"] is not None else None
        new_sections.append({"title": s["title"], "old": s["planned"],
                             "new": planned, "old_min": s["min_c"],
                             "new_min": min_c, "old_max": s["max_c"],
                             "new_max": max_c, "evidence_count": s["evidence_count"],
                             "weight": round(weights[s["title"]], 4)})
    # 按行精确重写预算字段(只动数值,保留行结构与冒号宽度)
    lines = text.split("\n")
    section_ranges = [(s["start"], s["end"]) for s in sections]
    for s, ns in zip(sections, new_sections):
        # 77Y/OBS-370:导语节无大纲行(start=None),跳过写回
        if s["start"] is None:
            continue
        for idx in range(s["start"], s["end"]):
            line = lines[idx]
            for field, new_val in (("planned_chars", ns["new"]),
                                   ("minimum_chars", ns["new_min"]),
                                   ("maximum_chars", ns["new_max"])):
                if new_val is None:
                    continue
                m = re.match(rf"^(\s*-\s*{field}[\uff1a:]\s*)\d+(\s*)$", line)
                if m:
                    lines[idx] = f"{m.group(1)}{new_val}{m.group(2)}"
            # 76W/OBS-300:weight_percent 与 planned_chars 原子一致——同一分配结果
            # 同步写回(round 到 1 位小数,各节合计≈100%)。
            mw = re.match(r"^(\s*-\s*weight_percent[\uff1a:]\s*)[\d.]+(\s*)$", line)
            if mw and target:
                wv = round(ns["new"] / target * 100, 1)
                lines[idx] = f"{mw.group(1)}{wv}{mw.group(2)}"
    total_new = sum(ns["new"] for ns in new_sections)
    deviation = abs(total_new - target) / target if target else 0.0
    return "\n".join(lines), {
        "target": target, "total_old": total_old, "total_new": total_new,
        "deviation": round(deviation, 4),
        "allocation_mode": alloc_mode,
        "tolerance": "±5%",
        "sections": new_sections,
    }, errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="大纲预算自动对齐(76F/OBS-278)")
    ap.add_argument("--outline", required=True)
    ap.add_argument("--target-visible-chars", type=int, default=None,
                    help="目标总字数;缺省读 outline 文章配置节 target_visible_chars")
    ap.add_argument("--article", default=None,
                    help="正文 markdown 路径(77A/OBS-306):按各节实际可见字数重排,不再只按 planned 估计")
    ap.add_argument("--dry-run", action="store_true",
                    help="只输出对齐结果,不写文件")
    a = ap.parse_args(argv)
    path = Path(a.outline)
    if not path.is_file():
        print(json.dumps({"ok": False, "errors": [f"文件不存在: {path}"]},
                         ensure_ascii=False, indent=2))
        return 1
    text = _read_text(path)
    target = a.target_visible_chars
    if target is None:
        m = re.search(r"-\s*target_visible_chars[\uff1a:]\s*(\d+)", text)
        if not m:
            print(json.dumps({"ok": False,
                              "errors": ["outline 文章配置节缺 target_visible_chars,"
                                         "请显式传 --target-visible-chars"]},
                             ensure_ascii=False, indent=2))
            return 1
        target = int(m.group(1))
    actual = None
    if a.article:
        art = Path(a.article)
        if not art.is_file():
            print(json.dumps({"ok": False, "errors": [f"正文文件不存在: {art}"]},
                             ensure_ascii=False, indent=2))
            return 1
        atext = _read_text(art)
        heads = list(re.finditer(r"^##\s+(.+)$", atext, re.MULTILINE))
        actual = {}
        # 77Y/OBS-370:计数口径与 count_visible_chars 同源(链接计文本/表格计单元格/
        # 代码计内容),不再用「去空白全长」粗算;导语区(文首/H1 至第一个 ##)
        # 计为「（导语）」节纳入 actual——此前导语字数不计入任何节,预算被正文节压占。
        intro_body = atext[:heads[0].start()] if heads else atext
        intro_chars = count_visible_chars(intro_body)
        if intro_chars > 0:
            actual[INTRO_SECTION_TITLE] = intro_chars
        for idx, hm in enumerate(heads):
            title = hm.group(1).strip()
            body = atext[hm.end(): heads[idx + 1].start() if idx + 1 < len(heads) else len(atext)]
            actual[title] = count_visible_chars(body)
    new_text, info, errors = align_outline(text, target, actual=actual)
    if actual is not None:
        # 77Y/OBS-370:实测各节可见字数留痕(count_visible_chars 口径可核验)
        info["actual"] = actual
    info["ok"] = not errors
    info["errors"] = errors
    if not errors and not a.dry_run:
        path.write_text(new_text, encoding="utf-8", newline="\n")
        info["written"] = str(path)
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
