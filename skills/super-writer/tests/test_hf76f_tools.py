"""76F/OBS-277/278:单产物预校验 + 大纲预算自动对齐工具测试。"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPT_DIR / "scripts"))

from align_outline_budget import align_outline, parse_sections  # noqa: E402
import validate_single_product as VSP  # noqa: E402

OUTLINE_OK = """# Outline

## 文章配置
- article_mode: medium
- length_mode: standard
- target_visible_chars: 3000
- acceptable_min: 2700
- acceptable_max: 3300
- planned_total_chars: 3000

## 第一节
- weight_percent: 60
- planned_chars: 1800
- minimum_chars: 1500
- maximum_chars: 2100
- evidence_ids: [e-1]
- event_ids: [ev-1]
- unique_information_goal: 目标甲

## 第二节
- weight_percent: 40
- planned_chars: 1200
- minimum_chars: 1000
- maximum_chars: 1400
- evidence_ids: [e-2]
- event_ids: [ev-2]
- unique_information_goal: 目标乙
"""


def test_align_outline_scales_to_target_and_preserves_protected():
    new_text, info, errors = align_outline(OUTLINE_OK, 6000)
    assert not errors
    assert info["total_new"] == 6000
    assert info["deviation"] == 0.0
    # 保护域:evidence_ids / event_ids / unique_information_goal 不动;
    # 76W/OBS-300:weight_percent 与 planned_chars 原子同步(两节各 1 evidence → 50.0/50.0)
    assert "- weight_percent: 50.0" in new_text
    assert "- evidence_ids: [e-1]" in new_text
    assert "- event_ids: [ev-1]" in new_text
    assert "- unique_information_goal: 目标甲" in new_text
    assert "target_visible_chars: 3000" in new_text  # 配置节不动
    # 76V/OBS-297:分节加权预算——两节各 1 evidence(等密度)→ 均分 3000/3000
    sections = parse_sections(new_text)
    assert sections[0]["planned"] == 3000
    assert sections[1]["planned"] == 3000
    assert info["allocation_mode"] == "evidence_weighted"
    assert info["tolerance"] == "±5%"


def test_align_outline_reaches_target_minus_five():
    new_text, info, errors = align_outline(OUTLINE_OK, 2850)
    assert not errors
    # 2850 对齐后偏差 = 0;两节等 evidence → 各 1425
    assert info["total_new"] == 2850
    sections = parse_sections(new_text)
    assert sections[0]["planned"] == 1425
    assert sections[1]["planned"] == 1425


def test_validate_single_product_outline(tmp_path):
    bad = tmp_path / "outline_bad.md"
    bad.write_text("# Outline\n## 第一节\n- weight_percent: 50\n", encoding="utf-8")
    errors, _ = VSP.check_outline(bad)
    assert errors and any("缺" in e or "无有效" in e for e in errors)

    ok = tmp_path / "outline_ok.md"
    ok.write_text(OUTLINE_OK, encoding="utf-8")
    errors, checks = VSP.check_outline(ok, 3000)
    assert not errors
    assert checks["deviation"] == 0.0

    drifted = tmp_path / "outline_drift.md"
    drifted.write_text(OUTLINE_OK.replace("planned_chars: 1800", "planned_chars: 2400"),
                       encoding="utf-8")
    errors, _ = VSP.check_outline(drifted, 3000)
    assert any("align_outline_budget" in e for e in errors)


def test_validate_single_product_core_card(tmp_path):
    p = tmp_path / "core-card.md"
    p.write_text("## Core Card\n\n- **Core Statement**：x\n", encoding="utf-8")
    errors, _ = VSP.check_core_card(p)
    assert any("Reader Change" in e for e in errors)
    p.write_text("## Core Card\n\n" + "".join(
        f"- **{f}**：x\n" for f in VSP.CORE_CARD_FIELDS), encoding="utf-8")
    errors, _ = VSP.check_core_card(p)
    assert not errors


def test_validate_single_product_semantic_map(tmp_path):
    p = tmp_path / "semantic-map.yaml"
    p.write_text("schema_version: '1.0'\narticle:\n  title: ''\n", encoding="utf-8")
    errors, _ = VSP.check_semantic_map(p)
    assert any("blocks" in e for e in errors)
    assert any("article.title" in e for e in errors)
    p.write_text("schema_version: '1.0'\narticle:\n  title: T\nblocks: []\n",
                 encoding="utf-8")
    errors, _ = VSP.check_semantic_map(p)
    assert not errors


def test_validate_single_product_handoff(tmp_path):
    p = tmp_path / "handoff.yaml"
    p.write_text("schema_version: '2.2'\n", encoding="utf-8")
    errors, _ = VSP.check_handoff(p)
    # 76Q/OBS-285:与 full-mode 同构——顶层必须 {handoff: {...}} 双层包裹,单层平铺直接拒。
    assert any("顶层必须是 {handoff: {...}}" in e for e in errors)
    good = """handoff:
  schema_version: "2.2"
  prose_craft_applied: true
  prose_craft_version: "1.0"
  title_candidates: ["A", "B"]
  hook_line: "钩子"
  selected_title: "A"
  title_selection_reason: "具体"
  formatter:
    cover:
      kicker: null
      strike: null
      tags: null
"""
    p.write_text(good, encoding="utf-8")
    errors, _ = VSP.check_handoff(p)
    assert not errors


def test_validate_single_product_registry(tmp_path):
    p = tmp_path / "registry.json"
    p.write_text(json.dumps([{"claim_id": "c1", "claim_text": "t",
                              "material_id": "m1"}]), encoding="utf-8")
    errors, _ = VSP.check_registry(p)
    # 76Q/OBS-287:registry 真实形状 = dict {claims, materials},数组形状直接拒。
    assert any("顶层必须是对象" in e for e in errors)
    p.write_text(json.dumps({
        "claims": [{"claim_id": "c1", "claim_text": "t", "material_id": "m1",
                    "source_url": "https://x.ai/a", "source_excerpt": "s"}],
        "materials": [{"material_id": "m1", "dedup_id": "d1",
                       "source_url": "https://x.ai/a"}],
    }), encoding="utf-8")
    errors, _ = VSP.check_registry(p)
    assert not errors


def test_tools_cli_exit_codes(tmp_path):
    ok = tmp_path / "outline_ok.md"
    ok.write_text(OUTLINE_OK, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-X", "utf8",
         str(SCRIPT_DIR / "scripts" / "validate_single_product.py"),
         "--product", "outline", "--file", str(ok)],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    data = json.loads(proc.stdout)
    assert data["valid"] is True

    align = subprocess.run(
        [sys.executable, "-X", "utf8",
         str(SCRIPT_DIR / "scripts" / "align_outline_budget.py"),
         "--outline", str(ok), "--target-visible-chars", "6000"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert align.returncode == 0, align.stdout + align.stderr
    info = json.loads(align.stdout)
    assert info["total_new"] == 6000
    # 对齐后单文件校验通过
    proc2 = subprocess.run(
        [sys.executable, "-X", "utf8",
         str(SCRIPT_DIR / "scripts" / "validate_single_product.py"),
         "--product", "outline", "--file", str(ok),
         "--target-visible-chars", "6000"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert proc2.returncode == 0, proc2.stdout + proc2.stderr
