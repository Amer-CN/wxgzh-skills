"""hotfix3 P0#2: copyright approved_scope enum (material / source_url / single_asset).

The orchestrator MUST NEVER forge known_allowed. Scope rules are strict:
  - material     : requires material_id; approves ONLY that material.
  - source_url   : requires source_url;  approves ONLY that exact URL.
  - single_asset : requires asset_id;    never marks the whole material
                   known_allowed — the approval travels as an asset-scoped record
                   (media_request.asset_approvals) applied AFTER asset extraction.

Negative cases (spec a-e):
  a. single_asset + material_id, NO asset_id  -> not known_allowed
  b. single_asset approves A-001              -> A-002 cannot upload (only A-001 scoped)
  c. material approves M-001                   -> M-002 stays unknown
  d. source_url approves exact URL             -> other URLs do not inherit
  e. unknown approved_scope                    -> not known_allowed
"""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

from wxgzh_pipeline import producers as P

H = "a" * 64  # a well-formed 64-hex evidence digest

REGISTRY = {
    "schema_version": "1.0",
    "materials": [
        {"material_id": "M-001", "source_url": "https://src.test/a",
         "aihot_permalink": "https://aihot.virxact.com/items/a", "title": "甲",
         "selected_claim_ids": ["C-01"]},
        {"material_id": "M-002", "source_url": "https://src.test/b",
         "aihot_permalink": "https://aihot.virxact.com/items/b", "title": "乙",
         "selected_claim_ids": ["C-02"]},
    ],
    "claims": [
        {"claim_id": "C-01", "material_id": "M-001", "claim_text": "一",
         "source_url": "https://src.test/a", "source_excerpt": "x"},
        {"claim_id": "C-02", "material_id": "M-002", "claim_text": "二",
         "source_url": "https://src.test/b", "source_excerpt": "y"},
    ],
}
DEDUP = [
    {"id": "M-001", "source_url": "https://src.test/a",
     "aihot_permalink": "https://aihot.virxact.com/items/a"},
    {"id": "M-002", "source_url": "https://src.test/b",
     "aihot_permalink": "https://aihot.virxact.com/items/b"},
]


def _appr(**fields):
    base = {"approval_id": "AP", "approved_at": "2026-07-26T00:00:00Z",
            "approved_by": "real-user", "approval_evidence_sha256": H}
    base.update(fields)
    return base


def _build(tmp_path, *approvals):
    rd = tmp_path / "run"
    for d in ("super_writer", "zh_human_writing", "aihot", "media_enrichment"):
        (rd / d).mkdir(parents=True)
    (rd / "super_writer" / "canonical_claim_registry.json").write_text(
        json.dumps(REGISTRY, ensure_ascii=False), encoding="utf-8")
    (rd / "aihot" / "deduplicated_items.json").write_text(
        json.dumps(DEDUP, ensure_ascii=False), encoding="utf-8")
    art = rd / "zh_human_writing" / "final_article.md"
    art.write_text("# t\n\nbody\n", encoding="utf-8")
    if approvals:
        (rd / "media_enrichment" / "copyright_approval.json").write_text(
            json.dumps({"approvals": list(approvals)}, ensure_ascii=False), encoding="utf-8")
    ctx = SimpleNamespace(run_dir=str(rd), network_mode="fake_live")
    state = SimpleNamespace(run_id="R", final_article_sha256=hashlib.sha256(
        art.read_bytes()).hexdigest())
    return json.loads(P._build_media_request(ctx, rd / "media_enrichment", state)
                      .read_text(encoding="utf-8"))


def _status(req):
    return {m["material_id"]: m["copyright_review"]["status"] for m in req["materials"]}


# --------------------------- negative cases a-e ---------------------------

def test_a_single_asset_with_material_id_no_asset_id_not_known_allowed(tmp_path):
    # single_asset MUST carry asset_id; a material_id alone must NOT approve the material
    req = _build(tmp_path, _appr(approved_scope="single_asset", material_id="M-001"))
    assert _status(req) == {"M-001": "unknown", "M-002": "unknown"}
    assert req["asset_approvals"] == []
    assert req["provenance"]["copyright_approvals_bound"] == 0


def test_b_single_asset_scopes_only_that_asset(tmp_path):
    req = _build(tmp_path, _appr(approved_scope="single_asset", asset_id="A-001"))
    # material stays unknown (so A-002 from it can never upload); only A-001 is scoped
    assert _status(req) == {"M-001": "unknown", "M-002": "unknown"}
    ids = [a["asset_id"] for a in req["asset_approvals"]]
    assert ids == ["A-001"] and "A-002" not in ids


def test_c_material_scope_only_that_material(tmp_path):
    req = _build(tmp_path, _appr(approved_scope="material", material_id="M-001"))
    assert _status(req) == {"M-001": "known_allowed", "M-002": "unknown"}


def test_d_source_url_scope_no_inheritance(tmp_path):
    req = _build(tmp_path, _appr(approved_scope="source_url", source_url="https://src.test/a"))
    # only the exact URL (M-001) is approved; M-002's different URL does not inherit
    assert _status(req) == {"M-001": "known_allowed", "M-002": "unknown"}


def test_e_unknown_scope_not_known_allowed(tmp_path):
    req = _build(tmp_path, _appr(approved_scope="whole_site", material_id="M-001"))
    assert _status(req) == {"M-001": "unknown", "M-002": "unknown"}
    assert req["provenance"]["copyright_approvals_bound"] == 0


# --------------------------- extra guards ---------------------------

def test_bad_evidence_hash_ignored(tmp_path):
    req = _build(tmp_path, _appr(approved_scope="material", material_id="M-001",
                                 approval_evidence_sha256="not-a-hash"))
    assert _status(req)["M-001"] == "unknown"


def test_material_scope_missing_binding_ignored(tmp_path):
    # material scope without material_id cannot approve anything
    req = _build(tmp_path, _appr(approved_scope="material", source_url="https://src.test/a"))
    assert _status(req) == {"M-001": "unknown", "M-002": "unknown"}


def test_source_url_for_unknown_url_approves_nobody(tmp_path):
    req = _build(tmp_path, _appr(approved_scope="source_url", source_url="https://src.test/zzz"))
    assert _status(req) == {"M-001": "unknown", "M-002": "unknown"}


def test_positive_material_and_single_asset_together(tmp_path):
    req = _build(tmp_path,
                 _appr(approval_id="A1", approved_scope="material", material_id="M-002"),
                 _appr(approval_id="A2", approved_scope="single_asset", asset_id="A-007"))
    assert _status(req) == {"M-001": "unknown", "M-002": "known_allowed"}
    assert [a["asset_id"] for a in req["asset_approvals"]] == ["A-007"]
    assert req["provenance"]["copyright_approvals_bound"] == 2
