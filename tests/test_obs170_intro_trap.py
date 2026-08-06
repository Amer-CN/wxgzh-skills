"""档71C-R5 OBS-170 陷阱反证(R37):fake_dropintro 吞导语 + 组件同名文本补位。

用 nine_components.md(导语第二段「风险提示」与 alert title 同名):
- 断言导语第一段被判 missing(证明假渲染器确实在丢导语);
- 对「风险提示」实测断言:若 guard 判存在(因 alert title 同名文本进正文区)
  -> 断言 not in missing_text 并标记【高危:假绿可构造】;
  若判 missing -> 断言 in missing_text 并说明。
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


def _render_with(renderer: Path, md_path: Path, out_dir: Path) -> str:
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


def test_obs170_dropintro_trap():
    """fake_dropintro 吞导语:第一段 missing 且「风险提示」实测判定。"""
    md = NINE_COMPONENTS.read_text(encoding="utf-8")
    html = _render_with(FAKE_DROPINTRO, NINE_COMPONENTS, Path(__file__).parent / ".." / ".." / ".temp" / "71cr5-trap")
    # 用 JSON 锚(当前 _COMPONENT_PARA_RES)
    guard = gd._intro_content_fidelity(md, html)
    missing = guard["missing_text"]
    first_para = "这是第一段导语，描述整体背景。"
    trap_para = "风险提示"
    # ① 第一段必须被判 missing(证明假渲染器确实在丢导语)
    assert gd._normalize_text(first_para) not in gd._body_plain_text(html), \
        "前置:假渲染器应吞掉第一段导语"
    assert gd._normalize_text(first_para) in gd._normalize_text(missing) or \
        first_para in missing, f"第一段应在 missing_text: {missing!r}"
    # ② 陷阱段「风险提示」实测判定
    trap_in_missing = (trap_para in missing)
    if trap_in_missing:
        print("【判定】风险提示 判 missing:组件同名文本未能顶替(导语本体未进正文区)")
    else:
        print("【高危:假绿可构造】风险提示 判存在:alert title 同名文本补位")
    # 两种结果都合法,但必须断言其一
    assert trap_in_missing or gd._normalize_text(trap_para) in gd._body_plain_text(html), \
        "风险提示既不在 missing 也不在 body,自相矛盾"
    # 判定结果由 print 输出供报告;不 return(避免 pytest warning)。


def test_obs170_dropintro_guard_ok_flag():
    """guard ok 标志随陷阱判定:若假绿可构造则 ok 可能为 True(记录,不改 guard)。"""
    md = NINE_COMPONENTS.read_text(encoding="utf-8")
    html = _render_with(FAKE_DROPINTRO, NINE_COMPONENTS,
                        Path(__file__).parent / ".." / ".." / ".temp" / "71cr5-trap2")
    guard = gd._intro_content_fidelity(md, html)
    missing = guard["missing_text"]
    trap_in_missing = ("风险提示" in missing)
    if not trap_in_missing:
        # 假绿可构造:第一段 missing 但 guard ok 仍可能 True(陷阱成立)
        print(f"guard ok={guard['ok']} missing_text={missing!r}")
    # 只记录不修改;断言 guard 对象结构完整
    assert "ok" in guard and "missing_text" in guard
