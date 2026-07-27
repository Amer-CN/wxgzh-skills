"""dev5 P0-2 tests: chart comparison-group gating (fail-closed).

Flags covered:
- CROSS_BENCHMARK_SAME_UNIT_REJECTED
- CROSS_BENCHMARK_EMPTY_UNIT_REJECTED
- SAME_BENCHMARK_SAME_METRIC_ACCEPTED
- TIMELINE_WITHOUT_TIME_REJECTED
- TIMELINE_WITH_REAL_DATES_ACCEPTED
- CHART_CAPTION_COVERS_GROUP
- visual-acceptance regression (C-10-a/C-11-a/C-33-a/C-34-a) -> 0 charts
"""

import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

from media_enrichment.chart_generator import (
    build_chart_specs, generate_chart, check_comparability,
    check_timeline_eligibility, ChartDataPoint,
)

MATS = {"M-001": {"source_url": "https://x.com/1"}, "M-002": {"source_url": "https://x.com/2"}}


def _claim(cid, text, numbers, chart_group=None, metric_name=None,
           series_label=None, unit=None, time_value=None, material="M-001",
           source_url="https://x.com/1"):
    c = {"claim_id": cid, "claim_text": text, "material_id": material,
         "source_url": source_url, "source_excerpt": text, "numbers": numbers}
    if chart_group is not None:
        c["chart_group"] = chart_group
    if metric_name is not None:
        c["metric_name"] = metric_name
    if series_label is not None:
        c["series_label"] = series_label
    if unit is not None:
        c["unit"] = unit
    if time_value is not None:
        c["time_value"] = time_value
    return c


class TestCrossBenchmarkRejected:
    def test_cross_benchmark_same_unit_rejected(self):
        """CROSS_BENCHMARK_SAME_UNIT_REJECTED: same declared unit, different groups."""
        claims = [
            _claim("C-A", "基准A得分", ["1679"], chart_group="Frontend Code Arena",
                   metric_name="Elo", series_label="K3", unit="Elo"),
            _claim("C-B", "基准B得分", ["1543"], chart_group="AA-Briefcase",
                   metric_name="Elo", series_label="K3", unit="Elo"),
        ]
        plan = build_chart_specs(claims, MATS)
        assert plan.specs == []
        assert any("incompatible chart group" in w for w in plan.warnings)

    def test_cross_benchmark_empty_unit_rejected(self):
        """CROSS_BENCHMARK_EMPTY_UNIT_REJECTED: empty units must not merge groups."""
        claims = [
            _claim("C-A", "基准A得分", ["1679"], chart_group="Frontend Code Arena",
                   metric_name="Elo", series_label="K3"),
            _claim("C-B", "基准B得分", ["1543"], chart_group="AA-Briefcase",
                   metric_name="Elo", series_label="K3"),
        ]
        plan = build_chart_specs(claims, MATS)
        assert plan.specs == []
        assert any("incompatible chart group" in w for w in plan.warnings)

    def test_forbidden_four_leaderboard_merge(self):
        """The exact dev4 bug: 1679/1543/1450/1326 must never merge into one chart."""
        dps = [
            ChartDataPoint("K3", 1679, "", "C-10-a", "M-001", "https://x.com/1", "e", "Frontend Code Arena", "Elo"),
            ChartDataPoint("K3", 1543, "", "C-11-a", "M-001", "https://x.com/1", "e", "AA-Briefcase", "Elo"),
            ChartDataPoint("K3", 1450, "", "C-33-a", "M-001", "https://x.com/1", "e", "3D Design", "Elo"),
            ChartDataPoint("K3", 1326, "", "C-34-a", "M-001", "https://x.com/1", "e", "DesignArena", "Elo"),
        ]
        ok, reason = check_comparability(dps)
        assert not ok
        assert "incompatible chart group" in reason

    def test_generate_chart_refuses_mixed_groups(self, tmp_path):
        from media_enrichment.chart_generator import ChartSpec
        dps = [
            ChartDataPoint("K3", 1679, "", "C-10-a", "M-001", "https://x.com/1", "e", "Frontend Code Arena", "Elo"),
            ChartDataPoint("K3", 1543, "", "C-11-a", "M-001", "https://x.com/1", "e", "AA-Briefcase", "Elo"),
        ]
        spec = ChartSpec("bar", "bad", dps, "", "Y", "X", "s")
        result = generate_chart(spec, tmp_path / "bad.png")
        assert not result.success
        assert "incompatible chart group" in result.error


