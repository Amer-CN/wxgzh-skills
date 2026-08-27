#!/usr/bin/env python3
"""77A/OBS-309: 中文语境半角引号机械归一（管线 zh 阶段强制前置）。

将 Markdown 中文正文中的 ASCII 双引号 " 成对转全角 “ ”：
- 成对判定全局进行（跨行配对），偶数位转开引号、奇数位转闭引号；
- 单边落单不猜：总数奇数时最后一个候选引号保持原样，仅留 WARNING（行号）；
- 跳过 fenced code block、行内代码 span、`:::` 指令头/收尾行与指令属性行，不触碰机器语法；
- 退出码恒 0，WARNING 仅供留痕（76C WXGZH_ALLOW_WARNINGS 语义不变）。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

OPEN, CLOSE = "\u201c", "\u201d"

_FENCE_RE = re.compile(r"^\s*(```|~~~)")
_DIRECTIVE_RE = re.compile(r"^\s*:::")
_ATTRIBUTE_LINE_RE = re.compile(r'^\s*[\w-]+\s*=\s*(["\']).*\1\s*$')


def _split_inline_code(line: str) -> list[tuple[str, bool]]:
    """按反引号把行切成 [(文本, 是否行内代码)]，含反引号与代码内容，保序完整。"""
    parts: list[tuple[str, bool]] = []
    buf: list[str] = []
    in_code = False
    for ch in line:
        buf.append(ch)
        if ch == "`":
            parts.append(("".join(buf), in_code))
            buf = []
            in_code = not in_code
    parts.append(("".join(buf), in_code))
    return parts


def _walk(text: str):
    """逐行产出 (行号, 保护行？, 行内代码分段列表)。

    围栏行、围栏内行、`:::` 指令头/收尾行与指令属性行整行原样保留；正文行分段处理。
    """
    lines = text.splitlines(keepends=True)
    in_fence = False
    in_component = False
    for ln, line in enumerate(lines, 1):
        if _DIRECTIVE_RE.match(line.lstrip()):
            # 77K/OBS-326: opening/closing directive heads are machine syntax.
            in_component = not in_component
            yield ln, True, [(line, False)]
            continue
        if in_component and _ATTRIBUTE_LINE_RE.match(line):
            yield ln, True, [(line, False)]
            continue
        if _FENCE_RE.match(line.lstrip()):
            in_fence = not in_fence
            yield ln, True, [(line, False)]
            continue
        if in_fence:
            yield ln, True, [(line, False)]
            continue
        yield ln, False, _split_inline_code(line)


def normalize_text(text: str) -> tuple[str, list[str]]:
    total = 0
    last_quote = None  # (行号, 该行第几个候选引号, 从 0 起)
    for ln, is_code, segs in _walk(text):
        if is_code:
            continue
        cnt = sum(seg.count('"') for seg, _c in segs if not _c)
        if cnt:
            last_quote = (ln, cnt - 1)
        total += cnt

    warnings: list[str] = []
    if total % 2 == 1:
        skip_ln, skip_idx = last_quote
        warnings.append(
            f"WARNING: 未配对半角引号保留(line {skip_ln});单边落单不猜,不硬改")
    else:
        skip_ln, skip_idx = None, None

    out_lines: list[str] = []
    counter = 0
    for ln, is_code, segs in _walk(text):
        if is_code:
            out_lines.append(segs[0][0])
            continue
        rebuilt = []
        for seg, is_inline_code in segs:
            if is_inline_code:
                rebuilt.append(seg)
                continue
            chars = []
            for ch in seg:
                if ch != '"':
                    chars.append(ch)
                    continue
                if ln == skip_ln and counter == skip_idx:
                    chars.append(ch)
                elif counter % 2 == 0:
                    chars.append(OPEN)
                else:
                    chars.append(CLOSE)
                counter += 1
            rebuilt.append("".join(chars))
        out_lines.append("".join(rebuilt))
    return "".join(out_lines), warnings


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--text", required=True, metavar="PATH",
                    help="final_article.md（或其他 Markdown）就地归一")
    args = ap.parse_args(argv)
    path = Path(args.text)
    # newline="" 读侧也保原文换行:无引号改动时字节级幂等(LF/CRLF 原样)
    with open(path, "r", encoding="utf-8", newline="") as fh:
        text = fh.read()
    new_text, warnings = normalize_text(text)
    for w in warnings:
        print(w)
    if new_text != text:
        # newline="" 保字节级幂等:无引号改动时禁止触碰原文(LF/CRLF 原样)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(new_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
