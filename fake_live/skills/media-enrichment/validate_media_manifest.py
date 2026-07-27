#!/usr/bin/env python3
"""FAKE-LIVE shim for media-enrichment's official validator (dev2 tests only).

Mirrors the installed validate_media_manifest.py CLI contract so the orchestrator
can run the official validator for REAL via subprocess. Checks that every bound
body image is eligible + upload success + exact mmbiz.qpic.cn host + binding
sha256 == manifest sha256, and count in [6, 8]. Exit 0 = PASS.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--media-manifest", required=True)
    ap.add_argument("--bindings", required=True)
    a = ap.parse_args(argv)
    man = json.loads(Path(a.media_manifest).read_text(encoding="utf-8"))
    bnd = json.loads(Path(a.bindings).read_text(encoding="utf-8"))
    by_id = {x["asset_id"]: x for x in man.get("assets", []) if x.get("decision") == "eligible"}
    body = bnd.get("body_images", [])
    problems = []
    for b in body:
        aid = b.get("asset_id")
        asset = by_id.get(aid)
        if asset is None:
            problems.append(f"{aid}: not eligible / not in manifest")
            continue
        up = asset.get("upload", {})
        if up.get("status") != "success":
            problems.append(f"{aid}: upload.status != success")
        if urlparse(up.get("remote_url") or "").hostname != "mmbiz.qpic.cn":
            problems.append(f"{aid}: remote_url host != mmbiz.qpic.cn")
        if asset.get("sha256") != b.get("sha256"):
            problems.append(f"{aid}: binding sha256 != manifest sha256")
    ok = (6 <= len(body) <= 8) and not problems
    print(json.dumps({"MEDIA_MANIFEST_VALIDATOR": "PASS" if ok else "FAIL",
                      "count": len(body), "problems": problems}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
