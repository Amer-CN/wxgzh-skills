#!/usr/bin/env python3
"""FAKE-LIVE shim for gzh-design's official HTML validator (dev2 tests only).

Mirrors the installed validate_gzh_html.py CLI so the orchestrator runs the
official validator for REAL via subprocess. Structural sanity only (real theme
identity is enforced by the pipeline's validate_theme_identity). Exit 0 = PASS.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    a = ap.parse_args(argv)
    p = Path(a.html)
    html = p.read_text(encoding="utf-8") if p.is_file() else ""
    problems = []
    if "<html" not in html:
        problems.append("missing <html>")
    if "chapter-title" not in html:
        problems.append("no chapter-title component")
    if "#059669" in html:
        problems.append("moyu-green fallback color present")
    ok = not problems
    print(json.dumps({"GZH_HTML_VALIDATOR": "PASS" if ok else "FAIL",
                      "problems": problems}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
