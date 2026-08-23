"""77F/OBS-315: component catalog stays synchronized with the validator registry."""

import importlib.util
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
SW_ROOT = SKILL_ROOT.parent / "super-writer"


def _load_semantic_validator():
    path = SW_ROOT / "scripts" / "validate_semantic_map.py"
    spec = importlib.util.spec_from_file_location("validate_semantic_map", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _catalog_rows():
    text = (SW_ROOT / "references" / "component-catalog.md").read_text(encoding="utf-8")
    rows = {}
    for line in text.splitlines():
        if not line.startswith("- `"):
            continue
        role_part, field_part = line.split(" — ", 1)
        role = role_part[3:-1]
        if field_part.startswith("必填 payload 字段："):
            field_text = field_part.removeprefix("必填 payload 字段：").strip("`")
            fields = tuple(field_text.split(", "))
        else:
            fields = ()
        rows[role] = fields
    return rows


def test_77f_component_catalog_matches_registry_single_source():
    validator = _load_semantic_validator()
    rows = _catalog_rows()
    assert rows.keys() == set(validator.ALLOWED_ROLES)
    assert rows == {role: tuple(validator.ROLE_REQUIRED_FIELDS.get(role, ()))
                    for role in validator.ALLOWED_ROLES}


def test_77f_semantic_map_precheck_rejects_unknown_and_incomplete_payload(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "validate_single_product",
        SW_ROOT / "scripts" / "validate_single_product.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    unknown = tmp_path / "unknown.yaml"
    unknown.write_text(
        'schema_version: "1.0"\n'
        "article:\n  title: T\n"
        "blocks:\n  - role: definitely-not-registered\n    payload: {}\n",
        encoding="utf-8")
    errors, _ = module.check_semantic_map(unknown)
    assert any("definitely-not-registered" in error and "component-catalog.md" in error
               for error in errors)

    incomplete = tmp_path / "incomplete.yaml"
    incomplete.write_text(
        'schema_version: "1.0"\n'
        "article:\n  title: T\n"
        "blocks:\n  - role: tip\n    payload: {}\n",
        encoding="utf-8")
    errors, _ = module.check_semantic_map(incomplete)
    assert any("role=tip" in error and "'text'" in error
               and "component-catalog.md" in error for error in errors)
