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


class TestCliCompat:
    def test_argparse_flags(self):
        src = (SKILL_ROOT / "scripts" / "render_article.py").read_text(encoding="utf-8")
        for flag in ('"--article"', '"--bindings"', '"--output-dir"', '"--theme"'):
            assert flag in src, f"render_article.py must accept {flag}"
