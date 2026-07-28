"""hotfix2 P0#2 + P0#3 negative/positive tests for the media-request producer.

P0#2 — media_request.json MUST be bound to super_writer/canonical_claim_registry.json
       VERBATIM: no invented claim/material IDs, no material-title-as-claim, no
       example.com fallback; missing/malformed/unmappable registry => FAIL_CLOSED.
P0#3 — the orchestrator MUST NOT forge copyright approval. known_allowed can ONLY
       come from a real approval record (with all binding fields) on disk; without
       one a source material stays "unknown" (never known_allowed) so it cannot be
       uploaded downstream.

These exercise wxgzh_pipeline.producers directly (offline, no side effects).
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
         "aihot_permalink": "https://aihot.virxact.com/items/a", "title": "素材甲",
         "selected_claim_ids": ["C-01", "C-02"]},
        {"material_id": "M-002", "source_url": "https://src.test/b",
         "aihot_permalink": "https://aihot.virxact.com/items/b", "title": "素材乙",
         "selected_claim_ids": ["C-03"]},
    ],
    "claims": [
        {"claim_id": "C-01", "material_id": "M-001", "claim_text": "论点一",
         "source_url": "https://src.test/a", "source_excerpt": "原文一"},
        {"claim_id": "C-02", "material_id": "M-001", "claim_text": "论点二",
         "source_url": "https://src.test/a", "source_excerpt": "原文二",
         "numbers": [{"value": 42, "unit": "GB"}], "chart_group": "g1",
         "metric_name": "vram"},
        {"claim_id": "C-03", "material_id": "M-002", "claim_text": "论点三",
         "source_url": "https://src.test/b", "source_excerpt": "原文三"},
    ],
}

# AI HOT dedup that matches the canonical registry (P0#3 cross-verification).
DEDUP = [
    {"id": "M-001", "title": "素材甲", "source_url": "https://src.test/a",
     "aihot_permalink": "https://aihot.virxact.com/items/a"},
    {"id": "M-002", "title": "素材乙", "source_url": "https://src.test/b",
     "aihot_permalink": "https://aihot.virxact.com/items/b"},
]


def _setup(tmp_path: Path, registry=REGISTRY, approvals=None, dedup=DEDUP):
    """Build a minimal run_dir with the canonical registry + AI HOT dedup + frozen
    article (+ optional copyright_approval.json); return (ctx, state, media_dir)."""
    rd = tmp_path / "run"
    (rd / "super_writer").mkdir(parents=True)
    (rd / "zh_human_writing").mkdir(parents=True)
    (rd / "aihot").mkdir(parents=True)
    md = rd / "media_enrichment"; md.mkdir(parents=True)
    if registry is not None:
        (rd / "super_writer" / "canonical_claim_registry.json").write_text(
            json.dumps(registry, ensure_ascii=False), encoding="utf-8")
    if dedup is not None:
        (rd / "aihot" / "deduplicated_items.json").write_text(
            json.dumps(dedup, ensure_ascii=False), encoding="utf-8")
    article = rd / "zh_human_writing" / "final_article.md"
    article.write_text("# 标题\n\n正文。\n", encoding="utf-8")
    if approvals is not None:
        (md / "copyright_approval.json").write_text(
            json.dumps(approvals, ensure_ascii=False), encoding="utf-8")
    ctx = SimpleNamespace(run_dir=str(rd), network_mode="fake_live")
    state = SimpleNamespace(run_id="RUN-T",
                            final_article_sha256=hashlib.sha256(
                                article.read_bytes()).hexdigest())
    return ctx, state, md


# ----------------------------- P0#2 -----------------------------

def test_media_request_binds_canonical_registry_verbatim(tmp_path):
    ctx, state, md = _setup(tmp_path)
    req_path = P._build_media_request(ctx, md, state)
    req = json.loads(req_path.read_text(encoding="utf-8"))

    # claim IDs/materials are EXACTLY the registry's — nothing invented, nothing dropped
    assert {c["claim_id"] for c in req["claims"]} == {"C-01", "C-02", "C-03"}
    assert {m["material_id"] for m in req["materials"]} == {"M-001", "M-002"}

    by_id = {c["claim_id"]: c for c in req["claims"]}
    # verbatim text/source/excerpt copied from the registry
    assert by_id["C-01"]["claim_text"] == "论点一"
    assert by_id["C-01"]["source_url"] == "https://src.test/a"
    assert by_id["C-01"]["source_excerpt"] == "原文一"
    # optional numbers/chart_group preserved verbatim when present
    assert by_id["C-02"]["numbers"] == [{"value": 42, "unit": "GB"}]
    assert by_id["C-02"]["chart_group"] == "g1"
    # selected_claim_ids preserved on materials
    assert next(m for m in req["materials"] if m["material_id"] == "M-001"
                )["selected_claim_ids"] == ["C-01", "C-02"]
    # provenance binds the exact registry hash; NO example.com fallback anywhere
    reg_p = Path(ctx.run_dir) / "super_writer" / "canonical_claim_registry.json"
    assert req["provenance"]["canonical_registry_sha256"] == \
        hashlib.sha256(reg_p.read_bytes()).hexdigest()
    assert "example.com" not in req_path.read_text(encoding="utf-8")


def test_missing_registry_fails_closed(tmp_path):
    ctx, state, md = _setup(tmp_path, registry=None)
    with pytest.raises(MediaRequestError):
        P._build_media_request(ctx, md, state)


def test_malformed_registry_fails_closed(tmp_path):
    ctx, state, md = _setup(tmp_path)
    (Path(ctx.run_dir) / "super_writer" / "canonical_claim_registry.json").write_text(
        "{not json", encoding="utf-8")
    with pytest.raises(MediaRequestError):
        P._build_media_request(ctx, md, state)


def test_empty_registry_fails_closed(tmp_path):
    ctx, state, md = _setup(tmp_path, registry={"materials": [], "claims": []})
    with pytest.raises(MediaRequestError):
        P._build_media_request(ctx, md, state)


def test_claim_referencing_unknown_material_fails_closed(tmp_path):
    bad = json.loads(json.dumps(REGISTRY))
    bad["claims"].append({"claim_id": "C-99", "material_id": "M-404",
                          "claim_text": "悬空", "source_url": "https://src.test/x",
                          "source_excerpt": "x"})
    ctx, state, md = _setup(tmp_path, registry=bad)
    with pytest.raises(MediaRequestError):
        P._build_media_request(ctx, md, state)


# ----------------------------- P0#3 -----------------------------

def _approval(material_id="M-001", scope="material"):
    return {"approvals": [{
        "approval_id": "AP-1", "approved_scope": scope,
        "material_id": material_id, "approved_at": "2026-07-26T00:00:00Z",
        "approved_by": "real-user", "approval_evidence_sha256": "e" * 64}]}


def test_no_approval_never_yields_known_allowed(tmp_path):
    """Without an approval record, the orchestrator must NOT self-approve."""
    ctx, state, md = _setup(tmp_path, approvals=None)
    req = json.loads(P._build_media_request(ctx, md, state).read_text(encoding="utf-8"))
    for m in req["materials"]:
        assert m["copyright_review"]["status"] == "unknown"
        assert m["copyright_review"]["status"] != "known_allowed"
    assert req["provenance"]["copyright_approvals_bound"] == 0


def test_valid_approval_yields_known_allowed_only_for_that_material(tmp_path):
    ctx, state, md = _setup(tmp_path, approvals=_approval("M-001"))
    req = json.loads(P._build_media_request(ctx, md, state).read_text(encoding="utf-8"))
    by_mid = {m["material_id"]: m for m in req["materials"]}
    cr = by_mid["M-001"]["copyright_review"]
    assert cr["status"] == "known_allowed"
    assert cr["approval_id"] == "AP-1" and cr["reviewed_by"] == "real-user"
    assert cr["evidence"] == "e" * 64
    # the un-approved material stays unknown
    assert by_mid["M-002"]["copyright_review"]["status"] == "unknown"
    assert req["provenance"]["copyright_approvals_bound"] == 1


def test_incomplete_approval_is_ignored(tmp_path):
    """A record missing binding fields cannot produce known_allowed."""
    incomplete = {"approvals": [{"approval_id": "AP-1", "material_id": "M-001",
                                 "approved_by": "real-user"}]}  # missing scope/at/evidence
    ctx, state, md = _setup(tmp_path, approvals=incomplete)
    req = json.loads(P._build_media_request(ctx, md, state).read_text(encoding="utf-8"))
    for m in req["materials"]:
        assert m["copyright_review"]["status"] == "unknown"
    assert req["provenance"]["copyright_approvals_bound"] == 0


def test_subprocess_media_request_failure_blocks_entry(tmp_path, monkeypatch):
    """When the registry is missing, _subprocess must FAIL_CLOSED (exit 2) and
    NEVER invoke the media entry (uploader) — proving no bypass of P0#2."""
    ctx, state, md = _setup(tmp_path, registry=None)
    ctx.skills_home = tmp_path
    ctx.stage_dir = lambda s: md

    from wxgzh_pipeline import execmodel as EM
    monkeypatch.setattr(EM, "resolve_entry",
                        lambda *a, **k: (tmp_path / "run_media_enrichment.py", None))

    called = {"ran": False}

    def _boom(*a, **k):
        called["ran"] = True
        raise AssertionError("entry (uploader) must NOT run when registry is missing")

    monkeypatch.setattr(P, "run_script", _boom)
    outputs, meta = P._subprocess(ctx, "media_enrichment", md,
                                  EM.EXPECTED_OUTPUTS["media_enrichment"], state)
    assert outputs == []
    assert "media_request_failed" in meta
    assert meta["entry_run"]["exit_code"] == 2
    assert called["ran"] is False
