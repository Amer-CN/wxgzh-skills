"""Tests for chart generator: dev5 group-gated 3 chart types + negatives."""

import pytest
from pathlib import Path
from media_enrichment.chart_generator import (
    extract_numbers_from_claim, check_comparability, build_chart_specs,
    generate_chart, ChartDataPoint, ChartSpec, group_claims_for_charts,
)
from media_enrichment.image_inspector import inspect_image

MATS = {"M-001": {"source_url": "https://x.com/1"}, "M-002": {"source_url": "https://x.com/2"}}


def _dp(label, value, unit="%", claim_id="C-01", group="MMLU", metric="得分", time_value=""):
    return ChartDataPoint(label, value, unit, claim_id, "M-001",
                          "https://example.com/1", f"{label} {value}{unit}",
                          chart_group=group, metric_name=metric, time_value=time_value)


class TestNumberExtraction:
    def test_percentage(self):
        nums = extract_numbers_from_claim({"claim_text": "x", "numbers": ["76.2%"]})
        assert any(n[1] == 76.2 and n[2] == "%" for n in nums)

    def test_plain_number(self):
        nums = extract_numbers_from_claim({"claim_text": "x", "numbers": ["15"]})
        assert any(n[1] == 15.0 for n in nums)

    def test_no_numbers(self):
        assert len(extract_numbers_from_claim({"claim_text": "x", "numbers": []})) == 0


class TestComparability:
    def test_same_group_same_unit_passes(self):
        dps = [_dp("模型A", 76.2, claim_id="C-01"), _dp("模型B", 32.2, claim_id="C-02")]
        assert check_comparability(dps)[0]

    def test_incompatible_units_fails(self):
        dps = [_dp("A", 76.2, unit="%"), _dp("B", 15, unit="currency", claim_id="C-02")]
        ok, reason = check_comparability(dps)
        assert not ok
        assert "mixed units" in reason

    def test_mixed_groups_fails(self):
        dps = [_dp("A", 76.2, group="MMLU"), _dp("B", 32.2, group="GSM8K", claim_id="C-02")]
        ok, reason = check_comparability(dps)
        assert not ok
        assert "incompatible chart group" in reason

    def test_missing_group_fails(self):
        dps = [_dp("A", 76.2, group=""), _dp("B", 32.2, group="", claim_id="C-02")]
        assert not check_comparability(dps)[0]

    def test_missing_traceability_fails(self):
        dps = [_dp("A", 76.2), _dp("B", 32.2, claim_id="")]
        assert not check_comparability(dps)[0]

    def test_single_point_fails(self):
        assert not check_comparability([_dp("A", 76.2)])[0]


class TestGroupClaimsForCharts:
    def test_claims_grouped_by_group_metric_unit(self):
        claims = [
            {"claim_id": "C-01", "claim_text": "A", "material_id": "M-001", "source_url": "https://x.com/1",
             "source_excerpt": "e1", "numbers": ["76.2%"], "chart_group": "MMLU", "metric_name": "得分", "series_label": "A"},
            {"claim_id": "C-02", "claim_text": "B", "material_id": "M-001", "source_url": "https://x.com/1",
             "source_excerpt": "e2", "numbers": ["32.2%"], "chart_group": "MMLU", "metric_name": "得分", "series_label": "B"},
        ]
        groups, warnings = group_claims_for_charts(claims, MATS)
        assert ("MMLU", "得分", "%") in groups
        assert len(groups[("MMLU", "得分", "%")]) == 2
        assert warnings == []

    def test_numbers_without_group_warn_and_skip(self):
        claims = [{"claim_id": "C-03", "claim_text": "C", "material_id": "M-002",
                   "source_url": "https://x.com/2", "source_excerpt": "e3", "numbers": ["15"]}]
        groups, warnings = group_claims_for_charts(claims, MATS)
        assert groups == {}
        assert any("incompatible chart group" in w for w in warnings)


