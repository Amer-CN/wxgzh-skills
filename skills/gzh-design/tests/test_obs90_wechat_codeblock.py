"""档67A OBS-90 + 删除线对比度 + OBS-77 回归测试。

OBS-90(微信友好代码块):
- render_article.py 的代码块输出不得含 <pre> / white-space:pre(pre 系列)
  —— 自家 lint(component_lint/lint_advanced_components)判 ERROR 的特征;
- 每行一个 <p style="margin:0">;前导/连续空格以 &nbsp; 保留(⛔/⚠️ 前缀对齐);
- 渲染输出必须通过 lint CHECKS 规则集(自家 lint 禁止的东西,自家渲染器不许输出);
- validate_gzh_html 对渲染输出 0 ERROR(代码区半角不误报)。
删除线对比度:
- 封面 strike 文字色=label_text(#737373,白底 4.74:1 >= 4.5:1);
- 删除线=同文字色、1px(text-decoration-thickness:1px),非橙色粗线。
"""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))


def _load_script(name: str):
    p = SKILL_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name.replace(".", "_"), p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _render_cli(md: str, theme="hammer"):
    td = Path(tempfile.mkdtemp(prefix="obs90-"))
    (td / "article.md").write_text(md, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(SKILL_ROOT / "scripts" / "render_article.py"),
         "--article", str(td / "article.md"), "--output-dir", str(td),
         "--theme", theme],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    html = (td / "final.html").read_text(encoding="utf-8") if (td / "final.html").is_file() else ""
    return proc, html


CODE_MD = """# 测试代码块

导语。

## 第一章

```bash
⛔ vibe-coding-guide 拦截：这是对根目录或家目录的递归删除，会清空整台机器（铁律 1）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：要安装新依赖了。装之前请先确认包名全称、用途、周下载量和最近更新时间（红线 10）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
    indent line with spaces
```

## 第二章

结尾。
"""

# 与 component_lint.py / lint_advanced_components.py 一致的禁用规则
LINT_CHECKS = [
    (re.compile(r"white-space\s*:\s*pre", re.I), "white-space:pre"),
    (re.compile(r"</?div[\s>]", re.I), "<div>"),
    (re.compile(r"\sclass\s*=", re.I), "class 属性"),
    (re.compile(r"\sid\s*=", re.I), "id 属性"),
    (re.compile(r"<style[\s>]", re.I), "<style>"),
    (re.compile(r"<script[\s>]", re.I), "<script>"),
    (re.compile(r"position\s*:\s*(fixed|absolute|sticky)", re.I), "position"),
    (re.compile(r"display\s*:\s*grid", re.I), "display:grid"),
    (re.compile(r"var\s*\(\s*--", re.I), "CSS 变量"),
    (re.compile(r"@(media|keyframes|import)", re.I), "@media 等"),
]


