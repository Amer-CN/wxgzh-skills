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
        sections.append({"title": title,
                         "start": text[:start].count("\n"),
                         "end": text[:end].count("\n"),
                         "planned": planned, "min_c": min_c, "max_c": max_c})
    return sections


def align_outline(text: str, target: int) -> tuple[str, dict, list[str]]:
    sections = parse_sections(text)
    errors = []
    if not sections:
        return text, {}, ["outline: 无有效内容节(缺 ## 节或 planned_chars)"]
    total_old = sum(s["planned"] for s in sections)
    if total_old <= 0:
        return text, {}, ["outline: 各节 planned_chars 合计为 0,无法对齐"]
    scale = target / total_old
    new_sections = []
    for s in sections:
        planned = max(1, round(s["planned"] * scale))
        min_c = max(1, round(s["min_c"] * scale)) if s["min_c"] is not None else None
        max_c = round(s["max_c"] * scale) if s["max_c"] is not None else None
        new_sections.append({"title": s["title"], "old": s["planned"],
                             "new": planned, "old_min": s["min_c"],
                             "new_min": min_c, "old_max": s["max_c"],
                             "new_max": max_c})
    # 按行精确重写预算字段(只动数值,保留行结构与冒号宽度)
    lines = text.split("\n")
    section_ranges = [(s["start"], s["end"]) for s in sections]
    for s, ns in zip(sections, new_sections):
        for idx in range(s["start"], s["end"]):
            line = lines[idx]
            for field, new_val in (("planned_chars", ns["new"]),
                                   ("minimum_chars", ns["new_min"]),
                                   ("maximum_chars", ns["new_max"])):
                if new_val is None:
                    continue
                m = re.match(rf"^(\s*-\s*{field}[\uff1a:])\s*\d+(\s*)$", line)
                if m:
                    lines[idx] = f"{m.group(1)}{new_val}{m.group(2)}"
    total_new = sum(ns["new"] for ns in new_sections)
    deviation = abs(total_new - target) / target if target else 0.0
    return "\n".join(lines), {
        "target": target, "total_old": total_old, "total_new": total_new,
        "deviation": round(deviation, 4), "sections": new_sections,
    }, errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="大纲预算自动对齐(76F/OBS-278)")
    ap.add_argument("--outline", required=True)
    ap.add_argument("--target-visible-chars", type=int, default=None,
                    help="目标总字数;缺省读 outline 文章配置节 target_visible_chars")
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
    new_text, info, errors = align_outline(text, target)
    info["ok"] = not errors
    info["errors"] = errors
    if not errors and not a.dry_run:
        path.write_text(new_text, encoding="utf-8", newline="\n")
        info["written"] = str(path)
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
