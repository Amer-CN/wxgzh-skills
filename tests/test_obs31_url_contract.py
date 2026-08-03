"""OBS-31/OBS-81 — material URL field-contract tests (档48).

Covers: shared URL extraction (source_url -> links.original, registry-side
priority), dedup<->registry consistency FAIL_CLOSED semantics, empty-value
handling (two empties are NEVER consistent), and an offline regression using
the REAL 档46R RUN aihot artifacts (read-only; no media execution, no uploads).
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from wxgzh_pipeline import producers as P
from wxgzh_pipeline.producers import MediaRequestError

RUN_AHOT = Path(r"F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260802T220853-codex-sol-luna-max-m6pyv4\aihot\deduplicated_items.json")
RUN_REGISTRY = Path(r"F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260802T220853-codex-sol-luna-max-m6pyv4\super_writer\canonical_claim_registry.json")


class TestMaterialSourceUrl:
    def test_links_original_fallback(self):
        assert P._material_source_url({"links": {"original": "https://x.com/1"}}) == "https://x.com/1"

    def test_source_url_wins_over_links(self):
        assert P._material_source_url({"source_url": "https://a", "links": {"original": "https://b"}}) == "https://a"

    def test_missing_everywhere(self):
        assert P._material_source_url({}) is None
        assert P._material_source_url({"links": {}}) is None


class TestConsistencyCheck:
    def test_matching_urls_pass(self):
        P._check_material_url_consistency("M-01", "https://x.com/1", "https://x.com/1")

    def test_different_urls_fail_closed(self):
        with pytest.raises(MediaRequestError, match="disagrees"):
            P._check_material_url_consistency("M-01", "https://a", "https://b")

    def test_one_side_missing_fails_closed(self):
        with pytest.raises(MediaRequestError, match="missing on one side"):
            P._check_material_url_consistency("M-01", None, "https://a")
        with pytest.raises(MediaRequestError, match="missing on one side"):
            P._check_material_url_consistency("M-01", "https://a", None)

    def test_both_sides_missing_fails_closed_not_consistent(self):
        # OBS-81: two empty values must NEVER be treated as consistent
        with pytest.raises(MediaRequestError, match="missing on one side"):
            P._check_material_url_consistency("M-01", None, None)


class TestRealRunOfflineRegression:
    """Read-only regression on the 档46R RUN artifacts: after the fix the
    dedup<->registry URL check must PASS for every material. No media stage is
    executed and nothing is uploaded."""

    def test_real_run_dedup_and_registry_agree(self, tmp_path):
        assert RUN_AHOT.is_file() and RUN_REGISTRY.is_file()
        rd = tmp_path  # _load_dedup_index expects <rd>/aihot/deduplicated_items.json
        (rd / "aihot").mkdir()
        shutil.copyfile(RUN_AHOT, rd / "aihot" / "deduplicated_items.json")
        _, index = P._load_dedup_index(rd)
        registry = json.loads(RUN_REGISTRY.read_text(encoding="utf-8"))
        checked = 0
        for mat in registry["materials"]:
            mid = mat["material_id"]
            di = index["by_id"].get(mat.get("dedup_id")) or index["by_id"].get(mid)
            assert di is not None, f"{mid}: dedup lookup failed"
            assert di["source_url"], f"{mid}: dedup source_url empty after fix"
            P._check_material_url_consistency(mid, di["source_url"], mat["source_url"])
            checked += 1
        assert checked == len(registry["materials"]) == 12
