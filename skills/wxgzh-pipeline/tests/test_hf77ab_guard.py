"""77AB/OBS-378:aihot 双前缀守卫——producers 冒充门双域判定 + 指令锚点 +
双文一致守卫(producers.AIHOT_SITE_PREFIXES == media url_security 同名常量)。

照 77W 两文一致守卫先例(test_hf77w_single_source.py):两子树无法共享
import,以守卫测试钉两文常量一致;producers 冒充门(77Y/OBS-373)防冒充
语义不放松——virxact 与 aihot.news 站内页填 links.original 均拦。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import wxgzh_pipeline.producers as PR

from conftest import SKILL_ROOT

MEDIA_SRC = SKILL_ROOT.parent / "media-enrichment" / "src"
sys.path.insert(0, str(MEDIA_SRC))

from media_enrichment.url_security import (  # noqa: E402
    AIHOT_SITE_PREFIXES as MEDIA_PREFIXES,
)


def _stage_with_items(tmp_path: Path, items) -> Path:
    sd = tmp_path / "aihot"
    sd.mkdir()
    (sd / "deduplicated_items.json").write_text(
        json.dumps(items, ensure_ascii=False), encoding="utf-8")
    return sd


def test_77ab_producers_gate_virxact_entry_passes(tmp_path):
    """①virxact 域条目过 producers 门(站内页归位 links.aihot,original 外站)。"""
    sd = _stage_with_items(tmp_path, [{
        "id": "x-77ab-v", "source_url": "https://blog.example.test/a",
        "links": {"original": "https://blog.example.test/a",
                  "aihot": "https://aihot.virxact.com/items/x-77ab-v"},
    }])
    assert PR._aihot_synthetic_original_check(sd) == []


def test_77ab_producers_gate_aihot_news_entry_passes(tmp_path):
    """②aihot.news 域条目同样过(双前缀核心断言——301 迁移后 news 域站内页
    归位即过,m9coc1 改写场景根除)。"""
    sd = _stage_with_items(tmp_path, [{
        "id": "x-77ab-n", "source_url": "https://blog.example.test/b",
        "links": {"original": "https://blog.example.test/b",
                  "aihot": "https://aihot.news/items/x-77ab-n"},
    }])
    assert PR._aihot_synthetic_original_check(sd) == []


def test_77ab_producers_gate_impersonation_dual_domain_blocked(tmp_path):
    """③冒充仍拦:两域站内页填 links.original 均 FAIL(防冒充语义不放松)。"""
    sd = _stage_with_items(tmp_path, [
        {"id": "x-77ab-n", "source_url": "https://blog.example.test/b",
         "links": {"original": "https://aihot.news/items/x-77ab-n"}},
        {"id": "x-77ab-v", "source_url": "https://blog.example.test/a",
         "links": {"original": "https://aihot.virxact.com/items/x-77ab-v"}},
    ])
    violations = PR._aihot_synthetic_original_check(sd)
    assert len(violations) == 2, violations
    assert all("冒充" in v for v in violations)
    assert any("x-77ab-n" in v for v in violations)   # news 域站内页 → 拦
    assert any("x-77ab-v" in v for v in violations)   # virxact 域站内页 → 同拦


def test_77ab_producers_gate_wired_to_constant():
    """producers 冒充门判定接线到 AIHOT_SITE_PREFIXES(内联单前缀绝版)。"""
    src = (SKILL_ROOT / "wxgzh_pipeline" / "producers.py").read_text(
        encoding="utf-8")
    assert "any(original.startswith(p) for p in AIHOT_SITE_PREFIXES)" in src
    assert 'original.startswith("https://aihot.virxact.com/")' not in src


def test_77ab_instruction_rewrite_ban_anchor():
    """④aihot 指令含 77AB/OBS-378 改写禁令+双前缀单一真源措辞;
    既有 77Y/OBS-373 冒充门措辞不丢失(追加模式,非改写)。"""
    instr = PR.AGENT_INSTRUCTIONS["aihot"]
    assert "77AB/OBS-378" in instr
    assert "virxact 与 aihot.news 双域" in instr
    assert "记录层禁改写上游返回的域名" in instr
    assert "permalink/links 保留原值" in instr
    assert "AIHOT_SITE_PREFIXES" in instr
    assert "守卫测试钉两子树一致" in instr
    # 追加模式:77A/76J/76U 既有义务锚点不丢失
    for keep in ("77A/OBS-307", "76J/OBS-273", "76U/OBS-294"):
        assert keep in instr, f"aihot 旧条文丢失 {keep}"


def test_77ab_dual_tree_prefixes_single_source():
    """⑤双文一致守卫:producers 与 media url_security 常量逐字相等
    (import 两侧比较),且恰含 virxact/aihot.news 两前缀。"""
    assert PR.AIHOT_SITE_PREFIXES == MEDIA_PREFIXES
    assert set(PR.AIHOT_SITE_PREFIXES) == {
        "https://aihot.virxact.com/", "https://aihot.news/"}
