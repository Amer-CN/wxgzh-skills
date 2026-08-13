#!/usr/bin/env python3
"""FAKE-LIVE shim mirroring gzh-design `scripts/validate_gzh_html.py`.

EXACT real CLI: positional file path (or --stdin). Structural sanity only; the
pipeline's own validate_theme_identity enforces the real hammer identity. Exit 0
= PASS. SIMULATED (fake_live only).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="validate_gzh_html (fake-live shim)")
    ap.add_argument("file", nargs="?")
    ap.add_argument("--stdin", action="store_true")
    a = ap.parse_args(argv)
    html = sys.stdin.read() if (a.stdin or not a.file) else Path(a.file).read_text(encoding="utf-8")
    problems = []
    if "<section" not in html:
        problems.append("no <section>")
    if 'leaf=""' not in html:
        problems.append("no span leaf")
    if "#059669" in html:
        problems.append("moyu-green fallback color present")
    ok = not problems
    print(f"[fake validate_gzh_html] PASS={ok} problems={problems}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
