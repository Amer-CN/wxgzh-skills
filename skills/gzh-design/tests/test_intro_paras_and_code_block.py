"""OBS-73 根治 tests for scripts/render_article.py.

Intro lines after the first line must render as body paragraphs BEFORE the
first chapter title (previously silently dropped by parse_article).
"""
import importlib.util
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))


def _load_render():
    p = SKILL_ROOT / "scripts" / "render_article.py"
    spec = importlib.util.spec_from_file_location("render_article", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _render_md(md):
    import json
    import tempfile
    td = Path(tempfile.mkdtemp())
    (td / "final_article.md").write_text(md, encoding="utf-8")
    R = _load_render()
    code = R.main(["--article", str(td / "final_article.md"),
                   "--output-dir", str(td), "--theme", "smartisan"])
    return td, code, (td / "final.html").read_text(encoding="utf-8")


MULTI_INTRO = """# 标题

第一行导语。

第二行导语段落。

第三行导语段落。

## 第一章

章节正文。

## 第二章

结尾。
"""


class TestOBS73IntroParas:
    def test_extra_intro_paragraphs_rendered_before_first_chapter(self):
        _, code, html = _render_md(MULTI_INTRO)
        assert code == 0
        assert "第二行导语段落。" in html
        assert "第三行导语段落。" in html
        body_header_1 = html.rindex("PART 01")
        assert html.index("第二行导语段落。") < body_header_1
        assert html.index("第三行导语段落。") < body_header_1
        assert html.index("第二行导语段落。") < html.index("第三行导语段落。")
        assert "第一行导语。" in html

    def test_parse_article_keeps_intro_and_first_line_in_paras(self):
        R = _load_render()
        parsed = R.parse_article(MULTI_INTRO)
        assert parsed["intro"] == "第一行导语。"
        # OBS-83: the FIRST line also enters intro_paras (body rendering)
        assert [i["kind"] for i in parsed["intro_paras"]] == ["para", "para", "para"]
        assert [i["text"] for i in parsed["intro_paras"]] == ["第一行导语。", "第二行导语段落。", "第三行导语段落。"]

    def test_single_intro_still_passes(self):
        _, code, html = _render_md("# T\n\n短导语。\n\n## 一\n\n正文。\n")
        assert code == 0
        assert "短导语。" in html


FENCED = """# 标题

导语。

## 第一章

正文段落。

```
rm -rf /tmp/x
git push --force origin main
    indented line
```

结束段落。
"""

FENCED_INTRO = """# 标题

导语。

```
deny: rm -rf /
deny: DROP TABLE
```

## 第一章

正文。
"""


class TestFencedCodeBlock:
    def test_no_backticks_and_verbatim_code(self):
        _, code, html = _render_md(FENCED)
        assert code == 0
        import html as _h
        assert "```" not in html
        # OBS-90(档67A):代码块不再输出 <pre>(微信友好结构,每行 <p style="margin:0">)
        assert "<pre" not in html
        assert "rm -rf /tmp/x" in _h.unescape(html).replace("\u3000", " ").replace("\xa0", " ")
        assert "git push --force origin main" in _h.unescape(html).replace("\u3000", " ").replace("\xa0", " ")
        # 缩进以 &nbsp; 保留,语义等价(unescape 后仍为 4 空格缩进行)
        assert "    indented line" in _h.unescape(html).replace("\u3000", " ").replace("\xa0", " ")

    def test_code_block_passes_validate_gzh_html(self):
        import validate_gzh_html as vh
        td, code, html = _render_md(FENCED)
        errors, warnings, leaf_count = vh.validate(html, "final.html")
        assert errors == [], errors

    def test_code_block_in_intro_region(self):
        _, code, html = _render_md(FENCED_INTRO)
        assert code == 0
        assert "```" not in html
        import html as _h
        assert "deny: rm -rf /" in _h.unescape(html).replace("\u3000", " ").replace("\xa0", " ")
        assert "deny: DROP TABLE" in _h.unescape(html).replace("\u3000", " ").replace("\xa0", " ")

    def test_code_block_is_selectable_text_not_image(self):
        _, _, html = _render_md(FENCED)
        # OBS-90:代码块为真实可选中的 <p> 文本,非图片、非 <pre> 伪装
        assert "<pre" not in html and "<img" not in html
        assert "font-family:'SF Mono',Consolas,Monaco,monospace" in html

    def test_unclosed_fence_lenient(self):
        _, code, html = _render_md("# T\n\n导语。\n\n## 一\n\n```\ncode line\n")
        assert code == 0
        import html as _h
        assert "code line" in _h.unescape(html).replace("\u3000", " ").replace("\xa0", " ")


# ── OBS-83 (hammer.3): first intro line must render IN FULL in the body ─────

class TestOBS83FirstLineInBody:
    def _body_paras(self, html):
        import html as _h
        import re as _re
        m = _re.findall(r'<p style="margin-bottom:16px;font-size:14px;line-height:1.9;text-align:justify;[^"]*">(.*?)</p>', html, _re.S)
        out = []
        for x in m:
            x = _re.sub(r'<[^>]+>', '', x)
            x = _h.unescape(x)
            out.append(''.join(x.split()))
        return out

    def test_first_line_43_chars_in_body(self):
        md = "# 标题\n\n" + "甲" * 43 + "。\n\n## 一\n\n正文。\n"
        _, code, html = _render_md(md)
        assert code == 0
        body = self._body_paras(html)
        assert "甲" * 43 + "。" in body, "43-char first line must appear IN FULL in a body paragraph"

    def test_first_line_200_chars_in_body(self):
        md = "# 标题\n\n" + "乙" * 200 + "。\n\n## 一\n\n正文。\n"
        _, code, html = _render_md(md)
        assert code == 0
        body = self._body_paras(html)
        assert "乙" * 200 + "。" in body, "200-char first line must appear IN FULL in a body paragraph"

    def test_only_first_line_no_second(self):
        md = "# 标题\n\n只有首段，没有第二段。\n\n## 一\n\n正文。\n"
        _, code, html = _render_md(md)
        assert code == 0
        body = self._body_paras(html)
        assert "只有首段，没有第二段。" in body

    def test_no_intro(self):
        md = "# 标题\n\n## 一\n\n正文。\n"
        _, code, html = _render_md(md)
        assert code == 0
        assert "正文。" in html
