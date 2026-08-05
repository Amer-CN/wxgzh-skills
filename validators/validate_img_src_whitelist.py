#!/usr/bin/env python3
"""档71C-1 OBS-110:final.html 的 <img src> 白名单门禁。

规则:所有 <img src="..."> 必须是 https:// 开头;命中 ../ 、file:// 、
本机盘符([A-Za-z]:\\) 、data: -> FAIL_CLOSED,报出行号与原文。

5c 悖论检查:先「只打印不拦」跑现 RUN final.html 确认命中 0 后启用 fail-closed。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_IMG_SRC_RE = re.compile(r'<img[^>]*\bsrc\s*=\s*"([^"]*)"', re.I)
_BAD_PREFIXES = ("../", "file://", "data:")
_DRIVE_RE = re.compile(r"^[A-Za-z]:")


def scan_img_src(html: str) -> list[dict]:
    """返回所有 <img src> 的 {line, src, reason};空 = 全部合规。"""
    hits = []
    for i, m in enumerate(_IMG_SRC_RE.finditer(html)):
        src = m.group(1)
        lineno = html.count("\n", 0, m.start()) + 1
        reason = None
        if not src.startswith("https://"):
            reason = "not https://"
        elif src.startswith(_BAD_PREFIXES) or _DRIVE_RE.match(src):
            reason = "bad prefix"
        if reason:
            hits.append({"line": lineno, "src": src[:120], "reason": reason})
    return hits


def validate(final_html: str | Path, enforce: bool = True) -> tuple[int, dict]:
    html = Path(final_html).read_text(encoding="utf-8")
    hits = scan_img_src(html)
    ok = not hits or not enforce
    return (0 if ok else 1), {
        "OBS110_IMG_SRC": "PASS" if ok else "FAIL",
        "img_src_total": len(_IMG_SRC_RE.findall(html)),
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
