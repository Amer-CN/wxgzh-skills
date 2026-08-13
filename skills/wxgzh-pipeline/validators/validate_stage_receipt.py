#!/usr/bin/env python3
"""Stage-receipt validator: required fields present + validator_exit_code == 0.
A stage without a valid receipt is treated as NOT executed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED = [
    "skill_name", "skill_dir", "skill_version", "skill_root_sha256",
    "invoked_entrypoint", "input_files", "input_hashes", "output_files",
    "output_hashes", "validator_path", "validator_sha256", "validator_exit_code",
    "started_at", "ended_at", "elapsed_seconds", "side_effects",
]


def validate(receipt_path: str | Path) -> tuple[int, dict]:
    p = Path(receipt_path)
    if not p.is_file():
        return 1, {"STAGE_RECEIPT": "FAIL", "reason": "receipt missing (stage treated as NOT executed)"}
    r = json.loads(p.read_text(encoding="utf-8"))
    missing = [f for f in REQUIRED if f not in r]
    exit_ok = r.get("validator_exit_code") == 0
    ok = not missing and exit_ok
    return (0 if ok else 1), {"STAGE_RECEIPT": "PASS" if ok else "FAIL",
                              "missing_fields": missing,
                              "validator_exit_code": r.get("validator_exit_code")}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipt", required=True)
    a = ap.parse_args(argv)
    code, report = validate(a.receipt)
    print(json.dumps(report, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
