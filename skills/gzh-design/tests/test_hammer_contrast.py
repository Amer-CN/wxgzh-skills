#!/usr/bin/env python3
"""锤子主题对比度热修回归测试 —— 11 项

测试项目：
1.  删除线文字不得使用 #999
2.  删除线文字不得使用 rgba(202,202,199,...)
3.  可见文字不得使用 color:rgba(202,202,199,...)
4.  小号砖红文字在浅背景上使用 #9F452C（而非 #B3593B）
5.  删除线文字使用 #737373
6.  删除线颜色使用 #B3593B（text-decoration-color）
6b. 固定品牌句使用 #8A4530（而非 #B3593B）
7.  正常正文对比度不得低于 4.5:1（含 #8A4530/#EAD6CC、#737373/#F7F7F7 FAIL 判定）
8.  大号粗体文字不得低于 3:1（14px/600 不属于大号文字）
9.  7 个主题原有测试不回归（导入检查）
10. 430px 无横向溢出

对比度判定规则：
- 使用未四舍五入的原始值比较（assert contrast_ratio >= 4.5）
- 14px/600 一律按普通文字 4.5:1 检查
- 只有 24px+/900 或 18px+/700 才按大号文字 3:1 检查
"""
import os
import re
import sys
import unittest
import importlib.util

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REFERENCES_DIR = os.path.join(SKILL_ROOT, "references")
THEME_HAMMER = os.path.join(REFERENCES_DIR, "theme-hammer.md")

# 动态加载 validate_gzh_html
vh_path = os.path.join(SKILL_ROOT, "scripts", "validate_gzh_html.py")
spec = importlib.util.spec_from_file_location("validate_gzh_html", vh_path)
vh_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vh_mod)
validate_html = vh_mod.validate


def _read_k3_article():
    """读取 K3 文章 HTML。"""
    path = os.path.join(
        SKILL_ROOT, "..", "..", "..", "articles",
        "01-k3-luan-zhan-shi-dai_hammer(hammer).html"
    )
    path = os.path.normpath(path)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _read_theme_hammer():
    """读取锤子主题文档。"""
    if not os.path.exists(THEME_HAMMER):
        return None
    with open(THEME_HAMMER, "r", encoding="utf-8") as f:
        return f.read()


# ---- 对比度辅助函数 ----

