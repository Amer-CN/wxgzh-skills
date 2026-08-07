"""档71E OBS-176:载体放宽正反例测试(7 条,R49)。

放宽:validate_codeblock_fidelity 的载体 = fenced code block ∪ 已批准 A 组组件块
(:::<name> … :::,name ∈ APPROVED_CARRIER_COMPONENTS,R48 单一来源导入)。
载体块体以外的正文一律不计数(R47);MIN_DENY_ASK_COVERAGE 保持 10。

正例 A 16 行在 :::alert 块内 → PASS
正例 B 16 行在三反引号 bash 围栏内 → PASS(向后兼容)
正例 C 8 条在 alert、8 条在围栏(跨载体合并计数)→ PASS
反例 D 16 行逐字但全在普通段落(无任何载体块)→ FAIL
反例 E 16 行在未批准组件块内(:::facts,B 组未接线)→ FAIL
反例 F 16 行改写/散文化 → FAIL
反例 G 载体内只有 9 条 → FAIL;载体内有 ⛔ 无 ⚠️ → FAIL

D/F 若 PASS = 放宽变成取消门禁 → S66。
"""
from __future__ import annotations

from pathlib import Path

from wxgzh_pipeline.writing_contract import (
    _carrier_blocks, extract_deny_ask_lines, validate_codeblock_fidelity,
)

FIX = Path(__file__).parent / "fixtures" / "obs88"
ITEMS = FIX / "items.four.json"

# 16 条护栏文案逐字(8 条 ⛔ + 8 条 ⚠️,与 test_obs88 ARTICLE 同一来源)
_DENY = [
    "⛔ vibe-coding-guide 拦截：这是对根目录或家目录的递归删除，会清空整台机器（铁律 1）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide",
    "⛔ vibe-coding-guide 拦截：这是对系统目录的递归删除，会让系统无法启动（铁律 1）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide",
    "⛔ vibe-coding-guide 拦截：这会删掉整个当前目录，包括你还没提交的代码（铁律 1）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide",
    "⛔ vibe-coding-guide 拦截：强推主分支会永久覆盖远端历史，别人的提交会消失（红线 11）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide",
    "⛔ vibe-coding-guide 拦截：这会删除整个数据库，且通常无法恢复（红线 6）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide",
    "⛔ vibe-coding-guide 拦截：这是把网上下载的内容直接执行，你没机会看清它要做什么（红线 10）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide",
    "⛔ vibe-coding-guide 拦截：递归 777 会把文件权限对所有人开放（红线 7）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide",
    "⛔ vibe-coding-guide 拦截：这是直接格式化或写裸设备，会造成不可恢复的数据丢失（铁律 1）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide",
]
_ASK = [
    "⚠️ vibe-coding-guide 提醒：要安装新依赖了。装之前请先确认包名全称、用途、周下载量和最近更新时间（红线 10）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide",
    "⚠️ vibe-coding-guide 提醒：这会丢弃你本地还没提交的改动，丢了找不回来（铁律 1）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide",
    "⚠️ vibe-coding-guide 提醒：这是在改数据库结构。请先出迁移文件再执行，不要直接改库（红线 6）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide",
    "⚠️ vibe-coding-guide 提醒：这条 DELETE 没有 WHERE 条件，会清空整张表（红线 6）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide",
    "⚠️ vibe-coding-guide 提醒：强推会覆盖远端历史。确认这个分支只有你一个人在用（红线 11）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide",
    "⚠️ vibe-coding-guide 提醒：要递归删除文件了。确认路径没写错、且这些文件已经提交过（铁律 1）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide",
    "⚠️ vibe-coding-guide 提醒：你正在把 .env 加进 Git。密钥一旦提交，删掉也留在历史里（红线 7）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide",
    "⚠️ vibe-coding-guide 提醒：这是往线上环境部署。确认已经在本地验证过（红线 11）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide",
]
ALL16 = _DENY + _ASK


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def _fence_article(lines, lang="bash"):
    return "# 标题\n\n```" + lang + "\n" + "\n".join(lines) + "\n```\n"


def _alert_article(lines, typ="warning"):
    body = "\n".join(lines)
    return f"# 标题\n\n:::alert type=\"{typ}\" title=\"护栏文案\"\n{body}\n:::\n"


# ── 正例 A:16 行在 :::alert 块内 ─────────────────────────────

def test_obs176_a_alert_block_true(tmp_path):
    art = _write(tmp_path, "article.md", _alert_article(ALL16))
    ok, rep = validate_codeblock_fidelity(art, ITEMS)
    assert ok is True, rep
    assert rep["covered_in_codeblocks"] == 16
    assert rep["carrier_kinds"] == ["alert"]
    assert rep["carrier_block_count"] == 1


# ── 正例 B:16 行在三反引号 bash 围栏内(向后兼容)─────────────

def test_obs176_b_fence_true(tmp_path):
    art = _write(tmp_path, "article.md", _fence_article(ALL16))
    ok, rep = validate_codeblock_fidelity(art, ITEMS)
    assert ok is True, rep
    assert rep["covered_in_codeblocks"] == 16
    assert rep["carrier_kinds"] == ["fence"]
    assert rep["carrier_block_count"] == 1


