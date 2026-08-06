"""档71C-R6 OBS-170 陷阱结论焊死(R38/R55):三条会因结论翻转而变红的测试。

修复前语义(fake_dropintro 吞导语 + 组件同名文本补位):
  ① 前置:假渲染器确实吞掉导语段
  ② 部分补位:nine_components.md 的「风险提示」被 alert title 补位 -> not in missing
  ③ 完全假绿:single_intro_trap.md 单段导语同名 -> guard ok=True

2d 修复后(判据分离,_intro_body_text 不含组件锚):②③ 期望翻转,
注释保留原期望(OBS-170)。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from conftest import SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT))
from wxgzh_pipeline.stages import gzh_design as gd

FAKE_DROPINTRO = SKILL_ROOT / "tests" / "fixtures" / "fake_dropintro.py"
NINE_COMPONENTS = SKILL_ROOT / "tests" / "fixtures" / "nine_components.md"
SINGLE_TRAP = SKILL_ROOT / "tests" / "fixtures" / "single_intro_trap.md"
FIRST_PARA = "这是第一段导语，描述整体背景。"
TRAP_PARA = "风险提示"


def _render(renderer: Path, md_path: Path, out_dir: Path) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(renderer),
         "--article", str(md_path), "--output-dir", str(out_dir),
         "--theme", "smartisan"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=120)
    assert proc.returncode == 0, proc.stderr[-500:]
    html_path = out_dir / "final.html"
    return html_path.read_text(encoding="utf-8") if html_path.is_file() else ""


def test_obs170_dropintro_drops_intro(tmp_path):
    """① 前置条件:假渲染器确实吞掉导语第一段。"""
    html = _render(FAKE_DROPINTRO, NINE_COMPONENTS, tmp_path / "r1")
    body = gd._body_plain_text(html)
    assert gd._normalize_text(FIRST_PARA) not in body, \
        "前置:fake_dropintro 应吞掉导语第一段"


def test_obs170_component_title_substitutes(tmp_path):
    """② 修复前语义:组件同名文本补位导语段。

    修复前:「风险提示」not in missing_text(补位坐实)且 guard ok=False(仅部分补位);
    修复后(2d 翻转):「风险提示」in missing_text 且 guard ok=False。
    """
    html = _render(FAKE_DROPINTRO, NINE_COMPONENTS, tmp_path / "r2")
    md = NINE_COMPONENTS.read_text(encoding="utf-8")
    guard = gd._intro_content_fidelity(md, html)
    # 修复后期望(OBS-170 翻转):同名补位失效,导语段被判 missing
    assert TRAP_PARA in guard["missing_text"], \
        f"修复后「风险提示」应 missing;missing_text={guard['missing_text']!r}"
    assert guard["ok"] is False, "修复后 guard 应 FAIL(导语缺失)"


def test_obs170_full_false_green_constructible(tmp_path):
    """③ 完全假绿:单段导语同名 -> 修复前 guard ok=True;修复后 ok=False。

    修复前:ok=True(完全假绿);修复后(2d 翻转):ok=False。
    """
    html = _render(FAKE_DROPINTRO, SINGLE_TRAP, tmp_path / "r3")
    md = SINGLE_TRAP.read_text(encoding="utf-8")
    guard = gd._intro_content_fidelity(md, html)
    # 修复后期望(OBS-170 翻转):完全假绿被拆穿
    assert guard["ok"] is False, f"修复后 guard 应 FAIL;ok={guard['ok']} missing={guard['missing_text']!r}"
    # 3c(71C-R7):同名导语段必须在 missing_text 中(补位失效)
    assert TRAP_PARA in guard["missing_text"], \
        f"修复后「风险提示」应在 missing_text;missing={guard['missing_text']!r}"
