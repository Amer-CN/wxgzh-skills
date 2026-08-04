"""档66 OBS-88:数字结构化 + 代码块保真(写作合同校验)测试。

覆盖:
1. 中文数字转换(四→4 / 五→5 / 十五→15 / 二十五→25)
2. 数字对比对提取(19→25 / 8→11 / 四→五;无对比为空;不伪造)
3. registry 校验:三组登记 PASS / 缺一组 FAIL / 文章无对比不要求(不伪造)
4. 代码块保真:15 条 deny/ask 全进 PASS / 覆盖不足 FAIL / 改写 FAIL / 前缀缺失 FAIL
5. ★反向验证:四素材夹具可提取 15 条文案,构造合规文章三组登记可过
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from wxgzh_pipeline.writing_contract import (
    cn_to_int, extract_number_pairs, extract_deny_ask_lines,
    validate_registry_numbers, validate_codeblock_fidelity,
)

FIX = Path(__file__).parent / "fixtures" / "obs88"
ITEMS = FIX / "items.four.json"
REGISTRY = FIX / "registry.three_groups.json"

ARTICLE = """# 测试文章

从 8 条扩到 11 条,自检清单从 19 条扩到 25 条,铁律从四条扩到五条。

```bash
⛔ vibe-coding-guide 拦截：这是对根目录或家目录的递归删除，会清空整台机器（铁律 1）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⛔ vibe-coding-guide 拦截：这是对系统目录的递归删除，会让系统无法启动（铁律 1）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⛔ vibe-coding-guide 拦截：这会删掉整个当前目录，包括你还没提交的代码（铁律 1）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⛔ vibe-coding-guide 拦截：强推主分支会永久覆盖远端历史，别人的提交会消失（红线 11）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⛔ vibe-coding-guide 拦截：这会删除整个数据库，且通常无法恢复（红线 6）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⛔ vibe-coding-guide 拦截：这是把网上下载的内容直接执行，你没机会看清它要做什么（红线 10）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⛔ vibe-coding-guide 拦截：递归 777 会把文件权限对所有人开放（红线 7）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⛔ vibe-coding-guide 拦截：这是直接格式化或写裸设备，会造成不可恢复的数据丢失（铁律 1）。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：要安装新依赖了。装之前请先确认包名全称、用途、周下载量和最近更新时间（红线 10）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：这会丢弃你本地还没提交的改动，丢了找不回来（铁律 1）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：这是在改数据库结构。请先出迁移文件再执行，不要直接改库（红线 6）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：这条 DELETE 没有 WHERE 条件，会清空整张表（红线 6）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：强推会覆盖远端历史。确认这个分支只有你一个人在用（红线 11）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：要递归删除文件了。确认路径没写错、且这些文件已经提交过（铁律 1）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：你正在把 .env 加进 Git。密钥一旦提交，删掉也留在历史里（红线 7）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
⚠️ vibe-coding-guide 提醒：这是往线上环境部署。确认已经在本地验证过（红线 11）。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide
```
"""


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


# ── 1. 中文数字 ─────────────────────────────────────────────

def test_cn_to_int():
    assert cn_to_int("四") == 4
    assert cn_to_int("五") == 5
    assert cn_to_int("十") == 10
    assert cn_to_int("十五") == 15
    assert cn_to_int("二十") == 20
    assert cn_to_int("二十五") == 25
    assert cn_to_int("两") == 2
    assert cn_to_int("19") == 19
    assert cn_to_int("abc") is None


# ── 2. 数字对比对提取 ───────────────────────────────────────

def test_extract_number_pairs():
    text = "红线从 8 条扩到 11 条;自检清单从 19 条扩到 25 条;铁律从四条扩到五条。"
    pairs = extract_number_pairs(text)
    assert (8, 11, "条") in pairs
    assert (19, 25, "条") in pairs
    assert (4, 5, "条") in pairs
    assert len(pairs) == 3


def test_extract_number_pairs_none_and_no_fake():
    assert extract_number_pairs("没有任何数字对比的文章。") == []
    # 解析失败或相同值不伪造
    assert extract_number_pairs("从 x 到 y;从 3 到 3") == []


# ── 3. registry 校验 ────────────────────────────────────────

def test_registry_three_groups_pass(tmp_path):
    art = _write(tmp_path, "article.md", ARTICLE)
    ok, rep = validate_registry_numbers(art, REGISTRY)
    assert ok is True, rep
    assert rep["OBS88_NUMBERS"] == "PASS"
    assert len(rep["registered"]) == 3


def test_registry_missing_group_fails(tmp_path):
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    reg["claims"] = [c for c in reg["claims"] if c["claim_id"] not in ("N-05", "N-06")]
    reg_p = _write(tmp_path, "registry.partial.json", json.dumps(reg, ensure_ascii=False))
    art = _write(tmp_path, "article.md", ARTICLE)
    ok, rep = validate_registry_numbers(art, reg_p)
    assert ok is False
    assert any(m["start"] == 4 and m["end"] == 5 for m in rep["missing"])


def test_registry_no_pairs_no_fake(tmp_path):
    art = _write(tmp_path, "article.md", "没有数字对比的文章。")
    empty_reg = _write(tmp_path, "registry.empty.json", json.dumps({"claims": []}))
    ok, rep = validate_registry_numbers(art, empty_reg)
    assert ok is True  # 文章无对比对,不要求任何登记(不伪造)
    assert rep["pairs_in_article"] == []


# ── 4. 代码块保真 ───────────────────────────────────────────

def test_codeblock_all_fifteen_pass(tmp_path):
    art = _write(tmp_path, "article.md", ARTICLE)
    ok, rep = validate_codeblock_fidelity(art, ITEMS)
    assert ok is True, rep
    assert rep["deny_ask_total"] == 16
    assert rep["covered_in_codeblocks"] == 16
    assert rep["deny_prefix_present"] and rep["ask_prefix_present"]


def test_codeblock_coverage_below_min_fails(tmp_path):
    art = _write(tmp_path, "article.md",
                 "# 标题\n\n```bash\n" + ARTICLE.split("```")[1].splitlines()[1] + "\n```\n")
    ok, rep = validate_codeblock_fidelity(art, ITEMS)
    assert ok is False
    assert rep["covered_in_codeblocks"] == 1


def test_codeblock_rewritten_fails(tmp_path):
    # 改写(半角括号、删前缀)→ 逐字不命中
    rewritten = ARTICLE.replace("（铁律 1）", "(铁律 1)").replace("⛔ ", "")
    art = _write(tmp_path, "article.md", rewritten)
    ok, rep = validate_codeblock_fidelity(art, ITEMS)
    assert ok is False
    assert rep["covered_in_codeblocks"] < 16


def test_codeblock_prefix_missing_fails(tmp_path):
    no_prefix = ARTICLE.replace("⛔ ", "").replace("⚠️ ", "")
    art = _write(tmp_path, "article.md", no_prefix)
    ok, rep = validate_codeblock_fidelity(art, ITEMS)
    assert ok is False
    assert rep["deny_prefix_present"] is False


# ── 5. ★反向验证:四素材夹具 ────────────────────────────────

def test_reverse_four_materials_extract_15_lines():
    lines = extract_deny_ask_lines(ITEMS)
    assert len(lines) == 16
    assert any("递归删除" in l for l in lines)
    assert any("drop database" in l or "数据库" in l for l in lines)
