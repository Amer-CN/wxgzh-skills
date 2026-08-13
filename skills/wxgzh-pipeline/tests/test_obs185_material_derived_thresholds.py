"""档71G OBS-185:门禁阈值去单篇化(R57)正反例测试(七条,R49)。

阈值由素材/文章实测量导出:required = min(10, len(lines));素材不含 deny/ask
文案时显式 N/A;⛔/⚠️ 前缀仅当素材实际含对应模板时才要求。
① 素材 16 条 / 载体内 16 条 → PASS,required_coverage=10
② 素材 16 条 / 载体内 9 条  → FAIL(沿用 G1 口径,不得因改造变绿)
③ 素材 4 条  / 载体内 4 条  → PASS,required_coverage=4(改造前必 FAIL)
④ 素材 4 条  / 载体内 2 条  → FAIL
⑤ 素材 0 条                 → PASS 且 OBS88_CODEBLOCK == "N/A"
⑥ 文章 1 对数字且已登记      → PASS(改造前必 FAIL)
⑦ 文章 1 对数字但未登记      → FAIL
fixture 一律自建于 tmp_path;不碰 tests/fixtures/obs88/items.four.json。
"""
from __future__ import annotations

import json
from pathlib import Path

from wxgzh_pipeline.writing_contract import (
    extract_deny_ask_entries, extract_deny_ask_lines,
    validate_codeblock_fidelity, validate_registry_numbers,
)

# 16 条护栏文案(与 71E/71F 同一来源,仅测试内自建)
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

# 素材内部文本(deny/ask 内文,用于 items summary 构造)
_INNER16 = [
    "这是对根目录或家目录的递归删除，会清空整台机器（铁律 1）",
    "这是对系统目录的递归删除，会让系统无法启动（铁律 1）",
    "这会删掉整个当前目录，包括你还没提交的代码（铁律 1）",
    "强推主分支会永久覆盖远端历史，别人的提交会消失（红线 11）",
    "这会删除整个数据库，且通常无法恢复（红线 6）",
    "这是把网上下载的内容直接执行，你没机会看清它要做什么（红线 10）",
    "递归 777 会把文件权限对所有人开放（红线 7）",
    "这是直接格式化或写裸设备，会造成不可恢复的数据丢失（铁律 1）",
    "要安装新依赖了。装之前请先确认包名全称、用途、周下载量和最近更新时间（红线 10）",
    "这会丢弃你本地还没提交的改动，丢了找不回来（铁律 1）",
    "这是在改数据库结构。请先出迁移文件再执行，不要直接改库（红线 6）",
    "这条 DELETE 没有 WHERE 条件，会清空整张表（红线 6）",
    "强推会覆盖远端历史。确认这个分支只有你一个人在用（红线 11）",
    "要递归删除文件了。确认路径没写错、且这些文件已经提交过（铁律 1）",
    "你正在把 .env 加进 Git。密钥一旦提交，删掉也留在历史里（红线 7）",
    "这是往线上环境部署。确认已经在本地验证过（红线 11）",
]


def _items(tmp_path, texts, with_prefix_templates=True) -> Path:
    items = []
    for i, txt in enumerate(texts, 1):
        prefix = "deny" if i % 2 == 1 else "ask"
        summary = f"match 'x{i}' && {prefix} '{txt}'"
        if with_prefix_templates and i == 1:
            summary = ("deny() { emit \"deny\" \"⛔ vibe-coding-guide 拦截：$1。确需执行请你自己在终端手动运行。$CLOSE_HINT\"; }\n"
                       "ask()  { emit \"ask\"  \"⚠️ vibe-coding-guide 提醒：$1。确认要继续吗？$CLOSE_HINT\"; }\n" + summary)
        items.append({"id": f"m-{i}", "summary": summary,
                      "source_provenance": {"source_type": "repo_path",
                                            "original_ref": "x", "content_sha256": "a" * 64}})
    p = tmp_path / "items.json"
    p.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    return p


def _alert_article(lines) -> str:
    return "# 标题\n\n:::alert type=\"warning\" title=\"护栏文案\"\n" + "\n".join(lines) + "\n:::\n"


def _write(tmp_path, name, text) -> Path:
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


# ── ① 素材 16 条 / 载体内 16 条 → PASS,required_coverage=10 ──

def test_obs185_16_of_16_pass(tmp_path):
    items = _items(tmp_path, _INNER16)
    art = _write(tmp_path, "article.md", _alert_article(ALL16))
    ok, rep = validate_codeblock_fidelity(art, items)
    assert ok is True, rep
    assert rep["covered_in_codeblocks"] == 16
    assert rep["required_coverage"] == 10
    assert rep["coverage_basis"] == "material_derived"
    assert rep["OBS88_CODEBLOCK"] == "PASS"


# ── ② 素材 16 条 / 载体内 9 条 → FAIL(沿用 G1 口径)────────

def test_obs185_9_of_16_fails(tmp_path):
    items = _items(tmp_path, _INNER16)
    art = _write(tmp_path, "article.md", _alert_article(ALL16[:9]))
    ok, rep = validate_codeblock_fidelity(art, items)
    assert ok is False, rep
    assert rep["covered_in_codeblocks"] == 9
    assert rep["required_coverage"] == 10


# ── ③ 素材 4 条 / 载体内 4 条 → PASS,required_coverage=4 ──

