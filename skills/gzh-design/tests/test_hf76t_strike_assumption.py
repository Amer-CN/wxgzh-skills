"""76T/OBS-293:封面划线句改义——strike_assumption 新字段接线测试。

- 含 strike_assumption:划线句显示旧认知句(text-decoration:line-through),标题作答,无重复;
- 字段缺失:划线句整行不渲染(不再用 hook_line/默认文案填充),其余封面完好、无报错。
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
RENDER = SKILL_ROOT / "scripts" / "render_article.py"


def _run(article_text: str, extra_args: list[str] | None = None):
    td = Path(tempfile.mkdtemp(prefix="render-76t-"))
    article = td / "article.md"
    article.write_text(article_text, encoding="utf-8")
    cmd = [sys.executable, "-X", "utf8", str(RENDER),
           "--article", str(article), "--output-dir", str(td), "--theme", "smartisan"]
    if extra_args:
        cmd += extra_args
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300)
    html = (td / "final.html").read_text(encoding="utf-8") if (td / "final.html").is_file() else ""
    return proc, html


ARTICLE = """# 旧认知已被推翻

导语段落。

## 第一章

正文。
"""


def test_strike_assumption_rendered_in_strike_slot():
    """含 strike_assumption → 划线句显示旧认知句,且不含 hook_line 内容。"""
    proc, html = _run(ARTICLE, ["--strike-assumption", "你还觉得写作只能靠天赋？"])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    # 划线句槽:line-through + 旧认知句
    assert "line-through" in html
    assert "你还觉得写作只能靠天赋？" in html
    # 划线句内容 = strike_assumption(非默认文案)
    assert "别急着划走" not in html, "默认划线文案不应出现"


def test_strike_assumption_missing_slot_not_rendered():
    """字段缺失 → 划线句整行不渲染,其余封面完好、无报错。"""
    proc, html = _run(ARTICLE)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    # 划线句槽(line-through)整行不渲染
    assert "line-through" not in html
    assert "别急着划走" not in html
    # 其余封面完好:标题/副标题/日期/品牌
    # 其余封面完好:正文/品牌/收尾(标题渲染依赖 --title 显式传,此处验证封面其余槽位)
    assert "第一章" in html and "导语段落" in html
    assert "给自己造把锤子" in html


def test_strike_old_field_not_used_for_strike_slot():
    """旧 strike 字段不再驱动划线句(缺失 strike_assumption 时整行不渲染,不回退旧行为)。"""
    proc, html = _run(ARTICLE, ["--strike", "旧字段内容"])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "line-through" not in html, "旧 strike 不得回退进划线槽"
    assert "旧字段内容" not in html or "line-through" not in html