# ── 正例 C:8 条在 alert、8 条在围栏(跨载体合并计数)──────────

def test_obs176_c_split_across_carriers_true(tmp_path):
    article = ("# 标题\n\n" + _alert_article(_DENY).replace("# 标题\n\n", "")
               + "\n" + _fence_article(_ASK))
    art = _write(tmp_path, "article.md", article)
    ok, rep = validate_codeblock_fidelity(art, ITEMS)
    assert ok is True, rep
    assert rep["covered_in_codeblocks"] == 16
    assert rep["carrier_kinds"] == ["alert", "fence"]
    assert rep["carrier_block_count"] == 2


# ── 反例 D:16 行逐字但全在普通段落里 → S66 若 PASS 则停机 ────

def test_obs176_d_plain_paragraphs_false(tmp_path):
    body = "\n\n".join(ALL16)
    art = _write(tmp_path, "article.md", "# 标题\n\n" + body + "\n")
    ok, rep = validate_codeblock_fidelity(art, ITEMS)
    assert ok is False, rep
    assert rep["covered_in_codeblocks"] == 0
    assert rep["carrier_block_count"] == 0


# ── 反例 E:16 行在未批准组件块内(:::facts,B 组未接线)────────

def test_obs176_e_unapproved_component_false(tmp_path):
    body = "\n".join(ALL16)
    art = _write(tmp_path, "article.md",
                 f"# 标题\n\n:::facts title=\"事实\"\n{body}\n:::\n")
    ok, rep = validate_codeblock_fidelity(art, ITEMS)
    assert ok is False, rep
    assert rep["covered_in_codeblocks"] == 0
    assert rep["carrier_block_count"] == 0


# ── 反例 F:16 行改写后放进 :::alert 块 → S66 若 PASS 则停机 ──────

def test_obs176_f_rewritten_prose_false(tmp_path):
    # R55:与正例 A 唯一差异 = 块内文本被改写;载体(alert type=warning)、
    # 行数、结构逐项与 A 一致。改写:去前缀 + 全角括号转半角 + 动词替换,
    # 保证 16 条 deny/ask 内文(含全角括号)不再以子串出现。
    rewritten = [
        l.replace("⛔ ", "").replace("⚠️ ", "")
         .replace("（", "(").replace("）", ")")
         .replace("拦截", "阻断").replace("提醒", "提示")
        for l in ALL16
    ]
    # 演示:同一 alert 载体,唯一变量=文本,covered 从 16 掉到 0
    ok_a, rep_a = validate_codeblock_fidelity(
        _write(tmp_path, "article.a.md", _alert_article(ALL16)), ITEMS)
    assert ok_a is True and rep_a["covered_in_codeblocks"] == 16, rep_a
    art = _write(tmp_path, "article.md", _alert_article(rewritten))
    ok, rep = validate_codeblock_fidelity(art, ITEMS)
    assert ok is False, rep
    assert rep["covered_in_codeblocks"] == 0, rep
    assert rep["carrier_kinds"] == ["alert"], rep


# ── 反例 G:只有 9 条 → FAIL;有 ⛔ 无 ⚠️ → FAIL ────────────────

def test_obs176_g_nine_lines_and_prefix_gap_false(tmp_path):
    # G1:载体内只有 9 条(8 ⛔ + 1 ⚠️)→ 覆盖 9 < 10
    nine = _DENY + _ASK[:1]
    art9 = _write(tmp_path, "article.nine.md", _alert_article(nine))
    ok9, rep9 = validate_codeblock_fidelity(art9, ITEMS)
    assert ok9 is False, rep9
    assert rep9["covered_in_codeblocks"] == 9
    # G2:载体内有 ⛔ 无 ⚠️ → ask_prefix 缺失
    deny_only = _write(tmp_path, "article.deny.md", _alert_article(_DENY))
    okd, repd = validate_codeblock_fidelity(deny_only, ITEMS)
    assert okd is False, repd
    assert repd["deny_prefix_present"] is True
    assert repd["ask_prefix_present"] is False


# ── 辅助:载体提取状态机口径(嵌套/未配对不计)─────────────────

def test_obs176_carrier_blocks_state_machine_matches_parse_article():
    # 状态机与安装侧 parse_article 同口径:组件内任何 ::: 行都是关闭行(无嵌套),
    # 被意外 ::: 关闭的块仍计入(块体=开关行之间);仅到文末仍未闭合的块丢弃。
    # OBS-184:测试名与 docstring 已与实测行为对齐。
    text = (":::alert type=\"warning\"\n闭合块\n:::\n"
            ":::alert type=\"warning\"\n未配对块\n"
            ":::quote\n组件内的 ::: 行关闭当前 alert,不开启 quote\n:::\n")
    blocks, kinds = _carrier_blocks(text)
    assert len(blocks) == 2, blocks
    assert blocks == ["闭合块", "未配对块"], blocks
    assert kinds == ["alert", "alert"], kinds


def test_obs176_items_still_16_lines():
    lines = extract_deny_ask_lines(ITEMS)
    assert len(lines) == 16
