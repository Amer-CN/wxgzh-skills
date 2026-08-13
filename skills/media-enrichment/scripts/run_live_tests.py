#!/usr/bin/env python3
"""Live AI HOT permalink test script.

Fetches at least 3 real AI HOT pages, extracts images, decodes proxies,
saves HTML snapshots, and records provenance. Does NOT use hotfix1's
canonical material_id/claim_id mappings — uses temporary FIXTURE-M-* IDs.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

from media_enrichment.page_fetcher import fetch_page
from media_enrichment.image_extractor import extract_images
from media_enrichment.proxy_decoder import decode_proxy_url
from media_enrichment.url_security import is_safe_url

# Real AI HOT permalinks from deduplicated_items (NOT from hotfix1)
TEST_PERMALINKS = [
    {
        "fixture_id": "FIXTURE-M-001",
        "permalink": "https://aihot.virxact.com/items/cmryrih7804c9rolge6wdk3v8",
    },
    {
        "fixture_id": "FIXTURE-M-002",
        "permalink": "https://aihot.virxact.com/items/cmrykywyx026jrolgq06set4j",
    },
    {
        "fixture_id": "FIXTURE-M-003",
        "permalink": "https://aihot.virxact.com/items/cmrxylm0f002xropg7xpd1pth",
    },
]

OUTPUT_DIR = SKILL_ROOT / "evidence"
SNAPSHOT_DIR = OUTPUT_DIR / "live_html_snapshots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)


def run_live_tests():
    """Run live AI HOT page tests."""
    results = []

    for test in TEST_PERMALINKS:
        fixture_id = test["fixture_id"]
        permalink = test["permalink"]

        print(f"\n[{fixture_id}] Fetching: {permalink}")

        # Fetch page
        fetch_result = fetch_page(permalink, mode="live", timeout=15)

        test_result = {
            "fixture_id": fixture_id,
            "permalink": permalink,
            "fetched_at": fetch_result.fetched_at,
            "success": fetch_result.success,
            "status_code": fetch_result.status_code,
            "final_url": fetch_result.final_url,
            "content_sha256": fetch_result.content_sha256,
            "duration_ms": fetch_result.duration_ms,
            "redirect_count": len(fetch_result.redirect_chain),
            "error": fetch_result.error,
        }

        if fetch_result.success:
            # Save HTML snapshot
            slug = permalink.rstrip("/").split("/")[-1]
            snapshot_path = SNAPSHOT_DIR / f"{fixture_id}_{slug}.html"
            snapshot_path.write_text(fetch_result.content, encoding="utf-8")
            test_result["snapshot_path"] = str(snapshot_path.relative_to(SKILL_ROOT))

            # Extract images
            extraction = extract_images(fetch_result.content, page_url=permalink)
            test_result["candidates_count"] = len(extraction.candidates)
            test_result["page_title"] = extraction.page_title

            # Analyze candidates
            candidates_info = []
            for c in extraction.candidates:
                # Decode proxy
                decode_result = decode_proxy_url(c.url)
                # Check safety
                sec_check = is_safe_url(decode_result.decoded_url)

                candidates_info.append({
                    "url": c.url,
                    "extraction_method": c.extraction_method,
                    "decoded_url": decode_result.decoded_url,
                    "decode_method": decode_result.decode_method,
                    "is_proxy": decode_result.is_proxy,
                    "url_safe": sec_check.safe,
                    "url_safety_reasons": sec_check.reasons,
                })

            test_result["candidates"] = candidates_info
            print(f"  Status: {fetch_result.status_code}")
            print(f"  Candidates: {len(extraction.candidates)}")
            print(f"  Snapshot: {snapshot_path}")
        else:
            print(f"  FAILED: {fetch_result.error}")
            test_result["candidates_count"] = 0
            test_result["candidates"] = []

        results.append(test_result)

    # Summary
    summary = {
        "test_run_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_pages_tested": len(results),
        "pages_fetched_successfully": sum(1 for r in results if r["success"]),
        "total_candidates_discovered": sum(r.get("candidates_count", 0) for r in results),
        "proxies_decoded": sum(
            1 for r in results for c in r.get("candidates", [])
            if c.get("is_proxy")
        ),
        "safe_candidates": sum(
            1 for r in results for c in r.get("candidates", [])
            if c.get("url_safe")
        ),
        "snapshots_saved": sum(1 for r in results if r.get("snapshot_path")),
        "results": results,
    }

    # Write report
    report_path = OUTPUT_DIR / "live_page_test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"LIVE AI HOT TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Pages tested: {summary['total_pages_tested']}")
    print(f"Pages fetched: {summary['pages_fetched_successfully']}")
    print(f"Candidates discovered: {summary['total_candidates_discovered']}")
    print(f"Proxies decoded: {summary['proxies_decoded']}")
    print(f"Safe candidates: {summary['safe_candidates']}")
    print(f"Snapshots saved: {summary['snapshots_saved']}")
    print(f"Report: {report_path}")

    return summary


if __name__ == "__main__":
    run_live_tests()
