"""档71C-2 OBS-123:图片指纹去魔数窗口 —— 4c 负对照 + 4d 两向 pytest。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from validators.validate_theme_identity import (
    FINGERPRINTS, _img_type_occurrences)

IMG2A = FINGERPRINTS["image_2a_standard"]
IMG_MT = FINGERPRINTS["image_media_text_card"]
INSTALLED_RENDERER = Path(
    r"F:\AIXM\wxgzh\.agents\skills\gzh-design\scripts\render_article.py")


def test_obs123_img_inside_paired_section_hits():
    """4d 正向:<img 在配对 section 内 -> 命中。"""
    html = (f'<section style="box-shadow:{IMG2A}">'
            '<p>x</p><img src="https://x.com/a.png">'
            "</section>")
    assert _img_type_occurrences(html, IMG2A) == 1


def test_obs123_img_after_section_close_misses():
    """4d 反向:<img 在该 section 闭合之后 380 字符处 -> 不命中。

    旧 400 字符窗口(令牌起点向后 400 字符内查 <img)会误命中,本测试先
    复现旧逻辑的误命中,再断言新结构判定不命中,证明魔数确实死了。"""
    html = (f'<section style="box-shadow:{IMG2A}"></section>'
            + "x" * 380
            + '<img src="https://x.com/b.png">')
    # 对照:旧 400 窗口在令牌起点向后 442 字符内能看见该 <img。
    i = html.find(IMG2A)
    assert "<img" in html[i:i + len(IMG2A) + 400]
    # 新判定:该 <img 在配对 </section> 之后,不得命中。
    assert _img_type_occurrences(html, IMG2A) == 0


def test_obs123_alert_fragment_no_img(tmp_path):
    """4c 负对照:hammer alert 组件产物(≈660 B,含共享阴影令牌)改后返回 []。"""
    if not INSTALLED_RENDERER.is_file():
        pytest.skip("安装侧渲染器不可得(技能未安装)")
    md = tmp_path / "a.md"
    md.write_text('# 标题\n\n## 章节\n\n:::alert type="warn"\n提示内容\n:::\n',
                  encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(INSTALLED_RENDERER),
         "--article", str(md), "--output-dir", str(out), "--theme", "smartisan"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    html = (out / "final.html").read_text(encoding="utf-8")
    # alert 共享 media-text 阴影令牌但无 <img,两个图片指纹都不得命中。
    assert _img_type_occurrences(html, IMG_MT) == 0
    assert _img_type_occurrences(html, IMG2A) == 0
