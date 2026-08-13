"""档71C-R2 OBS-144 文档化文本槽清单（doc-derived，唯一输入源）。

本文件是 references/advanced/*.md 的纯数据投影：
- 不 import 渲染器，不从 HTML 反推任何内容；
- 每条槽带 references 文件 + 行号注释；
- 模式维度展开（alert 5 型 / quote 3 型 / code-compare lang 有无）。

探针样本、锚实测导出、判据分裂全部以此清单为准（R26/R27）。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Slot:
    name: str            # 槽名（哨兵 S_<COMP>_<SLOT> 用）
    source: str          # 来源：头部属性名 / 块体位置
    ref: str             # references 文件 + 行号
    required: bool       # 必填还是可选
    mode: str            # 所属模式（type 取值 / lang 有无 / 位置）
    multi: bool = False  # 是否多项输入槽（N 项各一个哨兵）
    url: bool = False    # 是否 URL 槽(如 image=/url=,在 img src 属性,无文本锚)


@dataclass(frozen=True)
class ComponentSlots:
    component: str
    slots: tuple[Slot, ...]

    @property
    def required_slots(self) -> tuple[Slot, ...]:
        return tuple(s for s in self.slots if s.required)


# ── A 组 9 类文档化槽清单（全部引用 references/advanced/*.md 行号）──

SLOTS: tuple[ComponentSlots, ...] = (
    # alerts.md L8-10: :::alert type="warning" title="风险提示" + 正文
    # alerts.md L15-21: type 枚举 note/tip/important/warning/caution（5 模式展开）
    ComponentSlots("alert", (
        Slot("title", "头部属性 title", "references/advanced/alerts.md L8", False, "type=*"),
        Slot("body", "块体正文", "references/advanced/alerts.md L9", True, "type=note"),
        Slot("body", "块体正文", "references/advanced/alerts.md L9", True, "type=tip"),
        Slot("body", "块体正文", "references/advanced/alerts.md L9", True, "type=important"),
        Slot("body", "块体正文", "references/advanced/alerts.md L9", True, "type=warning"),
        Slot("body", "块体正文", "references/advanced/alerts.md L9", True, "type=caution"),
    )),
    # quotes.md L8-21: type=normal / highlight / sourced(source= 属性)
    # quotes.md L19: sourced 模式带 source 头部属性
    ComponentSlots("quote", (
        Slot("text", "块体正文", "references/advanced/quotes.md L10", True, "type=normal"),
        Slot("text", "块体正文", "references/advanced/quotes.md L15", True, "type=highlight"),
        Slot("text", "块体正文", "references/advanced/quotes.md L20", True, "type=sourced"),
        Slot("source", "头部属性 source", "references/advanced/quotes.md L19", False, "type=sourced"),
    )),
    # code-compare.md L8-15: title 可选 + @before/@after 各一段(lang 可选)
    ComponentSlots("code-compare", (
        Slot("title", "头部属性 title", "references/advanced/code-compare.md L8", False, "lang=无"),
        Slot("title", "头部属性 title", "references/advanced/code-compare.md L8", False, "lang=有"),
        Slot("before", "块体 @before 段", "references/advanced/code-compare.md L9-11", True, "lang=无"),
        Slot("before", "块体 @before 段", "references/advanced/code-compare.md L9-11", True, "lang=有"),
        Slot("after", "块体 @after 段", "references/advanced/code-compare.md L12-14", True, "lang=无"),
        Slot("after", "块体 @after 段", "references/advanced/code-compare.md L12-14", True, "lang=有"),
        Slot("lang", "块体 @before 行内 lang= 属性", "references/advanced/code-compare.md L9", False, "lang=有"),
    )),
    # media.md L7-13: media-text 块体 ![](alt) + 解释段
    ComponentSlots("media-text", (
        Slot("cap", "块体 ![]() alt（或头部 cap=）", "references/advanced/media.md L10", True, "默认"),
        Slot("exp", "块体解释段", "references/advanced/media.md L11", True, "默认"),
    )),
    # media.md L15-21: gallery title 可选 + N 张图各带 alt
    ComponentSlots("gallery", (
        Slot("title", "头部属性 title", "references/advanced/media.md L17", False, "默认"),
        Slot("caption", "块体 ![]() alt（N 项）", "references/advanced/media.md L18-19", True, "默认", multi=True),
    )),
    # media.md L23-27: long-image image= 必填 + caption= 可选
    ComponentSlots("long-image", (
        Slot("image", "头部属性 image", "references/advanced/media.md L25", True, "默认", url=True),
        Slot("caption", "头部属性 caption", "references/advanced/media.md L25/L33", True, "默认"),
    )),
    # links-resources.md L8-11: resources title 可选 + N 条链接(文字+URL)
    ComponentSlots("resources", (
        Slot("title", "头部属性 title", "references/advanced/links-resources.md L8", False, "默认"),
        Slot("link_text", "块体 - [文字](url) 文字", "references/advanced/links-resources.md L9-10", True, "默认", multi=True),
        Slot("url", "块体 - [文字](url) url", "references/advanced/links-resources.md L9-10", True, "默认", multi=True, url=True),
    )),
    # footnotes.md L8-11: 正文 [^N] 引用 + 文末 [^N]: 定义
    ComponentSlots("footnotes", (
        Slot("fn_text", "块体 [^N]: 定义文本（N 项）", "references/advanced/footnotes.md L11", True, "默认", multi=True),
    )),
    # dialogue.md L8-14: title 可选 + N 轮 @user/@assistant 消息
    # dialogue.md L18-23: 可选 name= 属性
    ComponentSlots("dialogue", (
        Slot("title", "头部属性 title", "references/advanced/dialogue.md L8", False, "默认"),
        Slot("msg", "块体 @user/@assistant 行（N 项）", "references/advanced/dialogue.md L9-12", True, "默认", multi=True),
        Slot("name", "块体行内 name= 属性", "references/advanced/dialogue.md L20-21", False, "默认", multi=True),
    )),
    # 76J/OBS-271:标准 Markdown 表格/列表 —— 语法门 probe 判据驱动,非 ::: 组件;
    # 来源=SKILL.md L98-99(表格/列表映射)+ references/theme-hammer.md 11a/11f/11g
    # (本文件此前为 references/advanced/*.md 纯数据投影,本条目为文档化扩展)。
    ComponentSlots("table", (
        Slot("header", "表头单元格", "SKILL.md L99 / references/theme-hammer.md 11f", True, "默认"),
        Slot("body", "数据单元格", "SKILL.md L99 / references/theme-hammer.md 11f", True, "默认"),
    )),
    ComponentSlots("list", (
        Slot("item_ul", "无序列表项(- / *) ", "SKILL.md L98 / references/theme-hammer.md 11a", True, "默认"),
        Slot("item_ol", "有序列表项(1. )", "SKILL.md L98 / references/theme-hammer.md 11g", True, "默认"),
    )),
)

BY_COMPONENT: dict[str, ComponentSlots] = {c.component: c for c in SLOTS}


# 4d(OBS-156):type 枚举常量(带 references 行号)。
# alerts.md L17-21: note/tip/important/warning/caution;quotes.md L9-21: normal/highlight/sourced。
ALERT_TYPES = frozenset({"note", "tip", "important", "warning", "caution"})
QUOTE_TYPES = frozenset({"normal", "highlight", "sourced"})


def total_slot_count() -> int:
    """槽总数（模式展开后）。"""
    return sum(len(c.slots) for c in SLOTS)


def required_slot_count() -> int:
    return sum(len(c.required_slots) for c in SLOTS)
