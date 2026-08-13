#!/usr/bin/env python3
"""档71C-1 OBS-110:final.html 的 <img src> 白名单门禁。

规则:所有 <img src=...> 必须是 https:// 开头;命中 ../ 、file:// 、
本机盘符([A-Za-z]:\\) 、data: -> FAIL_CLOSED,报出行号与原文。

5c 悖论检查:先「只打印不拦」跑现 RUN final.html 确认命中 0 后启用 fail-closed。

OBS-121(档71C-2):三处硬伤修复
- 3b 去死分支:先判 https:// 命中即放行;未命中者再细分「bad prefix(../ file://
  data: 盘符)」与「not https://」,两类 reason 都可达(旧实现 elif 使 bad prefix
  永不可达)。
- 3c 正则扩容:src 支持双引号 / 单引号 / 无引号三种写法(大小写不敏感)。
- 3d 自洽断言:已解析 <img src> 数 != <img 标签总数 -> FAIL(IMG_SRC_PARSE_GAP),
  打印两个数字与前 3 个未解析片段。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# 3c:双引号 / 单引号 / 无引号三种 src 写法(无引号以空白或 > 结尾)。
_IMG_SRC_RE = re.compile(
    r"""<img[^>]*\bsrc\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""", re.I)
_IMG_TAG_RE = re.compile(r"<img\b", re.I)
_BAD_PREFIXES = ("../", "file://", "data:")
_DRIVE_RE = re.compile(r"^[A-Za-z]:")


def scan_img_src(html: str) -> tuple[list[dict], int, list[str]]:
    """返回 (hits, parsed_count, unparsed_fragments)。

    parsed_count = 成功解析出 src 的 <img 标签数;unparsed_fragments = 未解析
    的 <img 标签原片段(前 3 个)。"""
    hits = []
    parsed = 0
    matched_starts = []
    for m in _IMG_SRC_RE.finditer(html):
        parsed += 1
        matched_starts.append(m.start())
        src = m.group(1) or m.group(2) or m.group(3) or ""
        lineno = html.count("\n", 0, m.start()) + 1
        # 3b:先判合规,命中即放行;两类失败 reason 都可达。
        if src.startswith("https://"):
            continue
        if src.startswith(_BAD_PREFIXES) or _DRIVE_RE.match(src):
            reason = "bad prefix"
        else:
            reason = "not https://"
        hits.append({"line": lineno, "src": src[:120], "reason": reason})
    unparsed = []
    for m in _IMG_TAG_RE.finditer(html):
        if m.start() not in matched_starts:
            unparsed.append(html[m.start():m.start() + 80])
    return hits, parsed, unparsed[:3]


def validate(final_html: str | Path, enforce: bool = True) -> tuple[int, dict]:
    html = Path(final_html).read_text(encoding="utf-8")
    hits, parsed, unparsed = scan_img_src(html)
    img_total = html.count("<img")
    # 3d:自洽断言 —— 解析数 != 标签总数,说明有 <img 未被解析,FAIL_CLOSED。
    if parsed != img_total:
        return 1, {
            "OBS110_IMG_SRC": "FAIL",
            "reason": "IMG_SRC_PARSE_GAP",
            "parsed_count": parsed,
            "img_count": img_total,
            "unparsed_fragments": unparsed,
            "enforce": enforce,
        }
    ok = not hits or not enforce
    return (0 if ok else 1), {
        "OBS110_IMG_SRC": "PASS" if ok else "FAIL",
        "img_src_total": parsed,
        "hits": hits,
        "enforce": enforce,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="OBS-110 img src whitelist")
    ap.add_argument("--final-html", required=True)
    ap.add_argument("--enforce", action="store_true", default=False,
                    help="启用 fail-closed(默认仅打印)")
    a = ap.parse_args(argv)
    code, report = validate(a.final_html, enforce=a.enforce)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
