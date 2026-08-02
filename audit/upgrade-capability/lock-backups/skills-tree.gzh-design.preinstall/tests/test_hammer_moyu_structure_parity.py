#!/usr/bin/env python3
"""锤子主题 ↔ 摸鱼绿主题 结构同构测试。

测试目标：
1. 两个主题都包含相同的 13 个主组件
2. 完整文章骨架顺序一致
3. 组件 HTML 去除颜色相关声明后，核心结构一致
4. 以下属性应一致：font-size, line-height, letter-spacing, margin, padding, gap,
   width/max-width, border-radius, display/flex 相关属性
5. 允许颜色、背景色、边框颜色和阴影颜色不同
6. 锤子主题不存在摸鱼绿色值残留
7. 摸鱼绿主题不被本任务修改
8. 其他主题不回归
"""

import os
import re
import sys
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
THEME_DIR = SKILL_ROOT / "references"

MOYU_FILE = THEME_DIR / "theme-moyu-green.md"
HAMMER_FILE = THEME_DIR / "theme-hammer.md"

# 摸鱼绿色值（不得出现在锤子主题中）
MOYU_GREEN_TOKENS = [
    "#059669", "#10b981", "#047857", "#34d399",
    "#6ee7b7", "#a7f3d0", "#bbf7d0", "#ecfdf5", "#f0fdf4",
]

# 锤子色值（不得出现在摸鱼绿主题中——仅验证未交叉污染）
HAMMER_TOKENS = ["#b3593b", "#c86442", "#8a4530", "#dab1a1", "#e3c6b9", "#ead6cc"]

# 13 个主组件标题模式
EXPECTED_COMPONENTS = [
    "组件 1 全局容器",
    "组件 2 封面",
    "组件 3 目录",
    "组件 4 章节标题",
    "组件 5 正文段落",
    "组件 6 行内样式",
    "组件 7 内容标签组",
    "组件 8 代码",
    "组件 9 引用与亮点",
    "组件 10 提示与信息",
    "组件 11 布局组件",
    "组件 12 媒体组件",
    "组件 13 结尾组件",
]

# 骨架步骤
EXPECTED_SKELETON_STEPS = [
    "1. 封面",
    "2. 目录",
    "3. 开头引言",
    "4. 前言正文",
    "5. 第一章",
    "6. 第二章",
    "7. 结语章",
    "8. 互动三连",
    "9. 品牌尾图",
]

# 需要对比的结构属性（不含颜色相关）
STRUCTURAL_PROPERTIES = [
    "font-size",
    "line-height",
    "letter-spacing",
    "margin",
    "margin-top",
    "margin-bottom",
    "margin-left",
    "margin-right",
    "padding",
    "padding-top",
    "padding-bottom",
    "padding-left",
    "padding-right",
    "gap",
    "width",
    "max-width",
    "min-width",
    "height",
    "min-height",
    "border-radius",
    "border-width",
    "display",
    "flex",
    "flex-direction",
    "align-items",
    "justify-content",
    "flex-wrap",
    "flex-shrink",
    "flex-grow",
    "overflow",
    "overflow-x",
    "overflow-y",
    "text-align",
    "text-transform",
    "white-space",
    "vertical-align",
    "border-collapse",
    "font-weight",
    "text-decoration",
]

# 颜色相关属性（允许不同）
COLOR_PROPERTIES = [
    "color", "background", "background-color", "border", "border-top",
    "border-bottom", "border-left", "border-right", "box-shadow",
    "border-color", "background-image",
]


def read_file(path):
    """读取文件内容（UTF-8）"""
    with open(path, encoding="utf-8") as f:
        return f.read()


def extract_code_blocks(md_text):
    """从 Markdown 中提取所有 ```html ... ``` 代码块"""
    pattern = r"```html\s*\n(.*?)```"
    return re.findall(pattern, md_text, re.DOTALL)


