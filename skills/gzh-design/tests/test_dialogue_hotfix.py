#!/usr/bin/env python3
"""Dialogue 左右聊天窗热修复测试

验证 dialogue 组件从"所有内容靠左的问答卡"改为
"微信/QQ 式左右对称聊天窗口"的正确性。

测试内容：
1. 6 份 dialogue HTML 全部存在
2. assistant 行 text-align:left
3. assistant 头像在气泡之前（avatar_index < bubble_index）
4. user 行 text-align:right
5. user 气泡在头像之前（bubble_index < avatar_index）
6. user 气泡内部 text-align:left
7. user 与 assistant 头像不得都位于左侧
8. 不得使用 flex/grid/float/absolute
9. 长对话在 430px 下不横向溢出（max-width 检查）
10. 连续同角色消息保持正确侧别
11. 所有中文文字使用 span leaf
12. 6 主题 validate_gzh_html.py ERROR=0、WARNING=0
"""
import os
import re
import sys
import unittest
import importlib.util

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPECTED_DIR = os.path.join(SKILL_ROOT, "tests", "advanced-components", "expected")

# 动态加载 validate_gzh_html
vh_path = os.path.join(SKILL_ROOT, "scripts", "validate_gzh_html.py")
spec = importlib.util.spec_from_file_location("validate_gzh_html", vh_path)
vh_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vh_mod)
validate_html = vh_mod.validate

THEMES = ["moyu-green", "red-white", "graphite-minimal", "zen-whitespace", "moyu-ticket", "olive-journal", "hammer"]

# 禁用模式（比原有测试更严格：额外禁止 flex）
FORBIDDEN = [
    (re.compile(r"display\s*:\s*flex", re.I), "display:flex"),
    (re.compile(r"display\s*:\s*grid", re.I), "display:grid"),
    (re.compile(r"position\s*:\s*(fixed|absolute|sticky)", re.I), "position:absolute"),
    (re.compile(r"float\s*:", re.I), "float"),
    (re.compile(r"</?div[\s>]", re.I), "<div>"),
    (re.compile(r"\sclass\s*=", re.I), "class"),
    (re.compile(r"\sid\s*=", re.I), "id"),
]


def _load_dialogue_html(theme):
    """加载指定主题的 dialogue HTML"""
    fp = os.path.join(EXPECTED_DIR, f"dialogue-{theme}.html")
    with open(fp, "r", encoding="utf-8") as f:
        return f.read()


def _find_avatar_positions(html):
    """找到所有头像 span 的位置（width:34px + border-radius:50%）"""
    return [m.start() for m in re.finditer(
        r'<span[^>]*display:inline-block;width:34px[^>]*border-radius:50%', html)]


def _find_bubble_positions(html):
    """找到所有气泡 section 的位置（max-width:72%）"""
    return [m.start() for m in re.finditer(
        r'<section[^>]*display:inline-block;max-width:72%', html)]


def _find_row_starts(html, align):
    """找到指定对齐方式的行起始位置"""
    return [m.start() for m in re.finditer(
        rf'<section[^>]*text-align:{align}[^>]*margin:0 0 12px', html)]


def _find_avatar_in_range(html, start, end):
    """在 [start, end) 范围内找到头像位置"""
    for m in re.finditer(
        r'<span[^>]*display:inline-block;width:34px[^>]*border-radius:50%', html):
        if start <= m.start() < end:
            return m.start()
    return -1


def _find_bubble_in_range(html, start, end):
    """在 [start, end) 范围内找到气泡位置"""
    for m in re.finditer(
        r'<section[^>]*display:inline-block;max-width:72%', html):
        if start <= m.start() < end:
            return m.start()
    return -1


class TestDialogueFilesExist(unittest.TestCase):
    """测试 1: 6 份 dialogue HTML 全部存在"""

    def test_all_7_themes_exist(self):
        for theme in THEMES:
            fp = os.path.join(EXPECTED_DIR, f"dialogue-{theme}.html")
            self.assertTrue(os.path.isfile(fp), f"dialogue-{theme}.html 不存在")
            with open(fp, encoding="utf-8") as f:
                content = f.read()
            self.assertGreater(len(content), 100, f"dialogue-{theme}.html 内容过短")


