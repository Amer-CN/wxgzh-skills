#!/usr/bin/env python3
"""dev2-hotfix1 tests: scripts/render_article.py — the official article renderer.

Proves render_article typesets an ARBITRARY markdown article + real bindings with
the OFFICIAL hammer components, with dynamic chapters, zero validator errors, the
hammer palette (moyu-green absent), and the authoritative fixed signature.
"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

import validate_gzh_html as vh


def _load_render():
    p = SKILL_ROOT / "scripts" / "render_article.py"
    spec = importlib.util.spec_from_file_location("render_article", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


ARTICLE = """# 把旧显卡折腾成本地 AI 画图机

一块两三百块的旧 A 卡，也能跑本地 Stable Diffusion。

## 缘起：一块旧显卡的第二次生命

抽屉里翻出一块 RX 580，插上电脑还能亮。

## 选型：为什么是它

显存 8G 是关键。

## 复盘：值不值得折腾

折腾三天，出图五分钟。
"""

BINDINGS = {
    "schema_version": "1.0", "body_image_count": 2,
    "body_images": [
        {"asset_id": "A-001", "remote_url": "https://mmbiz.qpic.cn/mmbiz_png/abc/640?wx_fmt=png",
         "caption": "RX 580 实拍", "alt_text": "旧显卡照片",
         "placement": {"anchor": "## 缘起", "position": "after", "confidence": 0.9}},
        {"asset_id": "A-002", "remote_url": "https://mmbiz.qpic.cn/mmbiz_png/def/640?wx_fmt=png",
         "caption": "出图效果", "alt_text": "生成的图片",
         "placement": {"anchor": "## 复盘", "position": "after", "confidence": 0.8}},
    ],
}


def _run(theme="smartisan", bindings=BINDINGS):
    td = Path(tempfile.mkdtemp())
    (td / "final_article.md").write_text(ARTICLE, encoding="utf-8")
    bp = None
    if bindings is not None:
        bp = td / "article_image_bindings.json"
        bp.write_text(json.dumps(bindings), encoding="utf-8")
    R = _load_render()
    argv = ["--article", str(td / "final_article.md"), "--output-dir", str(td), "--theme", theme]
    if bp:
        argv += ["--bindings", str(bp)]
    code = R.main(argv)
    return td, code


class TestRenderArticle:
    def test_outputs_created_and_exit_zero(self):
        td, code = _run()
        assert code == 0
        for name in ("final.html", "final_runtime.html",
                     "component_usage_report.json", "theme_identity_report.json"):
            assert (td / name).is_file(), f"missing {name}"

    def test_dynamic_chapter_count(self):
        td, _ = _run()
        usage = json.loads((td / "component_usage_report.json").read_text(encoding="utf-8"))
        # article has exactly 3 `## ` headings
        assert usage["components"]["chapter_title"] == 3
        assert usage["components"]["chapters"] == 3

    def test_validate_gzh_html_clean(self):
        td, _ = _run()
        html = (td / "final.html").read_text(encoding="utf-8")
        errors, warnings, leaf = vh.validate(html, "final.html")
        assert errors == [], errors
        assert leaf > 0

    def test_hammer_palette_no_moyu_green(self):
        td, _ = _run()
        html = (td / "final.html").read_text(encoding="utf-8")
        assert "#B3593B" in html          # hammer primary
        assert "#059669" not in html      # moyu-green must be absent

    def test_official_fingerprints_present(self):
        td, _ = _run()
        html = (td / "final.html").read_text(encoding="utf-8")
        # cover-breaking + toc-scroll + footer-cta + chapter PART markers
        assert "PART 01" in html and "PART ///" in html
        assert "overflow-x:scroll" in html               # toc-scroll
        assert "THANKS FOR READING" in html              # footer-cta
        assert "font-size:28px;font-weight:900" in html  # chapter number

    def test_both_image_component_types_with_two_images(self):
        td, _ = _run()
        usage = json.loads((td / "component_usage_report.json").read_text(encoding="utf-8"))["components"]
        assert usage["image_media_text_card"] >= 1
        assert usage["image_2a_standard"] >= 1

    def test_authoritative_fixed_signature(self):
        td, _ = _run()
        html = (td / "final.html").read_text(encoding="utf-8")
        assert "给自己造把锤子" in html
        assert "cd.hyxc.jz@foxmail.com" in html
        assert "热闹是 AI 的" in html

    def test_renders_without_bindings(self):
        td, code = _run(bindings=None)
        assert code == 0
        usage = json.loads((td / "component_usage_report.json").read_text(encoding="utf-8"))["components"]
        assert usage["images"] == 0
        assert usage["chapter_title"] == 3

    def test_rejects_non_hammer_theme(self):
        _, code = _run(theme="moyu-green")
        assert code == 2

    def test_theme_identity_report_no_fallback(self):
        td, _ = _run()
        rep = json.loads((td / "theme_identity_report.json").read_text(encoding="utf-8"))
        assert rep["theme"] == "hammer"
        assert rep["moyu_green_absent"] is True
        assert rep["theme_fallback_used"] is False
        assert rep["render_entry"] == "scripts/render_article.py"


class TestHf6CoverParams:
    """档HF-6:封面参数化——date 自动 + --strike/--brand/--tags 覆盖生效,
    默认值不传时与旧产出逐字一致(date 除外)。"""

    def _cli(self, td, extra=None):
        (td / "final_article.md").write_text(ARTICLE, encoding="utf-8")
        bp = td / "article_image_bindings.json"
        bp.write_text(json.dumps(BINDINGS), encoding="utf-8")
        R = _load_render()
        argv = ["--article", str(td / "final_article.md"),
                "--bindings", str(bp), "--output-dir", str(td), "--theme", "smartisan"]
        argv += (extra or [])
        code = R.main(argv)
        html = (td / "final.html").read_text(encoding="utf-8")
        return code, html

    def test_cover_date_auto_current_month(self, tmp_path):
        import re
        from datetime import datetime as dt
        code, html = self._cli(tmp_path)
        assert code == 0
        m = re.search(r'<span leaf="">\d{4}\.\d{2}</span>', html)
        assert m, "cover date must match YYYY.MM"
        assert m.group(0) == f'<span leaf="">{dt.now():%Y.%m}</span>'

    def test_cover_params_override(self, tmp_path):
        code, html = self._cli(tmp_path, [
            "--date", "2026.07", "--strike", "先别划走",
            "--brand", "测试品牌", "--tags", "甲,乙"])
        assert code == 0
        assert "2026.07" in html
        assert "先别划走" in html
        assert "测试品牌" in html
        assert '<span leaf="">甲</span>' in html
        assert '<span leaf="">乙</span>' in html
        assert "别急着划走" not in html

    def test_cover_defaults_byte_identical_except_date(self):
        from datetime import datetime as dt
        R = _load_render()
        parsed = R.parse_article(ARTICLE)
        fixed, _ = R.render("hammer", parsed, [], date="2026.07")
        auto, _ = R.render("hammer", parsed, [])
        assert fixed.replace("2026.07", f"{dt.now():%Y.%m}", 1) == auto


class TestHf7Signature:
    """档HF-7:署名第二句恢复用户传统落款——渲染产物含新句、不含旧句,
    第一句与署名结构不动。"""


class TestHf72eKicker:
    """档72E-1/OBS-251:--kicker 显式覆盖生效;默认沿用既有「深度观察 · 标签」构造。"""

    def test_kicker_override(self, tmp_path):
        td = Path(tempfile.mkdtemp())
        (td / "final_article.md").write_text(ARTICLE, encoding="utf-8")
        R = _load_render()
        code = R.main(["--article", str(td / "final_article.md"),
                      "--output-dir", str(td), "--theme", "smartisan",
                      "--kicker", "实测观察"])
        assert code == 0
        html = (td / "final.html").read_text(encoding="utf-8")
        assert '<span leaf="">实测观察</span>' in html
        assert "深度观察 · " not in html

    def test_kicker_default_construct(self, tmp_path):
        td = Path(tempfile.mkdtemp())
        (td / "final_article.md").write_text(ARTICLE, encoding="utf-8")
        R = _load_render()
        code = R.main(["--article", str(td / "final_article.md"),
                      "--output-dir", str(td), "--theme", "smartisan"])
        assert code == 0
        html = (td / "final.html").read_text(encoding="utf-8")
        assert "深度观察 · " in html

    def test_render_contains_traditional_brand_2(self, tmp_path):
        td = Path(tempfile.mkdtemp())
        (td / "final_article.md").write_text(ARTICLE, encoding="utf-8")
        R = _load_render()
        code = R.main(["--article", str(td / "final_article.md"),
                      "--output-dir", str(td), "--theme", "smartisan"])
        assert code == 0
        html = (td / "final.html").read_text(encoding="utf-8")
        assert "用克制的语言讲清楚AI前沿正在发生的事。" in html
        assert "热闹是 AI 的，淡定可以是我们的。" in html
        assert "不用马上跟上，知道一点，就不算掉队。" not in html


class TestCliCompat:
    def test_argparse_flags(self):
        src = (SKILL_ROOT / "scripts" / "render_article.py").read_text(encoding="utf-8")
        for flag in ('"--article"', '"--bindings"', '"--output-dir"', '"--theme"'):
            assert flag in src, f"render_article.py must accept {flag}"


class TestHf76dCoverTitle:
    """档76D/OBS-257:--title/--subtitle 显式覆盖生效;不传时沿用解析/H1/导语默认。"""

    def _render(self, argv):
        td = Path(tempfile.mkdtemp())
        (td / "final_article.md").write_text(ARTICLE, encoding="utf-8")
        R = _load_render()
        code = R.main(["--article", str(td / "final_article.md"),
                       "--output-dir", str(td), "--theme", "smartisan", *argv])
        assert code == 0
        return (td / "final.html").read_text(encoding="utf-8")

    def test_title_override(self):
        html = self._render(["--title", "定制封面标题"])
        assert "定制封面标题" in html
        assert "把旧显卡折腾成本地 AI 画图机" not in html

    def test_title_default_from_h1(self):
        html = self._render([])
        # 封面标题经 split_title 拆行渲染(H1 不在正文渲染),断言拆行片段
        assert '把旧显卡折腾成本地' in html and 'AI 画图机' in html

    def test_subtitle_override(self):
        html = self._render(["--subtitle", "定制副标题文案"])
        assert "定制副标题文案" in html

    def test_subtitle_default_from_intro(self):
        html = self._render([])
        assert "一块两三百块的旧 A 卡" in html


class TestCliCompatHf76d:
    def test_new_flags_accepted(self):
        src = (SKILL_ROOT / "scripts" / "render_article.py").read_text(encoding="utf-8")
        for flag in ('"--title"', '"--subtitle"'):
            assert flag in src, f"render_article.py must accept {flag}"
