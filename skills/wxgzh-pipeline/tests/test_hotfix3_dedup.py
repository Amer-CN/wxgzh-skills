"""hotfix3 P0#3: canonical registry must be cross-verified item-by-item against
the AI HOT dedup (aihot/deduplicated_items.json).

MediaRequestError (FAIL_CLOSED) when:
  - a canonical material is absent from dedup;
  - material_id present but source_url differs;
  - one dedup id maps to multiple different URLs (ambiguous);
  - the registry uses a URL not present in dedup;
  - the dedup file is missing or malformed.
On success, media_request.provenance carries the dedup hash + verified counts.
"""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from wxgzh_pipeline import producers as P
from wxgzh_pipeline.producers import MediaRequestError

REGISTRY = {
    "schema_version": "1.0",
    "materials": [
        {"material_id": "M-001", "source_url": "https://src.test/a",
         "aihot_permalink": "https://aihot.virxact.com/items/a",
         "selected_claim_ids": ["C-01"]},
        {"material_id": "M-002", "source_url": "https://src.test/b",
         "aihot_permalink": "https://aihot.virxact.com/items/b",
         "selected_claim_ids": ["C-02"]},
    ],
    "claims": [
        {"claim_id": "C-01", "material_id": "M-001", "claim_text": "一",
         "source_url": "https://src.test/a", "source_excerpt": "x"},
        {"claim_id": "C-02", "material_id": "M-002", "claim_text": "二",
         "source_url": "https://src.test/b", "source_excerpt": "y"},
    ],
}
DEDUP_OK = [
    {"id": "M-001", "source_url": "https://src.test/a",
     "aihot_permalink": "https://aihot.virxact.com/items/a"},
    {"id": "M-002", "source_url": "https://src.test/b",
     "aihot_permalink": "https://aihot.virxact.com/items/b"},
]


def _build(tmp_path, registry=REGISTRY, dedup=DEDUP_OK, write_dedup=True):
    rd = tmp_path / "run"
    for d in ("super_writer", "zh_human_writing", "aihot", "media_enrichment"):
        (rd / d).mkdir(parents=True)
    (rd / "super_writer" / "canonical_claim_registry.json").write_text(
        json.dumps(registry, ensure_ascii=False), encoding="utf-8")
    if write_dedup:
        (rd / "aihot" / "deduplicated_items.json").write_text(
            dedup if isinstance(dedup, str) else json.dumps(dedup, ensure_ascii=False),
            encoding="utf-8")
    art = rd / "zh_human_writing" / "final_article.md"
    art.write_text("# t\n\nbody\n", encoding="utf-8")
    ctx = SimpleNamespace(run_dir=str(rd), network_mode="fake_live")
    state = SimpleNamespace(run_id="R", final_article_sha256=hashlib.sha256(
        art.read_bytes()).hexdigest())
    return P._build_media_request(ctx, rd / "media_enrichment", state)


# ----------------------------- positive -----------------------------

def test_dedup_match_records_provenance(tmp_path):
    req = json.loads(_build(tmp_path).read_text(encoding="utf-8"))
    prov = req["provenance"]
    assert prov["material_mapping_verified"] is True
    assert prov["verified_material_count"] == 2
    assert len(prov["deduplicated_items_sha256"]) == 64
    assert len(prov["canonical_registry_sha256"]) == 64
    # each material carries the resolved dedup id
    assert {m["material_id"]: m["dedup_id"] for m in req["materials"]} == {
        "M-001": "M-001", "M-002": "M-002"}


# ----------------------------- negatives -----------------------------

def test_material_absent_from_dedup_fails_closed(tmp_path):
    dedup = [DEDUP_OK[0]]  # M-002 missing
    with pytest.raises(MediaRequestError):
        _build(tmp_path, dedup=dedup)


def test_source_url_mismatch_fails_closed(tmp_path):
    dedup = [DEDUP_OK[0], {"id": "M-002", "source_url": "https://src.test/DIFFERENT",
                           "aihot_permalink": "https://aihot.virxact.com/items/b"}]
    with pytest.raises(MediaRequestError):
        _build(tmp_path, dedup=dedup)


def test_permalink_mismatch_fails_closed(tmp_path):
    dedup = [DEDUP_OK[0], {"id": "M-002", "source_url": "https://src.test/b",
                           "aihot_permalink": "https://aihot.virxact.com/items/WRONG"}]
    with pytest.raises(MediaRequestError):
        _build(tmp_path, dedup=dedup)


def test_ambiguous_dedup_id_multiple_urls_fails_closed(tmp_path):
    dedup = [{"id": "M-001", "source_url": "https://src.test/a"},
             {"id": "M-001", "source_url": "https://src.test/OTHER"},
             DEDUP_OK[1]]
    with pytest.raises(MediaRequestError):
        _build(tmp_path, dedup=dedup)


def test_registry_url_not_in_dedup_fails_closed(tmp_path):
    reg = json.loads(json.dumps(REGISTRY))
    reg["materials"][0]["source_url"] = "https://src.test/not-in-dedup"
    reg["materials"][0].pop("material_id", None)  # force url-based lookup
    reg["materials"][0]["material_id"] = "M-001"
    # M-001 now claims a URL absent from dedup and its id maps to a different URL
    with pytest.raises(MediaRequestError):
        _build(tmp_path, registry=reg)


def test_missing_dedup_file_fails_closed(tmp_path):
    with pytest.raises(MediaRequestError):
        _build(tmp_path, write_dedup=False)


def test_malformed_dedup_fails_closed(tmp_path):
    with pytest.raises(MediaRequestError):
        _build(tmp_path, dedup="{not json")


def test_empty_dedup_fails_closed(tmp_path):
    with pytest.raises(MediaRequestError):
        _build(tmp_path, dedup=[])
