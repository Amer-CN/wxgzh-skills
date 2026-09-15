"""77AJ/OBS-387:toc 卡片标题去序号显示（显示副本脱序号）。

覆盖：带序号标题（中文数字/阿拉伯数字）→ 卡片标题无序号+单行 clamp；
无序号标题 → 原样；仅序号（脱空）→ 回退原文；章节标题组件仍带编号；
末卡 PART ///（写在最后）不动；副标题透传（77AI）零影响。
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

CLAMP = "white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"

ARTICLE_NUMBERED = (
    "# 去序号验证\n\n导语一句话。\n\n"
    "## 一、缘起背景\n\n首段首句甲。第二句。\n\n"
    "## 2.选型对比\n\n首段首句乙。第二句。\n\n"
    "## 无序号标题\n\n首段首句丙。第二句。\n\n"
)


def _load(name):
    p = SKILL_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".", "_"), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _render(article_text, theme="smartisan"):
    td = Path(tempfile.mkdtemp(prefix="toc-denum-"))
    (td / "final_article.md").write_text(article_text, encoding="utf-8")
    R = _load("render_article.py")
    code = R.main(["--article", str(td / "final_article.md"),
                   "--output-dir", str(td), "--theme", theme])
    assert code == 0
    return (td / "final.html").read_text(encoding="utf-8")


def test_77aj_numbered_titles_stripped_in_cards():
    """①带序号标题 → 卡片无序号（单行 clamp 在行），末卡不动。"""
    html = _render(ARTICLE_NUMBERED)
    toc = html.split("滑动", 1)[1].split("写在最后", 1)[0]
    assert "缘起背景" in toc and "选型对比" in toc
    assert "一、缘起背景" not in toc and "2.选型对比" not in toc
    title_line = next(ln for ln in html.splitlines() if "缘起背景" in ln)
    assert CLAMP in title_line


def test_77aj_plain_title_unchanged():
    """②无序号标题 → 卡片原样。"""
    html = _render(ARTICLE_NUMBERED)
    toc = html.split("滑动", 1)[1].split("写在最后", 1)[0]
    assert "无序号标题" in toc


def test_77aj_strip_empty_falls_back():
    """③仅序号（脱空）→ 回退原文，不炸。"""
    H = _load("generate_hammer_upgrade_samples.py")
    assert H._toc_display_title("一、") == "一、"
    assert H._toc_display_title("2. ") == "2. "


def test_77aj_chapter_body_keeps_numbers():
    """④章节标题组件仍带编号（LT-004 只删卡片显示，章节数据不动）。"""
    html = _render(ARTICLE_NUMBERED)
    body = html.split("写在最后", 1)[1]
    assert "一、缘起背景" in body and "2.选型对比" in body
