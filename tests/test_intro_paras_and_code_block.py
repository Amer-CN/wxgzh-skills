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

    def test_parse_article_keeps_intro_unchanged(self):
        R = _load_render()
        parsed = R.parse_article(MULTI_INTRO)
        assert parsed["intro"] == "第一行导语。"
        assert [i["kind"] for i in parsed["intro_paras"]] == ["para", "para"]
        assert [i["text"] for i in parsed["intro_paras"]] == ["第二行导语段落。", "第三行导语段落。"]

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
        assert "```" not in html
        assert "<pre" in html
        assert "rm -rf /tmp/x" in html
        assert "git push --force origin main" in html
        assert "    indented line" in html  # indentation preserved verbatim

    def test_code_block_passes_validate_gzh_html(self):
        import validate_gzh_html as vh
        td, code, html = _render_md(FENCED)
        errors, warnings, leaf_count = vh.validate(html, "final.html")
        assert errors == [], errors

    def test_code_block_in_intro_region(self):
        _, code, html = _render_md(FENCED_INTRO)
        assert code == 0
        assert "```" not in html
        assert "deny: rm -rf /" in html
        assert "deny: DROP TABLE" in html

    def test_code_block_is_selectable_text_not_image(self):
        _, _, html = _render_md(FENCED)
        assert "<pre" in html and "<img" not in html.split("<pre", 1)[1].split("</pre>", 1)[0]

    def test_unclosed_fence_lenient(self):
        _, code, html = _render_md("# T\n\n导语。\n\n## 一\n\n```\ncode line\n")
        assert code == 0
        assert "code line" in html
