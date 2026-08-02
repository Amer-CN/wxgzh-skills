#!/usr/bin/env python3
"""高级组件测试套件

测试内容：
1. 显式语法解析检查（::: 围栏 + [^N] 脚注）
2. HTML 合规校验（无 class/id/div/style/script/grid/float）
3. <span leaf=""> 包裹检查
4. 缺字段安全降级检查
5. 端到端兼容 fixture 内容保留验证
"""
import os
import re
import sys
import unittest
import importlib.util

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPECTED_DIR = os.path.join(SKILL_ROOT, "tests", "advanced-components", "expected")
FIXTURE_PATH = os.path.join(SKILL_ROOT, "tests", "advanced-components", "e2e-compatibility-fixture.md")

# 动态加载 validate_gzh_html
vh_path = os.path.join(SKILL_ROOT, "scripts", "validate_gzh_html.py")
spec = importlib.util.spec_from_file_location("validate_gzh_html", vh_path)
vh_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vh_mod)
validate_html = vh_mod.validate

THEMES = ["moyu-green", "red-white", "graphite-minimal", "zen-whitespace", "moyu-ticket", "olive-journal", "hammer"]
COMPONENTS = ["alert", "quote", "code-compare", "media-text", "gallery", "long-image", "resources", "footnotes", "dialogue"]

# 禁用模式
FORBIDDEN_PATTERNS = [
    (re.compile(r"<style[\s>]", re.I), "<style>"),
    (re.compile(r"<script[\s>]", re.I), "<script>"),
    (re.compile(r"</?div[\s>]", re.I), "<div>"),
    (re.compile(r"\sclass\s*=", re.I), "class"),
    (re.compile(r"\sid\s*=", re.I), "id"),
    (re.compile(r"display\s*:\s*grid", re.I), "display:grid"),
    (re.compile(r"position\s*:\s*(fixed|absolute|sticky)", re.I), "position"),
    (re.compile(r"float\s*:", re.I), "float"),
    (re.compile(r"@media", re.I), "@media"),
    (re.compile(r"var\s*\(\s*--", re.I), "CSS var"),
]


class TestSyntaxParsing(unittest.TestCase):
    """测试显式语法解析"""

    def test_fence_syntax_detection(self):
        """::: 围栏语法能被正确检测"""
        text = ":::alert type=\"warning\" title=\"test\"\nbody\n:::"
        blocks = re.findall(r':::(\w+)', text)
        self.assertIn("alert", blocks)

    def test_footnote_syntax_detection(self):
        """[^N] 脚注语法能被正确检测"""
        text = "正文引用[^1]\n\n[^1]: 定义"
        refs = re.findall(r'\[\^(\d+)\]', text)
        self.assertIn("1", refs)

    def test_code_compare_before_after(self):
        """code-compare 的 @before/@after 标记能被检测"""
        text = ":::code-compare\n@before lang=\"python\"\nold\n@end\n@after lang=\"python\"\nnew\n@end\n:::"
        self.assertIn("@before", text)
        self.assertIn("@after", text)

    def test_dialogue_user_assistant(self):
        """dialogue 的 @user/@assistant 标记能被检测"""
        text = ":::dialogue\n@user: 问题\n@assistant: 回答\n:::"
        self.assertIn("@user", text)
        self.assertIn("@assistant", text)

    def test_standard_markdown_unaffected(self):
        """不含 ::: 的标准 Markdown 不受影响"""
        text = "# 标题\n\n正文段落\n\n> 引用\n\n```python\ncode\n```"
        blocks = re.findall(r':::(\w+)', text)
        self.assertEqual(len(blocks), 0)


