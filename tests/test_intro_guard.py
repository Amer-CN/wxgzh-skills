"""OBS-73/OBS-83 content-fidelity guard tests (档51, hammer.3 semantics).

The guard inspects the BODY region only (hammer_para paragraphs + <pre> blocks);
EVERY intro paragraph — including the FIRST line — must be present IN FULL.
A cover-subtitle/oneliner occurrence does NOT count (档50 regression: the old
whole-HTML check passed while the first line lived only in the cover).
"""
from __future__ import annotations

from pathlib import Path

from wxgzh_pipeline.stages.gzh_design import (
    _body_plain_text,
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


def _html_with_body(paras: list[str]) -> str:
    body = "".join(
        f'<section style="margin:0 20px;"><p style="margin-bottom:16px;font-size:14px;'
        f'line-height:1.9;text-align:justify;color:#555555;"><span leaf="">{p}</span></p></section>'
        for p in paras)
    return f'<p style="font-size:24px;font-weight:900;">封面副标题占位</p>' + body + '<p>PART 01</p>'


class TestBodyPlainText:
    def test_only_body_paras_and_pre_are_extracted(self):
        html = ('<p style="font-size:24px;">封面不该出现</p>'
                '<section style="margin:0 20px;"><p style="margin-bottom:16px;font-size:14px;'
                'line-height:1.9;text-align:justify;color:#555;">正文段</p></section>'
                '<pre style="white-space:pre;">code  x</pre>'
                '<p>签名不该出现</p>')
        text = _body_plain_text(html)
        assert "正文段" in text and "codex" in text  # whitespace-normalized
        assert "封面不该出现" not in text and "签名不该出现" not in text


class TestContentFidelity:
    def test_all_paragraphs_including_first_in_body_passes(self):
        report = _intro_content_fidelity(MULTI_INTRO, _html_with_body(
            ["第一行导语。", "第二行导语段落。", "第三行导语段落。"]))
        assert report["ok"] is True
        assert report["intro_line_count"] == 3

    def test_first_line_only_in_cover_fails(self):
        # OBS-83: cover occurrence must NOT satisfy the first line
        html = ('<p style="font-size:24px;font-weight:900;">第一行导语。</p>'
                + _html_with_body(["第二行导语段落。", "第三行导语段落。"]))
        report = _intro_content_fidelity(MULTI_INTRO, html)
        assert report["ok"] is False
        assert "第一行导语。" in report["missing_text"]

    def test_first_line_200_chars_in_body_passes(self):
        md = "# T\n\n" + "甲" * 200 + "。\n\n## 一\n\n正文。\n"
        report = _intro_content_fidelity(md, _html_with_body(["甲" * 200 + "。"]))
        assert report["ok"] is True

    def test_missing_second_paragraph_fails_with_full_text(self):
        md = "# T\n\n第一行。\n\n被吞掉的第二段。\n\n## 一\n\n正文\n"
        report = _intro_content_fidelity(md, _html_with_body(["第一行。"]))
        assert report["ok"] is False
        assert "被吞掉的第二段。" in report["missing_text"]

    def test_html_entities_and_whitespace_normalized(self):
        md = "# T\n\n第一行 & 第二行。\n\n## 一\n\n正文\n"
        html = ('<section style="margin:0 20px;"><p style="margin-bottom:16px;font-size:14px;'
                'line-height:1.9;text-align:justify;color:#555;">第一行 &amp;  第二行。</p></section>')
        report = _intro_content_fidelity(md, html)
        assert report["ok"] is True


class TestRealHTMLRegression:
    """档50 first-line-only-in-cover HTML must FAIL under the new guard."""

    def test_run50_html_fails(self):
        run = Path(r"F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260802T220853-codex-sol-luna-max-m6pyv4")
        md = (run / "zh_human_writing" / "final_article.md").read_text(encoding="utf-8")
        html = (run / "gzh_design" / "final.html").read_text(encoding="utf-8")
        report = _intro_content_fidelity(md, html)
        assert report["ok"] is False
        assert "导语：多模型编排正在成为 AI 编程成本的关键杠杆" in report["missing_text"]
