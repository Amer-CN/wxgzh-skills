"""77B/OBS-310/311:numbers 图表字段归属 + core-card 单格式统一测试。

- OBS-310:chart_group/metric_name/series_label/time_value 归属 claim 级,
  numbers 元素仅 string | {value: number, unit};value 仅 number。
- OBS-311:canonical = `字段: 内容` 同行一行式,validate_single_product 与
  full-mode(validate_article_length --full-mode)同判。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR / "scripts"))

import validate_single_product as VSP  # noqa: E402

VALID_ARTICLE_LENGTH = SCRIPT_DIR / "scripts" / "validate_article_length.py"


def _registry(claims):
    return {"claims": claims,
            "materials": [{"material_id": "M-01", "dedup_id": "d-1",
                           "source_url": "https://src.example/x", "title": "title",
                           "aihot_permalink": "https://src.example/x"}]}


def _claim(numbers, extra=None):
    row = {"claim_id": "C-01", "claim_text": "论点", "material_id": "M-01",
           "source_url": "https://src.example/x", "source_excerpt": "摘录",
           "numbers": numbers}
    row.update(extra or {})
    return row


# ── OBS-310 ──────────────────────────────────────────────────────────────

def test_numbers_chart_fields_claim_level_pass(tmp_path):
    p = tmp_path / "registry.json"
    p.write_text(json.dumps(_registry([_claim(
        [{"value": 150.8, "unit": "元/股"}, "原始摘录"],
        {"chart_group": "ipo-pricing", "metric_name": "发行价",
         "series_label": "宇树", "time_value": "2026-08-19"})]),
        ensure_ascii=False), encoding="utf-8")
    errs, _ = VSP.check_registry(p)
    assert errs == [], errs


def test_numbers_chart_field_inside_array_rejected_with_pointer(tmp_path):
    bad = _claim([{"value": 150.8, "unit": "元/股", "chart_group": "ipo-pricing"}])
    p = tmp_path / "registry.json"
    p.write_text(json.dumps(_registry([bad]), ensure_ascii=False), encoding="utf-8")
    errs, _ = VSP.check_registry(p)
    joined = "\n".join(errs)
    assert "禁止进 numbers 数组" in joined, joined
    assert "77B/OBS-310" in joined, joined


def test_numbers_date_string_in_value_rejected_with_pointer(tmp_path):
    bad = _claim([{"value": "2026-08-19", "unit": "日期"}])
    p = tmp_path / "registry.json"
    p.write_text(json.dumps(_registry([bad]), ensure_ascii=False), encoding="utf-8")
    errs, _ = VSP.check_registry(p)
    joined = "\n".join(errs)
    assert "`value`" in joined and "claim.time_value" in joined, joined


# ── OBS-311 ──────────────────────────────────────────────────────────────

CARD_OK = ("# Core Card\n\n"
           "Core Statement: 一句话核心判断。\n"
           "Reader Change: 读者认知变化。\n"
           "Core Tension: 张力。\n"
           "Value Carrier: 载体。\n"
           "Scope: 适用边界。\n"
           "Result: holds\n")

CARD_BOLD_ONLY = ("# Core Card\n\n"
                  "**Core Statement**\n\n**Reader Change**\n\n"
                  "**Core Tension**\n\n**Value Carrier**\n\n"
                  "**Scope**\n\n**Result**\n")


def test_core_card_canonical_passes_single_product(tmp_path):
    p = tmp_path / "core-card.md"
    p.write_text(CARD_OK, encoding="utf-8")
    errs, _ = VSP.check_core_card(p)
    assert errs == [], errs


def test_core_card_bold_only_rejected_by_single_product(tmp_path):
    p = tmp_path / "core-card.md"
    p.write_text(CARD_BOLD_ONLY, encoding="utf-8")
    errs, _ = VSP.check_core_card(p)
    joined = "\n".join(errs)
    assert joined, "互斥形态(仅 **字段**)必须被拒"
    assert "Core Statement: 内容" in joined, joined


def _full_mode_core_card_verdict(text, tmp_path):
    p = tmp_path / "core-card.md"
    p.write_text(text, encoding="utf-8")
    art = tmp_path / "article.md"
    art.write_text("# t\n\n正文。\n", encoding="utf-8")
    r = subprocess.run([sys.executable, str(VALID_ARTICLE_LENGTH),
                        "--full-mode", "--core-card", str(p), "--article", str(art), "--json"],
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=60)
    return (r.stdout or "") + (r.stderr or "")


def test_core_card_canonical_same_judgement_as_full_mode(tmp_path):
    out = _full_mode_core_card_verdict(CARD_OK, tmp_path)
    assert "Core Statement" not in out, out[-600:]


def test_core_card_bold_only_same_judgement_as_full_mode(tmp_path):
    out = _full_mode_core_card_verdict(CARD_BOLD_ONLY, tmp_path)
    assert "Core Statement" in out and "has no content" in out, out[-600:]