class TestSameBenchmarkAccepted:
    def _claims(self, **extra):
        return [
            _claim("C-01-a", "K3得分32.2%", ["32.2%"], chart_group="ExploitBench",
                   metric_name="得分", series_label="Kimi K3", **extra),
            _claim("C-01-b", "GLM得分24.4%", ["24.4%"], chart_group="ExploitBench",
                   metric_name="得分", series_label="GLM-5.2", **extra),
        ]

    def test_same_benchmark_same_metric_accepted(self):
        """SAME_BENCHMARK_SAME_METRIC_ACCEPTED"""
        plan = build_chart_specs(self._claims(), MATS)
        types = [s.chart_type for s in plan.specs]
        assert "bar" in types and "comparison" in types

    def test_chart_caption_covers_group(self, tmp_path):
        """CHART_CAPTION_COVERS_GROUP: caption covers group + every series."""
        plan = build_chart_specs(self._claims(), MATS)
        for spec in plan.specs:
            assert "ExploitBench" in spec.caption
            assert "Kimi K3" in spec.caption
            assert "GLM-5.2" in spec.caption
            assert spec.caption != "K3得分32.2%", "caption must not be a single claim text"
            assert "ExploitBench" in spec.title

    def test_generated_png_ok(self, tmp_path):
        plan = build_chart_specs(self._claims(), MATS)
        result = generate_chart(plan.specs[0], tmp_path / "ok.png")
        assert result.success
        assert Path(result.chart_path).exists()


class TestTimelineGating:
    def test_timeline_without_time_rejected(self):
        """TIMELINE_WITHOUT_TIME_REJECTED: no time_value -> no timeline spec."""
        claims = [
            _claim("C-01", "四月ARR", ["2"], chart_group="Moonshot ARR",
                   metric_name="亿美元", series_label="4月"),
            _claim("C-02", "六月ARR", ["3"], chart_group="Moonshot ARR",
                   metric_name="亿美元", series_label="6月"),
        ]
        plan = build_chart_specs(claims, MATS)
        types = [s.chart_type for s in plan.specs]
        assert "timeline" not in types
        assert "bar" in types  # bar/comparison still fine
        assert any("timeline skipped" in w and "time_value" in w for w in plan.warnings)

    def test_timeline_with_real_dates_accepted(self, tmp_path):
        """TIMELINE_WITH_REAL_DATES_ACCEPTED"""
        claims = [
            _claim("C-01", "四月ARR", ["2"], chart_group="Moonshot ARR",
                   metric_name="亿美元", series_label="4月ARR", time_value="2026-04"),
            _claim("C-02", "六月ARR", ["3"], chart_group="Moonshot ARR",
                   metric_name="亿美元", series_label="6月ARR", time_value="2026-06"),
        ]
        plan = build_chart_specs(claims, MATS)
        tl = [s for s in plan.specs if s.chart_type == "timeline"]
        assert len(tl) == 1
        result = generate_chart(tl[0], tmp_path / "tl.png")
        assert result.success

    def test_timeline_partial_time_rejected(self):
        dps = [
            ChartDataPoint("4月", 2, "亿", "C-01", "M-001", "https://x.com/1", "e",
                           "Moonshot ARR", "亿美元", time_value="2026-04"),
            ChartDataPoint("6月", 3, "亿", "C-02", "M-001", "https://x.com/1", "e",
                           "Moonshot ARR", "亿美元", time_value=""),
        ]
        ok, reason = check_timeline_eligibility(dps)
        assert not ok
        assert "time_value" in reason


class TestVisualAcceptanceChartRegression:
    def test_visual_acceptance_numbers_produce_zero_charts(self):
        """Regression: the exact visual-acceptance chart claims -> 0 charts.

        C-10-a/C-11-a/C-33-a/C-34-a carried numbers but (correctly) no
        chart_group — cross-leaderboard merging must be refused fail-closed.
        """
        claims = [
            _claim("C-10-a", "K3在Frontend Code Arena以1679分位居第一", ["1679"]),
            _claim("C-11-a", "K3在AA-Briefcase获1543分", ["1543"]),
            _claim("C-33-a", "K3在3D Design评测中以1450 Elo排名第一", ["1450"]),
            _claim("C-34-a", "K3在DesignArena以1326 Elo取得第一", ["1326"]),
        ]
        plan = build_chart_specs(claims, MATS)
        assert plan.specs == [], "GENERATED_CHARTS must be 0 for ungrouped leaderboard numbers"
        assert any("incompatible chart group" in w for w in plan.warnings)
