"""hotfix4 P0#3: canonical->dedup mapping is ID-based ONLY — a URL can never be
used to find a substitute item for a wrong/missing ID (no by_url fallback).

Negative cases (spec a-e):
  a. wrong material_id + correct source_url  -> FAIL
  b. wrong material_id + correct permalink   -> FAIL
  c. two dedup ids share one source_url      -> FAIL (ambiguous)
  d. the same dedup id appears twice         -> FAIL (duplicate, even same URL)
  e. canonical dedup_id conflicts with the material_id mapping -> FAIL
"""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from wxgzh_pipeline import producers as P
from wxgzh_pipeline.producers import MediaRequestError

URL_A = "https://src.test/a"
PERM_A = "https://aihot.virxact.com/items/a"
URL_B = "https://src.test/b"
PERM_B = "https://aihot.virxact.com/items/b"

DEDUP_OK = [
    {"id": "M-001", "source_url": URL_A, "aihot_permalink": PERM_A},
    {"id": "M-002", "source_url": URL_B, "aihot_permalink": PERM_B},
]


def _registry(materials):
    claims = [{"claim_id": f"C-{i:02d}", "material_id": m["material_id"],
               "claim_text": "论点", "source_url": m["source_url"],
               "source_excerpt": "原文"} for i, m in enumerate(materials, 1)]
    for m, c in zip(materials, claims):
        m.setdefault("selected_claim_ids", [c["claim_id"]])
    return {"schema_version": "1.0", "materials": materials, "claims": claims}


def _build(tmp_path, materials, dedup=DEDUP_OK):
    rd = tmp_path / "run"
    for d in ("super_writer", "zh_human_writing", "aihot", "media_enrichment"):
        (rd / d).mkdir(parents=True)
    (rd / "super_writer" / "canonical_claim_registry.json").write_text(
        json.dumps(_registry(materials), ensure_ascii=False), encoding="utf-8")
    (rd / "aihot" / "deduplicated_items.json").write_text(
        json.dumps(dedup, ensure_ascii=False), encoding="utf-8")
    art = rd / "zh_human_writing" / "final_article.md"
    art.write_text("# t\n\nbody\n", encoding="utf-8")
    ctx = SimpleNamespace(run_dir=str(rd), network_mode="fake_live")
    state = SimpleNamespace(run_id="R", final_article_sha256=hashlib.sha256(
        art.read_bytes()).hexdigest())
    return P._build_media_request(ctx, rd / "media_enrichment", state)


def test_a_wrong_material_id_with_correct_url_fails(tmp_path):
    mats = [{"material_id": "M-404", "source_url": URL_A, "aihot_permalink": PERM_A}]
    with pytest.raises(MediaRequestError, match="URL fallback is FORBIDDEN"):
        _build(tmp_path, mats)


def test_b_wrong_material_id_with_correct_permalink_fails(tmp_path):
    mats = [{"material_id": "M-404", "source_url": "https://src.test/other",
             "aihot_permalink": PERM_A}]
    with pytest.raises(MediaRequestError):
        _build(tmp_path, mats)


def test_c_two_dedup_ids_share_one_url_fails(tmp_path):
    dedup = [{"id": "M-001", "source_url": URL_A, "aihot_permalink": PERM_A},
             {"id": "M-00X", "source_url": URL_A, "aihot_permalink": PERM_A}]
    mats = [{"material_id": "M-001", "source_url": URL_A, "aihot_permalink": PERM_A}]
    with pytest.raises(MediaRequestError, match="multiple different ids"):
        _build(tmp_path, mats, dedup=dedup)


def test_d_duplicate_dedup_id_fails_even_with_same_url(tmp_path):
    dedup = [{"id": "M-001", "source_url": URL_A, "aihot_permalink": PERM_A},
             {"id": "M-001", "source_url": URL_A, "aihot_permalink": PERM_A}]
    mats = [{"material_id": "M-001", "source_url": URL_A, "aihot_permalink": PERM_A}]
    with pytest.raises(MediaRequestError, match="more than once"):
        _build(tmp_path, mats, dedup=dedup)


def test_e_dedup_id_conflicting_with_material_id_mapping_fails(tmp_path):
    # the material's explicit dedup_id resolves to item B while its own
    # material_id resolves to a DIFFERENT item A => mapping conflict
    mats = [{"material_id": "M-001", "dedup_id": "M-002",
             "source_url": URL_B, "aihot_permalink": PERM_B}]
    with pytest.raises(MediaRequestError, match="conflicts"):
        _build(tmp_path, mats)


def test_positive_explicit_dedup_id_without_conflict(tmp_path):
    # a material whose upstream id differs from its material_id maps cleanly when
    # the material_id itself is NOT a dedup id
    dedup = [{"id": "ITEM-9", "source_url": URL_A, "aihot_permalink": PERM_A}]
    mats = [{"material_id": "M-001", "dedup_id": "ITEM-9",
             "source_url": URL_A, "aihot_permalink": PERM_A}]
    req = json.loads(_build(tmp_path, mats, dedup=dedup).read_text(encoding="utf-8"))
    assert req["materials"][0]["dedup_id"] == "ITEM-9"
    assert req["provenance"]["material_mapping_verified"] is True
    assert req["provenance"]["verified_material_count"] == 1
