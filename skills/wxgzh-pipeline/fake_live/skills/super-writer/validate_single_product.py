#!/usr/bin/env python3
"""FAKE-LIVE shim mirroring super-writer validate_single_product.py.
EXACT real CLI: --product / --file [--dedup --ledger --json]. SIMULATED."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="validate_single_product (fake-live shim)")
    ap.add_argument("--product", required=True)
    ap.add_argument("--file", required=True)
    ap.add_argument("--dedup", default=None)
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--target-visible-chars", type=int, default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    path = Path(a.file)
    errors = []
    if not path.is_file():
        errors.append(f"file missing: {path}")
    elif a.product == "registry":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            data = None
            errors.append(f"invalid JSON: {exc}")
        if not isinstance(data, dict) or not isinstance(data.get("materials"), list):
            errors.append("registry top-level must be {claims, materials}")
        else:
            for index, material in enumerate(data["materials"]):
                if not isinstance(material, dict):
                    errors.append(f"materials[{index}] must be an object")
                    continue
                for field in ("material_id", "dedup_id", "source_url", "title",
                              "aihot_permalink"):
                    value = material.get(field)
                    if value is None or value == "" or not isinstance(value, str):
                        errors.append(f"materials[{index}].{field} must be a non-empty string")
    report = {"product": a.product, "valid": not errors, "errors": errors,
              "simulated": True}
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
