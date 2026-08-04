"""Manifest builder module.

Builds the final media_manifest.json with deterministic ordering.
ManifestBuilder.build() is idempotent — multiple calls produce the same
result without double-counting summary stats.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any

from . import __version__ as SKILL_VERSION


@dataclass
class AssetRecord:
    """Record for a single media asset."""
    asset_id: str
    asset_origin: str  # "source" or "generated"
    material_ids: list[str]
    claim_ids: list[str]
    aihot_permalink: str | None = None
    source_page_url: str | None = None
    discovered_url: str | None = None
    resolved_original_url: str | None = None
    extraction_method: str | None = None
    decode_method: str | None = None
    local_path: str | None = None
    sha256: str | None = None
    perceptual_hash: str | None = None
    mime_type: str | None = None
    width: int | None = None
    height: int | None = None
    file_size: int | None = None
    quality_status: str = "fail"
    relevance_status: str = "uncertain"
    copyright_status: str = "unknown"
    copyright_risk: str = "high"
    decision: str = "rejected"
    reasons: list[str] = field(default_factory=list)
    duplicate_of: str | None = None
    dedup_method: str = ""
    caption: str | None = None
    alt_text: str | None = None
    placement: dict[str, Any] | None = None
    # hotfix5 P0#3: approval is bound to stable content/source identity and a
    # frozen discovery manifest, not merely the sequential display asset_id.
    asset_identity_sha256: str | None = None
    discovery_manifest_sha256: str | None = None
    approval_id: str | None = None
    approved_scope: str | None = None
    approved_by: str | None = None
    approved_at: str | None = None
    approval_evidence_sha256: str | None = None
    asset_approval_consumed: bool = False
    approval_identity_mismatch: list[str] = field(default_factory=list)
    upload: dict[str, Any] = field(default_factory=lambda: {
        "mode": "dry_run",
        "status": "not_uploaded",
        "remote_url": None,
        "response_sha256": None,
    })
    # OBS-86(档62):正文边界判定结果。page_region ∈ body / peripheral / unknown;
    # page_position = {"known": bool, "heading": str, "level": str}——
    # 跨章节归属,供 Pipeline 侧 OBS-87 approval_readiness 直接消费。
    page_region: str = "unknown"
    page_position: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "asset_origin": self.asset_origin,
            "material_ids": sorted(self.material_ids),
            "claim_ids": sorted(self.claim_ids),
            "aihot_permalink": self.aihot_permalink,
            "source_page_url": self.source_page_url,
            "discovered_url": self.discovered_url,
            "resolved_original_url": self.resolved_original_url,
            "extraction_method": self.extraction_method,
            "decode_method": self.decode_method,
            "local_path": self.local_path,
            "sha256": self.sha256,
            "perceptual_hash": self.perceptual_hash,
            "mime_type": self.mime_type,
            "width": self.width,
            "height": self.height,
            "file_size": self.file_size,
            "quality_status": self.quality_status,
            "relevance_status": self.relevance_status,
            "copyright_status": self.copyright_status,
            "copyright_risk": self.copyright_risk,
            "decision": self.decision,
            "reasons": sorted(self.reasons),
            "duplicate_of": self.duplicate_of,
            "dedup_method": self.dedup_method,
            "caption": self.caption,
            "alt_text": self.alt_text,
            "placement": self.placement,
            "asset_identity_sha256": self.asset_identity_sha256,
            "discovery_manifest_sha256": self.discovery_manifest_sha256,
            "approval_id": self.approval_id,
            "approved_scope": self.approved_scope,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "approval_evidence_sha256": self.approval_evidence_sha256,
            "asset_approval_consumed": self.asset_approval_consumed,
            "approval_identity_mismatch": sorted(self.approval_identity_mismatch),
            "upload": self.upload,
            "page_region": self.page_region,
            "page_position": self.page_position,
        }


@dataclass
class ManifestBuilder:
    """Builds the media_manifest.json. build() is idempotent."""

    run_id: str
    request_sha256: str
    article_sha256: str
    claims_total: int
    materials_total: int
    assets: list[AssetRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    # These are external counters set by the pipeline, NOT derived from assets
    pages_requested: int = 0
    pages_fetched: int = 0
    candidates_discovered: int = 0
    downloads_succeeded: int = 0

    def add_asset(self, asset: AssetRecord) -> None:
        """Add an asset record."""
        self.assets.append(asset)

    def _compute_summary(self) -> dict[str, int]:
        """Compute summary from assets. Called fresh each build()."""
        eligible = sum(1 for a in self.assets if a.decision == "eligible")
        review = sum(1 for a in self.assets if a.decision == "review_required")
        rejected = sum(1 for a in self.assets if a.decision == "rejected")
        charts = sum(1 for a in self.assets if a.asset_origin == "generated")
        uploaded = sum(1 for a in self.assets if a.upload.get("status") == "success")
        exact_dup = sum(1 for a in self.assets if a.duplicate_of and a.dedup_method == "sha256")
        phash_dup = sum(1 for a in self.assets if a.duplicate_of and a.dedup_method != "sha256")

        return {
            "pages_requested": self.pages_requested,
            "pages_fetched": self.pages_fetched,
            "candidates_discovered": self.candidates_discovered,
            "downloads_succeeded": self.downloads_succeeded,
            "exact_duplicates_removed": exact_dup,
            "perceptual_duplicates_removed": phash_dup,
            "rejected_assets": rejected,
            "review_required_assets": review,
            "eligible_assets": eligible,
            "generated_charts": charts,
            "uploaded_assets": uploaded,
        }

    def build(self) -> dict[str, Any]:
        """Build the manifest dict with deterministic ordering.

        No caching — every call recomputes from current state.
        This ensures mutations (e.g. appending errors) are always reflected.
        """
        sorted_assets = sorted(self.assets, key=lambda a: a.asset_id)
        summary = self._compute_summary()

        # Compute gate flags from real data
        has_errors = len(self.errors) > 0
        provenance_complete = all(
            a.sha256 and (a.source_page_url or a.asset_origin == "generated")
            for a in sorted_assets
            if a.decision != "rejected"
        ) and len(sorted_assets) > 0 or len(sorted_assets) == 0

        result = {
            "schema_version": "1.0",
            "skill_version": SKILL_VERSION,
            "run_id": self.run_id,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "input": {
                "request_sha256": self.request_sha256,
                "article_sha256": self.article_sha256,
                "claims_total": self.claims_total,
                "materials_total": self.materials_total,
            },
            "summary": summary,
            "assets": [a.to_dict() for a in sorted_assets],
            "errors": sorted(self.errors),
            "warnings": sorted(self.warnings),
            "gate": {
                "input_contract_pass": not has_errors,
                "provenance_complete": provenance_complete,
                "security_checks_pass": not has_errors,
                "secrets_detected": False,
                "publish_allowed": False,  # ALWAYS False
            },
        }

        return result

    def write(self, output_path: str) -> str:
        """Build and write manifest to file."""
        manifest = self.build()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)
        return output_path
