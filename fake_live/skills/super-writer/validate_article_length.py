#!/usr/bin/env python3
"""FAKE-LIVE shim mirroring super-writer `scripts/validate_article_length.py`.
EXACT real CLI subset: --article [--full-mode --outline --brief --evidence-map
--core-card --editor-report]. SIMULATED."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CJK = re.compile(r"[\u4e00-\u9fff]")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="validate_article_length (fake-live shim)")
    ap.add_argument("--article", required=True)
    ap.add_argument("--full-mode", action="store_true")
    ap.add_argument("--outline", default=None)
    ap.add_argument("--brief", default=None)
    ap.add_argument("--evidence-map", default=None)
    ap.add_argument("--core-card", default=None)
    ap.add_argument("--editor-report", default=None)
    a = ap.parse_args(argv)
    p = Path(a.article)
    if not p.is_file():
        print(f"[fake validate_article_length] article missing: {p}")
        return 1
    text = p.read_text(encoding="utf-8", errors="replace")
    if not CJK.search(text):
        print("[fake validate_article_length] no CJK content")
        return 1
    print(f"[fake validate_article_length] PASS full_mode={a.full_mode} chars={len(text)} simulated=True")
    return 0


if __name__ == "__main__":
    sys.exit(main())