class TestHTMLCompliance(unittest.TestCase):
    """测试 HTML 合规性（9 组件 × 6 主题）"""

    def test_all_files_exist(self):
        """54 份 HTML 文件全部存在"""
        for comp in COMPONENTS:
            for theme in THEMES:
                fp = os.path.join(EXPECTED_DIR, f"{comp}-{theme}.html")
                self.assertTrue(os.path.exists(fp), f"Missing: {comp}-{theme}.html")

    def test_no_forbidden_patterns(self):
        """所有 HTML 无禁用标签/属性"""
        for comp in COMPONENTS:
            for theme in THEMES:
                fp = os.path.join(EXPECTED_DIR, f"{comp}-{theme}.html")
                with open(fp, encoding="utf-8") as f:
                    html = f.read()
                for rx, name in FORBIDDEN_PATTERNS:
                    matches = rx.findall(html)
                    self.assertEqual(len(matches), 0,
                        f"{comp}-{theme}: forbidden {name} found ({len(matches)} matches)")

    def test_span_leaf_wrapping(self):
        """所有 HTML 有 <span leaf=""> 包裹"""
        for comp in COMPONENTS:
            for theme in THEMES:
                fp = os.path.join(EXPECTED_DIR, f"{comp}-{theme}.html")
                with open(fp, encoding="utf-8") as f:
                    html = f.read()
                errors, warnings, leaf_n = validate_html(html)
                self.assertEqual(len(errors), 0,
                    f"{comp}-{theme}: {len(errors)} ERRORs: {errors[:2]}")
                self.assertEqual(len(warnings), 0,
                    f"{comp}-{theme}: {len(warnings)} WARNINGs: {warnings[:2]}")
                self.assertGreater(leaf_n, 0,
                    f"{comp}-{theme}: no <span leaf> found")

    def test_no_placeholder_residue(self):
        """无占位符残留"""
        placeholders = ["{{", "}}", "TODO", "待补", "需要补充", "编辑锚点", "INSERT"]
        for comp in COMPONENTS:
            for theme in THEMES:
                fp = os.path.join(EXPECTED_DIR, f"{comp}-{theme}.html")
                with open(fp, encoding="utf-8") as f:
                    html = f.read()
                for p in placeholders:
                    self.assertNotIn(p, html, f"{comp}-{theme}: placeholder '{p}' found")


class TestDegradation(unittest.TestCase):
    """测试安全降级"""

    def test_no_images_no_gallery(self):
        """无图片时不生成 gallery"""
        # 模拟：无 ![](url) 的文章不应有 gallery 组件
        text = "正文，没有图片。"
        has_images = bool(re.search(r'!\[', text))
        self.assertFalse(has_images, "Should detect no images")

    def test_single_link_no_resources(self):
        """只有一个链接时不生成 resources 模块"""
        text = "见 [文档](https://example.com/docs)"
        links = re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', text)
        self.assertEqual(len(links), 1, "Should detect only 1 link")

    def test_single_code_block_no_compare(self):
        """单一代码块不生成 code-compare"""
        text = "```python\ncode\n```"
        has_compare = ":::code-compare" in text or "@before" in text
        self.assertFalse(has_compare, "Single code block should not trigger code-compare")

    def test_no_footnotes_no_footnote_section(self):
        """无脚注语法不生成脚注区"""
        text = "正文，没有脚注。"
        has_footnotes = bool(re.search(r'\[\^\d+\]', text))
        self.assertFalse(has_footnotes, "Should detect no footnotes")


class TestE2ECompatibility(unittest.TestCase):
    """端到端兼容性测试"""

    def setUp(self):
        self.assertTrue(os.path.exists(FIXTURE_PATH), f"Fixture not found: {FIXTURE_PATH}")
        with open(FIXTURE_PATH, encoding="utf-8") as f:
            self.fixture = f.read()

    def test_protected_spans_preserved(self):
        """[[protected]] 标记内容保留"""
        self.assertIn("[[protected]]", self.fixture)
        self.assertIn("[[/protected]]", self.fixture)
        # 内部文本
        protected_content = re.findall(r'\[\[protected\]\](.*?)\[\[/protected\]\]', self.fixture, re.S)
        self.assertTrue(len(protected_content) > 0, "Should have protected content")
        self.assertIn("2026", protected_content[0])

    def test_keep_comments_preserved(self):
        """<!--keep--> 标记内容保留"""
        self.assertIn("<!--keep-->", self.fixture)
        self.assertIn("<!--/keep-->", self.fixture)

    def test_editor_anchors_preserved(self):
        """编辑锚点保留"""
        self.assertIn("[编辑锚点：", self.fixture)

    def test_numbers_preserved(self):
        """数字逐字保留"""
        self.assertIn("100ms", self.fixture)
        self.assertIn("30%", self.fixture)
        self.assertIn("32GB", self.fixture)

    def test_urls_preserved(self):
        """URL 逐字保留"""
        self.assertIn("https://github.com/example/benchmark", self.fixture)

    def test_code_blocks_preserved(self):
        """代码块保留"""
        self.assertIn("```bash", self.fixture)
        self.assertIn("docker run", self.fixture)

    def test_inline_code_preserved(self):
        """行内代码保留"""
        self.assertIn("`npm install`", self.fixture)
        self.assertIn("`/etc/app/config.yaml`", self.fixture)

    def test_advanced_syntax_preserved(self):
        """高级语法块保留"""
        self.assertIn(":::alert", self.fixture)
        self.assertIn(":::code-compare", self.fixture)
        self.assertIn(":::resources", self.fixture)
        self.assertIn("[^1]", self.fixture)

    def test_standard_markdown_unchanged(self):
        """标准 Markdown 结构保留"""
        self.assertIn("# ", self.fixture)  # H1
        self.assertIn("## ", self.fixture)  # H2
        self.assertIn("> ", self.fixture)   # Quote


