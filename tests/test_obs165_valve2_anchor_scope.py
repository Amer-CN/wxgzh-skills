"""档71C-R5 OBS-171:阀二落成可回归测试。

用真渲染器渲染 nine_components.md 一次;参数化两套锚:
甲 = R2 的 6 条手抄 style 常量(逐字列出);乙 = 当前 JSON 全量。
monkeypatch gzh_design._COMPONENT_PARA_RES 后逐项断言。
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT))
from wxgzh_pipeline.stages import gzh_design as gd

NINE_COMPONENTS = SKILL_ROOT / "tests" / "fixtures" / "nine_components.md"

# R2 的 6 条手抄锚 style(逐字,来自档71C-2 提交时的 _COMPONENT_PARA_RES)
MANUAL_STYLES = [
    "margin:0;font-size:14px;color:#555555;line-height:1.8;",          # alert/dialogue
    "margin:0 0 6px;font-size:12px;color:#737373;line-height:1.7;",    # footnotes
    "margin:0;font-size:16px;font-weight:800;color:#8A4530;line-height:1.7;",  # quote
    "margin:0 0 24px;font-size:14px;color:#555555;line-height:1.8;",   # media-text
    "margin:0 0 16px;font-size:12px;color:#737373;text-align:center;",  # gallery
    "margin:0;font-size:14px;color:#555555;font-weight:600;line-height:1.6;",  # resources
]


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


def _cfg(styles) -> list:
    return [re.compile(f'<p style="{re.escape(s)}">(.*?)</p>', re.S) for s in styles]


def test_obs171_valve2_anchor_scope(tmp_path):
    """甲乙两套锚逐项对照:ok/line_count/missing/组件文本/body_len。"""
    from tests.test_obs119_visibility import _resolved_renderer
    renderer, log = _resolved_renderer()
    if renderer is None:
        pytest.skip("渲染器不可得: " + "|".join(log))
    md = NINE_COMPONENTS.read_text(encoding="utf-8")
    html = _render(renderer, NINE_COMPONENTS, tmp_path / "render")

    import json as _json
    cfg_a = _cfg(MANUAL_STYLES)                      # 甲:6 条手抄
    cfg_b = gd._COMPONENT_PARA_RES                   # 乙:当前 JSON 全量
    assert len(cfg_a) == 6, f"甲锚条数应 6,实际 {len(cfg_a)}"
    # 4a(OBS-174):乙条数与 JSON 同源 —— 从 component_anchors.json 现算 N。
    payload = _json.loads((SKILL_ROOT / "validators" / "component_anchors.json")
                          .read_text(encoding="utf-8"))
    n_json = len({row["style"] for row in payload["anchors"]
                  if row.get("style") and row["style"] != "URL_SLOT"})
    assert len(cfg_b) == n_json, f"乙锚条数 {len(cfg_b)} != JSON 同源 {n_json}"
    print(f"N(JSON distinct 非 URL style)={n_json}")

    results = {}
    orig = gd._COMPONENT_PARA_RES
    try:
        for label, cfg in (("甲", cfg_a), ("乙", cfg_b)):
            gd._COMPONENT_PARA_RES = cfg
            body = gd._body_plain_text(html)
            guard = gd._intro_content_fidelity(md, html)
            probes = {
                "alert_body": "这是alert的正文内容。",
                "quote_text": "这是quote的金句文本。",
                "code_compare_before": "old_code()",
                "media_exp": "这是media-text的解释段落。",
                "gallery_cap": "安装第一步",
                "long_image_cap": "完整流程图",
                "resources_text": "官方文档",
                "footnotes_fn": "数据来源说明",
                "dialogue_msg": "为什么样式丢失？",
            }
            in_body = {k: gd._normalize_text(v) in body for k, v in probes.items()}
            results[label] = {"ok": guard["ok"],
                              "line_count": guard["intro_line_count"],
                              "missing": guard["missing_text"],
                              "in_body": in_body,
                              "body_len": len(body)}
    finally:
        gd._COMPONENT_PARA_RES = orig

    # 逐项断言
    assert results["甲"]["ok"] == results["乙"]["ok"], "guard ok 应一致"
    assert results["甲"]["line_count"] == results["乙"]["line_count"] == 2
    assert results["甲"]["missing"] == results["乙"]["missing"] == ""
    for k in ("alert_body", "quote_text", "code_compare_before", "media_exp",
              "gallery_cap", "long_image_cap", "resources_text",
              "footnotes_fn", "dialogue_msg"):
        # 甲(6 条手抄)对部分组件无锚——如实分列断言(注释写明理由,4b)。
        if k in ("code_compare_before", "long_image_cap"):
            # code_compare_before: 甲无等宽代码锚(手抄 6 条无 SF Mono);
            # long_image_cap: 甲无 12px/24px caption 锚(手抄只有 gallery 的 16px 版)。
            assert results["乙"]["in_body"][k], f"乙缺 {k}"
            continue
        assert results["甲"]["in_body"][k], f"甲缺 {k}"
        assert results["乙"]["in_body"][k], f"乙缺 {k}"
    assert results["乙"]["body_len"] > results["甲"]["body_len"], \
        "乙(JSON 锚)正文区应比甲(手抄锚)长"
    print(f"甲锚条数={len(cfg_a)} 乙锚条数={len(cfg_b)} "
          f"body_len 甲/乙={results['甲']['body_len']}/{results['乙']['body_len']}")
