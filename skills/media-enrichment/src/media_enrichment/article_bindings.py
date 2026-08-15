"""Article image bindings builder — dev7-hotfix1.

Produces `article_image_bindings.json`: the FINAL binding of the article's body
images to their uploaded WeChat image-host URLs. This is the artifact the
downstream typesetting skill (gzh-design) consumes to place real image URLs in
the article, and the artifact `validate_media_manifest.py --bindings` checks per
asset.

A body image is bound iff it is eligible AND was uploaded successfully to the
WeChat image host (remote_url on mmbiz.qpic.cn / mmbiz.qlogo.cn). Rejected,
review-required, duplicate, or not-uploaded assets are never bound. The binding
sha256 is copied verbatim from the manifest asset so the validator can prove the
bound bytes match the inspected bytes.

Building bindings NEVER mutates the article and NEVER uploads anything — it is a
pure projection of the manifest that the runner already produced.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from . import __version__ as SKILL_VERSION
from .image_deduplicator import hamming_distance, PHASH_THRESHOLD

WECHAT_IMAGE_HOSTS = ("mmbiz.qpic.cn", "mmbiz.qlogo.cn")


def _is_wechat_url(url: str | None) -> bool:
    """EXACT WeChat image-host check (dev2-hotfix2).

    urlparse-based: scheme must be https and hostname must EQUAL one of the
    WeChat image hosts. Substring tricks (query strings, subdomain suffixes,
    paths, userinfo@) and plain http all FAIL.
    """
    if not url:
        return False
    try:
        p = urlparse(url)
    except ValueError:
        return False
    return p.scheme == "https" and p.hostname in WECHAT_IMAGE_HOSTS


def build_bindings(manifest: dict[str, Any], max_images: int | None = None) -> dict[str, Any]:
    """Project a media_manifest dict into an article_image_bindings dict.

    Only eligible + successfully-uploaded body images with a WeChat-host
    remote_url are bound. Deterministic ordering (by asset_id).
    76G-R:max_images(==max_total_images)约束最终入文图数——上传可能多于上限,
    绑定截断到上限(76C 语义)。
    """
    body_images: list[dict[str, Any]] = []
    for asset in sorted(manifest.get("assets", []), key=lambda a: a.get("asset_id", "")):
        if asset.get("decision") != "eligible":
            continue
        upload = asset.get("upload") or {}
        if upload.get("status") != "success":
            continue
        remote_url = upload.get("remote_url") or ""
        if not _is_wechat_url(remote_url):
            continue
        placement = asset.get("placement") or {}
        body_images.append({
            "asset_id": asset.get("asset_id"),
            "asset_origin": asset.get("asset_origin"),
            "sha256": asset.get("sha256"),
            "perceptual_hash": asset.get("perceptual_hash"),
            "remote_url": remote_url,
            "upload_mode": upload.get("mode"),
            "response_sha256": upload.get("response_sha256"),
            "material_ids": asset.get("material_ids") or [],
            "claim_ids": asset.get("claim_ids") or [],
            "caption": asset.get("caption"),
            "alt_text": asset.get("alt_text"),
            "placement": {
                "anchor": placement.get("anchor", ""),
                "position": placement.get("position", "after"),
                "confidence": placement.get("confidence", 0.0),
            },
        })

    # 76X-R/OBS-303:绑定前画面级去重——同一画面(sha256 逐字节相同或感知哈希
    # Hamming ≤ PHASH_THRESHOLD)只保留 readiness/质量更高者,落选资产本轮不绑定
    # 并留痕(记录被谁挤掉、依据什么哈希)。修复 pool-fetch 绕过 discover dedup
    # 导致的同画面双资产(20260815 dxghp1: A-005/A-011 同 sha256 各绑一次)。
    dedup_notes: list[dict] = []
    kept: list[dict] = []
    for b in body_images:
        dup_of = None
        for k in kept:
            if b.get("sha256") and b["sha256"] == k.get("sha256"):
                dup_of = k
                break
            b_ph = (b.get("perceptual_hash") or "").strip()
            k_ph = (k.get("perceptual_hash") or "").strip()
            if b_ph and k_ph and hamming_distance(b_ph, k_ph) <= PHASH_THRESHOLD:
                dup_of = k
                break
        if dup_of is None:
            kept.append(b)
            continue
        # 质量比较:优先有 claim/可读描述者;平局保留先到者(asset_id 排序稳定)
        b_score = (len(b.get("claim_ids") or []), bool((b.get("alt_text") or "").strip()))
        k_score = (len(dup_of.get("claim_ids") or []), bool((dup_of.get("alt_text") or "").strip()))
        if b_score > k_score:
            kept.remove(dup_of)
            kept.append(b)
            loser = dup_of
        else:
            loser = b
        dedup_notes.append({
            "kept_asset_id": dup_of.get("asset_id") if b_score <= k_score else b.get("asset_id"),
            "dropped_asset_id": loser.get("asset_id"),
            "basis": "sha256" if (b.get("sha256") and b["sha256"] == dup_of.get("sha256")) else "phash",
            "kept_sha256": (dup_of if b_score <= k_score else b).get("sha256"),
            "dropped_sha256": loser.get("sha256"),
            "note": "same frame deduped at binding (76X-R/OBS-303)",
        })
    body_images = kept

    # 76G-R:max_images 截断最终入文图数(76C 语义:max_total_images 只约束
    # 最终入文;上传可能多于上限,绑定截断到上限)
    if max_images is not None and max_images > 0:
        body_images = body_images[:max_images]

    return {
        "schema_version": "1.0",
        "skill_version": SKILL_VERSION,
        "run_id": manifest.get("run_id", "unknown"),
        "article_sha256": manifest.get("input", {}).get("article_sha256", ""),
        "body_image_count": len(body_images),
        "body_images": body_images,
        "binding_dedup_notes": dedup_notes,
        # bindings never grant publish rights; downstream still gates on its own.
        "publish_allowed": False,
    }


def write_bindings(manifest: dict[str, Any], output_path: str | Path,
                    max_images: int | None = None) -> str:
    bindings = build_bindings(manifest, max_images=max_images)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(bindings, f, ensure_ascii=False, indent=2, sort_keys=True)
    return str(output_path)
