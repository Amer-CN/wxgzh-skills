"""OBS-91(档67C):代码块可复制性回归测试(自动化,不依赖人眼)。

渲染 final.html → 提取代码行(<p style="margin:0;font-family:'SF Mono'…">) →
去标签 + html.unescape → 与源 final_article.md 的代码块逐行比对:
  a. 每行内容逐字节相同(行首缩进允许为 U+00A0,归一化为空格后比对);
  b. 无前导空白的行(如两条 /plugin 安装命令)零 U+00A0;
  c. ⛔/⚠️ 前缀与全部 16 条 deny/ask 文案逐字可还原。
★反向验证:旧实现(全空格转 &nbsp;)的输出必须被判 FAIL。
"""
from __future__ import annotations

import html as _h
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
RENDER = SKILL_ROOT / "scripts" / "render_article.py"

DENY = [
    "这是对根目录或家目录的递归删除，会清空整台机器（铁律 1）",
    "这是对系统目录的递归删除，会让系统无法启动（铁律 1）",
    "这会删掉整个当前目录，包括你还没提交的代码（铁律 1）",
    "强推主分支会永久覆盖远端历史，别人的提交会消失（红线 11）",
    "这会删除整个数据库，且通常无法恢复（红线 6）",
    "这是把网上下载的内容直接执行，你没机会看清它要做什么（红线 10）",
    "递归 777 会把文件权限对所有人开放（红线 7）",
    "这是直接格式化或写裸设备，会造成不可恢复的数据丢失（铁律 1）",
]
ASK = [
    "要安装新依赖了。装之前请先确认包名全称、用途、周下载量和最近更新时间（红线 10）",
    "这会丢弃你本地还没提交的改动，丢了找不回来（铁律 1）",
    "这是在改数据库结构。请先出迁移文件再执行，不要直接改库（红线 6）",
    "这条 DELETE 没有 WHERE 条件，会清空整张表（红线 6）",
    "强推会覆盖远端历史。确认这个分支只有你一个人在用（红线 11）",
    "要递归删除文件了。确认路径没写错、且这些文件已经提交过（铁律 1）",
    "你正在把 .env 加进 Git。密钥一旦提交，删掉也留在历史里（红线 7）",
    "这是往线上环境部署。确认已经在本地验证过（红线 11）",
]
DENY_PREFIX = "⛔ vibe-coding-guide 拦截："
ASK_PREFIX = "⚠️ vibe-coding-guide 提醒："
DENY_SUFFIX = "。确需执行请你自己在终端手动运行。关闭护栏：/plugin disable vibe-coding-guide"
ASK_SUFFIX = "。确认要继续吗？关闭护栏：/plugin disable vibe-coding-guide"

# 16 条 deny/ask:前 6 条带 4 空格缩进(测缩进保留),其余无缩进
_BLOCK = []
for i, d in enumerate(DENY):
    line = DENY_PREFIX + d + DENY_SUFFIX
    _BLOCK.append("    " + line if i < 6 else line)
for i, a in enumerate(ASK):
    line = ASK_PREFIX + a + ASK_SUFFIX
    _BLOCK.append("    " + line if i < 2 else line)

CODE_MD = "# 标题\n\n导语。\n\n## 第一章\n\n```bash\n" + "\n".join(_BLOCK) + "\n```\n\n## 第二章\n\n安装命令:\n\n```text\n/plugin marketplace add Amer-CN/vibe-coding-guide\n/plugin install vibe-coding-guide@vibe-coding-guide\n```\n\n结尾。\n"


def _render_cli(md: str, theme="hammer"):
    td = Path(tempfile.mkdtemp(prefix="obs91-"))
    (td / "article.md").write_text(md, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(RENDER), "--article", str(td / "article.md"),
         "--output-dir", str(td), "--theme", theme],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    html = (td / "final.html").read_text(encoding="utf-8") if (td / "final.html").is_file() else ""
    return proc, html


