"""76X-R/OBS-303:绑定层画面级去重测试。

- 同 sha256(逐字节相同)→ 只保留一个 binding,落选留痕(binding_dedup_notes);
- 感知哈希近似(Hamming ≤ 阈值)→ 同画面去重;
- 不同画面 → 各自正常绑定(反例);
- 质量优先:有 claim/可读描述者保留。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from media_enrichment.article_bindings import build_bindings  # noqa: E402


def _mk_asset(asset_id: str, sha: str, phash: str, claim_ids=None,
              alt_text=None) -> dict:
    return {
        "asset_id": asset_id, "asset_origin": "source",
        "decision": "eligible", "sha256": sha, "perceptual_hash": phash,
        "claim_ids": claim_ids or [], "alt_text": alt_text,
        "material_ids": ["M-01"],
        "upload": {"status": "success", "mode": "wechat_image_host",
                   "remote_url": f"https://mmbiz.qpic.cn/{asset_id}"},
        "placement": {"anchor": "锚", "position": "after", "confidence": 0.9},
    }


def test_same_sha256_deduped_with_note():
    """同 sha256 双资产(20260815 dxghp1 A-005/A-011 形态)→ 只绑一个,留痕。"""
    sha = "e0e8ca7564be7598e2198e76224b9d8228087d8485ec3b98a863c7b80a02c0ec"
    phash = "bb23e4723b89c4d8"
    manifest = {"run_id": "r1", "input": {"article_sha256": "a" * 64},
                "assets": [
                    _mk_asset("A-005", sha, phash, claim_ids=["C-14"],
                              alt_text="有 claim 有描述"),
                    _mk_asset("A-011", sha, phash),
                ]}
    b = build_bindings(manifest)
    assert b["body_image_count"] == 1, b["body_images"]
    assert b["body_images"][0]["asset_id"] == "A-005"  # 质量更高者保留
    notes = b.get("binding_dedup_notes") or []
    assert len(notes) == 1
    assert notes[0]["kept_asset_id"] == "A-005"
    assert notes[0]["dropped_asset_id"] == "A-011"
    assert notes[0]["basis"] == "sha256"
    assert "OBS-303" in notes[0]["note"]


def test_phash_near_deduped():
    """感知哈希近似(不同 sha 但同画面)→ 去重。"""
    m = {"run_id": "r2", "input": {"article_sha256": "b" * 64}, "assets": [
        _mk_asset("B-1", "s1", "bb23e4723b89c4d8", claim_ids=["C-1"]),
        _mk_asset("B-2", "s2", "bb23e4723b89c4d9"),  # Hamming 1 ≤ 5
    ]}
    b = build_bindings(m)
    assert b["body_image_count"] == 1
    assert b["body_images"][0]["asset_id"] == "B-1"
    assert (b.get("binding_dedup_notes") or [])[0]["basis"] == "phash"


def test_different_frames_both_bound():
    """不同画面(不同 sha + 感知哈希远离)→ 各自正常绑定(反例)。"""
    m = {"run_id": "r3", "input": {"article_sha256": "c" * 64}, "assets": [
        _mk_asset("C-1", "s1", "0000000000000000", claim_ids=["C-1"]),
        _mk_asset("C-2", "s2", "ffffffffffffffff"),  # Hamming 64 > 5
    ]}
    b = build_bindings(m)
    assert b["body_image_count"] == 2
    assert {x["asset_id"] for x in b["body_images"]} == {"C-1", "C-2"}
    assert not (b.get("binding_dedup_notes") or [])