def extract_component_sections(md_text):
    """按 '## 组件 N' 标题切分 Markdown，返回 {标题: 内容} 字典"""
    pattern = r"(## (组件 \d+[^|\n]*))"
    matches = list(re.finditer(pattern, md_text))
    sections = {}
    for i, m in enumerate(matches):
        title = m.group(2).strip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md_text)
        content = md_text[start:end]
        sections[title] = content
    return sections


def extract_style_attrs(html):
    """从 HTML 字符串中提取所有 style 属性中的声明"""
    declarations = []
    for style_match in re.finditer(r'style="([^"]*)"', html):
        style_content = style_match.group(1)
        for decl in style_content.split(";"):
            decl = decl.strip()
            if ":" in decl:
                prop, val = decl.split(":", 1)
                prop = prop.strip().lower()
                val = val.strip()
                declarations.append((prop, val))
    return declarations


def filter_structural_props(declarations):
    """过滤出结构属性（非颜色属性）"""
    return [(p, v) for p, v in declarations if p in STRUCTURAL_PROPERTIES]


def normalize_prop_value(prop, val):
    """规范化属性值以便比较

    颜色相关的 rgba 值可能包含在非颜色属性中（如 border: 1px solid #xxx），
    但结构属性（font-size, padding 等）不应包含颜色。
    这里只处理结构属性的规范化。
    """
    # 去除前后空格，统一大小写
    val = val.strip().lower()
    # 去除 px 单位差异（14px vs 14px 一致即可）
    return val