def _code_rows(html: str) -> list[tuple[str, str]]:
    """提取代码行 (raw_unescaped, normalized);normalized 把 U+00A0 归一为普通空格。"""
    out = []
    for m in re.finditer(r'<p style="margin:0;font-family:[^"]*?(?:SF Mono|monospace)[^"]*">(.*?)</p>',
                         html, re.DOTALL):
        row = re.sub(r"<[^>]+>", "", m.group(1))
        row = _h.unescape(row)
        out.append((row, row.replace("\xa0", " ")))
    return out


def _fenced_lines(md: str) -> list[str]:
    lines = []
    for m in re.finditer(r"```[^\n]*\n(.*?)```", md, re.DOTALL):
        lines.extend(m.group(1).splitlines())
    return lines


def _copyability_check(md: str, html: str) -> tuple[bool, dict]:
    """逐行比对源代码块与渲染输出;返回 (ok, report)。"""
    src = _fenced_lines(md)
    rows = _code_rows(html)
    problems = []
    if len(rows) != len(src):
        problems.append(f"行数不一致: source={len(src)} html={len(rows)}")
    for i, (sline, (raw, norm)) in enumerate(zip(src, rows)):
        if norm != sline:
            problems.append(f"L{i}: 行内容不一致\n  src ={sline!r}\n  html={norm!r}")
        # 无前导空白的行(首字符非空白)若含 U+00A0 → 可复制性受损
        if sline and not sline.startswith((" ", "\t")) and "\xa0" in raw:
            problems.append(f"L{i}: 无前导空白行含 U+00A0 -> {raw!r}")
    return (not problems), {"source_lines": src, "html_lines": rows,
                            "problems": problems}


class TestOBS91Copyability:
    def test_a_b_lines_byte_identical_and_zero_nbsp(self):
        proc, html = _render_cli(CODE_MD)
        assert proc.returncode == 0, proc.stderr
        ok, rep = _copyability_check(CODE_MD, html)
        assert ok, rep["problems"]

    def test_b_plugin_commands_zero_nbsp(self):
        proc, html = _render_cli(CODE_MD)
        assert proc.returncode == 0
        rows = _code_rows(html)
        for line in ("/plugin marketplace add Amer-CN/vibe-coding-guide",
                     "/plugin install vibe-coding-guide@vibe-coding-guide"):
            raw = next(r for r, _ in rows if r.replace("\xa0", " ") == line)
            assert "\xa0" not in raw, f"{line!r} 含 U+00A0: {raw!r}"

    def test_c_all_16_deny_ask_recoverable(self):
        proc, html = _render_cli(CODE_MD)
        assert proc.returncode == 0
        rows = _code_rows(html)
        norm = [r[1] for r in rows]
        for block in _BLOCK:
            assert block in norm, f"未逐字还原: {block[:40]}…"
        # ⛔/⚠️ 前缀逐字
        assert any(r.startswith(DENY_PREFIX) for r in norm)
        assert any(r.startswith(ASK_PREFIX) for r in norm)

    def test_leading_indent_preserved_as_nbsp(self):
        proc, html = _render_cli(CODE_MD)
        assert proc.returncode == 0
        rows = _code_rows(html)
        indented = [r for r in rows if r[1].startswith("    ⛔ vibe-coding-guide 拦截")]
        assert indented, "带 4 空格缩进的 deny 行应存在"
        assert indented[0][0].startswith("\xa0\xa0\xa0\xa0"), "行首缩进应为 U+00A0×4"

    def test_reverse_old_all_nbsp_impl_fails(self):
        """★反向验证:旧实现(全空格转 &nbsp;)的输出必须被判 FAIL。"""
        src = _fenced_lines(CODE_MD)
        rows = []
        for s in src:
            # 旧实现:所有空格转 &nbsp;(含行内与无前导空白行)
            rows.append(s.replace(" ", "\xa0"))
        html_fake = "".join(
            f'<p style="margin:0;font-family:\'SF Mono\',Consolas,monospace;font-size:13px;'
            f'line-height:1.7;color:#555555;"><span leaf="">{r}</span></p>'
            for r in rows)
        ok, rep = _copyability_check(CODE_MD, html_fake)
        assert ok is False, "旧全 &nbsp; 实现必须 FAIL"
        assert any("无前导空白行含 U+00A0" in p for p in rep["problems"]), rep["problems"]
