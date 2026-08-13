#!/usr/bin/env python3
"""FAKE-LIVE shim mirroring super-writer `scripts/validate_semantic_map.py`.
EXACT real CLI subset: --article / --semantic-map [--evidence-map --json]. SIMULATED."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="validate_semantic_map (fake-live shim)")
    ap.add_argument("--article", default=None)
    ap.add_argument("--semantic-map", default=None)
    ap.add_argument("--evidence-map", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.article and not Path(a.article).is_file():
        print(f"[fake validate_semantic_map] article missing: {a.article}")
        return 1
    print("[fake validate_semantic_map] PASS simulated=True")
    return 0


if __name__ == "__main__":
    sys.exit(main())
