"""Input contract module.

Loads request JSON, validates against JSON Schema, cross-validates
Claim/Material references, and verifies article SHA256.
Fail-closed: never produces a 'looks-successful' result on invalid input.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

SKILL_VERSION = "0.1.0-dev31"

@dataclass
class ValidationResult:
    """Result of input validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    request: dict[str, Any] | None = None
    request_sha256: str | None = None
    article_sha256: str | None = None


def compute_sha256(data: bytes) -> str:
    """Compute SHA256 hex digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def compute_file_sha256(path: str | Path) -> str:
    """Compute SHA256 hex digest of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_schema(schema_name: str) -> dict[str, Any]:
    """Load a JSON Schema from the schemas directory."""
    schema_dir = Path(__file__).resolve().parents[2] / "schemas"
    schema_path = schema_dir / f"{schema_name}.schema.json"
    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


def validate_request(request_path: str | Path) -> ValidationResult:
    """Validate a media enrichment request file.

    Steps:
    1. Load JSON
    2. Validate against JSON Schema
    3. Cross-validate Claim/Material references
    4. Verify article SHA256 (if article file exists)
    5. Verify article path exists

    Returns ValidationResult with valid=False on any failure.
    Never produces a 'looks-successful' result on invalid input.
    """
    result = ValidationResult(valid=False)
    errors: list[str] = []
    warnings: list[str] = []

    request_path = Path(request_path)

    # Step 1: Load JSON
    if not request_path.exists():
        errors.append(f"Request file not found: {request_path}")
        return ValidationResult(valid=False, errors=errors)

    try:
        raw = request_path.read_bytes()
    except OSError as exc:
        errors.append(f"Cannot read request file: {exc}")
        return ValidationResult(valid=False, errors=errors)

    result.request_sha256 = compute_sha256(raw)

    try:
        request = json.loads(raw)
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON: {exc}")
        return ValidationResult(valid=False, errors=errors)

    # Step 2: Validate against JSON Schema
    try:
        schema = _load_schema("media_enrichment_request")
        jsonschema.validate(instance=request, schema=schema)
    except jsonschema.ValidationError as exc:
        errors.append(f"Schema validation failed: {exc.message} (path: {'/'.join(str(p) for p in exc.absolute_path)})")
        return ValidationResult(valid=False, errors=errors, request_sha256=result.request_sha256)
    except FileNotFoundError as exc:
        errors.append(f"Schema file not found: {exc}")
        return ValidationResult(valid=False, errors=errors, request_sha256=result.request_sha256)

    # Step 3: Cross-validate Claim/Material references
    materials = request.get("materials", [])
    claims = request.get("claims", [])

    # 3a: material_id must be unique
    material_ids = [m["material_id"] for m in materials]
    seen_material_ids: set[str] = set()
    duplicate_material_ids = set()
    for mid in material_ids:
        if mid in seen_material_ids:
            duplicate_material_ids.add(mid)
        seen_material_ids.add(mid)
    if duplicate_material_ids:
        errors.append(f"Duplicate material_id(s): {sorted(duplicate_material_ids)}")

    # 3b: claim_id must be unique
    claim_ids = [c["claim_id"] for c in claims]
    seen_claim_ids: set[str] = set()
    duplicate_claim_ids = set()
    for cid in claim_ids:
        if cid in seen_claim_ids:
            duplicate_claim_ids.add(cid)
        seen_claim_ids.add(cid)
    if duplicate_claim_ids:
        errors.append(f"Duplicate claim_id(s): {sorted(duplicate_claim_ids)}")

    # 3c: each claim's material_id must exist
    material_id_set = set(material_ids)
    for claim in claims:
        if claim["material_id"] not in material_id_set:
            errors.append(
                f"Claim {claim['claim_id']} references non-existent material_id: {claim['material_id']}"
            )

    # 3d: claim source_url must match corresponding material source_url
    material_by_id = {m["material_id"]: m for m in materials}
    for claim in claims:
        mat = material_by_id.get(claim["material_id"])
        if mat:
            if claim["source_url"] != mat["source_url"]:
                errors.append(
                    f"Claim {claim['claim_id']} source_url '{claim['source_url']}' "
                    f"does not match material {claim['material_id']} source_url '{mat['source_url']}'"
                )

    # 3e: selected_claim_ids in materials must reference existing claims
    claim_id_set = set(claim_ids)
    for mat in materials:
        for cid in mat.get("selected_claim_ids", []):
            if cid not in claim_id_set:
                errors.append(
                    f"Material {mat['material_id']} selects non-existent claim_id: {cid}"
                )

    # Step 4: Verify article SHA256
    article_path = request.get("article", {}).get("path", "")
    article_sha256 = request.get("article", {}).get("sha256", "")
    result.article_sha256 = article_sha256

    # Resolve article path relative to request file directory
    article_full_path = request_path.parent / article_path if article_path else None

    if not article_path:
        errors.append("Article path is missing")
    elif not article_full_path.exists():
        errors.append(f"Article file not found: {article_full_path}")
    elif article_full_path.exists():
        actual_sha = compute_file_sha256(article_full_path)
        if actual_sha != article_sha256:
            errors.append(
                f"Article SHA256 mismatch: expected {article_sha256}, got {actual_sha}"
            )

    # Step 5: Check config
    config = request.get("config", {})
    if config.get("allow_unknown_license_for_publish") is True:
        errors.append("allow_unknown_license_for_publish must be false")

    # Step 6: Validate copyright_review on each material
    for mat in materials:
        cr = mat.get("copyright_review", {})
        status = cr.get("status", "unknown")
        if status == "known_allowed":
            if not cr.get("reviewed_by"):
                errors.append(f"Material {mat['material_id']}: copyright_review.status=known_allowed but reviewed_by is empty")
            if not cr.get("reviewed_at"):
                errors.append(f"Material {mat['material_id']}: copyright_review.status=known_allowed but reviewed_at is empty")
            if not cr.get("evidence"):
                errors.append(f"Material {mat['material_id']}: copyright_review.status=known_allowed but evidence is empty")

    # Step 7 (hotfix5 P0#3): approvals bind a frozen discovery manifest and a
    # stable identity, never merely the sequential display asset_id.
    import re as _re
    hex64 = _re.compile(r"^[0-9a-fA-F]{64}$")
    hash_fields = (
        "asset_sha256", "asset_identity_sha256", "discovery_manifest_sha256",
        "approval_evidence_sha256",
    )
    seen_asset_approvals: dict[str, dict] = {}
    for idx, ap in enumerate(request.get("asset_approvals", [])):
        aid = ap.get("asset_id", "")
        if ap.get("approved_scope") != "single_asset":
            errors.append(f"asset_approvals[{idx}]: approved_scope must be single_asset")
        for field_name in hash_fields:
            value = ap.get(field_name, "")
            if not isinstance(value, str) or not hex64.fullmatch(value):
                errors.append(
                    f"asset_approvals[{idx}] ({aid}): {field_name} must be a 64-hex sha256")
        identity_material = "\n".join((
            str(ap.get("material_id", "")),
            str(ap.get("source_page_url", "")),
            str(ap.get("resolved_original_url", "")),
            str(ap.get("asset_sha256", "")),
        )).encode("utf-8")
        expected_identity = compute_sha256(identity_material)
        if ap.get("asset_identity_sha256") != expected_identity:
            errors.append(
                f"asset_approvals[{idx}] ({aid}): asset_identity_sha256 does not match stable identity fields")
        if aid in seen_asset_approvals:
            prev = seen_asset_approvals[aid]
            if prev != ap:
                errors.append(f"asset_approvals: conflicting approvals for asset_id {aid}")
            else:
                errors.append(f"asset_approvals: duplicate approval for asset_id {aid}")
        else:
            seen_asset_approvals[aid] = ap

    if errors:
        return ValidationResult(valid=False, errors=errors, warnings=warnings, request_sha256=result.request_sha256, article_sha256=article_sha256)

    result.valid = True
    result.warnings = warnings
    result.request = request
    return result
