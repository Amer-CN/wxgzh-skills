#!/usr/bin/env python3
"""Pipeline-state validator: pipeline_state.json conforms to schema and
formally_published is always False.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import jsonschema

SKILL_ROOT = Path(__file__).resolve().parents[1]


def validate(state_path: str | Path) -> tuple[int, dict]:
    st = json.loads(Path(state_path).read_text(encoding="utf-8"))
    schema = json.loads((SKILL_ROOT / "schemas" / "pipeline_state.schema.json").read_text(encoding="utf-8"))
    v = jsonschema.Draft7Validator(schema)
    errs = [f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}"
            for e in v.iter_errors(st)]
    fp_false = st.get("formally_published") is False
    ok = not errs and fp_false
    return (0 if ok else 1), {"PIPELINE_STATE": "PASS" if ok else "FAIL",
                              "schema_errors": errs, "formally_published_is_false": fp_false}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", required=True)
    a = ap.parse_args(argv)
    code, report = validate(a.state)
    print(json.dumps(report, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
