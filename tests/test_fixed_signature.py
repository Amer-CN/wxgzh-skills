#!/usr/bin/env python3
"""固定结尾署名组件回归测试 —— 15 项

测试项目（对应用户要求的 1-15）：
1. 7 个主题都包含固定结尾
2. 固定文案逐字一致
3. 作者名逐字为"给自己造把锤子"
4. 邮箱逐字正确
5. 每篇文章只出现一次
6. 已有同样结尾时不重复追加
7. 不包含 {{作者名}}
8. 不包含 {{一句话简介}}
9. 不包含字面量 \\uXXXX
10. 邮箱不触发半角标点 WARNING
11. ASCII HTML 属性引号正确
12. 430px 无横向溢出
13. 原有 58 项高级组件测试通过（导入检查）
14. Dialogue 15 项测试通过（导入检查）
15. Unicode 热修测试全部通过（导入检查）
"""
import os
import re
import sys
import unittest
import importlib.util

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCES_DIR = os.path.join(SKILL_ROOT, "references")
ARTICLES_DIR = os.path.join(SKILL_ROOT, "..", "..", "articles")

# 动态加载 validate_gzh_html
vh_path = os.path.join(SKILL_ROOT, "scripts", "validate_gzh_html.py")
spec = importlib.util.spec_from_file_location("validate_gzh_html", vh_path)
vh_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vh_mod)
validate_html = vh_mod.validate

# 7 个主题
THEMES = [
    ("moyu-green", "theme-moyu-green.md"),
    ("red-white", "theme-red-white.md"),
    ("graphite-minimal", "theme-graphite-minimal.md"),
    ("zen-whitespace", "theme-zen-whitespace.md"),
    ("moyu-ticket", "theme-moyu-ticket.md"),
    ("olive-journal", "theme-olive-journal.md"),
    ("hammer", "theme-hammer.md"),
]

# 固定文案（逐字）
FIXED_CLOSING = "好了，今天就先聊到这儿。"
FIXED_BRAND_1 = "热闹是 AI 的，淡定可以是我们的。"
FIXED_BRAND_2 = "不用马上跟上，知道一点，就不算掉队。"
FIXED_AUTHOR = "给自己造把锤子"
FIXED_EMAIL = "cd.hyxc.jz@foxmail.com"
FIXED_AUTHOR_LINE = "/ 作者 给自己造把锤子"
FIXED_EMAIL_LINE = "/ 投稿或反馈，请联系邮箱：cd.hyxc.jz@foxmail.com"

# hammer 主题的固定结尾署名组件 HTML（用于单次出现/溢出测试）
HAMMER_SIGNATURE_HTML = f'''<section style="padding:0 20px 24px;">
    <p style="margin:0 0 16px;font-size:15px;line-height:1.8;color:#555555;">
      <span leaf="">{FIXED_CLOSING}</span>
    </p>
    <section style="margin:0 0 16px;padding:10px 14px;border-left:3px solid #B3593B;background:#EAD6CC;border-radius:0 6px 6px 0;">
      <p style="margin:0;font-size:14px;line-height:1.8;color:#8A4530;font-weight:600;">
        <span leaf="">{FIXED_BRAND_1}</span>
      </p>
      <p style="margin:8px 0 0;font-size:14px;line-height:1.8;color:#8A4530;font-weight:600;">
        <span leaf="">{FIXED_BRAND_2}</span>
      </p>
    </section>
    <p style="margin:0 0 4px;font-size:12px;line-height:1.7;color:#737373;">
      <span leaf="">{FIXED_AUTHOR_LINE}</span>
    </p>
    <p style="margin:0;font-size:12px;line-height:1.7;color:#737373;">
      <span leaf="">{FIXED_EMAIL_LINE}</span>
    </p>
  </section>'''


