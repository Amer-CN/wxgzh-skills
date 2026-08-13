#!/usr/bin/env python3
"""FAKE-LIVE shim mirroring media-enrichment `scripts/validate_media_manifest.py`.

EXACT real CLI: --manifest / --request / --bindings [/ --output-dir]. Checks that
every bound body image is eligible + upload success + exact mmbiz host + binding
sha256 == manifest sha256. Exit 0 = PASS. SIMULATED validator (fake_live only).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

MMBIZ = ("mmbiz.qpic.cn", "mmbiz.qlogo.cn")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="validate_media_manifest (fake-live shim)")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--request", default=None)
    ap.add_argument("--bindings", default=None)
    ap.add_argument("--output-dir", default=None)
    a = ap.parse_args(argv)

    man = json.loads(Path(a.manifest).read_text(encoding="utf-8"))
    by_id = {x["asset_id"]: x for x in man.get("assets", [])}
    problems = []
    if a.bindings:
        bnd = json.loads(Path(a.bindings).read_text(encoding="utf-8"))
        body = bnd.get("body_images", [])
        if not body:
            problems.append("bindings body_images empty")
        for b in body:
            aid = b.get("asset_id")
            m = by_id.get(aid)
            if not m:
                problems.append(f"{aid}: not in manifest")
                continue
            up = m.get("upload") or {}
            if m.get("decision") != "eligible":
                problems.append(f"{aid}: not eligible")
            if up.get("status") != "success":
                problems.append(f"{aid}: upload not success")
            host = urlparse(up.get("remote_url") or "").hostname or ""
            if host not in MMBIZ:
                problems.append(f"{aid}: host {host} not mmbiz")
            if b.get("sha256") != m.get("sha256"):
                problems.append(f"{aid}: sha mismatch")
    ok = not problems
    print(f"[fake validate_media_manifest] PASS={ok} problems={problems[:5]}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
