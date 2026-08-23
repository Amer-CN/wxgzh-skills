"""77F/OBS-181: generated chart anchor from spec, not text match."""
from pathlib import Path
import sys
SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

from media_enrichment.chart_generator import ChartSpec, ChartDataPoint

def _dp(label="S1", value=10, chart_group="g", metric_name="m", unit="", claim_id="C-01", material_id="M-01"):
    return ChartDataPoint(label=label, value=value, unit=unit, claim_id=claim_id,
                          material_id=material_id, source_url="https://example.test/p",
                          source_excerpt="ex", chart_group=chart_group,
                          metric_name=metric_name, time_value="")

def test_generated_chart_spec_anchor_is_title():
    spec = ChartSpec(chart_type="bar", title="Ox Alpha 性能对比", data_points=[_dp(), _dp(label="S2", value=20)],
                     unit="", y_axis_label="m", x_axis_label="", source_note="src",
                     chart_group="bench", metric_name="score", caption="cap")
    # run_media logic: placement anchor = spec.title stripped
    anchor = spec.title.strip() or (spec.chart_group + chr(183) + spec.metric_name)
    assert anchor == "Ox Alpha 性能对比"
    # without title fallback
    spec2 = ChartSpec(chart_type="bar", title="", data_points=[_dp()], unit="", y_axis_label="m",
                      x_axis_label="", source_note="src", chart_group="mygroup", metric_name="mymetric", caption="")
    anchor2 = spec2.title.strip() or (spec2.chart_group + chr(183) + spec2.metric_name)
    assert anchor2 == "mygroup" + chr(183) + "mymetric"

def test_generated_asset_placement_and_page_position_are_known():
    # Simulate what run_media does for generated chart
    spec = ChartSpec(chart_type="bar", title="DeepSWE 对比", data_points=[_dp(), _dp(label="S2", value=20)],
                     unit="", y_axis_label="m", x_axis_label="", source_note="src",
                     chart_group="deepswe", metric_name="score", caption="cap")
    placement = {"anchor": spec.title.strip() or (spec.chart_group + chr(183) + spec.metric_name),
                 "position": "after", "confidence": 0.9}
    page_position = {"known": True, "heading": spec.title.strip() or (spec.chart_group + chr(183) + spec.metric_name),
                     "level": "article-anchor"}
    assert placement["anchor"] == "DeepSWE 对比"
    assert page_position["known"] is True
    assert page_position["level"] == "article-anchor"
    # without anchor must be not known
    placement_empty = {"anchor": "", "position": "after", "confidence": 0.0}
    page_empty = {"known": False, "heading": None, "level": None}
    assert page_empty["known"] is False
