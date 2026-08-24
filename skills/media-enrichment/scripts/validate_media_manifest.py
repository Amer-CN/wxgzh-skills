#!/usr/bin/env python3
"""Media Manifest Validator.

Checks ALL P0 conditions with real verification — no unconditional PASS.
Exit code 0 = PASS, non-zero = FAIL.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

import jsonschema
from urllib.parse import urlparse
from media_enrichment.url_security import is_private_network_url
from media_enrichment.uploader import scan_for_secrets
from media_enrichment.image_inspector import inspect_image, compute_sha256
from media_enrichment.input_contract import compute_file_sha256
from media_enrichment.downloader_mime import detect_mime

WECHAT_IMAGE_HOSTS = ("mmbiz.qpic.cn", "mmbiz.qlogo.cn")


def _is_exact_wechat_url(url: str) -> bool:
    """dev2-hotfix2: EXACT host gate — https + hostname EQUALS a WeChat image
    host. Query/subdomain/path/userinfo tricks and http all FAIL."""
    if not url:
        return False
    try:
        p = urlparse(url)
    except ValueError:
        return False
    return p.scheme == "https" and p.hostname in WECHAT_IMAGE_HOSTS

SECRET_PATTERNS_RE = [
    re.compile(r"(?i)access_token"), re.compile(r"(?i)api[_-]?key"),
    re.compile(r"(?i)secret"), re.compile(r"(?i)password"),
    re.compile(r"(?i)cookie"), re.compile(r"(?i)bearer"),
    re.compile(r"(?i)authorization"),
]

PRIVATE_IP_RE = re.compile(
    r"(127\.\d+\.\d+\.\d+|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|"
    r"172\.(1[6-9]|2\d|3[01])\.\d+\.\d+|0\.0\.0\.0|169\.254\.\d+\.\d+|"
    r"localhost|::1|fd[0-9a-f]{2}:|fe80:|metadata\.google\.internal|100\.100\.100\.200)",
    re.IGNORECASE,
)

SAFE_FIELD_NAMES = {"secrets_detected", "secret_scan_passed", "no_secrets_found"}


def load_schema(name: str) -> dict:
    with open(SKILL_ROOT / "schemas" / f"{name}.schema.json", encoding="utf-8") as f:
        return json.load(f)


def validate_manifest(manifest_path: str, request_path: str | None = None) -> dict:
    checks: list[dict] = []
    all_pass = True

    def check(name: str, passed: bool, detail: str = ""):
        nonlocal all_pass
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "detail": detail})
        if not passed:
            all_pass = False

    try:
        with open(manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as exc:
        check("MANIFEST_LOADABLE", False, f"Cannot load: {exc}")
        return {"checks": checks, "pass": False, "exit_code": 1}
    check("MANIFEST_LOADABLE", True)

    # 1. INPUT_SCHEMA_VALID
    try:
        schema = load_schema("media_manifest")
        jsonschema.validate(instance=manifest, schema=schema)
        check("INPUT_SCHEMA_VALID", True)
    except jsonschema.ValidationError as exc:
        check("INPUT_SCHEMA_VALID", False, str(exc.message)[:200])

    # 2. MANIFEST_ERRORS_EMPTY
    errors = manifest.get("errors", [])
    check("MANIFEST_ERRORS_EMPTY", len(errors) == 0,
          f"errors: {errors[:3]}" if errors else "")

    # 3-6. GATE FLAGS
    gate = manifest.get("gate", {})
    check("GATE_INPUT_CONTRACT_PASS", gate.get("input_contract_pass") is True,
          f"input_contract_pass={gate.get('input_contract_pass')}")
    check("GATE_SECURITY_CHECKS_PASS", gate.get("security_checks_pass") is True,
          f"security_checks_pass={gate.get('security_checks_pass')}")
    check("GATE_PROVENANCE_COMPLETE", gate.get("provenance_complete") is True,
          f"provenance_complete={gate.get('provenance_complete')}")
    check("GATE_SECRETS_DETECTED_FALSE", gate.get("secrets_detected") is False,
          f"secrets_detected={gate.get('secrets_detected')}")
    check("GATE_PUBLISH_ALLOWED_FALSE", gate.get("publish_allowed") is False,
          f"publish_allowed={gate.get('publish_allowed')}")

    # 7. REQUEST SNAPSHOT VALIDATION
    request_available = request_path is not None and Path(request_path).exists()
    request_data = None
    if request_available:
        try:
            with open(request_path, "rb") as f:
                request_raw = f.read()
            request_data = json.loads(request_raw)
            claims = request_data.get("claims", [])
            materials = request_data.get("materials", [])

            # REQUEST_SHA256_MATCH
            actual_req_sha = hashlib.sha256(request_raw).hexdigest()
            manifest_req_sha = manifest.get("input", {}).get("request_sha256", "")
            check("REQUEST_SHA256_MATCH", actual_req_sha == manifest_req_sha,
                  f"expected={manifest_req_sha[:16]}, actual={actual_req_sha[:16]}")

            # CLAIMS_TOTAL_MATCH
            manifest_claims_total = manifest.get("input", {}).get("claims_total", -1)
            check("CLAIMS_TOTAL_MATCH", len(claims) == manifest_claims_total,
                  f"expected={manifest_claims_total}, actual={len(claims)}")

            # MATERIALS_TOTAL_MATCH
            manifest_materials_total = manifest.get("input", {}).get("materials_total", -1)
            check("MATERIALS_TOTAL_MATCH", len(materials) == manifest_materials_total,
                  f"expected={manifest_materials_total}, actual={len(materials)}")

            # claim_id unique
            claim_ids = [c["claim_id"] for c in claims]
            dup_claims = [cid for cid in claim_ids if claim_ids.count(cid) > 1]
            check("REQUEST_CLAIM_IDS_UNIQUE", len(dup_claims) == 0,
                  f"duplicates: {set(dup_claims)}" if dup_claims else "")

            # material_id unique
            mat_ids = [m["material_id"] for m in materials]
            dup_mats = [mid for mid in mat_ids if mat_ids.count(mid) > 1]
            check("REQUEST_MATERIAL_IDS_UNIQUE", len(dup_mats) == 0,
                  f"duplicates: {set(dup_mats)}" if dup_mats else "")

            # Claim references valid material
            mat_set = set(mat_ids)
            bad_refs = [c["claim_id"] for c in claims if c["material_id"] not in mat_set]
            check("REQUEST_CLAIM_MATERIAL_REF_VALID", len(bad_refs) == 0,
                  f"bad refs: {bad_refs}" if bad_refs else "")

            # Claim source_url matches material
            mat_by_id = {m["material_id"]: m for m in materials}
            url_mismatches = []
            for c in claims:
                mat = mat_by_id.get(c["material_id"])
                if mat and c["source_url"] != mat["source_url"]:
                    url_mismatches.append(c["claim_id"])
            check("REQUEST_SOURCE_URL_CONSISTENT", len(url_mismatches) == 0,
                  f"mismatches: {url_mismatches}" if url_mismatches else "")

        except Exception as exc:
            check("REQUEST_SHA256_MATCH", False, f"request load error: {exc}")
            check("CLAIMS_TOTAL_MATCH", False)
            check("MATERIALS_TOTAL_MATCH", False)
            check("REQUEST_CLAIM_IDS_UNIQUE", False)
            check("REQUEST_MATERIAL_IDS_UNIQUE", False)
            check("REQUEST_CLAIM_MATERIAL_REF_VALID", False)
            check("REQUEST_SOURCE_URL_CONSISTENT", False)
    else:
        # No request file — all request checks MUST FAIL
        check("REQUEST_SHA256_MATCH", False, "no request file provided")
        check("CLAIMS_TOTAL_MATCH", False, "no request file provided")
        check("MATERIALS_TOTAL_MATCH", False, "no request file provided")
        check("REQUEST_CLAIM_IDS_UNIQUE", False, "no request file provided")
        check("REQUEST_MATERIAL_IDS_UNIQUE", False, "no request file provided")
        check("REQUEST_CLAIM_MATERIAL_REF_VALID", False, "no request file provided")
        check("REQUEST_SOURCE_URL_CONSISTENT", False, "no request file provided")

    # 8. ARTICLE_HASH_MATCH — real recomputation
    article_sha = manifest.get("input", {}).get("article_sha256", "")
    # Try to find article from request
    article_path = None
    if request_path and Path(request_path).exists():
        try:
            with open(request_path, encoding="utf-8") as f:
                req = json.load(f)
                article_path = Path(request_path).parent / req.get("article", {}).get("path", "")
        except Exception:
            pass

    if article_path and article_path.exists():
        actual_sha = compute_file_sha256(article_path)
        check("ARTICLE_HASH_MATCH", actual_sha == article_sha,
              f"expected={article_sha[:16]}, actual={actual_sha[:16]}")
    elif article_path:
        # Article path was specified but file doesn't exist
        check("ARTICLE_HASH_MATCH", False,
              f"article file not found: {article_path}")
    else:
        check("ARTICLE_HASH_MATCH", False,
              "article file not available for hash verification")

    # 9. ASSET_IDS_UNIQUE
    asset_ids = [a.get("asset_id", "") for a in manifest.get("assets", [])]
    dup_assets = [aid for aid in asset_ids if asset_ids.count(aid) > 1]
    check("ASSET_IDS_UNIQUE", len(dup_assets) == 0,
          f"duplicates: {set(dup_assets)}" if dup_assets else "")

    # 10-12. ASSET local_path, HASH, DECODEABLE, DIMENSIONS for eligible/review_required
    for asset in manifest.get("assets", []):
        aid = asset.get("asset_id", "?")
        local_path = asset.get("local_path")
        decision = asset.get("decision", "rejected")

        if decision in ("eligible", "review_required"):
            # local_path must be a non-empty string
            if not local_path:
                check(f"ASSET_{aid}_LOCAL_PATH_NONEMPTY", False,
                      f"local_path is {'null' if local_path is None else 'empty'} for decision={decision}")
                continue
            check(f"ASSET_{aid}_LOCAL_PATH_NONEMPTY", True)

            path = Path(local_path)
            if not path.exists():
                check(f"ASSET_{aid}_FILE_EXISTS", False, f"file not found: {local_path}")
                continue
            check(f"ASSET_{aid}_FILE_EXISTS", True)

            # SHA256 match
            actual_sha = compute_file_sha256(path)
            expected_sha = asset.get("sha256", "")
            check(f"ASSET_{aid}_SHA256_MATCH", actual_sha == expected_sha,
                  f"expected={expected_sha[:16]}, actual={actual_sha[:16]}")

            # Decodeable
            inspection = inspect_image(path)
            check(f"ASSET_{aid}_DECODEABLE", inspection.is_valid or inspection.is_svg,
                  inspection.error if inspection.error else "")

            # Dimensions match (always check, not conditional)
            if asset.get("width") is not None and asset.get("height") is not None and not inspection.is_svg:
                check(f"ASSET_{aid}_DIMENSIONS_MATCH",
                      inspection.width == asset["width"] and inspection.height == asset["height"],
                      f"expected={asset['width']}x{asset['height']}, actual={inspection.width}x{inspection.height}")

            # MIME match (always check)
            if asset.get("mime_type") and not inspection.is_svg:
                check(f"ASSET_{aid}_MIME_MATCH",
                      inspection.mime_type == asset["mime_type"],
                      f"expected={asset['mime_type']}, actual={inspection.mime_type}")

            # File size match (always check)
            if asset.get("file_size") is not None:
                check(f"ASSET_{aid}_SIZE_MATCH",
                      inspection.file_size == asset["file_size"],
                      f"expected={asset['file_size']}, actual={inspection.file_size}")

    # 13. DUPLICATE_REFERENCES_VALID
    dup_errors = []
    for asset in manifest.get("assets", []):
        if asset.get("duplicate_of"):
            ref = asset["duplicate_of"]
            if not any(a.get("asset_id") == ref for a in manifest.get("assets", [])):
                dup_errors.append(f"{asset['asset_id']}: non-existent duplicate_of={ref}")
    check("DUPLICATE_REFERENCES_VALID", len(dup_errors) == 0,
          "; ".join(dup_errors) if dup_errors else "")

    # 14. PROVENANCE_COMPLETE
    prov_errors = []
    for asset in manifest.get("assets", []):
        if asset.get("decision") != "rejected" and asset.get("asset_origin") == "source":
            if not asset.get("sha256"):
                prov_errors.append(f"{asset['asset_id']}: missing sha256")
            if not asset.get("source_page_url"):
                prov_errors.append(f"{asset['asset_id']}: missing source_page_url")
    check("PROVENANCE_COMPLETE", len(prov_errors) == 0,
          "; ".join(prov_errors) if prov_errors else "")

    # 15. GENERATED_CHART_DATA_TRACEABLE — per data point
    trace_errors = []
    for asset in manifest.get("assets", []):
        if asset.get("asset_origin") == "generated":
            if not asset.get("claim_ids"):
                trace_errors.append(f"{asset['asset_id']}: missing claim_ids")
            if not asset.get("material_ids"):
                trace_errors.append(f"{asset['asset_id']}: missing material_ids")
            # Verify each claim_id exists in request
            if request_path and Path(request_path).exists():
                try:
                    with open(request_path, encoding="utf-8") as f:
                        req = json.load(f)
                    valid_claim_ids = set(c["claim_id"] for c in req.get("claims", []))
                    for cid in asset.get("claim_ids", []):
                        if cid not in valid_claim_ids:
                            trace_errors.append(f"{asset['asset_id']}: references non-existent claim_id={cid}")
                except Exception:
                    pass
    check("GENERATED_CHART_DATA_TRACEABLE", len(trace_errors) == 0,
          "; ".join(trace_errors) if trace_errors else "")

    # 16. UPLOAD_RESPONSES_SANITIZED
    upload_errors = []
    for asset in manifest.get("assets", []):
        upload = asset.get("upload", {})
        if upload.get("status") == "success":
            url = upload.get("remote_url", "")
            if url:
                for pat in SECRET_PATTERNS_RE:
                    if pat.search(url):
                        upload_errors.append(f"{asset['asset_id']}: remote_url contains sensitive pattern")
    check("UPLOAD_RESPONSES_SANITIZED", len(upload_errors) == 0,
          "; ".join(upload_errors) if upload_errors else "")

    # 17. NO_SECRETS_FOUND
    secret_findings = [f for f in scan_for_secrets(manifest)
                       if f.split(":")[-1].strip() not in SAFE_FIELD_NAMES]
    check("NO_SECRETS_FOUND", len(secret_findings) == 0,
          "; ".join(secret_findings) if secret_findings else "")

    # 18. NO_PRIVATE_NETWORK_URLS
    private_urls = []
    for asset in manifest.get("assets", []):
        for field_name in ("discovered_url", "resolved_original_url", "source_page_url", "aihot_permalink"):
            url = asset.get(field_name, "")
            if url and PRIVATE_IP_RE.search(url):
                private_urls.append(f"{asset['asset_id']}.{field_name}: {url}")
    check("NO_PRIVATE_NETWORK_URLS", len(private_urls) == 0,
          "; ".join(private_urls) if private_urls else "")

    # 19. NO_REJECTED_ASSET_MARKED_ELIGIBLE
    contradictory = []
    for asset in manifest.get("assets", []):
        if asset.get("decision") == "rejected" and asset.get("quality_status") == "pass" and \
           asset.get("relevance_status") == "relevant" and not asset.get("duplicate_of"):
            contradictory.append(asset.get("asset_id", "?"))
    check("NO_REJECTED_ASSET_MARKED_ELIGIBLE", len(contradictory) == 0,
          f"contradictory: {contradictory}" if contradictory else "")

    # 20. NO_UNKNOWN_LICENSE_AUTO_APPROVED
    unknown_approved = [a.get("asset_id", "?") for a in manifest.get("assets", [])
                        if a.get("decision") == "eligible" and a.get("copyright_status") == "unknown"]
    check("NO_UNKNOWN_LICENSE_AUTO_APPROVED", len(unknown_approved) == 0,
          f"auto-approved: {unknown_approved}" if unknown_approved else "")

    # 21. NO_ARTICLE_FACT_MUTATION — compare input hash with article file
    if article_path and article_path.exists():
        current_sha = compute_file_sha256(article_path)
        check("NO_ARTICLE_FACT_MUTATION", current_sha == article_sha,
              f"article hash changed: expected={article_sha[:16]}, current={current_sha[:16]}")
    else:
        check("NO_ARTICLE_FACT_MUTATION", False,
              "article file not available — cannot verify no mutation")

    # 22. PUBLISH_ALLOWED_FALSE (redundant with gate check, but explicit)
    check("PUBLISH_ALLOWED_FALSE", gate.get("publish_allowed") is False,
          f"publish_allowed={gate.get('publish_allowed')}")

    return {"checks": checks, "pass": all_pass, "exit_code": 0 if all_pass else 1}


def validate_bindings(manifest_path: str, bindings_path: str) -> dict:
    """dev7: per-asset check of the FINAL bound body assets.

    For every asset in article_image_bindings.json body_images:
    - exists in the manifest;
    - decision == eligible;
    - upload.status == success;
    - upload.remote_url non-empty and on the WeChat image host;
    - sha256 in bindings matches the manifest asset.
    Generated charts are checked by the same rules — no chart-only shortcut.
    """
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    with open(bindings_path, encoding="utf-8") as f:
        bindings = json.load(f)

    assets = {a.get("asset_id"): a for a in manifest.get("assets", [])}
    checks = []
    all_pass = True

    def check(name, ok, detail=""):
        nonlocal all_pass
        checks.append({"check": name, "status": "PASS" if ok else "FAIL",
                       "detail": detail if not ok else ""})
        if not ok:
            all_pass = False

    body = bindings.get("body_images", [])
    summary = manifest.get("summary") or {}
    candidate_count = (int(summary.get("eligible_assets") or 0)
                       + int(summary.get("review_required_assets") or 0))
    zero_image_shortfall = (not body and candidate_count == 0
                            and not manifest.get("errors"))
    # 77G/OBS-316: zero approvable assets is an audited shortfall, not a hidden
    # binding omission. Any candidate without a binding remains a failure.
    check("BINDINGS_NON_EMPTY", bool(body) or zero_image_shortfall,
          "no body_images in bindings")
    for b in body:
        aid = b.get("asset_id")
        a = assets.get(aid)
        check(f"BOUND_{aid}_IN_MANIFEST", a is not None,
              f"{aid} missing from manifest")
        if not a:
            continue
        up = a.get("upload") or {}
        remote = up.get("remote_url") or ""
        check(f"BOUND_{aid}_ELIGIBLE", a.get("decision") == "eligible",
              f"decision={a.get('decision')}")
        check(f"BOUND_{aid}_UPLOAD_SUCCESS", up.get("status") == "success",
              f"upload.status={up.get('status')}")
        check(f"BOUND_{aid}_REMOTE_URL_WECHAT",
              _is_exact_wechat_url(remote),
              f"remote_url={remote[:80]!r} (exact https+host required)")
        if b.get("sha256"):
            check(f"BOUND_{aid}_SHA256_MATCH", b["sha256"] == a.get("sha256"),
                  f"bindings sha {b['sha256'][:12]} != manifest {str(a.get('sha256'))[:12]}")

    return {"checks": checks, "pass": all_pass,
            "exit_code": 0 if all_pass else 1}


def main():
    parser = argparse.ArgumentParser(description="Validate media manifest")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--request", default=None, help="Request JSON for cross-validation")
    parser.add_argument("--bindings", default=None,
                        help="article_image_bindings.json — per-asset check of "
                             "final bound body assets (dev7)")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    report = validate_manifest(args.manifest, args.request)

    # dev7: merge per-binding checks so the formal validator inspects every
    # final bound asset (not just generated charts).
    if args.bindings:
        b_report = validate_bindings(args.manifest, args.bindings)
        report["checks"].extend(b_report["checks"])
        report["pass"] = report["pass"] and b_report["pass"]
        report["exit_code"] = 0 if report["pass"] else 1

    print("=" * 60)
    print("MEDIA MANIFEST VALIDATOR")
    print("=" * 60)
    for c in report["checks"]:
        status = "PASS" if c["status"] == "PASS" else "FAIL"
        print(f"  {status} {c['check']}: {c['status']}")
        if c.get("detail"):
            print(f"      {c['detail']}")
    print("=" * 60)
    print(f"RESULT: {'PASS' if report['pass'] else 'FAIL'}")
    print(f"EXIT CODE: {report['exit_code']}")

    if args.output_dir:
        out = Path(args.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        with open(out / "validator_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        with open(out / "validator_stdout.txt", "w", encoding="utf-8") as f:
            for c in report["checks"]:
                f.write(f"{c['check']}: {c['status']}\n")
                if c.get("detail"):
                    f.write(f"  {c['detail']}\n")
            f.write(f"\nRESULT: {'PASS' if report['pass'] else 'FAIL'}\n")
            f.write(f"EXIT CODE: {report['exit_code']}\n")
        with open(out / "validator_stderr.txt", "w", encoding="utf-8") as f:
            if not report["pass"]:
                for c in report["checks"]:
                    if c["status"] == "FAIL":
                        f.write(f"FAIL: {c['check']}: {c.get('detail', '')}\n")
        with open(out / "validator_exit_code.txt", "w", encoding="utf-8") as f:
            f.write(str(report["exit_code"]))

    sys.exit(report["exit_code"])


if __name__ == "__main__":
    main()
