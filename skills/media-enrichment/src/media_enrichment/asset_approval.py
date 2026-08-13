"""Stable discovery identity and single-asset approval verification."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_asset_identity(
    material_id: str,
    source_page_url: str,
    resolved_original_url: str,
    asset_sha256: str,
) -> str:
    payload = "\n".join((
        material_id,
        source_page_url,
        resolved_original_url,
        asset_sha256,
    )).encode("utf-8")
    return sha256_bytes(payload)


def canonical_manifest_bytes(manifest: dict[str, Any]) -> bytes:
    """Return deterministic bytes for the frozen discovery manifest.

    The digest field is excluded from its own digest calculation.
    """
    unsigned = dict(manifest)
    unsigned.pop("discovery_manifest_sha256", None)
    return (json.dumps(
        unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ) + "\n").encode("utf-8")


def freeze_discovery_manifest(assets: list[dict[str, Any]]) -> dict[str, Any]:
    frozen = {
        "schema_version": "1.0",
        "assets": sorted(assets, key=lambda item: (
            item["asset_identity_sha256"], item["asset_id"],
        )),
    }
    frozen["discovery_manifest_sha256"] = sha256_bytes(canonical_manifest_bytes(frozen))
    return frozen


def write_discovery_manifest(path: str | Path, manifest: dict[str, Any]) -> None:
    Path(path).write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def verify_discovery_manifest(manifest: dict[str, Any]) -> tuple[bool, str]:
    recorded = manifest.get("discovery_manifest_sha256", "")
    actual = sha256_bytes(canonical_manifest_bytes(manifest))
    return recorded == actual, actual


def approval_mismatches(
    approval: dict[str, Any],
    discovered: dict[str, Any],
    discovery_manifest_sha256: str,
) -> list[str]:
    checks = {
        "asset_id": discovered["asset_id"],
        "material_id": discovered["material_id"],
        "source_page_url": discovered["source_page_url"],
        "resolved_original_url": discovered["resolved_original_url"],
        "asset_sha256": discovered["asset_sha256"],
        "asset_identity_sha256": discovered["asset_identity_sha256"],
        "discovery_manifest_sha256": discovery_manifest_sha256,
    }
    return [
        field_name for field_name, actual_value in checks.items()
        if approval.get(field_name) != actual_value
    ]
