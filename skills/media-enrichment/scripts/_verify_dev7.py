#!/usr/bin/env python3
"""Portable verification script for media-enrichment dev7.

Uses Path(__file__) — no hardcoded drive paths.
Verifies dev7 acceptance criteria from evidence files.
"""

import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
EVIDENCE_DIR = SKILL_ROOT / "evidence"

REQUIRED_VERSION = "0.1.0-dev26"


def main():
    print("=== dev7 Verification ===")
    print(f"SKILL_ROOT: {SKILL_ROOT}")
    print(f"EVIDENCE_DIR: {EVIDENCE_DIR}")
    print()

    failures = []

    # 1. test_summary.json
    ts_path = EVIDENCE_DIR / "test_summary.json"
    if not ts_path.exists():
        print("FAIL: test_summary.json not found")
        sys.exit(1)
    ts = json.loads(ts_path.read_text(encoding="utf-8"))

    checks = {
        "skill_version_correct": ts.get("skill_version") == REQUIRED_VERSION,
        "PYTEST_EXIT_CODE": ts.get("PYTEST_EXIT_CODE", -1) == 0,
        "TESTS_TOTAL>0": ts.get("TESTS_TOTAL", 0) > 0,
        "TESTS_PASSED==TOTAL": ts.get("TESTS_PASSED", -1) == ts.get("TESTS_TOTAL", 0),
        "TESTS_FAILED=0": ts.get("TESTS_FAILED", -1) == 0,
        "RUNTIME_VERSION_RESIDUE_DEV3=0": ts.get("RUNTIME_VERSION_RESIDUE_DEV3", -1) == 0,
        "BUILD_VERSION_RESIDUE_DEV4=0": ts.get("BUILD_VERSION_RESIDUE_DEV4", -1) == 0,
        "CURRENT_EVIDENCE_VERSION_RESIDUE_DEV4=0": ts.get("CURRENT_EVIDENCE_VERSION_RESIDUE_DEV4", -1) == 0,
        "OUTPUT_ZIP_NAME_MATCH": ts.get("OUTPUT_ZIP_NAME_MATCH") is True,
        "PYTEST_NONZERO_BUILD_ABORT": ts.get("PYTEST_NONZERO_BUILD_ABORT", None) is not None,
        "ZERO_TESTS_BUILD_ABORT": ts.get("ZERO_TESTS_BUILD_ABORT", None) is not None,
        "FORMAL_VALIDATOR_EXIT_CODE=0": ts.get("FORMAL_VALIDATOR_EXIT_CODE", -1) == 0,
        "VALIDATOR_FALSE_PASS_TESTS=0": ts.get("VALIDATOR_FALSE_PASS_TESTS", -1) == 0,
        "COPYRIGHT_REVIEW_CONTRACT_PASS": ts.get("COPYRIGHT_REVIEW_CONTRACT_PASS") == True,
        "UNKNOWN_SOURCE_UPLOAD_CALLS=0": ts.get("UNKNOWN_SOURCE_UPLOAD_CALLS", -1) == 0,
        "RESTRICTED_SOURCE_UPLOAD_CALLS=0": ts.get("RESTRICTED_SOURCE_UPLOAD_CALLS", -1) == 0,
        "GENERATED_CHART_UPLOAD_PATH_PASS": ts.get("GENERATED_CHART_UPLOAD_PATH_PASS") == True,
        "TEST_SUMMARY_HARDCODED_PASS_FIELDS=0": ts.get("TEST_SUMMARY_HARDCODED_PASS_FIELDS", -1) == 0,
        "WECHAT_DRAFT_CREATED=false": ts.get("WECHAT_DRAFT_CREATED") == False,
        "WECHAT_ARTICLE_PUBLISHED=false": ts.get("WECHAT_ARTICLE_PUBLISHED") == False,
        "VERSION_CONSISTENCY_PASS": ts.get("VERSION_CONSISTENCY_PASS") == True,
        "THREE_CHART_FILES_PRESENT": ts.get("THREE_CHART_FILES_PRESENT") == True,
        "THREE_CHART_TYPES_PASS": ts.get("THREE_CHART_TYPES_PASS") == True,
    }

    for name, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {status} {name}")
        if not passed:
            failures.append(name)

    # 2. Chart files exist
    for chart in ["chart-bar.png", "chart-comparison.png", "chart-timeline.png"]:
        p = EVIDENCE_DIR / chart
        exists = p.exists()
        print(f"  {'PASS' if exists else 'FAIL'} {chart} exists")
        if not exists:
            failures.append(f"{chart} missing")

    # 3. validator_exit_code.txt
    vec_path = EVIDENCE_DIR / "validator_exit_code.txt"
    if vec_path.exists():
        vec = vec_path.read_text().strip()
        passed = vec == "0"
        print(f"  {'PASS' if passed else 'FAIL'} validator_exit_code=0 (got {vec})")
        if not passed:
            failures.append("validator_exit_code")
    else:
        print("  FAIL validator_exit_code.txt not found")
        failures.append("validator_exit_code.txt missing")

    print()
    if failures:
        print(f"RESULT: FAIL ({len(failures)} failures)")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("RESULT: ALL PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