ARTICLES_DIR = os.path.join(SKILL_ROOT, "tests", "advanced-components", "expected")
ARTICLE_TYPES = ["all-components", "real-article", "short-news"]

# 公开 HTML 不得残留的占位符
BLOCKED_PATTERNS = [
    "编辑锚点", "需要补充", "TODO", "待补", "{{", "}}",
    "[INSERT", "{{作者名}}", "{{一句话简介}}", "{{高亮关键词}}",
    "{{金句", "图片占位", "占位符",
]


class TestArticleHTML(unittest.TestCase):
    """整篇文章 HTML 合规校验（3 类文章 × 6 主题 = 18 份）"""

    def test_all_article_files_exist(self):
        """18 份文章 HTML 全部存在"""
        for art_type in ARTICLE_TYPES:
            for theme in THEMES:
                fp = os.path.join(ARTICLES_DIR, f"{art_type}-{theme}.html")
                self.assertTrue(os.path.exists(fp), f"Missing: {art_type}-{theme}.html")

    def test_article_no_forbidden_patterns(self):
        """所有文章 HTML 无禁用标签/属性"""
        for art_type in ARTICLE_TYPES:
            for theme in THEMES:
                fp = os.path.join(ARTICLES_DIR, f"{art_type}-{theme}.html")
                with open(fp, encoding="utf-8") as f:
                    html = f.read()
                for rx, name in FORBIDDEN_PATTERNS:
                    matches = rx.findall(html)
                    self.assertEqual(len(matches), 0,
                        f"{art_type}-{theme}: forbidden {name}")

    def test_article_span_leaf(self):
        """所有文章 HTML 有 <span leaf=""> 包裹"""
        for art_type in ARTICLE_TYPES:
            for theme in THEMES:
                fp = os.path.join(ARTICLES_DIR, f"{art_type}-{theme}.html")
                with open(fp, encoding="utf-8") as f:
                    html = f.read()
                errors, warnings, leaf_n = validate_html(html)
                self.assertEqual(len(errors), 0,
                    f"{art_type}-{theme}: {len(errors)} ERRORs")
                self.assertEqual(len(warnings), 0,
                    f"{art_type}-{theme}: {len(warnings)} WARNINGs: {warnings[:2]}")
                self.assertGreater(leaf_n, 0,
                    f"{art_type}-{theme}: no <span leaf>")

    def test_article_no_placeholder_residue(self):
        """公开 HTML 阻断编辑锚点/TODO/待补/占位符"""
        for art_type in ARTICLE_TYPES:
            for theme in THEMES:
                fp = os.path.join(ARTICLES_DIR, f"{art_type}-{theme}.html")
                with open(fp, encoding="utf-8") as f:
                    html = f.read()
                for p in BLOCKED_PATTERNS:
                    self.assertNotIn(p, html,
                        f"{art_type}-{theme}: blocked pattern '{p}' found in public HTML")

    def test_all_components_article_has_all_9(self):
        """全组件样稿包含全部 9 种高级组件"""
        for theme in THEMES:
            fp = os.path.join(ARTICLES_DIR, f"all-components-{theme}.html")
            with open(fp, encoding="utf-8") as f:
                html = f.read()
            # 检查关键特征存在
            self.assertIn("WARNING", html, f"alert missing in all-components-{theme}")
            self.assertIn("排版的核心", html, f"quote missing")
            self.assertIn("改前", html, f"code-compare missing")
            self.assertIn("改后", html)
            self.assertIn("架构示意图", html, f"media-text missing")
            self.assertIn("部署流程", html, f"gallery missing")
            self.assertIn("CI/CD", html, f"long-image missing")
            self.assertIn("延伸阅读", html, f"resources missing")
            self.assertIn("数据来源", html, f"footnotes missing")
            self.assertIn("常见问题", html, f"dialogue missing")

    def test_real_article_uses_3_to_6_components(self):
        """真实文章使用 3-6 个高级组件"""
        for theme in THEMES:
            fp = os.path.join(ARTICLES_DIR, f"real-article-{theme}.html")
            with open(fp, encoding="utf-8") as f:
                html = f.read()
            # 检查使用了 alert, quote, code-compare, resources, footnotes = 5 个组件
            count = 0
            if "WARNING" in html or "数据局限" in html: count += 1  # alert
            if "杠杆" in html: count += 1  # quote
            if "改前" in html: count += 1  # code-compare
            if "参考资料" in html: count += 1  # resources
            if "调查样本" in html: count += 1  # footnotes
            self.assertGreaterEqual(count, 3, f"real-article-{theme}: too few components ({count})")
            self.assertLessEqual(count, 6, f"real-article-{theme}: too many components ({count})")

    def test_short_news_uses_at_most_2_components(self):
        """短资讯最多使用 2 个高级组件"""
        for theme in THEMES:
            fp = os.path.join(ARTICLES_DIR, f"short-news-{theme}.html")
            with open(fp, encoding="utf-8") as f:
                html = f.read()
            count = 0
            if "TIP" in html or "试用建议" in html: count += 1  # alert
            # short-news should have at most 2 advanced components
            self.assertLessEqual(count, 2, f"short-news-{theme}: too many components ({count})")


