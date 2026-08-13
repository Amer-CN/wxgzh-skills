#!/usr/bin/env python3
"""Draft-delta validator (OBS-62R): AFTER = BEFORE + 1, all before-draft
update_times preserved, exactly one new update_time, and
draft_creation_result.json must show no deletion/publish/mass/schedule.

Operates purely on desensitized batchget snapshots (no live API here).
Draft identity is update_time ONLY — this validator never reads media_id,
so the first-8-chars-[REDACTED] desensitization collision (OBS-62) cannot
produce a false NEW_DRAFT_COUNT=0. Legacy offline fixtures
(drafts[].fingerprint, no items[]) keep the historical fingerprint-set
logic; their creation-flag check applies when draft_creation_result.json
exists next to the after file.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_CREATION_FLAG_KEYS = ("deleted_any", "formally_published", "mass_send", "scheduled")


def _creation_result(after: str | Path) -> dict | None:
    """draft_creation_result.json lives in the same audit dir as the snapshots."""
    p = Path(after).with_name("draft_creation_result.json")
    if not p.is_file():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _creation_flags(creation: dict | None) -> dict:
    return {k: bool((creation or {}).get(k)) for k in _CREATION_FLAG_KEYS}


def _validate_items(b: dict, a: dict, creation: dict | None) -> tuple[int, dict]:
    b_items, a_items = b.get("items") or [], a.get("items") or []
    bt, at = b.get("total_count", len(b_items)), a.get("total_count", len(a_items))
    b_times = {it["update_time"] for it in b_items if "update_time" in it}
    a_times = {it["update_time"] for it in a_items if "update_time" in it}
    new_times = a_times - b_times
    flags = _creation_flags(creation)
    if creation is None:
        # Real pipeline always writes draft_creation_result.json (contract
        # required output) — fail closed when it is missing.
        creation_ok = False
        creation_status = "FAIL"
    else:
        creation_ok = not any(flags.values())
        creation_status = "PASS" if creation_ok else "FAIL"
    report = {
        "BEFORE_TOTAL": bt,
        "AFTER_TOTAL": at,
        "NEW_DRAFT_COUNT": at - bt,
        "AFTER_eq_BEFORE_plus_1": at == bt + 1,
        "UPDATE_TIME_SUBSET": b_times.issubset(a_times),
        "OLD_DRAFTS_PRESERVED": b_times.issubset(a_times),
        "NEW_UPDATE_TIME_COUNT": len(new_times),
        "NEW_DRAFT_UNIQUE": len(new_times) == 1,
        "CREATION_RESULT": creation_status,
        "CREATION_RESULT_FLAGS": flags,
    }
    ok = (report["NEW_DRAFT_COUNT"] == 1 and report["OLD_DRAFTS_PRESERVED"]
          and report["NEW_DRAFT_UNIQUE"] and creation_ok)
    report["DRAFT_DELTA"] = "PASS" if ok else "FAIL"
    return (0 if ok else 1), report


def _validate_legacy(b: dict, a: dict, creation: dict | None) -> tuple[int, dict]:
    bf = {d.get("fingerprint") for d in b.get("drafts", []) if d.get("fingerprint")}
    af = {d.get("fingerprint") for d in a.get("drafts", []) if d.get("fingerprint")}
    new = af - bf
    bt, at = b.get("total_count", len(bf)), a.get("total_count", len(af))
    flags = _creation_flags(creation)
    if creation is None:
        creation_ok = True  # historical fixture behaviour; no file to inspect
        creation_status = "N/A"
    else:
        creation_ok = not any(flags.values())
        creation_status = "PASS" if creation_ok else "FAIL"
    report = {
        "BEFORE_TOTAL": bt, "AFTER_TOTAL": at,
        "AFTER_eq_BEFORE_plus_1": at == bt + 1,
        "OLD_DRAFTS_PRESERVED": bf.issubset(af),
        "NEW_DRAFT_COUNT": len(new), "NEW_DRAFT_UNIQUE": len(new) == 1,
        "CREATION_RESULT": creation_status,
        "CREATION_RESULT_FLAGS": flags,
    }
    ok = (report["AFTER_eq_BEFORE_plus_1"] and report["OLD_DRAFTS_PRESERVED"]
          and report["NEW_DRAFT_UNIQUE"] and creation_ok)
    report["DRAFT_DELTA"] = "PASS" if ok else "FAIL"
    return (0 if ok else 1), report


def validate(before: str | Path, after: str | Path) -> tuple[int, dict]:
    b = json.loads(Path(before).read_text(encoding="utf-8"))
    a = json.loads(Path(after).read_text(encoding="utf-8"))
    creation = _creation_result(after)
    if b.get("items") is not None or a.get("items") is not None:
        return _validate_items(b, a, creation)
    return _validate_legacy(b, a, creation)


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
