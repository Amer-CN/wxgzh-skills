"""Chart generator module.

Generates original data charts from canonical claim numbers.
3 chart types: bar, comparison, timeline.

dev5 gating (fail-closed):
- A data point is chartable ONLY when its claim carries explicit
  chart_group + metric_name + series_label fields.
- bar/comparison require: same chart_group, same metric_name, same unit,
  >= 2 data points, complete traceability.
- Cross-benchmark values are NEVER merged, even when units are identical
  or empty ("incompatible chart group").
- timeline requires a real time_value on EVERY data point; input order is
  never used as a fake time axis.
- Chart title/caption/alt describe the full chart_group and all series,
  never a single claim text.
Only reads claims[].numbers. Fail-closed on incomparable data.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from .image_inspector import ImageInspection, inspect_image, compute_sha256


@dataclass
class ChartDataPoint:
    """A single data point with full traceability."""
    label: str            # series_label from the claim
    value: float
    unit: str
    claim_id: str
    material_id: str
    source_url: str
    source_excerpt: str
    chart_group: str = ""
    metric_name: str = ""
    time_value: str = ""


@dataclass
class ChartSpec:
    """Specification for a chart."""
    chart_type: str  # "bar", "comparison", "timeline"
    title: str
    data_points: list[ChartDataPoint]
    unit: str
    y_axis_label: str
    x_axis_label: str
    source_note: str
    chart_group: str = ""
    metric_name: str = ""
    caption: str = ""


@dataclass
class ChartBuildResult:
    """Result of chart spec building: specs + fail-closed warnings."""
    specs: list[ChartSpec] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ChartGenerationResult:
    """Result of chart generation."""
    success: bool = False
    chart_path: str = ""
    sha256: str = ""
    inspection: ImageInspection | None = None
    spec: ChartSpec | None = None
    data_traceability: list[dict[str, str]] = field(default_factory=list)
    error: str = ""


def extract_numbers_from_claim(claim: dict[str, Any]) -> list[tuple[str, float, str]]:
    """Extract numeric values from claim's numbers field."""
    results: list[tuple[str, float, str]] = []
    for number in claim.get("numbers", []):
        if isinstance(number, dict):
            value = number.get("value")
            unit = str(number.get("unit", ""))
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                results.append((f"{value}{unit}", float(value), unit))
            continue
        parsed = _parse_number_string(number)
        if parsed:
            results.append(parsed)
    return results


def _parse_number_string(s: str) -> tuple[str, float, str] | None:
    """Parse a number string into (raw, value, unit)."""
    if not isinstance(s, str):
        return None
    s = s.strip()
    if not s:
        return None

    pct_match = re.match(r'^(\d+\.?\d*)\s*%$', s)
    if pct_match:
        return (s, float(pct_match.group(1)), "%")

    currency_match = re.match(r'^[\$￥€£]\s*(\d+\.?\d*)$', s)
    if currency_match:
        return (s, float(currency_match.group(1)), "currency")

    plain_match = re.match(r'^(\d+\.?\d*)$', s)
    if plain_match:
        return (s, float(plain_match.group(1)), "")

    mag_match = re.match(r'^(\d+\.?\d*)\s*(亿|万|千|百|million|billion|thousand)$', s, re.IGNORECASE)
    if mag_match:
        return (s, float(mag_match.group(1)), mag_match.group(2))

    return None


def check_comparability(data_points: list[ChartDataPoint]) -> tuple[bool, str]:
    """Check if data points are comparable for a bar/comparison chart.

    dev5 rules: same non-empty chart_group, same non-empty metric_name,
    same unit (may be empty but must be identical), >= 2 points,
    complete traceability, non-empty series labels.
    """
    if len(data_points) < 2:
        group = data_points[0].chart_group if data_points else ""
        return False, f"incompatible chart group '{group}': need at least 2 data points"

    groups = set(dp.chart_group for dp in data_points)
    if "" in groups or len(groups) > 1:
        return False, f"incompatible chart group: chart_group values {sorted(groups)!r} (missing or mixed benchmark groups must not be merged)"

    metrics = set(dp.metric_name for dp in data_points)
    if "" in metrics or len(metrics) > 1:
        return False, f"incompatible chart group '{data_points[0].chart_group}': metric_name values {sorted(metrics)!r} (missing or mixed metrics must not be merged)"

    units = set(dp.unit for dp in data_points)
    if len(units) > 1:
        return False, f"incompatible chart group '{data_points[0].chart_group}': mixed units {sorted(units)!r}"

    for dp in data_points:
        if not dp.claim_id or not dp.material_id or not dp.source_url:
            return False, f"incompatible chart group '{dp.chart_group}': data point '{dp.label}' missing traceability"
        if not dp.label:
            return False, f"incompatible chart group '{dp.chart_group}': data point for claim '{dp.claim_id}' missing series_label"
    return True, ""