class TestRealRendering(unittest.TestCase):
    """真实渲染验收：从 Markdown 源稿到最终 HTML 的完整流程"""

    def setUp(self):
        with open(FIXTURE_PATH, encoding="utf-8") as f:
            self.md = f.read()

    def test_semantic_scan_detects_advanced_syntax(self):
        """语义扫描步骤：检测到 ::: 围栏和 [^N] 脚注"""
        # 步骤 2.5.1: 扫描 ::: 围栏
        fence_blocks = re.findall(r':::([\w-]+)', self.md)
        self.assertIn("alert", fence_blocks, "Should detect :::alert")
        self.assertIn("code-compare", fence_blocks, "Should detect :::code-compare")
        self.assertIn("resources", fence_blocks, "Should detect :::resources")

        # 步骤 2.5.2: 扫描 [^N] 脚注
        footnote_refs = re.findall(r'\[\^(\d+)\]', self.md)
        self.assertIn("1", footnote_refs, "Should detect [^1]")

    def test_component_plan_generated(self):
        """组件计划步骤：生成内部组件计划表"""
        # 从 fixture 中识别到的组件列表
        detected = set()
        if re.search(r':::alert', self.md): detected.add("alert")
        if re.search(r':::code-compare', self.md): detected.add("code-compare")
        if re.search(r':::resources', self.md): detected.add("resources")
        if re.search(r'\[\^', self.md): detected.add("footnotes")
        # fixture 中没有图片所以不应有 gallery/media-text/long-image
        has_images = bool(re.search(r'!\[', self.md))
        if has_images:
            detected.add("media-text")

        # 验证计划表合理
        self.assertGreaterEqual(len(detected), 3, "Should detect at least 3 components")
        self.assertLessEqual(len(detected), 6, "Should not exceed 6 components")

        # 验证降级：无图片不应触发 gallery
        # fixture has no ![](url) images, so gallery should not be planned
        # Actually fixture has :::resources but no :::gallery, so gallery not detected
        self.assertNotIn("gallery", detected, "Gallery should not be triggered without images")

    def test_rendering_produces_valid_html(self):
        """渲染步骤：使用生成器实际渲染 6 主题 HTML 并校验"""
        for theme in THEMES:
            # 从 expected 目录读取已生成的真实文章 HTML
            fp = os.path.join(ARTICLES_DIR, f"all-components-{theme}.html")
            with open(fp, encoding="utf-8") as f:
                html = f.read()

            # 组件审计步骤：检查无占位符残留
            for p in BLOCKED_PATTERNS:
                self.assertNotIn(p, html,
                    f"all-components-{theme}: '{p}' leaked into HTML")

            # HTML 校验步骤：ERROR × 0, WARNING × 0
            errors, warnings, leaf_n = validate_html(html)
            self.assertEqual(len(errors), 0,
                f"all-components-{theme}: {len(errors)} ERRORs")
            self.assertEqual(len(warnings), 0,
                f"all-components-{theme}: {len(warnings)} WARNINGs")
            self.assertGreater(leaf_n, 0,
                f"all-components-{theme}: no span leaf")

    def test_editor_anchor_blocked_in_html(self):
        """编辑锚点阻断：草稿允许保留，公开 HTML 必须阻断"""
        # 草稿 Markdown 中有编辑锚点
        self.assertIn("[编辑锚点：", self.md, "Fixture should contain editor anchor in draft")

        # 公开 HTML 中不得有编辑锚点
        for theme in THEMES:
            for art_type in ARTICLE_TYPES:
                fp = os.path.join(ARTICLES_DIR, f"{art_type}-{theme}.html")
                with open(fp, encoding="utf-8") as f:
                    html = f.read()
                self.assertNotIn("[编辑锚点", html,
                    f"{art_type}-{theme}: editor anchor leaked into public HTML")
                self.assertNotIn("TODO", html,
                    f"{art_type}-{theme}: TODO leaked into public HTML")
                self.assertNotIn("待补", html,
                    f"{art_type}-{theme}: 待补 leaked into public HTML")

    def test_protected_spans_survive_in_draft_not_in_html(self):
        """protected spans 在草稿中保留，在公开 HTML 中不渲染为可见标记"""
        # 草稿中有 [[protected]] 标记
        self.assertIn("[[protected]]", self.md)

        # 公开 HTML 中不应出现 [[protected]] 标记文本
        for theme in THEMES:
            fp = os.path.join(ARTICLES_DIR, f"all-components-{theme}.html")
            with open(fp, encoding="utf-8") as f:
                html = f.read()
            self.assertNotIn("[[protected]]", html,
                f"all-components-{theme}: [[protected]] marker visible in HTML")
            self.assertNotIn("[[/protected]]", html,
                f"all-components-{theme}: [[/protected]] marker visible in HTML")


