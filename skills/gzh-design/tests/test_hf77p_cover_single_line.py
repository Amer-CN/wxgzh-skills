"""77P/OBS-340: cover strike and subtitle render-only single-line safety net."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
RENDER = SKILL_ROOT / "scripts" / "render_article.py"


def test_cover_strike_and_subtitle_render_one_line():
    td = Path(tempfile.mkdtemp(prefix="render-77p-"))
    article = td / "article.md"
    article.write_text("""# 标题

这个导语副标题被故意写得很长，用来验证渲染端的安全网不会让它折行。

## 第一章

正文。
""", encoding="utf-8")
    long_strike = "这个划线旧认知也被故意写得很长，用来验证渲染端安全网。"
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(RENDER),
         "--article", str(article), "--output-dir", str(td),
         "--theme", "smartisan", "--strike-assumption", long_strike],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert result.returncode == 0, result.stdout + result.stderr
    html = (td / "final.html").read_text(encoding="utf-8")
    assert long_strike in html
    assert "这个导语副标题被故意写得很长" in html
    assert "white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" in html
