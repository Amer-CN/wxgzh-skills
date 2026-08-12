"""76J/OBS-271:标准 Markdown 表格与无序/有序列表的解析与渲染。

- parse_article:表格块(首行 header + 分隔行跳过)、`- `/`* ` 无序列表、
  `1. ` 有序列表聚块为独立 item;
- 渲染:表格走官方 11f 样式(theme-hammer.md),无序列表走 11a pill-list,
  有序列表走 11g ordered-list;
- 语法门视角:控制符(`|`、`-`、`1.`)不得原样进入正文文本,哨兵文本必须
  完整出现(与 validators/validate_syntax_gate.py 的 probe 判据同语义)。
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from render_article import parse_article  # noqa: E402

RENDER = SKILL_ROOT / "scripts" / "render_article.py"


def _run_cli(article_text: str, timeout=300):
    td = Path(tempfile.mkdtemp(prefix="render-tbl-"))
    article = td / "article.md"
    article.write_text(article_text, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(RENDER),
         "--article", str(article), "--output-dir", str(td), "--theme", "smartisan"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout)
    html = (td / "final.html").read_text(encoding="utf-8") if (td / "final.html").is_file() else ""
    return proc, html


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", "", html)
    return re.sub(r"\s+", "", text)


# ── parse_article ───────────────────────────────────────────────

def test_parse_table_with_separator():
    md = "# 标题\n\n导语。\n\n## 章节\n\n| 列A | 列B |\n| --- | --- |\n| 甲 | 1 |\n| 乙 | 2 |\n"
    parsed = parse_article(md)
    items = parsed["chapters"][0]["paras"]
    tables = [i for i in items if i.get("kind") == "table"]
    assert len(tables) == 1, items
    t = tables[0]
    assert t["header"] == ["列A", "列B"]
    assert t["rows"] == [["甲", "1"], ["乙", "2"]]


def test_parse_ulist_and_olist():
    md = ("# 标题\n\n导语。\n\n## 章节\n\n- 第一项\n- 第二项\n\n"
          "1. 步骤一\n2. 步骤二\n\n结尾。\n")
    parsed = parse_article(md)
    paras = parsed["chapters"][0]["paras"]
    lists = [i for i in paras if i.get("kind") == "list"]
    assert len(lists) == 2, paras
    ul, ol = lists
    assert ul["ordered"] is False and ul["items"] == ["第一项", "第二项"]
    assert ol["ordered"] is True and ol["items"] == ["步骤一", "步骤二"]


def test_parse_ulist_star_and_intro_list():
    md = "# 标题\n\n- 导语项\n\n## 章节\n\n* 星号项\n"
    parsed = parse_article(md)
    intro_lists = [i for i in parsed["intro_paras"] if i.get("kind") == "list"]
    assert intro_lists and intro_lists[0]["items"] == ["导语项"]
    ch_lists = [i for i in parsed["chapters"][0]["paras"] if i.get("kind") == "list"]
    assert ch_lists and ch_lists[0]["items"] == ["星号项"]


# ── render ──────────────────────────────────────────────────────

def test_render_table_no_control_char_in_body():
    md = ("# 标题\n\n导语。\n\n## 章节\n\n"
          "| SENTINEL_A1 | 值 |\n| --- | --- |\n| 甲 | 1 |\n")
    proc, html = _run_cli(md)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "<table" in html and "<th" in html and "<td" in html
    body = _strip_html(html)
    assert "SENTINEL_A1" in body
    assert "|SENTINEL_A1" not in body and "|" not in body


def test_render_ulist_pill_and_olist_numbered():
    md = ("# 标题\n\n导语。\n\n## 章节\n\n"
          "- SENTINEL_A1\n- 第二项\n\n"
          "1. SENTINEL_A1\n2. 第二项\n")
    proc, html = _run_cli(md)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "border-radius:999px" in html, "无序列表应走 11a pill-list"
    assert "width:22px" in html and "border-radius:50%" in html, "有序列表应走 11g"
    body = _strip_html(html)
    assert "SENTINEL_A1" in body
    assert "-SENTINEL_A1" not in body
    # 有序项文本在 flex:1 的项 p 内(编号圆点是 p 外独立 span,门禁按 p 提取正文)
    ol_item = re.search(
        r'<p style="font-size:14px;color:#555555;margin:0;line-height:1.9;flex:1;">(.*?)</p>', html)
    assert ol_item and _strip_html(ol_item.group(1)) == "SENTINEL_A1"


def test_render_gate_probe_sample_semantics():
    """与 validators/validate_syntax_gate.py 的 table/ulist probe 样本同构:
    控制符不进正文、哨兵完整出现(该文件用 gzh_design._body_plain_text 实测,
    本测试用去标签归一化正文做同语义验证)。"""
    for control_line in ("| SENTINEL_A1 | 值 |\n| --- | --- |",
                         "- SENTINEL_A1",
                         "* SENTINEL_A1",
                         "1. SENTINEL_A1"):
        md = "# 探针样本\n\n这是导语占位段落，不含任何控制符。\n\n## 章节一\n\n" \
             + control_line + "\n\nSENTINEL_A2 结尾普通段落。\n"
        proc, html = _run_cli(md)
        assert proc.returncode == 0, (control_line, proc.stdout + proc.stderr)
        body = _strip_html(html)
        assert "SENTINEL_A1" in body, control_line
        assert "SENTINEL_A2" in body, control_line
        if control_line.startswith("|"):
            assert "|" not in body, control_line
        elif control_line.startswith("- ") or control_line.startswith("* "):
            assert "-SENTINEL_A1" not in body and "*SENTINEL_A1" not in body, control_line
        elif control_line.startswith("1. "):
            ol_item = re.search(
                r'<p style="font-size:14px;color:#555555;margin:0;line-height:1.9;flex:1;">(.*?)</p>', html)
            assert ol_item and _strip_html(ol_item.group(1)) == "SENTINEL_A1", control_line
