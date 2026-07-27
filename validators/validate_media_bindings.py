#!/usr/bin/env python3
"""Media bindings validator: each bound image must be eligible + upload success
+ mmbiz.qpic.cn remote_url + binding sha256 == manifest sha256; and >= 6 images.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

MIN_BODY_IMAGES = 6
TARGET_BODY_IMAGES = 8
MMBIZ_HOST = "mmbiz.qpic.cn"


def validate(media_manifest: str | Path, bindings: str | Path) -> tuple[int, dict]:
    man = json.loads(Path(media_manifest).read_text(encoding="utf-8"))
    bnd = json.loads(Path(bindings).read_text(encoding="utf-8"))
    by_id = {a["asset_id"]: a for a in man.get("assets", []) if a.get("decision") == "eligible"}
    body = bnd.get("body_images", [])
    problems = []
    for b in body:
        aid = b.get("asset_id")
        a = by_id.get(aid)
        up = (a or {}).get("upload", {}) if a else {}
        url = (up.get("remote_url") or b.get("wechat_remote_url") or "")
        if a is None:
            problems.append(f"{aid}: not eligible / not in manifest")
            continue
        if up.get("status") != "success":
            problems.append(f"{aid}: upload.status != success")
        if urlparse(url).hostname != MMBIZ_HOST:
            problems.append(f"{aid}: remote_url host != {MMBIZ_HOST} (exact-match)")
        if a.get("sha256") != b.get("sha256"):
            problems.append(f"{aid}: binding sha256 != manifest sha256")
    count = len(body)
    report = {
        "body_image_count": count, "min_required": MIN_BODY_IMAGES, "target": TARGET_BODY_IMAGES,
        "min_met": count >= MIN_BODY_IMAGES, "target_met": count >= TARGET_BODY_IMAGES,
        "target_not_met_is_warning": True, "problems": problems,
        "all_bindings_consistent": not problems,
    }
    ok = (count >= MIN_BODY_IMAGES) and (count <= 8) and not problems
    report["MEDIA_BINDINGS"] = "PASS" if ok else "FAIL"
    if count < MIN_BODY_IMAGES:
        report["blocking_reason"] = "fewer than 6 bound images — MUST NOT upload"
    return (0 if ok else 1), report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--media-manifest", required=True)
    ap.add_argument("--bindings", required=True)
    a = ap.parse_args(argv)
    code, report = validate(a.media_manifest, a.bindings)
    print(json.dumps(report, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
