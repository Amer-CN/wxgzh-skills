#!/usr/bin/env python3
"""toc-scroll 卡片单行截断回归：标题/副标题再长只占一行（省略号截断）。"""
import importlib.util
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

CLAMP = "white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"

LONG_TITLES = [
    "这是一个超级无敌长的章节标题用来验证单行截断第一章内容足够长",
    "第二章标题同样很长很长很长长到必须单行显示不能换行臃肿卡片",
    "第三章标题也是超长超长超长的一行大标题验证等高不臃肿的效果",
]

ARTICLE = (
    "# 单行截断验证文章\n\n导语一句话。\n\n"
    + "".join(f"## {t}\n\n本章正文一句话。\n\n" for t in LONG_TITLES)
)

LONG_SUBTITLE = "这是一个超长的副标题输入用来验证PART三斜杠卡片副标题同样单行截断不换行"


def _load(name):
    p = SKILL_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".", "_"), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _render(article_text):
    td = Path(tempfile.mkdtemp(prefix="toc-single-"))
    (td / "final_article.md").write_text(article_text, encoding="utf-8")
    R = _load("render_article.py")
    code = R.main(["--article", str(td / "final_article.md"),
                   "--output-dir", str(td), "--theme", "smartisan"])
    assert code == 0
    return (td / "final.html").read_text(encoding="utf-8")


class TestTocCardSingleLine:
    def test_long_titles_preserved_and_clamped(self):
        html = _render(ARTICLE)
        for t in LONG_TITLES:
            assert t in html
        assert html.count(CLAMP) >= 8

    def test_part_slash_subtitle_single_line(self):
        H = _load("generate_hammer_upgrade_samples.py")
        html = H._toc_card(H.PALETTES["hammer"], "PART ///", "写在最后",
                           LONG_SUBTITLE, highlight=False)
        assert LONG_SUBTITLE in html
        sub_line = next(
            ln for ln in html.splitlines() if LONG_SUBTITLE in ln)
        assert CLAMP in sub_line
