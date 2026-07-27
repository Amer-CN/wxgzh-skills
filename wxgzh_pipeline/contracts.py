"""Load stage contracts (YAML) + JSON schemas, and validate handoff objects."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import jsonschema
import yaml

SKILL_ROOT = Path(__file__).resolve().parents[1]

CONTRACT_FILES = {
    "aihot": "01_aihot.yaml",
    "super_writer": "02_super_writer.yaml",
    "zh_human_writing": "03_zh_human_writing.yaml",
    "media_enrichment": "04_media_enrichment.yaml",
    "gzh_design": "05_gzh_design.yaml",
    "wechat_draft": "06_wechat_draft.yaml",
}


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