class TestOBS90CodeblockWechat:
    def test_no_pre_no_white_space_pre_in_output(self):
        proc, html = _render_cli(CODE_MD)
        assert proc.returncode == 0, proc.stderr
        assert "<pre" not in html
        assert "white-space:pre" not in html
        assert "white-space: pre" not in html

    def test_each_line_is_paragraph_with_margin_zero(self):
        _, html = _render_cli(CODE_MD)
        # 代码行以 <p style="margin:0;..."> 呈现(行内含 <span leaf=""> 包裹)
        lines = re.findall(r'<p style="margin:0;[^"]*">(.*?)</p>', html, re.DOTALL)
        # OBS-91/档67D:行内空格保持普通空格(可复制性);行首缩进转全角空格 U+3000
        assert any("⛔ vibe-coding-guide 拦截" in l for l in lines)
        assert any("⚠️ vibe-coding-guide 提醒" in l for l in lines)
        # 行首缩进以全角空格 U+3000 保留(缩进行)
        assert any("\u3000\u3000\u3000\u3000" in l for l in lines)

    def test_output_passes_lint_checks(self):
        """★自家 lint 禁止的东西,自家渲染器不许输出。"""
        _, html = _render_cli(CODE_MD)
        hits = [name for rx, name in LINT_CHECKS if rx.search(html)]
        assert hits == [], f"渲染输出命中自家 lint 禁用规则: {hits}"

    def test_output_passes_validate_gzh_html(self):
        vh = _load_script("validate_gzh_html.py")
        _, html = _render_cli(CODE_MD)
        errors, warnings, _ = vh.validate(html, "obs90-test")
        assert errors == [], f"validate_gzh_html errors: {errors}"
        # 代码区(等宽字体)内半角/引号不触发 WARN
        assert not any("半角" in w for w in warnings), warnings

    def test_code_style_identifies_code_region_by_monospace_only(self):
        vh = _load_script("validate_gzh_html.py")
        # white-space:pre 不再是代码区特征
        assert not re.search(r"white-space\\s*:\\s*pre", vh.CODE_STYLE.pattern)
        assert "monospace" in vh.CODE_STYLE.pattern.lower()
        # 普通段落(无等宽字体)不判为代码区
        plain = '<p style="margin:0;font-size:15px;color:#555555;"><span leaf="">普通段落,</span></p>'
        assert vh.CODE_STYLE.search(plain) is None
        # 代码行(等宽)判为代码区
        code = '<p style="margin:0;font-family:\'SF Mono\',Consolas,monospace;">x=1,</p>'
        assert vh.CODE_STYLE.search(code) is not None

    def test_obs95_1a_structure_gate(self):
        """★OBS-95 最小闸门:渲染输出的代码块必须命中 common-components 1a 结构。"""
        proc, html = _render_cli(CODE_MD)
        assert proc.returncode == 0
        # 深底 + 顶栏 + 三色圆点 + box-shadow
        assert "background:#1E293B" in html
        assert "background:#0F172A" in html
        assert "background:#FF5F56" in html
        assert "background:#FFBD2E" in html
        assert "background:#27C93F" in html
        assert "box-shadow:0 4px 16px -8px rgba(15,23,42,0.4)" in html
        # 每行独立 <p style="margin:0;...">
        rows = re.findall(r'<p style="margin:0;font-family:[^"]*SF Mono[^"]*">', html)
        assert len(rows) >= 1
        # 语言标签(bash)存在
        assert "color:#64748B;font-family:Consolas,Monaco,monospace" in html
        # 无 white-space:pre、无 <pre>
        assert "white-space:pre" not in html
        assert "<pre" not in html


class TestStrikeContrast:
    def test_strike_text_contrast_label_text(self):
        gh = _load_script("generate_hammer_upgrade_samples.py")
        html = gh.hammer_cover("hammer", kicker="K", strike="别急着划走",
                               title_line1="A", title_line2="B", subtitle="S")
        # 文字色 = label_text #737373
        assert "color:#737373" in html or "color:var" not in html
        assert re.search(r'color:#737373;margin:0 0 6px;text-decoration:line-through', html)
        # 删除线同色、1px(不再 #B3593B 橙粗线)
        assert "text-decoration-color:#737373" in html
        assert "text-decoration-thickness:1px" in html
        assert "text-decoration-color:#B3593B" not in html
        assert "text-decoration-thickness:1.5px" not in html

    def test_strike_contrast_ratio_ge_4_5(self):
        # #737373 vs #FFFFFF
        def lum(hexcolor):
            r, g, b = (int(hexcolor[i:i+2], 16) / 255 for i in (0, 2, 4))
            def lin(c):
                return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
            return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)
        l_txt = lum("737373")
        ratio = (1.0 + 0.05) / (l_txt + 0.05)
        assert ratio >= 4.5, f"对比度 {ratio:.2f}:1 < 4.5:1"

    def test_strike_in_real_render(self):
        proc, html = _render_cli(CODE_MD, theme="hammer")
        assert proc.returncode == 0
        assert "别急着划走" in html
        assert "text-decoration-color:#737373" in html
        assert "text-decoration-thickness:1px" in html


class TestOBS77FixedSignatureRegression:
    """OBS-77 三项 fixed_signature 回归:主题文档无占位符、含固定结尾引用。"""

    THEMES = ["moyu-green", "red-white", "graphite-minimal", "zen-whitespace",
              "moyu-ticket", "olive-journal", "hammer"]

    def test_no_author_placeholder_in_theme_docs(self):
        for name in self.THEMES:
            t = (SKILL_ROOT / "references" / f"theme-{name}.md").read_text(encoding="utf-8")
            assert "我是 {{作者名}}" not in t, name

    def test_no_intro_placeholder_in_theme_docs(self):
        for name in self.THEMES:
            t = (SKILL_ROOT / "references" / f"theme-{name}.md").read_text(encoding="utf-8")
            assert "{{一句话简介，如" not in t, name

    def test_all_themes_reference_fixed_signature(self):
        for name in self.THEMES:
            t = (SKILL_ROOT / "references" / f"theme-{name}.md").read_text(encoding="utf-8")
            assert ("固定结尾署名组件" in t) or ("common-components.md" in t), name