def test_obs185_4_of_4_pass(tmp_path):
    texts = _INNER16[:2] + _INNER16[8:10]
    lines = [ALL16[0], ALL16[1], ALL16[8], ALL16[9]]
    items = _items(tmp_path, texts)
    art = _write(tmp_path, "article.md", _alert_article(lines))
    ok, rep = validate_codeblock_fidelity(art, items)
    assert ok is True, rep
    assert rep["covered_in_codeblocks"] == 4
    assert rep["required_coverage"] == 4
    assert rep["coverage_basis"] == "material_derived"


# ── ④ 素材 4 条 / 载体内 2 条 → FAIL ──────────────────────

def test_obs185_2_of_4_fails(tmp_path):
    texts = _INNER16[:2] + _INNER16[8:10]
    items = _items(tmp_path, texts)
    art = _write(tmp_path, "article.md", _alert_article([ALL16[0], ALL16[1]]))
    ok, rep = validate_codeblock_fidelity(art, items)
    assert ok is False, rep
    assert rep["covered_in_codeblocks"] == 2
    assert rep["required_coverage"] == 4


# ── ⑤ 素材 0 条 → PASS 且 OBS88_CODEBLOCK == "N/A" ────────

def test_obs185_zero_lines_not_applicable(tmp_path):
    items = _items(tmp_path, [], with_prefix_templates=False)
    assert extract_deny_ask_lines(items) == []
    art = _write(tmp_path, "article.md", "# 标题\n\n正文,没有任何载体。\n")
    ok, rep = validate_codeblock_fidelity(art, items)
    assert ok is True, rep
    assert rep["OBS88_CODEBLOCK"] == "N/A"
    assert rep["coverage_basis"] == "not_applicable"
    assert rep["not_applicable_reason"] == "injected material contains no deny/ask lines"


# ── ⑥ 文章 1 对数字且已登记 → PASS ────────────────────────

def test_obs185_one_pair_registered_pass(tmp_path):
    art = _write(tmp_path, "article.md", "# 标题\n\n## 一、数字\n\n红线从 8 条扩到 11 条。\n")
    reg = {"claims": [
        {"claim_id": "N-1", "claim_text": "红线从 8 条扩到 11 条", "source_url": "u",
         "numbers": [{"value": 8, "unit": "条"}], "chart_group": "红线数量",
         "metric_name": "红线条数", "series_label": "8 条红线"},
        {"claim_id": "N-2", "claim_text": "红线扩到 11 条", "source_url": "u",
         "numbers": [{"value": 11, "unit": "条"}], "chart_group": "红线数量",
         "metric_name": "红线条数", "series_label": "11 条红线"},
    ]}
    reg_p = _write(tmp_path, "reg.json", json.dumps(reg, ensure_ascii=False))
    ok, rep = validate_registry_numbers(art, reg_p)
    assert ok is True, rep
    assert rep["required_pairs"] == 1
    assert rep["OBS88_NUMBERS"] == "PASS"


# ── ⑦ 文章 1 对数字但未登记 → FAIL ────────────────────────

def test_obs185_one_pair_unregistered_fails(tmp_path):
    art = _write(tmp_path, "article.md", "# 标题\n\n## 一、数字\n\n红线从 8 条扩到 11 条。\n")
    reg_p = _write(tmp_path, "reg.empty.json", json.dumps({"claims": []}))
    ok, rep = validate_registry_numbers(art, reg_p)
    assert ok is False, rep
    assert rep["required_pairs"] == 1
    assert any(m["start"] == 8 and m["end"] == 11 for m in rep["missing"])


# ── OBS-195(档71H):前缀要求由实测条目导出 ────────────────────

_FIX_DENY_ONLY = Path(__file__).parent / "fixtures" / "obs88" / "items.deny_only_stray_warn.json"


def test_obs185_no_drift_vs_71gf(tmp_path):
    """3e(档71H):items.four.json 上 entries/lines 等价 + 五字段与 71G-F 完全一致。"""
    p = Path(__file__).parent / "fixtures" / "obs88" / "items.four.json"
    assert [t for _, t in extract_deny_ask_entries(p)] == extract_deny_ask_lines(p)
    art = _write(tmp_path, "article.md", _alert_article(ALL16))
    ok, rep = validate_codeblock_fidelity(art, p)
    assert ok is True, rep
    assert rep["deny_ask_total"] == 16
    assert rep["covered_in_codeblocks"] == 16
    assert rep["required_coverage"] == 10
    assert rep["deny_prefix_required"] is True
    assert rep["ask_prefix_required"] is True


def test_obs185_deny_only_stray_warn_ask_not_required(tmp_path):
    """3f(档71H,R83 单变量):素材只有 deny 条目、⚠️ 出现在无关位置 →
    ask_prefix_required=False;文章载体无 ⚠️ 也 OBS88_CODEBLOCK=PASS。"""
    entries = extract_deny_ask_entries(_FIX_DENY_ONLY)
    assert [k for k, _ in entries] == ["deny", "deny"]
    assert not any(k == "ask" for k, _ in entries)
    raw = _FIX_DENY_ONLY.read_text(encoding="utf-8")
    assert "⚠️" in raw  # 无关位置确实含 ⚠️ 字符
    assert "ask '" not in raw and "ask(" not in raw
    # 载体内只有两条 deny 行(含 ⛔),无 ⚠️
    art = _write(tmp_path, "article.md", _alert_article([ALL16[0], ALL16[1]]))
    ok, rep = validate_codeblock_fidelity(art, _FIX_DENY_ONLY)
    assert ok is True, rep
    assert rep["ask_prefix_required"] is False
    assert rep["deny_prefix_required"] is True
    assert rep["ask_prefix_present"] is False
    assert rep["covered_in_codeblocks"] == 2
    assert rep["required_coverage"] == 2
    assert rep["OBS88_CODEBLOCK"] == "PASS"
