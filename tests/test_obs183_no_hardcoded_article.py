"""档71F OBS-183 反硬编码门禁:注入指令不得含单篇文章专有字面量(R54)。

断言 AGENT_INSTRUCTIONS["super_writer"] 不含下列任一子串(逐个断言,失败信息
打印命中的字面量);并正向断言通用关键词仍在(证明规则没被删光)。
"""
from __future__ import annotations

from wxgzh_pipeline.producers import (
    AGENT_INSTRUCTIONS, AIHOT_INJECTION_INSTRUCTIONS,
)

_FORBIDDEN = [
    "8→11", "19→25", "四→五", "16 条", "8 条 ⛔", "8 条 ⚠️",
    "第一章", "第二章", "第三章",
    "红线条数", "自检清单条数", "铁律条数", "vibe-coding-guide",
]
_REQUIRED = [":::alert", "fenced code block", "逐字"]


def _scan_targets() -> list[tuple[str, str]]:
    """OBS-187(档71G,5b):扫描范围 = AGENT_INSTRUCTIONS 全部三个值
    + producers._agent() 中 aihot 注入路径运行时拼装指令常量(模块级导出,
    不复制)。"""
    targets = [(key, str(value)) for key, value in AGENT_INSTRUCTIONS.items()]
    targets.append(("AIHOT_INJECTION_INSTRUCTIONS", AIHOT_INJECTION_INSTRUCTIONS))
    return targets


def test_obs183_instructions_no_article_literals():
    """逐个断言禁用字面量不存在(全部指令字符串);失败信息打印命中的字面量与宿主。"""
    for host, instr in _scan_targets():
        for token in _FORBIDDEN:
            assert token not in instr, f"命中禁用字面量: {token} (宿主: {host})"


def test_obs183_instructions_keep_generic_keywords():
    """正向断言:通用规则关键词仍在(super_writer 指令)。"""
    instr = AGENT_INSTRUCTIONS["super_writer"]
    for token in _REQUIRED:
        assert token in instr, f"缺失通用关键词: {token}"


def test_obs183_instructions_three_keys_nonempty():
    """AGENT_INSTRUCTIONS 三个键齐全且均为非空字符串。"""
    for key in ("aihot", "super_writer", "zh_human_writing"):
        value = AGENT_INSTRUCTIONS.get(key)
        assert isinstance(value, str) and value.strip(), f"键缺失或为空: {key}"
