#!/usr/bin/env python3
"""FAKE-LIVE shim mirroring media-enrichment `scripts/run_media_enrichment.py`.

EXACT real CLI: --request / --output-dir / --fixture-dir. Emits a contract-valid
media_manifest.json + article_image_bindings.json with 8 eligible body images on
mmbiz.qpic.cn. SIMULATED — no network, no upload, marked simulated=true. Used only
to exercise the orchestrator's real subprocess machinery in fake_live mode.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

N_IMAGES = 8  # within [BODY_IMAGES_MIN=6, BODY_IMAGES_TARGET=8]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="media-enrichment (fake-live shim)")
    ap.add_argument("--request", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--fixture-dir", default=None)
    a = ap.parse_args(argv)

    req = json.loads(Path(a.request).read_text(encoding="utf-8"))
    run_id = req.get("run_id", "fake-run")
    article_sha = req.get("article", {}).get("sha256", "")
    req_sha = hashlib.sha256(Path(a.request).read_bytes()).hexdigest()

    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    assets, body = [], []
    events = []
    _t = 100.0
    for i in range(1, N_IMAGES + 1):
        aid = f"A-{i:03d}"
        sha = hashlib.sha256(f"{run_id}:{aid}".encode()).hexdigest()
        url = f"https://mmbiz.qpic.cn/mmbiz_png/{sha[:32]}/640?wx_fmt=png"
        placement = {"anchor": f"## 章节{i}", "position": "after", "confidence": 0.9}
        assets.append({
            "asset_id": aid, "asset_origin": "source", "decision": "eligible",
            "sha256": sha, "material_ids": ["M-001"], "claim_ids": [f"C-{i:02d}"],
            "quality_status": "pass", "relevance_status": "relevant",
            "copyright_status": "known_allowed", "source_page_url": "https://example.com/a",
            "placement": placement, "caption": f"图{i}", "alt_text": f"图示 {i}",
            "upload": {"mode": "wechat_audit", "status": "success", "remote_url": url,
                       "response_sha256": hashlib.sha256(url.encode()).hexdigest()},
        })
        body.append({"asset_id": aid, "asset_origin": "source", "sha256": sha,
                     "remote_url": url, "upload_mode": "wechat_audit",
                     "material_ids": ["M-001"], "claim_ids": [f"C-{i:02d}"],
                     "caption": f"图{i}", "alt_text": f"图示 {i}", "placement": placement})
        events.append({"asset_id": aid, "mode": "wechat_audit", "status": "success",
                       "started_at": "2026-07-28T00:00:00Z", "ended_at": "2026-07-28T00:00:01Z",
                       "start_monotonic": round(_t, 6), "end_monotonic": round(_t + 0.5, 6)})
        _t += 1.0

    manifest = {
        "schema_version": "1.0", "simulated": True, "run_id": run_id,
        "input": {"article_sha256": article_sha, "request_sha256": req_sha,
                  "claims_total": len(req.get("claims", [])),
                  "materials_total": len(req.get("materials", []))},
        "summary": {"eligible_assets": N_IMAGES, "uploaded_assets": N_IMAGES},
        "assets": assets, "errors": [], "warnings": [],
        "gate": {"input_contract_pass": True, "provenance_complete": True,
                 "security_checks_pass": True, "secrets_detected": False,
                 "publish_allowed": False},
    }
    (out / "media_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    bindings = {"schema_version": "1.0", "simulated": True, "run_id": run_id,
                "article_sha256": article_sha, "body_image_count": N_IMAGES,
                "body_images": body, "publish_allowed": False}
    (out / "article_image_bindings.json").write_text(
        json.dumps(bindings, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    (out / "upload_events.json").write_text(
        json.dumps({"schema_version": "1.0", "serial": True, "simulated": True,
                    "events": events}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[fake media-enrichment] manifest+bindings+events N={N_IMAGES} simulated=True article_sha={article_sha[:12]}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
