#!/usr/bin/env python3
"""FAKE-LIVE shim mirroring zh-human-writing `scripts/fidelity_guard.py`.
EXACT real CLI subset: --original / --edited [--profile --source --output]. SIMULATED."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="fidelity_guard (fake-live shim)")
    ap.add_argument("--original", required=True)
    ap.add_argument("--edited", required=True)
    ap.add_argument("--profile", default="essay")
    ap.add_argument("--source", default="unknown")
    ap.add_argument("--protected-spans", default=None)
    ap.add_argument("--output", default="json")
    ap.add_argument("--no-warnings", action="store_true")
    a = ap.parse_args(argv)
    for label, p in (("original", a.original), ("edited", a.edited)):
        if not Path(p).is_file():
            print(f"[fake fidelity_guard] {label} missing: {p}")
            return 1
    print('{"FIDELITY": "PASS", "simulated": true}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
