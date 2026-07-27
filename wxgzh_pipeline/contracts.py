"""Load stage contracts (YAML) + JSON schemas, validate handoff objects, and
ENFORCE each stage's YAML contract against real on-disk outputs (dev2)."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import jsonschema
import yaml

from . import execmodel as EM

SKILL_ROOT = Path(__file__).resolve().parents[1]

CONTRACT_FILES = {
    "aihot": "01_aihot.yaml",
    "super_writer": "02_super_writer.yaml",
    "zh_human_writing": "03_zh_human_writing.yaml",
    "media_enrichment": "04_media_enrichment.yaml",
    "gzh_design": "05_gzh_design.yaml",
    "wechat_draft": "06_wechat_draft.yaml",
}

STAGE_ORDER = {"aihot": 1, "super_writer": 2, "zh_human_writing": 3,
               "media_enrichment": 4, "gzh_design": 5, "wechat_draft": 6}


@lru_cache(maxsize=None)
def load_contract(stage: str) -> dict:
    return yaml.safe_load((SKILL_ROOT / "contracts" / CONTRACT_FILES[stage]).read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def load_schema(name: str) -> dict:
    return json.loads((SKILL_ROOT / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))


def validate(obj: dict, schema_name: str) -> list[str]:
    """Return a list of validation error messages ([] == valid)."""
    schema = load_schema(schema_name)
    errs = []
    v = jsonschema.Draft7Validator(schema)
    for e in sorted(v.iter_errors(obj), key=lambda e: list(e.absolute_path)):
        loc = "/".join(str(p) for p in e.absolute_path) or "<root>"
        errs.append(f"{loc}: {e.message}")
    return errs


def is_valid(obj: dict, schema_name: str) -> bool:
    return not validate(obj, schema_name)


def enforce_contract(stage: str, sd) -> tuple[bool, dict]:
    """Really consume the stage's YAML contract and enforce it against on-disk
    outputs: contract stage/order must match, and every declared required output
    must be present in the stage dir. Returns (ok, report)."""
    sd = Path(sd)
    c = load_contract(stage)
    problems = []
    if c.get("stage") != stage:
        problems.append(f"contract.stage={c.get('stage')} != {stage}")
    if c.get("order") != STAGE_ORDER.get(stage):
        problems.append(f"contract.order={c.get('order')} != {STAGE_ORDER.get(stage)}")
    expected = list(EM.EXPECTED_OUTPUTS.get(stage, []))
    missing = [o for o in expected if not (sd / o).is_file()]
    if missing:
        problems.append(f"missing required outputs: {missing}")
    must_after = c.get("must_run_after")
    ok = not problems
    return ok, {"CONTRACT": "PASS" if ok else "FAIL", "stage": stage,
                "contract_file": CONTRACT_FILES[stage], "required_outputs": expected,
                "must_run_after": must_after, "problems": problems}