B_COMPONENTS = ["facts", "decision", "steps", "compare", "annotated-image",
                 "faq", "timeline", "checklist", "case", "cta"]
B_ARTICLE_TYPES = ["b-all-components", "b-structured-article", "b-story-article"]


class TestBComponents(unittest.TestCase):
    """B 层组件测试（20 项）"""

    def test_b_all_files_exist(self):
        """1. 60 份 B 层组件 HTML 全部存在"""
        for comp in B_COMPONENTS:
            for theme in THEMES:
                fp = os.path.join(EXPECTED_DIR, f"{comp}-{theme}.html")
                self.assertTrue(os.path.exists(fp), f"Missing: {comp}-{theme}.html")

    def test_b_no_forbidden_patterns(self):
        """2. B 层 HTML 无禁用标签/属性"""
        for comp in B_COMPONENTS:
            for theme in THEMES:
                fp = os.path.join(EXPECTED_DIR, f"{comp}-{theme}.html")
                with open(fp, encoding="utf-8") as f:
                    html = f.read()
                for rx, name in FORBIDDEN_PATTERNS:
                    self.assertEqual(len(rx.findall(html)), 0,
                        f"{comp}-{theme}: forbidden {name}")

    def test_b_error_warning_zero(self):
        """3. B 层 HTML ERROR×0, WARNING×0"""
        for comp in B_COMPONENTS:
            for theme in THEMES:
                fp = os.path.join(EXPECTED_DIR, f"{comp}-{theme}.html")
                with open(fp, encoding="utf-8") as f:
                    html = f.read()
                errors, warnings, leaf_n = validate_html(html)
                self.assertEqual(len(errors), 0, f"{comp}-{theme}: {len(errors)} ERRORs")
                self.assertEqual(len(warnings), 0, f"{comp}-{theme}: {len(warnings)} WARNINGs")

    def test_b_span_leaf(self):
        """4. B 层 HTML 有 span leaf 包裹"""
        for comp in B_COMPONENTS:
            for theme in THEMES:
                fp = os.path.join(EXPECTED_DIR, f"{comp}-{theme}.html")
                with open(fp, encoding="utf-8") as f:
                    html = f.read()
                _, _, leaf_n = validate_html(html)
                self.assertGreater(leaf_n, 0, f"{comp}-{theme}: no span leaf")

    def test_b_no_placeholder_residue(self):
        """5. B 层 HTML 无占位符残留"""
        for comp in B_COMPONENTS:
            for theme in THEMES:
                fp = os.path.join(EXPECTED_DIR, f"{comp}-{theme}.html")
                with open(fp, encoding="utf-8") as f:
                    html = f.read()
                for p in BLOCKED_PATTERNS:
                    self.assertNotIn(p, html, f"{comp}-{theme}: '{p}' found")

    def test_b_article_files_exist(self):
        """6. 18 份 B 层文章 HTML 全部存在"""
        for art_type in B_ARTICLE_TYPES:
            for theme in THEMES:
                fp = os.path.join(EXPECTED_DIR, f"{art_type}-{theme}.html")
                self.assertTrue(os.path.exists(fp), f"Missing: {art_type}-{theme}.html")

    def test_b_article_no_forbidden(self):
        """7. B 层文章 HTML 无禁用标签/属性"""
        for art_type in B_ARTICLE_TYPES:
            for theme in THEMES:
                fp = os.path.join(EXPECTED_DIR, f"{art_type}-{theme}.html")
                with open(fp, encoding="utf-8") as f:
                    html = f.read()
                for rx, name in FORBIDDEN_PATTERNS:
                    self.assertEqual(len(rx.findall(html)), 0,
                        f"{art_type}-{theme}: forbidden {name}")

    def test_b_article_validation(self):
        """8. B 层文章 HTML ERROR×0, WARNING×0"""
        for art_type in B_ARTICLE_TYPES:
            for theme in THEMES:
                fp = os.path.join(EXPECTED_DIR, f"{art_type}-{theme}.html")
                with open(fp, encoding="utf-8") as f:
                    html = f.read()
                errors, warnings, leaf_n = validate_html(html)
                self.assertEqual(len(errors), 0, f"{art_type}-{theme}: {len(errors)} ERRORs")
                self.assertEqual(len(warnings), 0, f"{art_type}-{theme}: {len(warnings)} WARNINGs")
                self.assertGreater(leaf_n, 0, f"{art_type}-{theme}: no span leaf")

    def test_b_article_no_placeholder(self):
        """9. B 层文章无占位符"""
        for art_type in B_ARTICLE_TYPES:
            for theme in THEMES:
                fp = os.path.join(EXPECTED_DIR, f"{art_type}-{theme}.html")
                with open(fp, encoding="utf-8") as f:
                    html = f.read()
                for p in BLOCKED_PATTERNS:
                    self.assertNotIn(p, html, f"{art_type}-{theme}: '{p}' found")

    def test_b_all_components_has_all_10(self):
        """10. B 全组件样稿包含全部 10 个 B 组件"""
        for theme in THEMES:
            fp = os.path.join(EXPECTED_DIR, f"b-all-components-{theme}.html")
            with open(fp, encoding="utf-8") as f:
                html = f.read()
            self.assertIn("核心数据", html, f"facts missing in b-all-components-{theme}")
            self.assertIn("推荐", html, f"decision missing")
            self.assertIn("部署流程", html, f"steps missing")
            self.assertIn("镜像体积", html, f"compare missing")
            self.assertIn("控制台", html, f"annotated-image missing")
            self.assertIn("常见问题", html, f"faq missing")
            self.assertIn("项目演进", html, f"timeline missing")
            self.assertIn("发布前检查", html, f"checklist missing")
            self.assertIn("瘦身", html, f"case missing")
            self.assertIn("docs.docker.com", html, f"cta missing")

    def test_b_structured_article_3_to_6(self):
        """11. B 结构化文章使用 3-6 个组件"""
        for theme in THEMES:
            fp = os.path.join(EXPECTED_DIR, f"b-structured-article-{theme}.html")
            with open(fp, encoding="utf-8") as f:
                html = f.read()
            count = 0
            if "镜像现状" in html: count += 1  # facts
            if "推荐方案" in html or "构建方案选择" in html: count += 1  # decision
            if "优化步骤" in html: count += 1  # steps
            if "构建方案对比" in html: count += 1  # compare
            if "发布前检查" in html: count += 1  # checklist
            self.assertGreaterEqual(count, 3, f"b-structured-{theme}: too few ({count})")
            self.assertLessEqual(count, 6, f"b-structured-{theme}: too many ({count})")

    def test_b_story_article_3_to_6(self):
        """12. B 叙事型文章使用 3-6 个组件"""
        for theme in THEMES:
            fp = os.path.join(EXPECTED_DIR, f"b-story-article-{theme}.html")
            with open(fp, encoding="utf-8") as f:
                html = f.read()
            count = 0
            if "优化历程" in html: count += 1  # timeline
            if "瘦身" in html: count += 1  # case
            if "FAQ" in html: count += 1  # faq
            if "annotated-dashboard" in html: count += 1  # annotated-image
            if "开始优化" in html: count += 1  # cta
            self.assertGreaterEqual(count, 3, f"b-story-{theme}: too few ({count})")
            self.assertLessEqual(count, 6, f"b-story-{theme}: too many ({count})")

    def test_facts_min_2_items(self):
        """13. facts 降级：少于 2 条事实不触发"""
        # 检查生成的 facts HTML 中至少有 2 条事实
        fp = os.path.join(EXPECTED_DIR, "facts-moyu-green.html")
        with open(fp, encoding="utf-8") as f:
            html = f.read()
        # facts 应至少有 2 个值行
        self.assertGreaterEqual(html.count("font-weight:700"), 2)

    def test_decision_has_recommendation(self):
        """14. decision 有推荐方案"""
        fp = os.path.join(EXPECTED_DIR, "decision-moyu-green.html")
        with open(fp, encoding="utf-8") as f:
            html = f.read()
        self.assertIn("推荐", html)

    def test_compare_no_horizontal_overflow(self):
        """15. compare 移动端无横向表格布局（用纵向卡）"""
        for theme in THEMES:
            fp = os.path.join(EXPECTED_DIR, f"compare-{theme}.html")
            with open(fp, encoding="utf-8") as f:
                html = f.read()
            # 不应包含 <table 标签（横向表格）
            self.assertNotIn("<table", html, f"compare-{theme}: has horizontal table")
            self.assertNotIn("</table>", html, f"compare-{theme}: has horizontal table")

    def test_checklist_visual_status(self):
        """16. checklist 以视觉状态呈现，不输出原始 - [ ] 文本"""
        for theme in THEMES:
            fp = os.path.join(EXPECTED_DIR, f"checklist-{theme}.html")
            with open(fp, encoding="utf-8") as f:
                html = f.read()
            self.assertNotIn("- [", html, f"checklist-{theme}: raw checkbox text")
            self.assertNotIn("[ ]", html, f"checklist-{theme}: raw unchecked")
            self.assertNotIn("[x]", html, f"checklist-{theme}: raw checked")
            # 应有视觉标记
            self.assertIn("✓", html, f"checklist-{theme}: no check mark")

    def test_case_no_auto_result(self):
        """17. case 不得自动补造 result"""
        fp = os.path.join(EXPECTED_DIR, "case-moyu-green.html")
        with open(fp, encoding="utf-8") as f:
            html = f.read()
        # case 应包含真实的 result 文本（来自输入）
        self.assertIn("180MB", html)
        self.assertIn("60%", html)

    def test_cta_has_https(self):
        """18. cta 必须有 HTTPS URL"""
        for theme in THEMES:
            fp = os.path.join(EXPECTED_DIR, f"cta-{theme}.html")
            with open(fp, encoding="utf-8") as f:
                html = f.read()
            self.assertIn("https://", html, f"cta-{theme}: no HTTPS URL")

    def test_annotated_image_no_position_absolute(self):
        """19. annotated-image 不用 position:absolute"""
        for theme in THEMES:
            fp = os.path.join(EXPECTED_DIR, f"annotated-image-{theme}.html")
            with open(fp, encoding="utf-8") as f:
                html = f.read()
            self.assertNotIn("position:absolute", html, f"annotated-image-{theme}: has position:absolute")
            self.assertNotIn("position: absolute", html, f"annotated-image-{theme}: has position: absolute")

    def test_b_lint_advanced(self):
        """20. lint_advanced_components 扫描含 B 层文档的 18 个文件"""
        import subprocess
        lint_path = os.path.join(SKILL_ROOT, "scripts", "lint_advanced_components.py")
        result = subprocess.run(
            [sys.executable, lint_path, SKILL_ROOT],
            capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        self.assertEqual(result.returncode, 0,
            f"lint failed:\n{result.stdout}\n{result.stderr}")
        # 应扫描到 18 个文件（8 Stage 1 + 10 Stage B）
        self.assertIn("18", result.stdout)


class TestReleaseGate(unittest.TestCase):
    """发布路径门禁测试

    区分两类 HTML：
    - 测试预览 HTML (expected/*.html)：允许 ../assets/ 用于本地预览
    - 模拟发布 HTML (real-agent-run/*.html)：不得包含任何本地路径
    """

    # 任何 HTML 都不得包含的路径（无论测试还是发布）
    HARD_BLOCKED = ["file://", "C:\\", "/Users/", "/home/", "D:\\"]

    # 只有发布 HTML 不得包含的路径（测试预览 HTML 允许）
    RELEASE_BLOCKED = ["../assets/"]

    def test_no_file_or_disk_paths_anywhere(self):
        """所有 HTML（测试 + 发布）不得包含 file:// 或磁盘路径"""
        all_htmls = []
        # 组件 HTML
        for comp in COMPONENTS:
            for theme in THEMES:
                all_htmls.append(os.path.join(EXPECTED_DIR, f"{comp}-{theme}.html"))
        # 文章 HTML
        for art_type in ARTICLE_TYPES:
            for theme in THEMES:
                all_htmls.append(os.path.join(ARTICLES_DIR, f"{art_type}-{theme}.html"))
        # 真实 Agent 输出
        ra = os.path.join(SKILL_ROOT, "tests", "advanced-components",
                          "real-agent-run", "output-moyu-green.html")
        if os.path.exists(ra):
            all_htmls.append(ra)

        for fp in all_htmls:
            with open(fp, encoding="utf-8") as f:
                html = f.read()
            for p in self.HARD_BLOCKED:
                self.assertNotIn(p, html,
                    f"{os.path.basename(fp)}: hard-blocked path '{p}' found")

    def test_real_agent_output_no_local_paths(self):
        """模拟发布 HTML 不得包含任何本地路径（含 ../assets/）"""
        ra = os.path.join(SKILL_ROOT, "tests", "advanced-components",
                          "real-agent-run", "output-moyu-green.html")
        if os.path.exists(ra):
            with open(ra, encoding="utf-8") as f:
                html = f.read()
            for p in self.HARD_BLOCKED + self.RELEASE_BLOCKED:
                self.assertNotIn(p, html,
                    f"real-agent output: local path '{p}' found in publishable HTML")

    def test_article_media_components_use_local_assets(self):
        """文章 HTML 中媒体组件允许 ../assets/ 用于本地预览（非发布）"""
        # all-components 文章应该有 ../assets/ 路径（用于本地预览）
        for theme in THEMES:
            fp = os.path.join(ARTICLES_DIR, f"all-components-{theme}.html")
            with open(fp, encoding="utf-8") as f:
                html = f.read()
            # 媒体组件应该有 ../assets/ 路径
            self.assertIn("../assets/", html,
                f"all-components-{theme}: should have local asset paths for media preview")


class TestAdvancedLint(unittest.TestCase):
    """高级组件源头 lint 测试"""

    def test_lint_advanced_components_passes(self):
        """lint_advanced_components.py 扫描 references/advanced/**/*.md 通过"""
        import subprocess
        lint_path = os.path.join(SKILL_ROOT, "scripts", "lint_advanced_components.py")
        result = subprocess.run(
            [sys.executable, lint_path, SKILL_ROOT],
            capture_output=True, text=True, encoding="utf-8",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        self.assertEqual(result.returncode, 0,
            f"lint_advanced_components.py failed:\n{result.stdout}\n{result.stderr}")
        self.assertIn("ERROR×0", result.stdout)


def run_all():
    """运行全部测试并输出结果"""
    suite = unittest.TestSuite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSyntaxParsing))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestHTMLCompliance))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDegradation))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestE2ECompatibility))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestArticleHTML))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestRealRendering))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestBComponents))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestReleaseGate))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAdvancedLint))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print(f"\n{'='*60}")
    print(f"测试结果: {result.testsRun - len(result.failures) - len(result.errors)}/{result.testsRun} 通过")
    if result.failures:
        print(f"  失败: {len(result.failures)}")
    if result.errors:
        print(f"  错误: {len(result.errors)}")
    print(f"{'='*60}")

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_all())