def check_timeline_eligibility(data_points: list[ChartDataPoint]) -> tuple[bool, str]:
    """Timeline requires a real time_value on EVERY point (never input order)."""
    comparable, reason = check_comparability(data_points)
    if not comparable:
        return False, reason
    missing = [dp.claim_id for dp in data_points if not (dp.time_value or "").strip()]
    if missing:
        return False, (f"timeline skipped for chart group '{data_points[0].chart_group}': "
                       f"data points {missing} lack a real time_value (input order must not be used as a time axis)")
    return True, ""


def group_claims_for_charts(
    claims: list[dict[str, Any]],
    materials_by_id: dict[str, dict[str, Any]],
) -> tuple[dict[tuple[str, str, str], list[ChartDataPoint]], list[str]]:
    """Group chartable data points by (chart_group, metric_name, unit).

    Claims that carry numbers but no explicit chart_group/metric_name/
    series_label are skipped fail-closed with a warning.
    """
    groups: dict[tuple[str, str, str], list[ChartDataPoint]] = {}
    warnings: list[str] = []

    for claim in claims:
        numbers = extract_numbers_from_claim(claim)
        if not numbers:
            continue
        chart_group = (claim.get("chart_group") or "").strip()
        metric_name = (claim.get("metric_name") or "").strip()
        series_label = (claim.get("series_label") or "").strip()
        if not chart_group or not metric_name or not series_label:
            warnings.append(
                f"chart skipped: incompatible chart group for claim '{claim.get('claim_id', '?')}' "
                f"(numbers present but chart_group/metric_name/series_label not declared — "
                f"cross-benchmark merging by unit alone is forbidden)")
            continue

        mat = materials_by_id.get(claim.get("material_id", ""), {})
        declared_unit = (claim.get("unit") or "").strip()
        for raw, value, unit in numbers:
            effective_unit = unit or declared_unit
            dp = ChartDataPoint(
                label=series_label,
                value=value,
                unit=effective_unit,
                claim_id=claim.get("claim_id", ""),
                material_id=claim.get("material_id", ""),
                source_url=claim.get("source_url", mat.get("source_url", "")),
                source_excerpt=claim.get("source_excerpt", ""),
                chart_group=chart_group,
                metric_name=metric_name,
                time_value=(claim.get("time_value") or "").strip(),
            )
            groups.setdefault((chart_group, metric_name, effective_unit), []).append(dp)

    return groups, warnings


def _group_caption(chart_group: str, metric_name: str, dps: list[ChartDataPoint]) -> str:
    """Caption/alt text covering the FULL chart group — never one claim text."""
    parts = "；".join(f"{dp.label} {dp.value}{dp.unit}" for dp in dps)
    return f"{chart_group}·{metric_name}对比（共{len(dps)}项）：{parts}"


def build_chart_specs(
    claims: list[dict[str, Any]],
    materials_by_id: dict[str, dict[str, Any]],
) -> ChartBuildResult:
    """Build chart specifications with dev5 fail-closed gating.

    Returns ChartBuildResult(specs, warnings). Incomparable groups produce
    warnings, never charts.
    """
    groups, warnings = group_claims_for_charts(claims, materials_by_id)
    result = ChartBuildResult(warnings=warnings)

    for (chart_group, metric_name, unit), dps in groups.items():
        comparable, reason = check_comparability(dps)
        if not comparable:
            result.warnings.append(f"chart skipped: {reason}")
            continue

        y_label = f"{metric_name} ({unit})" if unit else metric_name
        source_note = "数据来源：Super Writer canonical claims"
        title = f"{chart_group}：{metric_name}对比"
        caption = _group_caption(chart_group, metric_name, dps)

        result.specs.append(ChartSpec(
            chart_type="bar", title=title, data_points=dps, unit=unit,
            y_axis_label=y_label, x_axis_label="", source_note=source_note,
            chart_group=chart_group, metric_name=metric_name, caption=caption,
        ))
        result.specs.append(ChartSpec(
            chart_type="comparison", title=title, data_points=dps, unit=unit,
            y_axis_label=y_label, x_axis_label="", source_note=source_note,
            chart_group=chart_group, metric_name=metric_name, caption=caption,
        ))

        # timeline: per-group only, and only with a real time_value on every point
        timeline_ok, timeline_reason = check_timeline_eligibility(dps)
        if timeline_ok:
            tl_dps = sorted(dps, key=lambda d: d.time_value)
            result.specs.append(ChartSpec(
                chart_type="timeline", title=f"{chart_group}：{metric_name}时间线",
                data_points=tl_dps, unit=unit,
                y_axis_label=y_label, x_axis_label="时间", source_note=source_note,
                chart_group=chart_group, metric_name=metric_name,
                caption=_group_caption(chart_group, metric_name, tl_dps),
            ))
        else:
            result.warnings.append(timeline_reason)

    return result


