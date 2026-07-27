#!/usr/bin/env python3
"""Article-freeze validator: the frozen final_article.md must still hash to the
recorded final_article_sha256; downstream artifacts must reference that same sha
(so no stage silently edited article facts).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def validate(final_article: str | Path, expected_sha256: str,
             downstream_refs: list[str] | None = None) -> tuple[int, dict]:
    actual = _sha(final_article)
    unchanged = actual == expected_sha256
    ds = []
    for ref in (downstream_refs or []):
        p = Path(ref)
        if not p.is_file():
            ds.append({"ref": str(p), "exists": False, "references_frozen_sha": False})
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        ds.append({"ref": str(p), "exists": True, "references_frozen_sha": expected_sha256 in txt})
    downstream_ok = all(d["references_frozen_sha"] for d in ds) if ds else True
    report = {"expected_sha256": expected_sha256, "actual_sha256": actual,
              "final_article_unchanged": unchanged, "downstream": ds,
              "downstream_all_reference_frozen_sha": downstream_ok}
    ok = unchanged and downstream_ok
    report["ARTICLE_FREEZE"] = "PASS" if ok else "FAIL"
    return (0 if ok else 1), report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--final-article", required=True)
    ap.add_argument("--expected-sha256", required=True)
    ap.add_argument("--downstream", nargs="*", default=[])
    a = ap.parse_args(argv)
    code, report = validate(a.final_article, a.expected_sha256, a.downstream)
    print(json.dumps(report, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