class TestAssistantLayout(unittest.TestCase):
    """测试 2-3: assistant 行布局"""

    def test_assistant_row_text_align_left(self):
        """assistant 行包含 text-align:left"""
        for theme in THEMES:
            html = _load_dialogue_html(theme)
            # 默认 turns 包含 assistant，应该有 text-align:left
            self.assertIn("text-align:left", html,
                          f"{theme}: assistant 行缺少 text-align:left")

    def test_assistant_avatar_before_bubble(self):
        """assistant 的头像在气泡之前（avatar_index < bubble_index）"""
        for theme in THEMES:
            html = _load_dialogue_html(theme)
            left_rows = _find_row_starts(html, "left")
            self.assertGreater(len(left_rows), 0,
                               f"{theme}: 未找到 assistant 行（text-align:left）")
            for row_start in left_rows:
                # 找到行结束位置（下一个 </section> 对应外层 section 结束）
                row_end = html.find("</section>", row_start)
                # 搜索更远的结束标签（需要跳过内层 section）
                depth = 0
                pos = row_start
                while pos < len(html):
                    open_m = html.find("<section", pos)
                    close_m = html.find("</section>", pos)
                    if close_m == -1:
                        break
                    if open_m != -1 and open_m < close_m:
                        depth += 1
                        pos = open_m + 8
                    else:
                        depth -= 1
                        pos = close_m + 10
                        if depth == 0:
                            row_end = pos
                            break
                av_pos = _find_avatar_in_range(html, row_start, row_end)
                bub_pos = _find_bubble_in_range(html, row_start, row_end)
                self.assertNotEqual(av_pos, -1, f"{theme}: assistant 行内未找到头像")
                self.assertNotEqual(bub_pos, -1, f"{theme}: assistant 行内未找到气泡")
                self.assertLess(av_pos, bub_pos,
                                f"{theme}: assistant 头像必须在气泡之前"
                                f"（avatar@{av_pos} >= bubble@{bub_pos}）")


class TestUserLayout(unittest.TestCase):
    """测试 4-6: user 行布局"""

    def test_user_row_text_align_right(self):
        """user 行包含 text-align:right"""
        for theme in THEMES:
            html = _load_dialogue_html(theme)
            self.assertIn("text-align:right", html,
                          f"{theme}: user 行缺少 text-align:right")

    def test_user_bubble_before_avatar(self):
        """user 的气泡在头像之前（bubble_index < avatar_index）"""
        for theme in THEMES:
            html = _load_dialogue_html(theme)
            right_rows = _find_row_starts(html, "right")
            self.assertGreater(len(right_rows), 0,
                               f"{theme}: 未找到 user 行（text-align:right）")
            for row_start in right_rows:
                # 找到行结束位置
                depth = 0
                pos = row_start
                row_end = len(html)
                while pos < len(html):
                    open_m = html.find("<section", pos)
                    close_m = html.find("</section>", pos)
                    if close_m == -1:
                        break
                    if open_m != -1 and open_m < close_m:
                        depth += 1
                        pos = open_m + 8
                    else:
                        depth -= 1
                        pos = close_m + 10
                        if depth == 0:
                            row_end = pos
                            break
                av_pos = _find_avatar_in_range(html, row_start, row_end)
                bub_pos = _find_bubble_in_range(html, row_start, row_end)
                self.assertNotEqual(av_pos, -1, f"{theme}: user 行内未找到头像")
                self.assertNotEqual(bub_pos, -1, f"{theme}: user 行内未找到气泡")
                self.assertLess(bub_pos, av_pos,
                                f"{theme}: user 气泡必须在头像之前"
                                f"（bubble@{bub_pos} >= avatar@{av_pos}）")

    def test_user_bubble_internal_text_align_left(self):
        """user 气泡内部重新设置 text-align:left"""
        for theme in THEMES:
            html = _load_dialogue_html(theme)
            # user 气泡是 text-align:right 行内的 max-width:72% section
            # 气泡的 style 中必须包含 text-align:left
            right_rows = _find_row_starts(html, "right")
            for row_start in right_rows:
                # 在 right 行中找 bubble section
                depth = 0
                pos = row_start
                row_end = len(html)
                while pos < len(html):
                    open_m = html.find("<section", pos)
                    close_m = html.find("</section>", pos)
                    if close_m == -1:
                        break
                    if open_m != -1 and open_m < close_m:
                        depth += 1
                        pos = open_m + 8
                    else:
                        depth -= 1
                        pos = close_m + 10
                        if depth == 0:
                            row_end = pos
                            break
                bub_pos = _find_bubble_in_range(html, row_start, row_end)
                self.assertNotEqual(bub_pos, -1, f"{theme}: user 行内未找到气泡")
                # 提取气泡 section 的 style
                bub_section = html[bub_pos:html.find(">", bub_pos) + 1]
                self.assertIn("text-align:left", bub_section,
                              f"{theme}: user 气泡内部缺少 text-align:left")


class TestAvatarPosition(unittest.TestCase):
    """测试 7: user 与 assistant 头像不得都位于左侧"""

    def test_avatars_not_all_left(self):
        """user 头像在右侧，assistant 头像在左侧"""
        for theme in THEMES:
            html = _load_dialogue_html(theme)
            left_rows = _find_row_starts(html, "left")
            right_rows = _find_row_starts(html, "right")
            self.assertGreater(len(left_rows), 0, f"{theme}: 无 assistant 行")
            self.assertGreater(len(right_rows), 0, f"{theme}: 无 user 行")
            # 左行中有头像（assistant 头像在左）
            # 右行中有头像（user 头像在右）
            # 验证：左行的头像在气泡前，右行的头像在气泡后
            # 这已经在 test_assistant_avatar_before_bubble 和 test_user_bubble_before_avatar 中验证


