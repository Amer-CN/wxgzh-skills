"""档45R OBS-73 content-fidelity guard tests (replaces 档40 line-count guard).

The renderer now emits every intro paragraph, so multi-line intros are LEGAL;
the guard asserts CONTENT fidelity: paragraph text must exist in the rendered
plain text (first line: 40-char prefix; later lines: full, whitespace-normalized).
The three archived RUN articles are exercised end-to-end in 档45R step 4 (offline
re-render); here we unit-test the guard's logic incl. FAIL paths.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from wxgzh_pipeline.stages.gzh_design import (
    _INTRO_MAX_LEN,
    _html_to_plain_text,
    _intro_content_fidelity,
    _intro_paras,
)

MULTI_INTRO = """# 标题

第一行导语。

第二行导语段落。

第三行导语段落。

## 第一章

章节正文。
"""


def _html_with(paras: list[str]) -> str:
    return "".join(f"<section><p>{p}</p></section>" for p in paras) + "<p>PART 01</p>"


class TestIntroParas:
    def test_paras_extraction_matches_renderer_region(self):
        assert _intro_paras(MULTI_INTRO) == ["第一行导语。", "第二行导语段落。", "第三行导语段落。"]

    def test_single_intro_still_parsed(self):
        assert _intro_paras("# T\n\n导语。\n\n## 一\n\n正文\n") == ["导语。"]


class TestContentFidelity:
    def test_all_paragraphs_present_passes(self):
        report = _intro_content_fidelity(MULTI_INTRO, _html_with(
            ["第一行导语。", "第二行导语段落。", "第三行导语段落。"]))
        assert report["ok"] is True
        assert report["intro_line_count"] == 3

    def test_first_line_truncated_to_prefix_passes(self):
        # oneliner keeps the first 40 chars; the full line need not appear
        long_first = "甲" * 100
        md = f"# T\n\n{long_first}\n\n第二段。\n\n## 一\n\n正文\n"
        report = _intro_content_fidelity(
            md, _html_with([long_first[:_INTRO_MAX_LEN], "第二段。"]))
        assert report["ok"] is True

    def test_missing_second_paragraph_fails_with_full_text(self):
        md = "# T\n\n第一行。\n\n被吞掉的第二段。\n\n## 一\n\n正文\n"
        report = _intro_content_fidelity(md, _html_with(["第一行。"]))
        assert report["ok"] is False
        assert "被吞掉的第二段。" in report["missing_text"]
        assert report["intro_line_count"] == 2
        assert report["guidance"]

    def test_missing_first_line_prefix_fails(self):
        md = "# T\n\n第一行导语。\n\n## 一\n\n正文\n"
        report = _intro_content_fidelity(md, _html_with(["完全不相关"]))
        assert report["ok"] is False
        assert "第一行导语。" in report["missing_text"]

    def test_html_entities_and_whitespace_normalized(self):
        md = "# T\n\n第一行 & 第二行。\n\n## 一\n\n正文\n"
        html = "<p>第一行 &amp;  第二行。</p><p>PART 01</p>"
        report = _intro_content_fidelity(md, html)
        assert report["ok"] is True

    def test_plain_text_extraction(self):
        assert _html_to_plain_text("<p>a &amp; b</p><pre>  c\n d </pre>") == "a&bcd"


class TestThreeArchivedRunShape:
    """The three archived RUNs' intro shapes (档40 documented): 2 / 1x198 / 8
    lines. With the NEW renderer all become legal — the guard only requires the
    rendered text to contain them. Shape-level sanity checks only here; the
    end-to-end PASS is 档45R step 4."""

    def test_run1_two_paras_shape(self):
        paras = _intro_paras(Path(r"F:\AIXM\wxgzh\repos\wxgzh-pipeline\audit\runs\20260731T135947-ai-bbg4al\stages\zh_human_writing\final_article.md").read_text(encoding="utf-8"))
        assert len(paras) == 2

    def test_run2_single_long_para_shape(self):
        paras = _intro_paras(Path(r"F:\AIXM\wxgzh\repos\wxgzh-pipeline\audit\runs\20260801T182628-topic-ui5f7p\stages\zh_human_writing\final_article.md").read_text(encoding="utf-8"))
        assert len(paras) == 1 and sum(len(p) for p in paras) == 198

    def test_event_run_eight_paras_shape(self):
        paras = _intro_paras(Path(r"F:\AIXM\wxgzh\repos\wxgzh-pipeline\audit\runs\20260801T231452-vibe-coding-guide-v2-1-1vg6jx\zh_human_writing\final_article.md").read_text(encoding="utf-8"))
        assert len(paras) == 8
