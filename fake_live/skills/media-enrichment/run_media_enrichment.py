#!/usr/bin/env python3
"""FAKE-LIVE shim for media-enrichment (dev2 tests only).

Stands in for the installed media-enrichment run entrypoint. Produces a
contract-valid media_manifest.json + article_image_bindings.json for the frozen
article, with 8 eligible body images bound to FAKE mmbiz.qpic.cn URLs. Performs
NO network fetch and NO real WeChat upload — the "upload" results are synthetic.
This exercises the orchestrator's real subprocess machinery with zero side effects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

N_IMAGES = 8  # within [BODY_IMAGES_MIN=6, <=8]


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage-dir", required=True)
    ap.add_argument("--article", required=True)
    ap.add_argument("--article-sha", default="")
    a = ap.parse_args(argv)
    sd = Path(a.stage_dir)
    sd.mkdir(parents=True, exist_ok=True)

    assets = []
    body = []
    for i in range(1, N_IMAGES + 1):
        aid = f"A-{i}"
        sha = _sha(aid)
        # exact host mmbiz.qpic.cn (fake path); no real upload happened
        url = f"http://mmbiz.qpic.cn/mmbiz_jpg/FAKE{i:02d}/640?wx_fmt=jpeg"
        assets.append({"asset_id": aid, "decision": "eligible", "sha256": sha,
                       "source_url": f"https://example.com/source/{i}",
                       "upload": {"status": "success", "remote_url": url,
                                  "note": "FAKE-LIVE synthetic upload — no real WeChat call"}})
        body.append({"asset_id": aid, "sha256": sha, "wechat_remote_url": url,
                     "section": i, "caption": f"figure {i}"})

    manifest = {"artifact": "media_manifest", "mode": "fake_live",
                "frozen_article_sha256": a.article_sha, "assets": assets}
    bindings = {"artifact": "article_image_bindings", "mode": "fake_live",
                "frozen_article_sha256": a.article_sha, "body_images": body}
    (sd / "media_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    (sd / "article_image_bindings.json").write_text(
        json.dumps(bindings, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(json.dumps({"MEDIA_ENRICHMENT_FAKE_LIVE": "ok", "body_images": len(body),
                      "real_upload": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