def generate_chart(spec: ChartSpec, output_path: str | Path, max_pixels: int = 40_000_000) -> ChartGenerationResult:
    """Generate a PNG chart from a ChartSpec (re-enforces dev5 gating)."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = ChartGenerationResult(spec=spec)

    comparable, reason = check_comparability(spec.data_points)
    if not comparable:
        result.error = f"data not comparable: {reason}"
        return result

    if spec.chart_type == "timeline":
        timeline_ok, timeline_reason = check_timeline_eligibility(spec.data_points)
        if not timeline_ok:
            result.error = f"data not comparable: {timeline_reason}"
            return result

    try:
        cjk_fonts = [f.name for f in fm.fontManager.ttflist if any(
            kw in f.name.lower()
            for kw in ["simhei", "simsun", "microsoft yahei", "noto sans cjk", "wenquanyi", "droid sans fallback"]
        )]
        if cjk_fonts:
            plt.rcParams["font.sans-serif"] = [cjk_fonts[0]] + plt.rcParams.get("font.sans-serif", [])
        plt.rcParams["axes.unicode_minus"] = False

        fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
        labels = [dp.label[:20] + "..." if len(dp.label) > 20 else dp.label for dp in spec.data_points]
        values = [dp.value for dp in spec.data_points]

        if spec.chart_type == "bar":
            bars = ax.bar(labels, values, color=["#4472C4", "#ED7D31", "#A5A5A5", "#FFC000", "#5B9BD5"][:len(values)])
            ax.set_ylabel(spec.y_axis_label)
            ax.set_title(spec.title, fontsize=14, fontweight="bold")
            for bar, dp in zip(bars, spec.data_points):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width() / 2., height,
                        f"{dp.value}{dp.unit}", ha="center", va="bottom", fontsize=10)

        elif spec.chart_type == "comparison":
            bars = ax.barh(labels, values, color=["#4472C4", "#ED7D31", "#A5A5A5", "#FFC000", "#5B9BD5"][:len(values)])
            ax.set_xlabel(spec.y_axis_label)
            ax.set_title(spec.title, fontsize=14, fontweight="bold")
            for bar, dp in zip(bars, spec.data_points):
                width = bar.get_width()
                ax.text(width, bar.get_y() + bar.get_height() / 2.,
                        f" {dp.value}{dp.unit}", ha="left", va="center", fontsize=10)

        elif spec.chart_type == "timeline":
            # Real timeline: x axis = real time_value labels (points pre-sorted)
            x_positions = list(range(len(values)))
            time_labels = [f"{dp.time_value}\n{dp.label[:12]}" for dp in spec.data_points]
            ax.plot(x_positions, values, marker="o", linewidth=2, markersize=8, color="#4472C4")
            ax.set_xticks(x_positions)
            ax.set_xticklabels(time_labels, rotation=30, ha="right", fontsize=9)
            ax.set_ylabel(spec.y_axis_label)
            ax.set_xlabel(spec.x_axis_label)
            ax.set_title(spec.title, fontsize=14, fontweight="bold")
            ax.grid(True, axis="y", alpha=0.3)
            for i, dp in enumerate(spec.data_points):
                ax.annotate(f"{dp.value}{dp.unit}",
                           (i, dp.value), textcoords="offset points",
                           xytext=(0, 10), ha="center", fontsize=9)

        else:
            result.error = f"unknown chart type: {spec.chart_type}"
            plt.close(fig)
            return result

        fig.text(0.05, 0.01, spec.source_note, fontsize=8, color="gray", transform=fig.transFigure)
        legend_parts = [f"{dp.label[:15]}: {dp.source_url[:50]}" for dp in spec.data_points[:3]]
        if legend_parts:
            fig.text(0.99, 0.01, " | ".join(legend_parts), fontsize=6, color="gray", ha="right", transform=fig.transFigure)

        plt.tight_layout(rect=[0, 0.03, 1, 1])
        fig.savefig(str(output_path), format="png", bbox_inches="tight")
        plt.close(fig)

    except Exception as exc:
        result.error = f"chart generation failed: {exc}"
        plt.close("all")
        return result

    inspection = inspect_image(output_path, max_pixels)
    result.inspection = inspection
    result.chart_path = str(output_path)
    result.sha256 = inspection.sha256

    for dp in spec.data_points:
        result.data_traceability.append({
            "label": dp.label, "value": dp.value, "unit": dp.unit,
            "claim_id": dp.claim_id, "material_id": dp.material_id,
            "source_url": dp.source_url, "source_excerpt": dp.source_excerpt,
            "chart_group": dp.chart_group, "metric_name": dp.metric_name,
            "time_value": dp.time_value,
        })

    result.success = True
    return result