class TestThreeChartTypes:
    def _make_dps(self, with_time=False):
        return [
            _dp("模型A", 76.2, claim_id="C-01", time_value="2026-05" if with_time else ""),
            _dp("模型B", 32.2, claim_id="C-02", time_value="2026-06" if with_time else ""),
        ]

    def test_bar_chart(self, tmp_path):
        spec = ChartSpec("bar", "Bar Test", self._make_dps(), "%", "Y", "X", "source",
                         chart_group="MMLU", metric_name="得分", caption="MMLU得分对比")
        result = generate_chart(spec, tmp_path / "bar.png")
        assert result.success
        assert Path(result.chart_path).exists()

    def test_comparison_chart(self, tmp_path):
        spec = ChartSpec("comparison", "Comparison Test", self._make_dps(), "%", "Y", "X", "source",
                         chart_group="MMLU", metric_name="得分")
        result = generate_chart(spec, tmp_path / "comparison.png")
        assert result.success

    def test_timeline_chart_with_time(self, tmp_path):
        spec = ChartSpec("timeline", "Timeline Test", self._make_dps(with_time=True), "%", "Y", "时间", "source",
                         chart_group="MMLU", metric_name="得分")
        result = generate_chart(spec, tmp_path / "timeline.png")
        assert result.success
        from PIL import Image
        assert Image.open(result.chart_path).format == "PNG"

    def test_timeline_without_time_fails(self, tmp_path):
        spec = ChartSpec("timeline", "Timeline Bad", self._make_dps(with_time=False), "%", "Y", "时间", "source",
                         chart_group="MMLU", metric_name="得分")
        result = generate_chart(spec, tmp_path / "tl_bad.png")
        assert not result.success
        assert "time_value" in result.error

    def test_timeline_does_not_fallback_to_bar(self, tmp_path):
        bar_spec = ChartSpec("bar", "Bar", self._make_dps(with_time=True), "%", "Y", "X", "source",
                             chart_group="MMLU", metric_name="得分")
        tl_spec = ChartSpec("timeline", "Timeline", self._make_dps(with_time=True), "%", "Y", "时间", "source",
                            chart_group="MMLU", metric_name="得分")
        assert generate_chart(bar_spec, tmp_path / "bar.png").sha256 != \
               generate_chart(tl_spec, tmp_path / "timeline.png").sha256

    def test_chart_traceability(self, tmp_path):
        spec = ChartSpec("bar", "Trace Test", self._make_dps(), "%", "Y", "X", "source",
                         chart_group="MMLU", metric_name="得分")
        result = generate_chart(spec, tmp_path / "trace.png")
        for t in result.data_traceability:
            assert t["claim_id"] and t["material_id"] and t["source_url"] and t["source_excerpt"]
            assert t["chart_group"] == "MMLU"

    def test_incompatible_data_rejected(self, tmp_path):
        dps = [_dp("A", 76.2, unit="%"), _dp("B", 15, unit="currency", claim_id="C-02")]
        spec = ChartSpec("bar", "Bad", dps, "mixed", "Y", "X", "source")
        assert not generate_chart(spec, tmp_path / "bad.png").success

    def test_generated_chart_is_valid_png(self, tmp_path):
        spec = ChartSpec("bar", "Valid Test", self._make_dps(), "%", "Y", "X", "source",
                         chart_group="MMLU", metric_name="得分")
        result = generate_chart(spec, tmp_path / "valid.png")
        inspection = inspect_image(result.chart_path)
        assert inspection.is_valid
        assert inspection.mime_type == "image/png"


class TestBuildChartSpecs:
    def test_specs_generated_for_valid_group(self):
        claims = [
            {"claim_id": "C-01", "claim_text": "A", "material_id": "M-001", "source_url": "https://x.com/1",
             "source_excerpt": "e1", "numbers": ["76.2%"], "chart_group": "MMLU", "metric_name": "得分", "series_label": "A"},
            {"claim_id": "C-02", "claim_text": "B", "material_id": "M-001", "source_url": "https://x.com/1",
             "source_excerpt": "e2", "numbers": ["32.2%"], "chart_group": "MMLU", "metric_name": "得分", "series_label": "B"},
        ]
        plan = build_chart_specs(claims, MATS)
        types = [s.chart_type for s in plan.specs]
        assert "bar" in types and "comparison" in types
        # no time_value -> no timeline, with explicit warning
        assert "timeline" not in types
        assert any("timeline skipped" in w for w in plan.warnings)

    def test_separate_groups_never_merge(self):
        claims = [
            {"claim_id": "C-01", "claim_text": "A", "material_id": "M-001", "source_url": "https://x.com/1",
             "source_excerpt": "e1", "numbers": ["76.2%"], "chart_group": "MMLU", "metric_name": "得分", "series_label": "A"},
            {"claim_id": "C-03", "claim_text": "C", "material_id": "M-002", "source_url": "https://x.com/2",
             "source_excerpt": "e3", "numbers": ["15%"], "chart_group": "GSM8K", "metric_name": "得分", "series_label": "C"},
        ]
        plan = build_chart_specs(claims, MATS)
        # each group has only 1 point -> nothing chartable, fail-closed
        assert plan.specs == []
        assert any("incompatible chart group" in w for w in plan.warnings)
