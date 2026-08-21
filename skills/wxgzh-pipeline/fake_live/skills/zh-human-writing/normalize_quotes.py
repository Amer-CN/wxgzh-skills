#!/usr/bin/env python3
"""FAKE-LIVE shim mirroring zh-human-writing `scripts/normalize_quotes.py`.
EXACT real CLI subset: --text PATH. SIMULATED with the same pairwise algorithm
so fake_live receipts/hashes stay deterministic with live behavior."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

OPEN, CLOSE = "\u201c", "\u201d"
_FENCE_RE = re.compile(r"^\s*(```|~~~)")


def _split_inline_code(line: str) -> list[tuple[str, bool]]:
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


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="normalize_quotes (fake-live shim)")
    ap.add_argument("--text", required=True)
    a = ap.parse_args(argv)
    path = Path(a.text)
    if not path.is_file():
        print(f"[fake normalize_quotes] text missing: {a.text}")
        return 1
    with open(path, "r", encoding="utf-8", newline="") as fh:
        lines = fh.read().splitlines(keepends=True)
    in_fence = False
    out_lines = []
    counter = 0
    for line in lines:
        if _FENCE_RE.match(line.lstrip()):
            in_fence = not in_fence
            out_lines.append(line)
            continue
        if in_fence:
            out_lines.append(line)
            continue
        rebuilt = []
        for seg, is_code in _split_inline_code(line):
            if is_code:
                rebuilt.append(seg)
                continue
            chars = []
            for ch in seg:
                if ch != '"':
                    chars.append(ch)
                    continue
                if counter % 2 == 0:
                    chars.append(OPEN)
                else:
                    chars.append(CLOSE)
                counter += 1
            rebuilt.append("".join(chars))
        out_lines.append("".join(rebuilt))
    # newline="" 保字节级幂等:无引号改动时禁止触碰原文(LF/CRLF 原样)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write("".join(out_lines))
    if counter % 2 == 1:
        print("WARNING: 未配对半角引号保留(单边落单不猜,不硬改)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
