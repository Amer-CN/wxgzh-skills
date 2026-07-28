#!/usr/bin/env python3
"""FAKE-LIVE shim mirroring zh-human-writing `scripts/pattern_audit.py`.
EXACT real CLI subset: --text [--profile --check-level --output]. SIMULATED."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="pattern_audit (fake-live shim)")
    ap.add_argument("--text", required=True)
    ap.add_argument("--profile", default="essay")
    ap.add_argument("--check-level", default="hard_residue_only")
    ap.add_argument("--output", default="json")
    a = ap.parse_args(argv)
    if not Path(a.text).is_file():
        print(f"[fake pattern_audit] text missing: {a.text}")
        return 1
    print('{"PATTERN_AUDIT": "PASS", "hard_residue": 0, "simulated": true}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
