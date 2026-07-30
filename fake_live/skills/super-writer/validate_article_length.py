#!/usr/bin/env python3
"""FAKE-LIVE shim mirroring super-writer `scripts/validate_article_length.py`.
EXACT real CLI subset: --article [--full-mode --outline --brief --evidence-map
--core-card --editor-report]. SIMULATED."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CJK = re.compile(r"[\u4e00-\u9fff]")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="validate_article_length (fake-live shim)")
    ap.add_argument("--article", required=True)
    ap.add_argument("--full-mode", action="store_true")
    ap.add_argument("--outline", default=None)
    ap.add_argument("--brief", default=None)
    ap.add_argument("--evidence-map", default=None)
    ap.add_argument("--core-card", default=None)
    ap.add_argument("--editor-report", default=None)
    ap.add_argument("--generation-profile", default=None)
    ap.add_argument("--material-readiness", default=None)
    ap.add_argument("--material-ledger", default=None)
    ap.add_argument("--material-report", default=None)
    ap.add_argument("--semantic-map", default=None)
    ap.add_argument("--article-mode", default=None)
    ap.add_argument("--target-visible-chars", type=int, default=None)
    ap.add_argument("--acceptable-min", type=int, default=None)
    ap.add_argument("--acceptable-max", type=int, default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    p = Path(a.article)
    if not p.is_file():
        print(f"[fake validate_article_length] article missing: {p}")
        return 1
    text = p.read_text(encoding="utf-8", errors="replace")
    if not CJK.search(text):
        print("[fake validate_article_length] no CJK content")
        return 1
    required = [a.outline, a.brief, a.evidence_map, a.core_card, a.editor_report,
                a.generation_profile, a.material_readiness, a.material_ledger,
                a.material_report, a.semantic_map]
    if a.full_mode and any(not value or not Path(value).is_file() for value in required):
        print(json.dumps({"passed": False, "errors": ["missing full-mode artifact"]}))
        return 1
    bound_report = p.parent / "full_mode_validator_report.json"
    if bound_report.is_file():
        result = json.loads(bound_report.read_text(encoding="utf-8"))
    else:
        result = {"passed": True, "article_mode": a.article_mode,
                  "target_visible_chars": a.target_visible_chars,
                  "acceptable_min": a.acceptable_min, "acceptable_max": a.acceptable_max,
                  "visible_chars_no_whitespace": len(re.sub(r"\s+", "", text)),
                  "errors": [], "warnings": [], "simulated": True}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
