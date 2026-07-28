#!/usr/bin/env python3
"""FAKE-LIVE shim mirroring zh-human-writing `scripts/change_report.py`.
EXACT real CLI: --original / --edited. SIMULATED."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="change_report (fake-live shim)")
    ap.add_argument("--original", required=True)
    ap.add_argument("--edited", required=True)
    a = ap.parse_args(argv)
    for label, p in (("original", a.original), ("edited", a.edited)):
        if not Path(p).is_file():
            print(f"[fake change_report] {label} missing: {p}")
            return 1
    orig = Path(a.original).read_text(encoding="utf-8", errors="replace")
    edit = Path(a.edited).read_text(encoding="utf-8", errors="replace")
    print(f'{{"CHANGE_REPORT": "OK", "orig_chars": {len(orig)}, "edited_chars": {len(edit)}, "simulated": true}}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
