#!/usr/bin/env python3
"""Delivery validator: final_delivery.json present, formally_published False,
draft_created True, all 6 stages have receipts, and MANIFEST recomputes clean.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

STAGES = ["aihot", "super_writer", "zh_human_writing", "media_enrichment", "gzh_design", "wechat_draft"]


def validate(run_dir: str | Path) -> tuple[int, dict]:
    run_dir = Path(run_dir)
    delivery = run_dir / "final_delivery.json"
    manifest = run_dir / "MANIFEST.json"
    if not delivery.is_file() or not manifest.is_file():
        return 1, {"DELIVERY": "FAIL", "reason": "final_delivery.json or MANIFEST.json missing"}
    d = json.loads(delivery.read_text(encoding="utf-8"))
    m = json.loads(manifest.read_text(encoding="utf-8"))
    hash_bad = 0
    for e in m.get("files", []):
        p = run_dir / e["path"]
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != e["sha256"]:
            hash_bad += 1
    stages_ok = all((run_dir / s / "stage_receipt.json").is_file() for s in STAGES)
    report = {
        "formally_published_false": d.get("formally_published") is False,
        "draft_created": d.get("draft_created"),
        "draft_created_true": d.get("draft_created") is True,
        "all_stage_receipts_present": stages_ok,
        "manifest_hash_mismatch": hash_bad,
        "manifest_file_count": m.get("file_count"),
    }
    ok = (report["formally_published_false"] and report["draft_created_true"]
          and stages_ok and hash_bad == 0)
    report["DELIVERY"] = "PASS" if ok else "FAIL"
    return (0 if ok else 1), report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    a = ap.parse_args(argv)
    code, report = validate(a.run_dir)
    print(json.dumps(report, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
