#!/usr/bin/env python3
"""Media Enrichment CLI — main entry point.

Orchestrates: validate → fetch → extract → decode → download → inspect →
dedup → classify → generate charts → upload → placement → manifest.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

from media_enrichment import __version__ as SKILL_VERSION
from media_enrichment.input_contract import validate_request
from media_enrichment.page_fetcher import fetch_page, scan_no_repost
from media_enrichment.image_extractor import extract_images
from media_enrichment.proxy_decoder import decode_proxy_url
from media_enrichment.url_security import is_safe_url
from media_enrichment.downloader import download_image
from media_enrichment.image_inspector import inspect_image
from media_enrichment.image_deduplicator import deduplicate_asset, DedupState
from media_enrichment.image_classifier import classify_image
from media_enrichment.chart_generator import build_chart_specs, generate_chart
from media_enrichment.uploader import create_uploader, scan_for_secrets, timed_upload
from media_enrichment.placement_planner import find_anchors
from media_enrichment.manifest_builder import ManifestBuilder, AssetRecord
from media_enrichment.asset_approval import (
    approval_mismatches,
    freeze_discovery_manifest,
    stable_asset_identity,
    verify_discovery_manifest,
    write_discovery_manifest,
)


def main():
    parser = argparse.ArgumentParser(description="Media Enrichment Skill")
    parser.add_argument("--request", required=True)
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--fixture-dir", default=None)
    parser.add_argument(
        "--phase", choices=("discover", "continue"), default="discover",
        help="discover never uploads; continue requires --discovery-manifest and stable approvals",
    )
    parser.add_argument("--discovery-manifest", default=None)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Validate input
    print("[media-enrichment] Validating input contract...")
    validation = validate_request(args.request)
    if not validation.valid:
        print("[media-enrichment] Input validation FAILED:")
        for err in validation.errors:
            print(f"  ERROR: {err}")
        builder = ManifestBuilder(
            run_id="validation_failed",
            request_sha256=validation.request_sha256 or "",
            article_sha256=validation.article_sha256 or "",
            claims_total=0, materials_total=0,
        )
        builder.errors = list(validation.errors)
        builder.warnings = list(validation.warnings)
        builder.write(str(output_dir / "media_manifest.json"))
        sys.exit(1)

    request = validation.request
    config = request.get("config", {})
    print(f"[media-enrichment] Input validation PASSED")

    article_path = request.get("article", {}).get("path", "")
    article_sha256 = request.get("article", {}).get("sha256", "")
    builder = ManifestBuilder(
        run_id=request.get("run_id", "unknown"),
        request_sha256=validation.request_sha256 or "",
        article_sha256=article_sha256,
        claims_total=len(request.get("claims", [])),
        materials_total=len(request.get("materials", [])),
    )

    dedup_state = DedupState()
    requested_upload_mode = config.get("upload_mode", "dry_run")
    upload_mode = "dry_run" if args.phase == "discover" else requested_upload_mode
    # dev2-hotfix2: serial upload event log (proves no overlap, one attempt/asset)
    upload_events: list = []

    # Validate upload_mode. Discovery is side-effect-free regardless of request.
    try:
        create_uploader(requested_upload_mode)
        uploader = create_uploader(upload_mode)
    except ValueError as exc:
        builder.errors.append(str(exc))
        builder.write(str(output_dir / "media_manifest.json"))
        print(f"[media-enrichment] ERROR: {exc}")
        sys.exit(1)

    materials = request.get("materials", [])
    claims = request.get("claims", [])
    materials_by_id = {m["material_id"]: m for m in materials}
    network_mode = config.get("network_mode", "live")
    fixture_dir = args.fixture_dir or str(SKILL_ROOT / "fixtures" / "html")
    # hotfix5 P0#3: approvals are considered only in the continue phase and are
    # matched to a stable identity after discovery and content hashing complete.
    asset_approvals = {ap["asset_id"]: ap for ap in request.get("asset_approvals", [])}
    consumed_asset_approvals: set[str] = set()
    discovery_records: list[dict] = []
    pending_uploads: list[tuple[AssetRecord, str, object, str]] = []
    # offline image "downloads" read from a sibling images/ fixture dir (no network)
    fixture_images_dir = Path(fixture_dir).parent / "images"

    max_images_per_material = config.get("max_images_per_material", 3)
    max_total_images = config.get("max_total_images", 12)
    total_assets_added = 0
    asset_counter = 0

    for mat in materials:
        material_id = mat["material_id"]
        permalink = mat.get("aihot_permalink", "")
        source_url = mat.get("source_url", "")
        material_image_count = 0
        # Get copyright status from material's copyright_review
        copyright_review = mat.get("copyright_review", {})
        mat_copyright_status = copyright_review.get("status", "unknown")

        print(f"\n[media-enrichment] Processing material {material_id}: {permalink}")

        if total_assets_added >= max_total_images:
            builder.warnings.append(f"max_total_images ({max_total_images}) reached — skipping {material_id}")
            print(f"  SKIP: max_total_images reached")
            continue

        builder.pages_requested += 1
        # dev7: prefer the ORIGINAL source page (materials[].source_url).
        # aihot_permalink stays for traceability and is only a fallback
        # when the original page cannot be fetched.
        page_url = ""
        fetch_result = None
        if source_url and source_url != permalink:
            fetch_result = fetch_page(source_url, mode=network_mode, fixture_dir=fixture_dir)
            if fetch_result.success:
                page_url = source_url
            else:
                builder.warnings.append(
                    f"{material_id}: source_url fetch failed — falling back to "
                    f"aihot_permalink ({str(fetch_result.error)[:120]})")
        if not page_url:
            fetch_result = fetch_page(permalink, mode=network_mode, fixture_dir=fixture_dir)
            if fetch_result.success:
                page_url = permalink

        if not page_url:
            builder.errors.append(f"Failed to fetch page for {material_id}: {fetch_result.error}")
            print(f"  FETCH FAILED: {fetch_result.error}")
            continue

        builder.pages_fetched += 1
        page_kind = "source_url" if page_url == source_url and source_url != permalink else "aihot_permalink"
        print(f"  Fetched via {page_kind}: {fetch_result.status_code}")

        # dev7: explicit no-repost scan targets the ORIGINAL source page.
        # If found there, all images from this material become restricted.
        if page_kind == "source_url":
            no_repost_hits = scan_no_repost(fetch_result.content)
            if no_repost_hits:
                mat_copyright_status = "restricted"
                builder.warnings.append(
                    f"{material_id}: explicit no-repost statement on source page "
                    f"({'/'.join(no_repost_hits)}) — images restricted")

        extraction = extract_images(fetch_result.content, page_url=page_url)
        builder.candidates_discovered += len(extraction.candidates)
        print(f"  Candidates: {len(extraction.candidates)}")

        for candidate in extraction.candidates:
            if total_assets_added >= max_total_images:
                builder.warnings.append(f"max_total_images ({max_total_images}) reached — stopping discovery")
                break
            if material_image_count >= max_images_per_material:
                builder.warnings.append(f"max_images_per_material ({max_images_per_material}) reached for {material_id}")
                break

            asset_counter += 1
            asset_id = f"A-{asset_counter:03d}"
            effective_copyright = mat_copyright_status

            decode_result = decode_proxy_url(candidate.url)
            resolved_url = decode_result.decoded_url

            sec_check = is_safe_url(resolved_url, require_dns=(network_mode == "live"))
            if not sec_check.safe:
                asset = AssetRecord(
                    asset_id=asset_id, asset_origin="source",
                    material_ids=[material_id], claim_ids=mat.get("selected_claim_ids", []),
                    aihot_permalink=permalink, source_page_url=page_url,
                    discovered_url=candidate.url, resolved_original_url=resolved_url,
                    extraction_method=candidate.extraction_method, decode_method=decode_result.decode_method,
                    decision="rejected", reasons=[f"URL security: {', '.join(sec_check.reasons)}"],
                    quality_status="fail", relevance_status="irrelevant",
                )
                builder.add_asset(asset)
                continue

            images_dir = output_dir / "images"
            download_result = download_image(resolved_url, images_dir,
                                              max_bytes=config.get("max_download_bytes", 15728640),
                                              mode=network_mode, fixture_dir=fixture_images_dir)
            if not download_result.success:
                asset = AssetRecord(
                    asset_id=asset_id, asset_origin="source",
                    material_ids=[material_id], claim_ids=mat.get("selected_claim_ids", []),
                    aihot_permalink=permalink, source_page_url=page_url,
                    discovered_url=candidate.url, resolved_original_url=resolved_url,
                    extraction_method=candidate.extraction_method, decode_method=decode_result.decode_method,
                    decision="rejected", reasons=[f"download failed: {download_result.error}"],
                    quality_status="fail",
                )
                builder.add_asset(asset)
                continue

            builder.downloads_succeeded += 1

            inspection = inspect_image(download_result.local_path,
                                        max_pixels=config.get("max_pixels", 40_000_000))

            dedup_result = deduplicate_asset(
                asset_id=asset_id, sha256=inspection.sha256,
                original_url=resolved_url, perceptual_hash=inspection.perceptual_hash,
                width=inspection.width, height=inspection.height, state=dedup_state,
            )

            if dedup_result.is_duplicate:
                asset = AssetRecord(
                    asset_id=asset_id, asset_origin="source",
                    material_ids=[material_id], claim_ids=mat.get("selected_claim_ids", []),
                    discovered_url=candidate.url, resolved_original_url=resolved_url,
                    sha256=inspection.sha256,
                    decision="rejected", reasons=[dedup_result.dedup_reason],
                    duplicate_of=dedup_result.duplicate_of,
                    dedup_method=dedup_result.dedup_method,
                    quality_status="pass" if inspection.is_valid else "fail",
                )
                builder.add_asset(asset)
                continue

            identity_sha256 = stable_asset_identity(
                material_id, page_url, resolved_url, inspection.sha256,
            )
            discovery_record = {
                "asset_id": asset_id,
                "material_id": material_id,
                "source_page_url": page_url,
                "resolved_original_url": resolved_url,
                "asset_sha256": inspection.sha256,
                "asset_identity_sha256": identity_sha256,
            }
            discovery_records.append(discovery_record)

            classification = classify_image(
                url=resolved_url, inspection=inspection,
                min_width=config.get("min_width", 640), min_height=config.get("min_height", 360),
                context=candidate.context, copyright_status=effective_copyright,
                extraction_method=candidate.extraction_method,
            )

            asset = AssetRecord(
                asset_id=asset_id, asset_origin="source",
                material_ids=[material_id], claim_ids=mat.get("selected_claim_ids", []),
                aihot_permalink=permalink, source_page_url=page_url,
                discovered_url=candidate.url, resolved_original_url=resolved_url,
                extraction_method=candidate.extraction_method, decode_method=decode_result.decode_method,
                local_path=download_result.local_path, sha256=inspection.sha256,
                perceptual_hash=inspection.perceptual_hash, mime_type=inspection.mime_type,
                width=inspection.width, height=inspection.height, file_size=inspection.file_size,
                quality_status="pass" if inspection.is_valid else "fail",
                relevance_status="relevant" if classification.decision == "eligible" else "uncertain",
                copyright_status=effective_copyright,
                copyright_risk="high" if classification.decision == "rejected" else "medium",
                asset_identity_sha256=identity_sha256,
                decision=classification.decision,
                reasons=classification.rejection_reasons or classification.relevance_reasons,
            )
            pending_uploads.append((asset, download_result.local_path, inspection, candidate.extraction_method))
            builder.add_asset(asset)
            total_assets_added += 1
            material_image_count += 1

    # Freeze discovery before any source upload can occur. Discovery mode writes
    # the manifest and stops at classification; continue mode compares a freshly
    # resolved discovery against the user-approved frozen manifest.
    current_discovery = freeze_discovery_manifest(discovery_records)
    discovery_path = output_dir / "asset_discovery_manifest.json"
    write_discovery_manifest(discovery_path, current_discovery)
    current_discovery_sha = current_discovery["discovery_manifest_sha256"]

    approved_discovery = None
    approved_records: dict[str, dict] = {}
    discovery_file_valid = False
    if args.phase == "continue":
        if not args.discovery_manifest:
            builder.errors.append("continue phase requires --discovery-manifest")
        else:
            try:
                approved_discovery = json.loads(
                    Path(args.discovery_manifest).read_text(encoding="utf-8"))
                discovery_file_valid, approved_sha = verify_discovery_manifest(approved_discovery)
                if not discovery_file_valid:
                    builder.errors.append("approval_identity_mismatch: discovery manifest sha256 invalid")
                approved_records = {
                    item["asset_id"]: item for item in approved_discovery.get("assets", [])
                }
            except (OSError, ValueError, KeyError, TypeError) as exc:
                builder.errors.append(f"approval_identity_mismatch: cannot read discovery manifest: {exc}")

        current_by_id = {item["asset_id"]: item for item in discovery_records}
        for asset, local_path, inspection, extraction_method in pending_uploads:
            approval = asset_approvals.get(asset.asset_id)
            frozen = approved_records.get(asset.asset_id)
            mismatches: list[str] = []

            # hotfix6/hotfix4 approval precedence:
            #   restricted/no-repost > material/source_url > stable single_asset > unknown.
            # A stable approval may upgrade only an otherwise-unknown source asset;
            # it can never override an explicit restricted/no-repost decision.
            if approval is not None and asset.copyright_status == "restricted":
                asset.reasons.append(
                    "restricted/no-repost overrides single_asset approval")
            elif approval is not None and asset.copyright_status != "known_allowed":
                if not discovery_file_valid or frozen is None:
                    mismatches.append("discovery_manifest")
                else:
                    mismatches.extend(approval_mismatches(
                        approval, frozen,
                        approved_discovery["discovery_manifest_sha256"],
                    ))
                    fresh = current_by_id.get(asset.asset_id)
                    if fresh is None:
                        mismatches.append("fresh_discovery")
                    else:
                        for field_name in (
                            "material_id", "source_page_url", "resolved_original_url",
                            "asset_sha256", "asset_identity_sha256",
                        ):
                            if fresh.get(field_name) != frozen.get(field_name):
                                mismatches.append(f"fresh_{field_name}")
                if mismatches:
                    asset.approval_identity_mismatch = sorted(set(mismatches))
                    asset.reasons.append(
                        "approval_identity_mismatch: " + ", ".join(asset.approval_identity_mismatch))
                else:
                    consumed_asset_approvals.add(asset.asset_id)
                    asset.discovery_manifest_sha256 = approval["discovery_manifest_sha256"]
                    asset.approval_id = approval["approval_id"]
                    asset.approved_scope = approval["approved_scope"]
                    asset.approved_by = approval["approved_by"]
                    asset.approved_at = approval["approved_at"]
                    asset.approval_evidence_sha256 = approval["approval_evidence_sha256"]
                    asset.asset_approval_consumed = True
                    asset.copyright_status = "known_allowed"
                    classification = classify_image(
                        url=asset.resolved_original_url, inspection=inspection,
                        min_width=config.get("min_width", 640),
                        min_height=config.get("min_height", 360),
                        context="", copyright_status="known_allowed",
                        extraction_method=extraction_method,
                    )
                    asset.decision = classification.decision
                    asset.relevance_status = (
                        "relevant" if classification.decision == "eligible" else "uncertain")
                    asset.copyright_risk = (
                        "high" if classification.decision == "rejected" else "medium")
                    asset.reasons = (
                        classification.rejection_reasons or classification.relevance_reasons)

            # Material/source_url approval is represented by the material's
            # copyright_review.status=known_allowed and needs no per-asset approval.
            # All approval modes still require a valid frozen discovery manifest
            # in continue, plus the normal quality/relevance/dedup gates.
            if (discovery_file_valid
                    and asset.copyright_status == "known_allowed"
                    and asset.decision == "eligible"
                    and asset.quality_status == "pass"
                    and asset.relevance_status == "relevant"
                    and asset.duplicate_of is None):
                upload_result = timed_upload(
                    uploader, upload_events, local_path, asset.asset_id,
                    copyright_status=asset.copyright_status,
                )
                asset.upload = {
                    "mode": upload_mode, "status": upload_result.status,
                    "remote_url": upload_result.remote_url,
                    "response_sha256": upload_result.response_sha256,
                }

    for aid in sorted(set(asset_approvals) - consumed_asset_approvals):
        builder.warnings.append(f"asset_approval for {aid} NOT consumed")

    # Generate charts (dev5: fail-closed chart_group/metric gating)
    print(f"\n[media-enrichment] Generating charts...")
    claims_with_numbers = [c for c in claims if c.get("numbers")]
    if claims_with_numbers:
        plan = build_chart_specs(claims_with_numbers, materials_by_id)
        for w in plan.warnings:
            builder.warnings.append(w)
            print(f"  WARN: {w}")
        for i, spec in enumerate(plan.specs):
            chart_path = output_dir / "charts" / f"chart-{i+1:03d}.png"
            chart_result = generate_chart(spec, chart_path)
            if chart_result.success:
                asset_counter += 1
                asset_id = f"A-{asset_counter:03d}"
                chart_upload = {
                    "mode": upload_mode, "status": "not_uploaded",
                    "remote_url": None, "response_sha256": None,
                }
                # Discovery is strictly side-effect-free: do not even invoke a
                # dry-run uploader or emit an upload-attempt event. Generated
                # charts may be uploaded only in the explicit continue phase.
                if args.phase == "continue" and discovery_file_valid:
                    chart_upload_result = timed_upload(
                        uploader, upload_events, chart_result.chart_path, asset_id,
                        copyright_status="known_allowed",
                    )
                    chart_upload = {
                        "mode": upload_mode, "status": chart_upload_result.status,
                        "remote_url": chart_upload_result.remote_url,
                        "response_sha256": chart_upload_result.response_sha256,
                    }
                asset = AssetRecord(
                    asset_id=asset_id, asset_origin="generated",
                    material_ids=list(set(dp.material_id for dp in spec.data_points)),
                    claim_ids=[dp.claim_id for dp in spec.data_points],
                    extraction_method="generated", decode_method="none",
                    local_path=chart_result.chart_path, sha256=chart_result.sha256,
                    perceptual_hash=chart_result.inspection.perceptual_hash if chart_result.inspection else None,
                    mime_type="image/png",
                    width=chart_result.inspection.width if chart_result.inspection else None,
                    height=chart_result.inspection.height if chart_result.inspection else None,
                    file_size=chart_result.inspection.file_size if chart_result.inspection else None,
                    quality_status="pass", relevance_status="relevant",
                    copyright_status="known_allowed", copyright_risk="low",
                    decision="eligible", reasons=["Generated from canonical claim data"],
                    caption=spec.caption or spec.title, alt_text=spec.caption or spec.title,
                    upload=chart_upload,
                )
                builder.add_asset(asset)
                print(f"  Chart {i+1}: {chart_path} ({spec.chart_type})")
            else:
                builder.warnings.append(f"Chart generation failed: {chart_result.error}")
    else:
        builder.warnings.append("No claims with numbers — no charts generated")

    # Placement
    article_full_path = Path(args.request).parent / article_path if article_path else None
    if article_full_path and article_full_path.exists():
        claim_texts = [c.get("claim_text", "") for c in claims if c.get("claim_text")]
        placements = find_anchors(article_full_path, claim_texts)
        for asset in builder.assets:
            if asset.decision in ("eligible", "review_required") and asset.claim_ids:
                for cid in asset.claim_ids:
                    claim = next((c for c in claims if c["claim_id"] == cid), None)
                    if claim:
                        placement = placements.get(claim.get("claim_text", ""))
                        if placement and placement.anchor:
                            asset.placement = {"anchor": placement.anchor, "position": placement.position, "confidence": placement.confidence}
                            # dev5: generated charts keep their group-level caption/alt —
                            # a single claim text must never represent a multi-point chart
                            if asset.asset_origin != "generated":
                                asset.caption = placement.caption
                                asset.alt_text = placement.alt_text
    else:
        builder.warnings.append("Article file not found for placement planning")

    # Secrets scan
    manifest = builder.build()
    secrets = [f for f in scan_for_secrets(manifest) if f.split(":")[-1].strip() not in {"secrets_detected", "secret_scan_passed", "no_secrets_found"}]
    if secrets:
        builder.errors.extend([f"SECRET_DETECTED: {s}" for s in secrets])
        manifest = builder.build()
    manifest["gate"]["secrets_detected"] = len(secrets) > 0

    manifest_path = output_dir / "media_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2, sort_keys=True)

    # dev7-hotfix1: emit article_image_bindings.json — the FINAL binding of body
    # images to their uploaded WeChat-host URLs (pure projection of the manifest;
    # never mutates the article, never uploads). Downstream gzh-design consumes it
    # and validate_media_manifest.py --bindings checks it per asset.
    from media_enrichment.article_bindings import write_bindings
    bindings_path = output_dir / "article_image_bindings.json"
    write_bindings(manifest, bindings_path)

    # dev2-hotfix2: persist the serial upload event log for downstream audit
    events_path = output_dir / "upload_events.json"
    with open(events_path, "w", encoding="utf-8") as f:
        json.dump({"schema_version": "1.0", "serial": True,
                   "events": upload_events}, f, ensure_ascii=False, indent=2)

    print(f"\n[media-enrichment] Manifest: {manifest_path}")
    print(f"[media-enrichment] Bindings: {bindings_path}")
    print(f"  Assets: {len(builder.assets)}")
    print(f"  Eligible: {sum(1 for a in builder.assets if a.decision == 'eligible')}")
    print(f"  Review: {sum(1 for a in builder.assets if a.decision == 'review_required')}")
    print(f"  Rejected: {sum(1 for a in builder.assets if a.decision == 'rejected')}")
    print(f"  Errors: {len(builder.errors)}")
    print(f"  Warnings: {len(builder.warnings)}")

    sys.exit(1 if builder.errors else 0)


if __name__ == "__main__":
    main()
