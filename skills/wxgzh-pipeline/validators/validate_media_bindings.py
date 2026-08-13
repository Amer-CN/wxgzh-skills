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
MMBIZ_HOSTS = ("mmbiz.qpic.cn", "mmbiz.qlogo.cn")


def _exact_wechat_url(url: str) -> bool:
    """dev2-hotfix2: https + hostname EQUALS a WeChat image host."""
    if not url:
        return False
    try:
        p = urlparse(url)
    except ValueError:
        return False
    return p.scheme == "https" and p.hostname in MMBIZ_HOSTS


def validate(media_manifest: str | Path, bindings: str | Path,
             body_images_min: int = MIN_BODY_IMAGES,
             body_images_min_source: str = "default") -> tuple[int, dict]:
    if not isinstance(body_images_min, int) or isinstance(body_images_min, bool) or body_images_min < 1:
        raise ValueError("body_images_min must be an integer >= 1")
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
        if not _exact_wechat_url(url):
            problems.append(f"{aid}: remote_url must be https on {MMBIZ_HOSTS} (exact-match)")
        if a.get("sha256") != b.get("sha256"):
            problems.append(f"{aid}: binding sha256 != manifest sha256")
    count = len(body)
    report = {
        "body_image_count": count, "min_required": body_images_min,
        "body_images_min_source": body_images_min_source,
        "target": TARGET_BODY_IMAGES,
        "min_met": count >= body_images_min, "target_met": count >= TARGET_BODY_IMAGES,
        "target_not_met_is_warning": True, "problems": problems,
        "all_bindings_consistent": not problems,
    }
    # 76C(用户裁决 2026-08-11):图片数量不再是发文限制条件。
    # body_images_min 保留为「目标值」,不足时降级——生图兜底 + 少图交付,
    # 留痕 image_shortfall(不静默)。count > 8 上限与 bindings 一致性仍 FAIL。
    shortfall = max(0, body_images_min - count)
    report["image_shortfall"] = shortfall > 0
    report["image_shortfall_count"] = shortfall
    ok = (count <= 8) and not problems
    report["MEDIA_BINDINGS"] = "PASS" if ok else "FAIL"
    if shortfall > 0:
        report["note"] = (f"body_images_min {body_images_min} 为目标值,实际 {count},少图交付留痕(76C 降级)→ 允许少图交付")
    return (0 if ok else 1), report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--media-manifest", required=True)
    ap.add_argument("--bindings", required=True)
    ap.add_argument("--body-images-min", type=int, default=MIN_BODY_IMAGES)
    a = ap.parse_args(argv)
    code, report = validate(a.media_manifest, a.bindings,
                            body_images_min=a.body_images_min,
                            body_images_min_source="--body-images-min" if "--body-images-min" in (argv or sys.argv) else "default")
    print(json.dumps(report, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
