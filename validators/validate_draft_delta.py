#!/usr/bin/env python3
"""Draft-delta validator: AFTER = BEFORE + 1, all old fingerprints preserved,
exactly one new unique draft. Operates purely on desensitized batchget snapshots
(no live API here).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _fps(snap: dict) -> set:
    return {d["fingerprint"] for d in snap.get("drafts", [])}


def validate(before: str | Path, after: str | Path) -> tuple[int, dict]:
    b = json.loads(Path(before).read_text(encoding="utf-8"))
    a = json.loads(Path(after).read_text(encoding="utf-8"))
    bf, af = _fps(b), _fps(a)
    new = af - bf
    bt, at = b.get("total_count", len(bf)), a.get("total_count", len(af))
    report = {
        "BEFORE_TOTAL": bt, "AFTER_TOTAL": at,
        "AFTER_eq_BEFORE_plus_1": at == bt + 1,
        "OLD_DRAFTS_PRESERVED": bf.issubset(af),
        "NEW_DRAFT_COUNT": len(new), "NEW_DRAFT_UNIQUE": len(new) == 1,
    }
    ok = report["AFTER_eq_BEFORE_plus_1"] and report["OLD_DRAFTS_PRESERVED"] and report["NEW_DRAFT_UNIQUE"]
    report["DRAFT_DELTA"] = "PASS" if ok else "FAIL"
    return (0 if ok else 1), report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", required=True)
    a = ap.parse_args(argv)
    code, report = validate(a.before, a.after)
    print(json.dumps(report, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
