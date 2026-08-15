"""76J 生产暴露小修批测试。

- 任务 1/OBS-272:zh 握手指令含专名明规(Luma Agents/ComfyUI/MiniMax H3 永不
  改写,FT-001 advisory 命中无需处理、不影响交付);
- 任务 3/OBS-271:语法门 probe 对 table/ulist/ulist_star/olist 判「支持」
  (需安装侧新渲染器,不可得时 skip);_body_plain_text 经锚样式测得表格/列表
  文本且控制符不进正文;
- 任务 4a/OBS-273:aihot 指令引用 deduplicated_items.json 字段模板
  (contracts/01_aihot.yaml),字段名/类型文档化;
- 任务 4b/OBS-269 打磨:图注标题清理(站点前缀/「 | 」/「 - 」后缀段/多余冒号)。
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

import wxgzh_pipeline.producers as PR

from conftest import SKILL_ROOT

from wxgzh_pipeline.stages.gzh_design import _body_plain_text


def test_obs272_zh_instruction_product_name_rule():
    instr = PR.AGENT_INSTRUCTIONS["zh_human_writing"]
    assert "产品名/专名中的词永不改写" in instr
    assert "Luma Agents" in instr and "ComfyUI" in instr and "MiniMax H3" in instr
    assert "FT-001 advisory 命中无需处理" in instr
    assert "不影响交付" in instr


def test_obs272_zh_instruction_no_agent_rewrite_ambiguity():
    """消除「见 Agent 就改写」误读空间:任何词形都不得因疑似 AI 味改写。"""
    instr = PR.AGENT_INSTRUCTIONS["zh_human_writing"]
    assert "Agent、agent、Agents" in instr
    assert "不得" in instr and "改写或删除" in instr


def test_obs273_aihot_instruction_references_dedup_template():
    instr = PR.AGENT_INSTRUCTIONS["aihot"]
    assert "deduplicated_items.json" in instr
    assert "contracts/01_aihot.yaml" in instr
    assert "不得自造字段名" in instr


def test_obs273_aihot_contract_declares_template_fields():
    """模板是契约文件内的文档化注释(agent 照此写),读原文断言字段齐全。"""
    text = (SKILL_ROOT / "contracts" / "01_aihot.yaml").read_text(encoding="utf-8")
    for field in ("id", "title", "source_url", "links", "content",
                  "published_at", "category", "score", "selected",
                  "aihot_permalink", "provenance"):
        assert field in text, f"字段模板缺 {field}"
    assert "76J/OBS-273" in text and "deduplicated_items.json" in text


def test_obs271_body_plain_text_measures_table_and_list():
    """锚注册后(component_anchors.json 含 table/list 样式),_body_plain_text
    测得单元格/列表项文本;控制符 `|`/`-` 不进正文(语法门 probe 同语义)。"""
    html = (
        '<section style="margin-bottom:24px;overflow-x:auto;">'
        '<table style="width:100%;border-collapse:collapse;font-size:13px;">'
        "<thead><tr>"
        '<th style="background:#B3593B;color:#fff;font-weight:700;padding:8px 12px;'
        'text-align:left;"><p style="margin:0;font-size:13px;line-height:1.6;'
        'color:#fff;"><span leaf="">S_TABLE_HEADER</span></p></th>'
        "</tr></thead><tbody><tr>"
        '<td style="padding:8px 12px;border-bottom:1px solid rgba(202,202,199,0.18);'
        'color:#555555;"><p style="margin:0;font-size:13px;line-height:1.6;'
        'color:#555555;"><span leaf="">S_TABLE_BODY</span></p></td>'
        "</tr></tbody></table></section>"
        '<section style="margin-bottom:14px;"><p style="margin:0 0 6px;'
        'font-size:13px;line-height:1.6;color:#555555;"><span leaf="">S_LIST_ITEM_UL</span></p></section>'
        '<section style="display:flex;align-items:flex-start;gap:10px;margin-bottom:12px;">'
        '<p style="font-size:14px;color:#555555;margin:0;line-height:1.9;flex:1;">'
        '<span leaf="">S_LIST_ITEM_OL</span></p></section>')
    body = _body_plain_text(html)
    for sent in ("S_TABLE_HEADER", "S_TABLE_BODY", "S_LIST_ITEM_UL", "S_LIST_ITEM_OL"):
        assert sent in body, f"{sent} 应进正文区文本"
    assert "|" not in body and "-" not in body


def test_obs271_real_renderer_probe_table_and_lists_supported(tmp_path):
    """安装侧新渲染器下,语法门 probe 对 table/ulist/ulist_star/olist 判「支持」。
    依赖安装侧渲染器(relock 后为新版),不可得时 skip。"""
    import subprocess
    import sys
    from wxgzh_pipeline import skill_discovery as SD
    from wxgzh_pipeline import paths as P
    try:
        root = P.skills_home(P.resolve_project_root())
    except Exception:
        root = None
    if root is None:
        pytest.skip("skills home 不可得")
    renderer = Path(root) / "gzh-design" / "scripts" / "render_article.py"
    if not renderer.is_file():
        pytest.skip("安装侧渲染器不可得")
    probe_dir = tmp_path / "probe"
    out = tmp_path / "p"; out.mkdir(exist_ok=True)
    md = out / "s.md"
    for key, label, _token, needle, control_line in [
            ("table", "| 表格", "|", "|SENTINEL_A1",
             "| SENTINEL_A1 | 值 |\n| --- | --- |\n"),
            ("ulist", "行首 - 无序列表", "- ", "-SENTINEL_A1", "- SENTINEL_A1\n"),
            ("ulist_star", "行首 * 无序列表", "* ", "*SENTINEL_A1", "* SENTINEL_A1\n"),
            ("olist", "行首 1. 有序列表", "1. ", "1.SENTINEL_A1", "1. SENTINEL_A1\n")]:
        sample = ("# 探针样本\n\n这是导语占位段落，不含任何控制符。\n\n"
                  "## 章节一\n\n" + control_line + "SENTINEL_A2 结尾普通段落。\n")
        d = probe_dir / key
        d.mkdir(parents=True, exist_ok=True)
        md = d / "sample.md"
        md.write_text(sample, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", str(renderer),
             "--article", str(md), "--output-dir", str(d),
             "--theme", "smartisan"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120)
        html = (d / "final.html").read_text(encoding="utf-8") if (d / "final.html").is_file() else ""
        body = _body_plain_text(html)
        assert needle not in body, f"{key}: 控制符残留 {needle}"
        assert "SENTINEL_A1" in body and "SENTINEL_A2" in body, f"{key}: 哨兵缺失"


