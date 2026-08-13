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

CORE_CARD_FIELDS = ["Core Statement", "Reader Change", "Core Tension", "Value Carrier"]


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
    if "## Core Card" not in text:
        out_errors.append("core-card: 缺 `## Core Card` 节")
    for field in CORE_CARD_FIELDS:
        if f"**{field}**" not in text:
            out_errors.append(f"core-card: 缺 `**{field}**` 字段")
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
    for field in HANDOFF_REQUIRED_FIELDS:
        # formatter.cover 为嵌套路径
        if "." in field:
            head, tail = field.split(".", 1)
            if not isinstance(data.get(head), dict) or tail not in data[head]:
                out_errors.append(f"handoff: 缺必填字段 `{field}`")
        elif field not in data:
            out_errors.append(f"handoff: 缺必填字段 `{field}`")
    for field, ftype in HANDOFF_TITLE_FIELDS.items():
        if field not in data:
            out_errors.append(f"handoff: 缺标题字段 `{field}`(76A/76B)")
        elif not isinstance(data.get(field), ftype):
            out_errors.append(f"handoff: `{field}` 类型应为 {ftype.__name__}")
    return out_errors, {"schema_version": data.get("schema_version")}


def check_registry(path: Path) -> tuple[list, dict]:
    raw = _read_text(path)
    try:
        data = json.loads(raw)
    except ValueError as exc:
        return [f"registry: JSON 解析失败: {exc}"], {}
    out_errors = []
    if not isinstance(data, list):
        out_errors.append("registry: 顶层必须是数组")
        return out_errors, {}
    for i, row in enumerate(data):
        if not isinstance(row, dict):
            out_errors.append(f"registry[{i}]: 条目必须是对象")
            continue
        for field in ("material_id", "claim_id", "claim_text", "source_excerpt"):
            if not row.get(field):
                out_errors.append(f"registry[{i}]: 缺必填字段 `{field}`(76G-R)")
    return out_errors, {"entries": len(data)}


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
    else:
        errors, checks = checker(path)
    result = {"product": a.product, "file": str(path),
              "valid": not errors, "errors": errors, "checks": checks}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