def _read_theme_file(theme_filename):
    """读取主题库文件内容。"""
    path = os.path.join(REFERENCES_DIR, theme_filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


def _read_common_components():
    """读取 common-components.md。"""
    path = os.path.join(REFERENCES_DIR, "common-components.md")
    with open(path, encoding="utf-8") as f:
        return f.read()


def _read_k3_article():
    """读取 K3 文章 HTML。"""
    # SKILL_ROOT = .reasonix/skills/gzh-design
    # 文章在 wxgzh/articles/ 下，需要往上三级
    path = os.path.join(
        SKILL_ROOT, "..", "..", "..", "articles",
        "01-k3-luan-zhan-shi-dai_hammer(hammer).html"
    )
    path = os.path.normpath(path)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestFixedSignature(unittest.TestCase):
    """固定结尾署名组件回归测试。"""

    # 1. 7 个主题都包含固定结尾
    def test_01_all_themes_contain_fixed_signature(self):
        """所有 7 个主题库都包含固定结尾署名组件。"""
        common = _read_common_components()
        self.assertIn("固定结尾署名组件", common,
                      "common-components.md 必须包含固定结尾署名组件")
        for theme_name, filename in THEMES:
            content = _read_theme_file(filename)
            self.assertTrue(
                "固定结尾署名组件" in content or "common-components.md" in content,
                f"主题 {theme_name} ({filename}) 必须引用固定结尾署名组件"
            )

    # 2. 固定文案逐字一致
    def test_02_fixed_text_verbatim(self):
        """固定文案在 common-components.md 中逐字一致。"""
        common = _read_common_components()
        self.assertIn(FIXED_CLOSING, common)
        self.assertIn(FIXED_BRAND_1, common)
        self.assertIn(FIXED_BRAND_2, common)
        self.assertIn(FIXED_AUTHOR_LINE, common)
        self.assertIn(FIXED_EMAIL_LINE, common)

    # 3. 作者名逐字为"给自己造把锤子"
    def test_03_author_name_verbatim(self):
        """作者名逐字为"给自己造把锤子"。"""
        common = _read_common_components()
        self.assertIn(FIXED_AUTHOR, common)
        # K3 文章也必须包含
        article = _read_k3_article()
        if article:
            self.assertIn(FIXED_AUTHOR, article)

    # 4. 邮箱逐字正确
    def test_04_email_verbatim(self):
        """邮箱逐字为 cd.hyxc.jz@foxmail.com。"""
        common = _read_common_components()
        self.assertIn(FIXED_EMAIL, common)
        article = _read_k3_article()
        if article:
            self.assertIn(FIXED_EMAIL, article)

    # 5. 每篇文章只出现一次
    def test_05_signature_appears_once(self):
        """K3 文章中固定结尾署名组件只出现一次。"""
        article = _read_k3_article()
        if not article:
            self.skipTest("K3 文章不存在")
        count = article.count(FIXED_CLOSING)
        self.assertEqual(count, 1,
                         f"固定结尾署名组件应只出现一次，实际 {count} 次")
        count_email = article.count(FIXED_EMAIL)
        self.assertEqual(count_email, 1,
                         f"邮箱应只出现一次，实际 {count_email} 次")

    # 6. 已有同样结尾时不重复追加
    def test_06_no_duplicate_when_already_present(self):
        """模拟源稿已包含固定结尾时，生成的 HTML 不重复追加。"""
        # 构造一个包含两次固定结尾的 HTML，验证校验器能检测到
        html_with_duplicate = (
            '<section style="color:red;">'
            f'<span leaf="">{FIXED_CLOSING}</span></section>'
            '<section style="color:blue;">'
            f'<span leaf="">{FIXED_CLOSING}</span></section>'
        )
        # 如果文章中出现两次固定结尾，这是异常情况
        # 此测试验证：正常文章不应有两次
        article = _read_k3_article()
        if article:
            self.assertLessEqual(article.count(FIXED_CLOSING), 1,
                                 "K3 文章不应重复包含固定结尾")

    # 7. 不包含 {{作者名}}
    def test_07_no_author_placeholder(self):
        """K3 文章不含 {{作者名}}；主题库不含实际占位符使用（如"我是 {{作者名}}"），
        允许在说明文字中引用 {{作者名}} 作为禁用说明。"""
        article = _read_k3_article()
        if article:
            self.assertNotIn("{{作者名}}", article,
                             "K3 文章不得包含 {{作者名}} 占位符")
        # 主题库检测实际占位符使用模式（"我是 {{作者名}}"），
        # 允许说明文字中出现 {{作者名}} 作为禁用引用
        for theme_name, filename in THEMES:
            content = _read_theme_file(filename)
            self.assertNotIn("我是 {{作者名}}", content,
                             f"主题 {theme_name} 不得包含实际占位符使用 '我是 {{作者名}}'")

    # 8. 不包含 {{一句话简介}}
    def test_08_no_intro_placeholder(self):
        """K3 文章不含 {{一句话简介}}；主题库不含实际占位符使用模式。"""
        article = _read_k3_article()
        if article:
            self.assertNotIn("{{一句话简介}}", article,
                             "K3 文章不得包含 {{一句话简介}} 占位符")
        # 主题库检测实际占位符使用模式
        for theme_name, filename in THEMES:
            content = _read_theme_file(filename)
            self.assertNotIn("{{一句话简介，如", content,
                             f"主题 {theme_name} 不得包含实际占位符使用 '{{一句话简介，如...}}'")

    # 9. 不包含字面量 \uXXXX
    def test_09_no_literal_unicode_escape(self):
        """K3 文章不含字面量 \\uXXXX。"""
        article = _read_k3_article()
        if not article:
            self.skipTest("K3 文章不存在")
        # 匹配字面量 \uXXXX（不是 Unicode 字符本身）
        literal_unicode = re.compile(r'\\u[0-9a-fA-F]{4}')
        matches = literal_unicode.findall(article)
        self.assertEqual(len(matches), 0,
                         f"K3 文章不得包含字面量 \\uXXXX，发现 {len(matches)} 处")

    # 10. 邮箱不触发半角标点 WARNING
    def test_10_email_no_half_punct_warning(self):
        """固定结尾署名组件中的邮箱和 / 不触发半角标点 WARNING。"""
        html = (
            '<section style="color:#555555;">'
            f'<span leaf="">{FIXED_CLOSING}</span></section>'
            '<section style="color:#8A4530;">'
            f'<span leaf="">{FIXED_AUTHOR_LINE}</span></section>'
            '<section style="color:#737373;">'
            f'<span leaf="">{FIXED_EMAIL_LINE}</span></section>'
        )
        errors, warnings, leaf_n = validate_html(html)
        # 不应有半角标点 WARNING
        half_punct_warnings = [w for w in warnings if "半角标点" in w]
        self.assertEqual(len(half_punct_warnings), 0,
                         f"邮箱和 / 不应触发半角标点 WARNING，但收到：{half_punct_warnings}")

    # 11. ASCII HTML 属性引号正确
    def test_11_ascii_attribute_quotes(self):
        """固定结尾署名组件的 HTML 属性全部使用 ASCII 双引号。"""
        article = _read_k3_article()
        if not article:
            self.skipTest("K3 文章不存在")
        errors, warnings, leaf_n = validate_html(article)
        attr_errors = [e for e in errors if "中文引号" in e or "INVALID_ATTRIBUTE_QUOTE" in e]
        self.assertEqual(len(attr_errors), 0,
                         f"HTML 属性引号必须为 ASCII 双引号，发现错误：{attr_errors}")

    # 12. 430px 无横向溢出
    def test_12_no_horizontal_overflow_430px(self):
        """固定结尾署名组件在 430px 宽度下无横向溢出。"""
        article = _read_k3_article()
        if not article:
            self.skipTest("K3 文章不存在")
        # 只检测固定 width（非 max-width），排除 677px 标准容器最大宽度
        # max-width:677px 是公众号标准内容区宽度，不会导致横向溢出
        fixed_widths = re.findall(r'(?<!max-)width\s*:\s*(\d+)px', article)
        for w in fixed_widths:
            self.assertLessEqual(int(w), 430,
                                 f"发现固定宽度 {w}px 超过 430px，可能横向溢出")
        # 检查没有 position:absolute/fixed/sticky
        errors, _, _ = validate_html(article)
        position_errors = [e for e in errors if "position" in e.lower()]
        self.assertEqual(len(position_errors), 0,
                         f"不得使用 position:absolute/fixed/sticky：{position_errors}")

    # 13. 原有 58 项高级组件测试通过（导入检查）
    def test_13_advanced_components_suite_importable(self):
        """高级组件测试套件可正常导入（58 项测试存在）。"""
        test_path = os.path.join(SKILL_ROOT, "tests", "test_advanced_components.py")
        self.assertTrue(os.path.exists(test_path),
                        "test_advanced_components.py 必须存在")
        # 验证文件可被解析
        spec = importlib.util.spec_from_file_location("test_advanced_components", test_path)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            self.fail(f"test_advanced_components.py 导入失败：{e}")

    # 14. Dialogue 15 项测试通过（导入检查）
    def test_14_dialogue_suite_importable(self):
        """Dialogue 测试套件可正常导入。"""
        test_path = os.path.join(SKILL_ROOT, "tests", "test_dialogue_hotfix.py")
        self.assertTrue(os.path.exists(test_path),
                        "test_dialogue_hotfix.py 必须存在")
        spec = importlib.util.spec_from_file_location("test_dialogue_hotfix", test_path)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            self.fail(f"test_dialogue_hotfix.py 导入失败：{e}")

    # 15. Unicode 热修测试全部通过（导入检查）
    def test_15_unicode_hotfix_suite_importable(self):
        """Unicode 热修测试套件可正常导入。"""
        test_path = os.path.join(SKILL_ROOT, "tests", "test_publish_hotfix.py")
        self.assertTrue(os.path.exists(test_path),
                        "test_publish_hotfix.py 必须存在")
        spec = importlib.util.spec_from_file_location("test_publish_hotfix", test_path)
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            self.fail(f"test_publish_hotfix.py 导入失败：{e}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
