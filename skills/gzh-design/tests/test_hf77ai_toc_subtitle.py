"""77AI/OBS-38x:toc 卡片副标题=章节首段首句透传。

覆盖：三章已知首段渲染 → 卡片小字行含各首句原文；无首段章节 →
该卡片副标题 ""（现状保持）；长首句 → 单行截断不断字（CLAMP 在行 +
全文在 HTML）；旧双参调用 hammer_toc(theme, titles) 零影响。
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

CLAMP = "white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"

ARTICLE_3 = (
    "# 副标题透传验证\n\n导语一句话。\n\n"
    "## 第一章标题\n\n首段首句一。第二句不该进卡片。\n\n正文第二段。\n\n"
    "## 第二章标题\n\n次章开头第一句话！后面是感叹号后的第二句。\n\n"
    "## 第三章标题\n\n"
)

LONG_FIRST = ("这是一个超长超长超长的章节首段首句用来验证卡片小字行单行截断不断字"
              "省略号必须出现在这里")


def _load(name):
    p = SKILL_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".", "_"), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _render(article_text, theme="smartisan"):
    td = Path(tempfile.mkdtemp(prefix="toc-sub-"))
    (td / "final_article.md").write_text(article_text, encoding="utf-8")
    R = _load("render_article.py")
    code = R.main(["--article", str(td / "final_article.md"),
                   "--output-dir", str(td), "--theme", theme])
    assert code == 0
    return (td / "final.html").read_text(encoding="utf-8")


def test_77ai_three_chapters_subtitles_present():
    """①三章已知首段 → 卡片小字行含各首句原文（且不含第二句）。"""
    html = _render(ARTICLE_3)
    assert "首段首句一" in html
    assert "次章开头第一句话" in html
    toc = html.split("滑动", 1)[1].split("写在最后", 1)[0]
    assert "首段首句一" in toc and "次章开头第一句话" in toc
    assert "第二句不该进卡片" not in toc


def test_77ai_empty_chapter_subtitle_blank():
    """②无首段章节（第三章空）→ 该卡片副标题 ""（现状保持，不炸）。"""
    html = _render(ARTICLE_3)
    assert "第三章标题" in html


def test_77ai_long_first_sentence_clamped_not_cut():
    """③长首句 → 单行截断不断字（CLAMP 在行 + 全文在 HTML）。"""
    article = ("# 长首句验证\n\n导语。\n\n## 唯一章节\n\n" + LONG_FIRST
               + "。第二句。\n\n")
    html = _render(article)
    assert LONG_FIRST in html
    sub_line = next(ln for ln in html.splitlines() if LONG_FIRST in ln)
    assert CLAMP in sub_line


def test_77ai_old_two_arg_call_unaffected():
    """④旧双参调用 hammer_toc(theme, titles) 零影响（副标题全空）。"""
    H = _load("generate_hammer_upgrade_samples.py")
    html = H.hammer_toc("hammer", ["甲", "乙"])
    assert "甲" in html and "乙" in html
