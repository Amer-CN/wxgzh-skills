#!/usr/bin/env python3
"""Verify the orchestrator skill zips reproducibly: build twice into temp and
assert byte-identical (same sha256).
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT))
from wxgzh_pipeline.zipping import deterministic_zip  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(SKILL_ROOT))
    a = ap.parse_args(argv)
    with tempfile.TemporaryDirectory() as td:
        z1 = Path(td) / "build1.zip"
        z2 = Path(td) / "build2.zip"
        s1 = deterministic_zip(a.src, z1, arc_prefix="wxgzh-pipeline")
        s2 = deterministic_zip(a.src, z2, arc_prefix="wxgzh-pipeline")
    reproducible = s1 == s2
    print(json.dumps({"src": a.src, "sha_build1": s1, "sha_build2": s2,
                      "REPRODUCIBLE": reproducible}, ensure_ascii=False, indent=2))
    return 0 if reproducible else 1


if __name__ == "__main__":
    sys.exit(main())