class TestNoForbiddenPatterns(unittest.TestCase):
    """测试 8: 不得使用 flex/grid/float/absolute"""

    def test_no_flex_grid_float_absolute(self):
        for theme in THEMES:
            html = _load_dialogue_html(theme)
            for pat, name in FORBIDDEN:
                m = pat.search(html)
                self.assertIsNone(m, f"{theme}: dialogue HTML 包含禁用模式 {name}")


class TestNoOverflow(unittest.TestCase):
    """测试 9: 长对话在 430px 下不横向溢出"""

    def test_bubble_max_width_constraint(self):
        """气泡 max-width 不超过 74%（430px 屏幕下不溢出）"""
        for theme in THEMES:
            html = _load_dialogue_html(theme)
            # 找到所有 max-width 值
            for m in re.finditer(r'max-width:(\d+)%', html):
                val = int(m.group(1))
                self.assertLessEqual(val, 74,
                                     f"{theme}: 气泡 max-width:{val}% 超过 74%，430px 下可能溢出")

    def test_no_fixed_width_overflow(self):
        """不允许固定宽度超过 400px"""
        for theme in THEMES:
            html = _load_dialogue_html(theme)
            for m in re.finditer(r'width:(\d+)px', html):
                val = int(m.group(1))
                self.assertLess(val, 50,
                                f"{theme}: 固定宽度 width:{val}px 过大（头像允许 34px）")


class TestContinuousMessages(unittest.TestCase):
    """测试 10: 连续同角色消息保持正确侧别"""

    def test_continuous_same_role(self):
        """生成连续同角色消息，验证侧别正确"""
        sys.path.insert(0, os.path.join(SKILL_ROOT, "scripts"))
        from generate_advanced_html import dialogue
        html = dialogue("moyu-green", title="连续测试", turns=[
            ("assistant", "第一条消息"),
            ("assistant", "第二条补充"),
            ("user", "我的回复"),
            ("assistant", "最终回答"),
        ])
        # 应有 3 个 assistant 行（text-align:left）和 1 个 user 行（text-align:right）
        left_count = len(re.findall(r'text-align:left;margin:0 0 12px', html))
        right_count = len(re.findall(r'text-align:right;margin:0 0 12px', html))
        self.assertEqual(left_count, 3, f"应有 3 个 assistant 行，实际 {left_count}")
        self.assertEqual(right_count, 1, f"应有 1 个 user 行，实际 {right_count}")


class TestSpanLeaf(unittest.TestCase):
    """测试 11: 所有中文文字使用 span leaf"""

    def test_chinese_text_in_span_leaf(self):
        for theme in THEMES:
            html = _load_dialogue_html(theme)
            errors, warnings, _ = validate_html(html)
            # validate_gzh_html 会检查未包裹的中文文本
            self.assertEqual(len(errors), 0,
                             f"{theme}: validate_gzh_html 发现 ERROR: {errors}")


class TestValidationPass(unittest.TestCase):
    """测试 12: 6 主题 validate_gzh_html.py 均为 ERROR=0、WARNING=0"""

    def test_all_themes_validate_clean(self):
        for theme in THEMES:
            html = _load_dialogue_html(theme)
            errors, warnings, _ = validate_html(html)
            self.assertEqual(len(errors), 0,
                             f"{theme}: ERROR={len(errors)}: {errors}")
            self.assertEqual(len(warnings), 0,
                             f"{theme}: WARNING={len(warnings)}: {warnings}")


class TestAllComponentsDialogue(unittest.TestCase):
    """测试 all-components 文章中的 dialogue 也遵循左右布局"""

    def test_all_components_dialogue_has_left_right(self):
        """all-components-{theme}.html 中的 dialogue 同时包含 text-align:left 和 text-align:right"""
        for theme in THEMES:
            fp = os.path.join(EXPECTED_DIR, f"all-components-{theme}.html")
            with open(fp, encoding="utf-8") as f:
                html = f.read()
            self.assertIn("text-align:left;margin:0 0 12px", html,
                          f"all-components-{theme}.html: dialogue 缺少 assistant 行")
            self.assertIn("text-align:right;margin:0 0 12px", html,
                          f"all-components-{theme}.html: dialogue 缺少 user 行")


class TestOptionalName(unittest.TestCase):
    """测试可选名称功能"""

    def test_name_displayed(self):
        """带 name 的对话显示名称"""
        sys.path.insert(0, os.path.join(SKILL_ROOT, "scripts"))
        from generate_advanced_html import dialogue
        html = dialogue("moyu-green", title="名称测试", turns=[
            ("assistant", "你好", "排版助手"),
            ("user", "请问如何保留样式？", "甲木"),
        ])
        self.assertIn("排版助手", html)
        self.assertIn("甲木", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