def _hex_to_rgb(hex_color):
    """#RRGGBB -> (r, g, b)"""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _relative_luminance(rgb):
    """计算相对亮度（WCAG 2.1）"""
    def _linear(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb
    return 0.2126 * _linear(r) + 0.7152 * _linear(g) + 0.0722 * _linear(b)


def _contrast_ratio(hex_fg, hex_bg):
    """计算前景/背景对比度"""
    fg_lum = _relative_luminance(_hex_to_rgb(hex_fg))
    bg_lum = _relative_luminance(_hex_to_rgb(hex_bg))
    lighter = max(fg_lum, bg_lum)
    darker = min(fg_lum, bg_lum)
    return (lighter + 0.05) / (darker + 0.05)


class TestHammerContrast(unittest.TestCase):
    """锤子主题对比度热修回归测试。"""

    # 1. 删除线文字不得使用 #999
    def test_01_no_999_in_strikethrough(self):
        """删除线文字不得使用 color:#999。"""
        article = _read_k3_article()
        if not article:
            self.skipTest("K3 文章不存在")
        # 检查 line-through 附近是否有 color:#999
        # 同时检查 color:#999 是否出现在任何带 line-through 的元素中
        # 先全局检查：任何 color:#999 都是禁止的
        # 但我们只关注删除线上下文，这里全面检查 color:#999 用于文字
        matches = re.findall(r'color:\s*#999', article, re.IGNORECASE)
        self.assertEqual(len(matches), 0,
            f"发现 {len(matches)} 处 color:#999（已废弃），应统一使用 #737373")

    # 2. 删除线文字不得使用 rgba(202,202,199,...)
    def test_02_no_light_gray_in_strikethrough(self):
        """删除线文字不得使用 rgba(202,202,199,...) 作为文字色。"""
        article = _read_k3_article()
        if not article:
            self.skipTest("K3 文章不存在")
        # 查找所有包含 line-through 且 color:rgba(202,202,199,...) 的样式
        # 匹配模式：color:rgba(202,202,199,...)...text-decoration...line-through
        # 或 text-decoration...line-through...color:rgba(202,202,199,...)
        strikethrough_with_light_gray = re.findall(
            r'(?:color:\s*rgba\(202,\s*202,\s*199[^)]*\)[^"\']*text-decoration[^"\']*line-through'
            r'|text-decoration[^"\']*line-through[^"\']*color:\s*rgba\(202,\s*202,\s*199[^)]*\))',
            article, re.IGNORECASE
        )
        self.assertEqual(len(strikethrough_with_light_gray), 0,
            f"发现 {len(strikethrough_with_light_gray)} 处删除线文字使用 rgba(202,202,199,...)，应使用 #737373")

    # 3. 可见文字不得使用 color:rgba(202,202,199,...)
    def test_03_no_light_gray_text_color(self):
        """可见文字不得使用 color:rgba(202,202,199,...) 作为文字色。
        注意：只检查 color 属性，不删除边框和背景中的 rgba(202,202,199,...)。"""
        article = _read_k3_article()
        if not article:
            self.skipTest("K3 文章不存在")
        # 逐个检查 style="..." 中是否有 color:rgba(202,202,199,...)
        # 但排除 background / border 中的 rgba(202,202,199,...)
        style_attrs = re.findall(r'style="([^"]*)"', article)
        bad_count = 0
        for style in style_attrs:
            # 分解每个属性
            props = re.split(r';\s*', style)
            for prop in props:
                prop = prop.strip()
                if prop.startswith('color:') and 'rgba(202,202,199' in prop:
                    bad_count += 1
                    break  # 每个 style 属性只算一次
        self.assertEqual(bad_count, 0,
            f"发现 {bad_count} 处可见文字使用 color:rgba(202,202,199,...)，应使用 #737373")

    # 4. 小号砖红文字在浅背景上使用 #9F452C
    def test_04_small_brick_red_uses_dark_variant(self):
        """小号砖红文字（11px 标签、14px body strong）在浅背景上使用 #9F452C，
        而非 #B3593B。"""
        article = _read_k3_article()
        if not article:
            self.skipTest("K3 文章不存在")
        # 检查 11px 标签不应使用 #B3593B
        # 模式：font-size:11px...color:#B3593B 或 color:#B3593B...font-size:11px
        style_attrs = re.findall(r'style="([^"]*)"', article)
        bad_11px = 0
        bad_strong = 0
        for tag, style in re.findall(r'<(\w+)\s+style="([^"]*)"', article):
            props = dict(
                (m.group(1).strip(), m.group(2).strip())
                for m in re.finditer(r'([\w-]+)\s*:\s*([^;]+)', style)
            )
            font_size = props.get('font-size', '')
            color = props.get('color', '')
            # 11px 标签不应使用 #B3593B
            if '11px' in font_size and color.upper() == '#B3593B':
                bad_11px += 1
            # <strong> 标签（14px body emphasis）不应使用 #B3593B
            if tag == 'strong' and color.upper() == '#B3593B':
                bad_strong += 1
        self.assertEqual(bad_11px, 0,
            f"发现 {bad_11px} 处 11px 标签使用 #B3593B，应使用 #9F452C")
        self.assertEqual(bad_strong, 0,
            f"发现 {bad_strong} 处 <strong> 使用 #B3593B，应使用 #9F452C")

    # 5. 删除线文字使用 #737373
    def test_05_strikethrough_text_color_is_737373(self):
        """删除线文字使用 color:#737373。"""
        article = _read_k3_article()
        if not article:
            self.skipTest("K3 文章不存在")
        # 收集所有带 line-through 的样式
        strikethrough_styles = []
        for tag, style in re.findall(r'<(\w+)\s+style="([^"]*)"', article):
            if 'line-through' in style:
                props = dict(
                    (m.group(1).strip(), m.group(2).strip())
                    for m in re.finditer(r'([\w-]+)\s*:\s*([^;]+)', style)
                )
                color = props.get('color', '')
                strikethrough_styles.append(color)
        # 至少要有删除线文字
        self.assertGreater(len(strikethrough_styles), 0,
            "K3 文章应包含删除线文字（如'中国品牌只能靠便宜？'等）")
        # 所有删除线文字的 color 必须是 #737373
        for color in strikethrough_styles:
            self.assertEqual(color.upper(), '#737373',
                f"删除线文字 color 应为 #737373，实际为 {color}")

    # 6. 删除线颜色使用 #B3593B
    def test_06_strikethrough_decoration_color_is_brick(self):
        """删除线颜色（text-decoration-color）使用 #B3593B。"""
        article = _read_k3_article()
        if not article:
            self.skipTest("K3 文章不存在")
        # 收集所有带 line-through 的样式，检查 text-decoration-color
        for tag, style in re.findall(r'<(\w+)\s+style="([^"]*)"', article):
            if 'line-through' in style:
                props = dict(
                    (m.group(1).strip(), m.group(2).strip())
                    for m in re.finditer(r'([\w-]+)\s*:\s*([^;]+)', style)
                )
                deco_color = props.get('text-decoration-color', '')
                self.assertEqual(deco_color.upper(), '#B3593B',
                    f"删除线 text-decoration-color 应为 #B3593B，实际为 {deco_color}")

    # 6b. 固定品牌句使用 #8A4530（而非 #B3593B）
    def test_06b_brand_sentence_uses_dark_variant(self):
        """固定品牌句（14px/600 在 #EAD6CC 底上）使用 #8A4530，不得使用 #B3593B。"""
        article = _read_k3_article()
        if not article:
            self.skipTest("K3 文章不存在")
        # 品牌句的 background:#EAD6CC 在外层 <section> 上，<p> 标签只有 color
        # 检查所有 14px/600 的 <p> 标签中 color 为 #8A4530 的数量
        brand_count = 0
        bad_brand_count = 0
        for tag, style in re.findall(r'<(\w+)\s+style="([^"]*)"', article):
            if tag != 'p':
                continue
            props = dict(
                (m.group(1).strip(), m.group(2).strip())
                for m in re.finditer(r'([\w-]+)\s*:\s*([^;]+)', style)
            )
            color = props.get('color', '')
            font_size = props.get('font-size', '')
            font_weight = props.get('font-weight', '')
            # 14px/600 的品牌句
            if '14px' in font_size and '600' in font_weight:
                if color.upper() == '#8A4530':
                    brand_count += 1
                elif color.upper() == '#B3593B':
                    bad_brand_count += 1
        # K3 文章应至少有 2 句品牌句使用 #8A4530
        self.assertGreaterEqual(brand_count, 2,
            f"K3 文章应包含至少 2 句使用 #8A4530 的固定品牌句，实际 {brand_count} 句")
        # 不得有品牌句使用 #B3593B
        self.assertEqual(bad_brand_count, 0,
            f"发现 {bad_brand_count} 句品牌句使用 #B3593B（应使用 #8A4530）")

    # 7. 正常正文对比度不得低于 4.5:1
    def test_07_body_text_contrast_at_least_45(self):
        """正文文字对比度 ≥ 4.5:1（使用未四舍五入的原始值判定）。"""
        # #555555 on #FFFFFF
        ratio = _contrast_ratio('#555555', '#FFFFFF')
        self.assertGreaterEqual(ratio, 4.5,
            f"正文色 #555555 在白底上对比度 {ratio}:1，低于 4.5:1")
        # #737373（次要文字）on #FFFFFF
        ratio_secondary = _contrast_ratio('#737373', '#FFFFFF')
        self.assertGreaterEqual(ratio_secondary, 4.5,
            f"次要文字 #737373 在白底上对比度 {ratio_secondary}:1，低于 4.5:1")
        # #737373 on #F7F7F7 — 必须 FAIL（4.45:1 < 4.5:1）
        ratio_secondary_f7 = _contrast_ratio('#737373', '#F7F7F7')
        self.assertLess(ratio_secondary_f7, 4.5,
            f"#737373 在 #F7F7F7 底上对比度 {ratio_secondary_f7}:1，应低于 4.5:1（若用于此背景需改用 #6B6B6B）")
        # #9F452C（深砖红）on #FFFFFF
        ratio_brick = _contrast_ratio('#9F452C', '#FFFFFF')
        self.assertGreaterEqual(ratio_brick, 4.5,
            f"深砖红 #9F452C 在白底上对比度 {ratio_brick}:1，低于 4.5:1")
        # #9F452C on #F7F7F7
        ratio_brick_f7 = _contrast_ratio('#9F452C', '#F7F7F7')
        self.assertGreaterEqual(ratio_brick_f7, 4.5,
            f"深砖红 #9F452C 在 #F7F7F7 底上对比度 {ratio_brick_f7}:1，低于 4.5:1")
        # #8A4530（固定品牌句深砖红）on #EAD6CC — 14px/600 属于普通文字，必须 ≥ 4.5:1
        ratio_brand = _contrast_ratio('#8A4530', '#EAD6CC')
        self.assertGreaterEqual(ratio_brand, 4.5,
            f"固定品牌句 #8A4530 在 #EAD6CC 底上对比度 {ratio_brand}:1，低于 4.5:1（14px/600 属于普通文字）")
        # #B3593B on #EAD6CC — 14px/600 必须 FAIL（3.40:1 < 4.5:1）
        ratio_brick_ead = _contrast_ratio('#B3593B', '#EAD6CC')
        self.assertLess(ratio_brick_ead, 4.5,
            f"#B3593B 在 #EAD6CC 底上对比度 {ratio_brick_ead}:1，应低于 4.5:1（不可用于 14px/600 品牌句）")

    # 8. 大号粗体文字不得低于 3:1
    def test_08_large_bold_contrast_at_least_30(self):
        """大号粗体文字（#B3593B, 24px+/900）在白色背景上对比度 ≥ 3:1。
        注意：14px/600 不属于大号文字，必须满足 4.5:1（在 test_07 中检查）。"""
        # #B3593B on #FFFFFF（大号粗体使用场景）
        ratio = _contrast_ratio('#B3593B', '#FFFFFF')
        self.assertGreaterEqual(ratio, 3.0,
            f"主砖红 #B3593B 在白底上对比度 {ratio}:1，低于 3:1（大号粗体最低要求）")
        # #B3593B on #FAF9F5
        ratio_faf = _contrast_ratio('#B3593B', '#FAF9F5')
        self.assertGreaterEqual(ratio_faf, 3.0,
            f"主砖红 #B3593B 在 #FAF9F5 底上对比度 {ratio_faf}:1，低于 3:1")
        # #B3593B on #EAD6CC — 大号粗体场景（如 24px+/900 标题）
        ratio_ead = _contrast_ratio('#B3593B', '#EAD6CC')
        self.assertGreaterEqual(ratio_ead, 3.0,
            f"主砖红 #B3593B 在 #EAD6CC 底上对比度 {ratio_ead}:1，低于 3:1（大号粗体）")
        # 但 14px/600 品牌句不得使用 #B3593B on #EAD6CC（仅 3.40:1 < 4.5:1）
        # 这个检查在 test_07 中已完成

    # 9. 7 个主题原有测试不回归（导入检查）
    def test_09_existing_tests_importable(self):
        """原有测试套件可正常导入（不回归）。"""
        test_files = [
            "test_advanced_components.py",
            "test_dialogue_hotfix.py",
            "test_publish_hotfix.py",
            "test_fixed_signature.py",
        ]
        for tf in test_files:
            tf_path = os.path.join(SKILL_ROOT, "tests", tf)
            if not os.path.exists(tf_path):
                continue
            spec = importlib.util.spec_from_file_location(tf.replace(".py", ""), tf_path)
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
            except Exception as e:
                self.fail(f"导入 {tf} 失败：{e}")

    # 10. 430px 无横向溢出
    def test_10_no_horizontal_overflow_430px(self):
        """K3 文章在 430px 宽度下无横向溢出。"""
        article = _read_k3_article()
        if not article:
            self.skipTest("K3 文章不存在")
        # 只检测固定 width（非 max-width），排除 677px 标准容器最大宽度
        fixed_widths = re.findall(r'(?<!max-)width\s*:\s*(\d+)px', article)
        for w in fixed_widths:
            self.assertLessEqual(int(w), 430,
                f"发现固定宽度 {w}px 超过 430px，可能横向溢出")
        # 检查没有 position:absolute/fixed/sticky
        errors, _, _ = validate_html(article)
        position_errors = [e for e in errors if "position" in e.lower()]
        self.assertEqual(len(position_errors), 0,
            f"不得使用 position:absolute/fixed/sticky：{position_errors}")
        # validator ERROR=0
        self.assertEqual(len(errors), 0,
            f"validator 发现 ERROR：{errors}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
