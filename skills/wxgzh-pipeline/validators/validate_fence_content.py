#!/usr/bin/env python3
"""档71B OBS-104:围栏内容非代码 —— 提示型 WARN + 强制留痕(绝不阻断)。

★新铁律:先定内容判据,再看载体。三条任一命中即标记 suspect_non_code:
  ① 块内非 ASCII 字符占比 > 40%,且块内不含任何代码标记符
     代码标记符集合(逐字,可扩不可缩):
     = { } ; ( ) $ -- -> :: #! import def class function sudo rm git pip npm curl
  ② 任一行以提示图标开头:⛔ ⚠️ ✅ ❌ 📌 💡 🚫
  ③ 围栏语言标签属于 {bash, sh, zsh, shell, python, py, js, ts, json, yaml, sql},
     但块内零个该语言标记符

行为:WARN + 必须写一条 allowance_record
  (rule = fence_content_not_code,含块序号、语言标签、命中的判据编号、前 3 行片段)。
★退出码不变、绝不阻断。

★门禁悖论检查:writing_contract.validate_codeblock_fidelity 仍要求那 16 行在
代码围栏内;本门禁只提示不阻断,两者不构成不可满足集合。本档不改
writing_contract 的判据(载体判据改造与接线必须同档 = 71C)。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# ① 代码标记符集合(逐字,可扩不可缩)
CODE_MARKERS = [
    "=", "{", "}", ";", "(", ")", "$", "--", "->", "::", "#!", "import",
    "def", "class", "function", "sudo", "rm", "git", "pip", "npm", "curl",
]
# ② 提示图标
ICON_PREFIXES = ("⛔", "⚠️", "✅", "❌", "📌", "💡", "🚫")
# ③ 语言标签 -> 该语言的标记符(非空子集)
LANG_MARKERS = {
    "bash": ["if", "fi", "$", "#!/", "sudo", "rm", "git"],
    "sh": ["if", "fi", "$", "#!/", "sudo", "rm", "git"],
    "zsh": ["if", "fi", "$", "#!/", "sudo", "rm", "git"],
    "shell": ["if", "fi", "$", "#!/", "sudo", "rm", "git"],
    "python": ["def", "import", "print", "=", ":"],
    "py": ["def", "import", "print", "=", ":"],
    "js": ["function", "const", "let", "=>", ";"],
    "ts": ["function", "const", "let", "=>", ";"],
    "json": ["{", "}", ":", ","],
    "yaml": [":", "-", "#"],
    "sql": ["SELECT", "FROM", "WHERE", ";"],
}
NON_ASCII = re.compile(r"[^\x00-\x7F]")
FENCE_RE = re.compile(r"^```([A-Za-z0-9_+-]*)\s*$", re.M)


def _non_ascii_ratio(text: str) -> float:
    if not text:
        return 0.0
    return len(NON_ASCII.findall(text)) / len(text)


def classify_fence_block(lang: str, body: str) -> list[int]:
    """返回命中的判据编号列表(空 = 不标记 suspect)。"""
    hits: list[int] = []
    # ① 非 ASCII > 40% 且无任何代码标记符
    if _non_ascii_ratio(body) > 0.40:
        if not any(m in body for m in CODE_MARKERS):
            hits.append(1)
    # ② 任一行以提示图标开头
    if any(ln.strip().startswith(ICON_PREFIXES) for ln in body.splitlines()):
        hits.append(2)
    # ③ 语言标签在列表内但块内零个该语言标记符
    lang_lower = (lang or "").strip().lower()
    if lang_lower in LANG_MARKERS:
        if not any(m in body for m in LANG_MARKERS[lang_lower]):
            hits.append(3)
    return hits


def scan_fences(article_text: str) -> list[dict]:
    """扫描全部 fenced code block,返回 suspect 记录列表(含留痕字段)。"""
    lines = article_text.splitlines()
    fences = [(i, ln) for i, ln in enumerate(lines) if FENCE_RE.match(ln)]
    records = []
    for idx in range(0, len(fences) - 1, 2):
        start, open_line = fences[idx]
        end = fences[idx + 1][0]
        lang = open_line[3:].strip()
        body = "\n".join(lines[start + 1:end])
        hits = classify_fence_block(lang, body)
        if not hits:
            continue
        snippet_lines = [l for l in body.splitlines() if l.strip()][:3]
        records.append({
            "block_index": idx // 2 + 1,
            "language": lang or "(none)",
            "criteria_hit": hits,
            "line_range": [start + 1, end + 1],
            "first_lines": snippet_lines,
            "rule": "fence_content_not_code",
        })
    return records


def write_allowance(records: list[dict], audit_dir: Path) -> Path | None:
    """把 suspect 记录写入 allowance_record.json(追加语义,保留既有条目)。"""
    if not records:
        return None
    path = audit_dir / "allowance_record.json"
    existing = []
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8")).get("entries", [])
        except (OSError, ValueError):
            existing = []
    entries = existing + [{
        "rule": r["rule"], "category": "advisory",
        "block_index": r["block_index"], "language": r["language"],
        "criteria_hit": r["criteria_hit"], "line_range": r["line_range"],
        "first_lines": r["first_lines"],
    } for r in records]
    path.write_text(json.dumps(
        {"schema_version": "1.0", "allow_warnings": True, "entries": entries},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="OBS-104 fence content advisory")
    ap.add_argument("--article", required=True)
    ap.add_argument("--audit-dir", required=True)
    a = ap.parse_args(argv)
    article = Path(a.article).read_text(encoding="utf-8")
    records = scan_fences(article)
    out = write_allowance(records, Path(a.audit_dir))
    report = {
        "OBS104_FENCE_CONTENT": "ADVISORY",
        "suspect_count": len(records),
        "records": records,
        "allowance_record": str(out) if out else None,
        "note": "提示型门禁:不阻断,仅留痕;与 writing_contract 载体判据不构成冲突",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0  # 绝不阻断


if __name__ == "__main__":
    sys.exit(main())