class TestStructureParity(unittest.TestCase):
    """锤子主题与摸鱼绿主题的结构同构测试"""

    @classmethod
    def setUpClass(cls):
        cls.moyu_md = read_file(MOYU_FILE)
        cls.hammer_md = read_file(HAMMER_FILE)
        cls.moyu_sections = extract_component_sections(cls.moyu_md)
        cls.hammer_sections = extract_component_sections(cls.hammer_md)
        cls.moyu_code_blocks = extract_code_blocks(cls.moyu_md)
        cls.hammer_code_blocks = extract_code_blocks(cls.hammer_md)

    def test_01_both_have_13_components(self):
        """两个主题都包含相同的 13 个主组件"""
        for comp in EXPECTED_COMPONENTS:
            # 模糊匹配：组件标题可能含额外描述
            moyu_found = any(comp in s for s in self.moyu_sections)
            hammer_found = any(comp in s for s in self.hammer_sections)
            self.assertTrue(
                moyu_found,
                f"摸鱼绿缺少组件: {comp} (found: {list(self.moyu_sections.keys())})"
            )
            self.assertTrue(
                hammer_found,
                f"锤子缺少组件: {comp} (found: {list(self.hammer_sections.keys())})"
            )

    def test_02_skeleton_order_matches(self):
        """完整文章骨架顺序一致"""
        for step in EXPECTED_SKELETON_STEPS:
            moyu_found = step in self.moyu_md
            hammer_found = step in self.hammer_md
            self.assertTrue(moyu_found, f"摸鱼绿骨架缺少步骤: {step}")
            self.assertTrue(hammer_found, f"锤子骨架缺少步骤: {step}")

    def test_03_core_font_size_consistency(self):
        """核心字号一致：14px 正文 / 1.9 行高 / 0.5px 字间距 / 677px 最大宽度"""
        core_specs = [
            ("正文字号", "14px"),
            ("正文行高", "1.9"),
            ("全局行高", "1.75"),
            ("字间距", "0.5px"),
            ("最大宽度", "677px"),
        ]
        for name, val in core_specs:
            self.assertIn(val, self.moyu_md, f"摸鱼绿缺少核心规格: {name}={val}")
            self.assertIn(val, self.hammer_md, f"锤子缺少核心规格: {name}={val}")

    def test_04_component_structural_properties_match(self):
        """组件 HTML 去除颜色声明后，结构属性一致"""
        # 只从组件章节（## 组件 N）中提取代码块，排除锤子独有的语义色规则等非组件章节
        def extract_component_code_blocks(sections):
            """从组件 sections 字典中提取所有 HTML 代码块"""
            blocks = []
            for title, content in sections.items():
                if title.startswith("组件 "):
                    blocks.extend(extract_code_blocks(content))
            return blocks

        moyu_component_blocks = extract_component_code_blocks(self.moyu_sections)
        hammer_component_blocks = extract_component_code_blocks(self.hammer_sections)

        moyu_decls = filter_structural_props(
            extract_style_attrs("\n".join(moyu_component_blocks))
        )
        hammer_decls = filter_structural_props(
            extract_style_attrs("\n".join(hammer_component_blocks))
        )

        # 提取结构属性值的多重集（允许重复）
        moyu_prop_multiset = {}
        for prop, val in moyu_decls:
            key = f"{prop}:{normalize_prop_value(prop, val)}"
            moyu_prop_multiset[key] = moyu_prop_multiset.get(key, 0) + 1

        hammer_prop_multiset = {}
        for prop, val in hammer_decls:
            key = f"{prop}:{normalize_prop_value(prop, val)}"
            hammer_prop_multiset[key] = hammer_prop_multiset.get(key, 0) + 1

        # 找出差异
        all_keys = set(moyu_prop_multiset.keys()) | set(hammer_prop_multiset.keys())
        diffs = []
        for key in sorted(all_keys):
            m_count = moyu_prop_multiset.get(key, 0)
            h_count = hammer_prop_multiset.get(key, 0)
            if m_count != h_count:
                diffs.append(f"  {key}: moyu={m_count}, hammer={h_count}")

        if diffs:
            self.fail(
                "结构属性出现次数不一致（font-size/margin/padding/gap/border-radius 等）:\n"
                + "\n".join(diffs)
            )

    def test_05_no_moyu_green_tokens_in_hammer(self):
        """锤子主题不存在摸鱼绿色值残留"""
        hammer_lower = self.hammer_md.lower()
        found = []
        for token in MOYU_GREEN_TOKENS:
            if token in hammer_lower:
                # 找到出现位置以便报告
                for i, line in enumerate(self.hammer_md.split("\n"), 1):
                    if token in line.lower():
                        found.append(f"  line {i}: {token} in '{line.strip()[:80]}'")
                        break
        if found:
            self.fail(
                f"锤子主题中发现摸鱼绿色值残留:\n" + "\n".join(found)
            )

    def test_06_moyu_green_not_modified(self):
        """摸鱼绿主题未被本任务修改（检查不含锤子色值）"""
        moyu_lower = self.moyu_md.lower()
        found = []
        for token in HAMMER_TOKENS:
            if token in moyu_lower:
                for i, line in enumerate(self.moyu_md.split("\n"), 1):
                    if token in line.lower():
                        found.append(f"  line {i}: {token}")
                        break
        if found:
            self.fail(
                f"摸鱼绿主题中发现锤子色值（可能是交叉污染）:\n" + "\n".join(found)
            )

    def test_07_cover_has_both_versions(self):
        """封面有图版和无图版均存在"""
        for name, md in [("摸鱼绿", self.moyu_md), ("锤子", self.hammer_md)]:
            self.assertIn("有右侧图片版", md, f"{name}缺少'有右侧图片版'")
            self.assertIn("无右侧图片版", md, f"{name}缺少'无右侧图片版'")

    def test_08_toc_structure(self):
        """目录横向滚动结构：第一卡高亮 + 后续白底 + PART ///"""
        for name, sections in [("摸鱼绿", self.moyu_sections), ("锤子", self.hammer_sections)]:
            toc_section = ""
            for key, content in sections.items():
                if "组件 3" in key and "目录" in key:
                    toc_section = content
                    break
            self.assertIn("overflow-x:scroll", toc_section, f"{name}目录缺少横向滚动")
            self.assertIn("white-space:nowrap", toc_section, f"{name}目录缺少 nowrap")
            self.assertIn("PART 01", toc_section, f"{name}目录缺少 PART 01")
            self.assertIn("PART ///", toc_section, f"{name}目录缺少 PART ///")
            self.assertIn("写在最后", toc_section, f"{name}目录缺少'写在最后'")

    def test_09_chapter_title_structure(self):
        """章节标题：大编号 + PART + 竖线 + 中文标题 + 英文副标题"""
        for name, sections in [("摸鱼绿", self.moyu_sections), ("锤子", self.hammer_sections)]:
            ct_section = ""
            for key, content in sections.items():
                if "组件 4" in key and "章节标题" in key:
                    ct_section = content
                    break
            self.assertIn("font-size:28px", ct_section, f"{name}章节编号不是 28px")
            self.assertIn("font-size:8px", ct_section, f"{name}PART 不是 8px")
            self.assertIn("PART", ct_section, f"{name}缺少 PART")
            self.assertIn("font-size:17px", ct_section, f"{name}中文标题不是 17px")
            self.assertIn("font-size:11px", ct_section, f"{name}英文副标题不是 11px")
            self.assertIn("width:1px;height:36px", ct_section, f"{name}竖线结构不一致")

    def test_10_footer_cta_structure(self):
        """footer CTA：3 个按钮（点赞/在看/转发）+ THANKS FOR READING"""
        for name, sections in [("摸鱼绿", self.moyu_sections), ("锤子", self.hammer_sections)]:
            footer_section = ""
            for key, content in sections.items():
                if "组件 13" in key and ("结尾" in key or "footer" in key.lower()):
                    footer_section = content
                    break
            self.assertIn("点赞", footer_section, f"{name}footer缺少'点赞'")
            self.assertIn("在看", footer_section, f"{name}footer缺少'在看'")
            self.assertIn("转发", footer_section, f"{name}footer缺少'转发'")
            self.assertIn("THANKS FOR READING", footer_section, f"{name}缺少 THANKS FOR READING")
            self.assertIn("svg", footer_section.lower(), f"{name}footer缺少SVG图标")

    def test_11_inline_styles_count(self):
        """行内样式 9 种子组件都存在"""
        for name, md in [("摸鱼绿", self.moyu_md), ("锤子", self.hammer_md)]:
            for i in "abcdefghi":
                self.assertIn(f"### 6{i}.", md, f"{name}缺少 6{i} 行内样式")

    def test_12_layout_components_present(self):
        """布局组件 11a-11g 都存在"""
        for name, md in [("摸鱼绿", self.moyu_md), ("锤子", self.hammer_md)]:
            for suffix in "abcdefg":
                self.assertIn(f"### 11{suffix}.", md, f"{name}缺少 11{suffix} 布局组件")

    def test_13_hammer_has_semantic_color_rules(self):
        """锤子主题有独有的语义色使用规则（对比度铁律）"""
        self.assertIn("语义色使用规则", self.hammer_md, "锤子主题缺少语义色使用规则")
        self.assertIn("对比度", self.hammer_md, "锤子主题缺少对比度铁律")
        # 摸鱼绿不要求有此章节
        # （但也不应因本任务被添加）

    def test_14_hammer_fixed_signature_mapping(self):
        """锤子主题引用了固定结尾署名组件"""
        self.assertIn("固定结尾署名组件", self.hammer_md, "锤子主题未引用固定结尾署名组件")
        self.assertIn("#8A4530", self.hammer_md, "锤子主题缺少品牌句文字色 #8A4530")

    def test_15_other_themes_not_affected(self):
        """其他主题文件未被本任务修改（检查不含锤子新增的命名修正标记）"""
        # 6d 命名修正是锤子独有的
        other_themes = [
            "theme-red-white.md",
            "theme-graphite-minimal.md",
            "theme-zen-whitespace.md",
            "theme-moyu-ticket.md",
            "theme-olive-journal.md",
        ]
        for theme_file in other_themes:
            path = THEME_DIR / theme_file
            if path.exists():
                content = read_file(path)
                # 其他主题不应出现锤子独有的"陶土"命名（除非它们本来就有）
                # 这里只验证它们没有被意外修改到包含锤子色值
                for token in ["#B3593B", "#C86442", "#8A4530"]:
                    self.assertNotIn(
                        token.lower(), content.lower(),
                        f"{theme_file} 不应包含锤子色值 {token}"
                    )


if __name__ == "__main__":
    unittest.main()
