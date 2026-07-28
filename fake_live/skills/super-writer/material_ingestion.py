#!/usr/bin/env python3
"""FAKE-LIVE shim mirroring super-writer `scripts/material_ingestion.py`.
EXACT real CLI: --ledger / --output [--diagnostic-output --json]. SIMULATED."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="material_ingestion (fake-live shim)")
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--diagnostic-output", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not Path(a.ledger).is_file():
        print(f"[fake material_ingestion] ledger missing: {a.ledger}")
        return 1
    report = {"simulated": True, "MATERIAL_INGESTION": "PASS",
              "ledger": str(a.ledger), "errors": []}
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    Path(a.output).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                              encoding="utf-8")
    print("[fake material_ingestion] PASS simulated=True")
    return 0


if __name__ == "__main__":
    sys.exit(main())
