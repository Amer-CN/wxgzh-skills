"""档69 OBS-98:校验器 strike 断言改为形态语义判定回归测试。

覆盖(档69 第 2.1 条):
a. 67D 现行 strike 实现(#737373 文字 + 同色 1px)-> PASS
b. ★反向验证:旧橙色粗线形态(#B3593B + 1.5px)-> 必须 FAIL
c. 低对比度 rgba(202,202,199,0.35) 文字 + 任意 decoration-color -> FAIL
   (含带 #B3593B 的情形,无豁免)
d. thickness 1.5px -> FAIL;无 text-decoration-color -> FAIL
e. line_through == 0 -> PASS
"""
from __future__ import annotations

import re

from conftest import load_validator, SKILL_ROOT

FIXTURE = (SKILL_ROOT / "fixtures" / "offline_pipeline_fixture" / "gzh_design"
           / "outputs" / "final.html")


v_mod = load_validator("validate_theme_identity")


def _theme(html: str, tmp_path) -> tuple[int, dict]:
    p = tmp_path / "final.html"
    p.write_text(html, encoding="utf-8")
    return v_mod.validate(p, expected_chapters=6, usage_out=tmp_path / "usage.json")


def _base_html() -> str:
    return FIXTURE.read_text(encoding="utf-8")


def _replace_strike(html: str, style_body: str) -> str:
    """把 fixture 中唯一的 line-through <p> 的整个 style 属性替换。"""
    pat = re.compile(r'<p style="[^"]*?text-decoration:line-through[^"]*"')
    m = pat.search(html)
    assert m, "fixture must contain one line-through <p>"
    return html[:m.start()] + f'<p style="{style_body}"' + html[m.end():]


def _strike_style_body(color, deco, thickness):
    return (f"font-size:15px;color:{color};margin:0 0 6px;"
            f"text-decoration:line-through;text-decoration-color:{deco};"
            f"text-decoration-thickness:{thickness};letter-spacing:0.5px")


# a. 67D 现行实现 -> PASS(结构层 strike 项)
def test_obs98_current_67d_strike_passes(tmp_path):
    html = _base_html()
    ok, rep = _theme(html, tmp_path)
    assert rep["LINE_THROUGH_COUNT"] == 1
    assert rep["strikethrough_forbidden_rgba_present"] is False
    assert rep["strikethrough_props_ok"] is True
    assert rep["structure_ok"] is True  # 无执行证据,THEME_IDENTITY 仍 FAIL,但结构通过


# b. ★反向验证:旧橙色粗线形态必须 FAIL
def test_obs98_old_orange_thick_strike_fails(tmp_path):
    old = _strike_style_body("rgba(202,202,199,0.35)", "#B3593B", "1.5px")
    html = _replace_strike(_base_html(), old)
    ok, rep = _theme(html, tmp_path)
    assert rep["strikethrough_props_ok"] is False
    assert rep["strikethrough_forbidden_rgba_present"] is True  # 低对比色,无豁免
    assert rep["structure_ok"] is False


# c. 低对比度 rgba 文字 + 任意 decoration-color -> FAIL(含带 #B3593B 的情形)
def test_obs98_low_contrast_rgba_with_primary_deco_fails(tmp_path):
    low = _strike_style_body("rgba(202,202,199,0.35)", "#B3593B", "1px")
    html = _replace_strike(_base_html(), low)
    ok, rep = _theme(html, tmp_path)
    assert rep["strikethrough_forbidden_rgba_present"] is True
    assert rep["structure_ok"] is False


def test_obs98_low_contrast_rgba_any_deco_fails(tmp_path):
    low = _strike_style_body("rgba(202,202,199,0.35)", "#737373", "1px")
    html = _replace_strike(_base_html(), low)
    ok, rep = _theme(html, tmp_path)
    assert rep["strikethrough_forbidden_rgba_present"] is True
    assert rep["structure_ok"] is False


# d1. thickness 1.5px -> FAIL
def test_obs98_thickness_1_5px_fails(tmp_path):
    thick = _strike_style_body("#737373", "#737373", "1.5px")
    html = _replace_strike(_base_html(), thick)
    ok, rep = _theme(html, tmp_path)
    assert rep["strikethrough_props_ok"] is False
    assert rep["structure_ok"] is False


# d2. 无 text-decoration-color -> FAIL
def test_obs98_missing_decoration_color_fails(tmp_path):
    nodeco = ("font-size:15px;color:#737373;margin:0 0 6px;"
              "text-decoration:line-through;text-decoration-thickness:1px;"
              "letter-spacing:0.5px")
    html = _replace_strike(_base_html(), nodeco)
    ok, rep = _theme(html, tmp_path)
    assert rep["strikethrough_props_ok"] is False
    assert rep["structure_ok"] is False


# d3. decoration-color 与 color 不同色 -> FAIL
# (同色系细线语义:decoration 必须与文字同色)
def test_obs98_decoration_color_mismatch_fails(tmp_path):
    mism = _strike_style_body("#737373", "#555555", "1px")
    html = _replace_strike(_base_html(), mism)
    ok, rep = _theme(html, tmp_path)
    assert rep["strikethrough_props_ok"] is False
    assert rep["structure_ok"] is False


# d4. decoration-color 为主题主色 #B3593B(即使与 color 同色) -> FAIL
# (主题主色不得用作删除线色)
def test_obs98_primary_as_decoration_color_fails(tmp_path):
    prim = _strike_style_body("#B3593B", "#B3593B", "1px")
    html = _replace_strike(_base_html(), prim)
    ok, rep = _theme(html, tmp_path)
    assert rep["strikethrough_props_ok"] is False
    assert rep["structure_ok"] is False


# d5. 对比度不足(color #A0A0A0 白底 < 4.5) -> FAIL
def test_obs98_low_contrast_hex_fails(tmp_path):
    low = _strike_style_body("#A0A0A0", "#A0A0A0", "1px")
    html = _replace_strike(_base_html(), low)
    ok, rep = _theme(html, tmp_path)
    assert rep["strikethrough_props_ok"] is False
    assert rep["structure_ok"] is False


# e. line_through == 0 -> PASS
def test_obs98_no_strike_passes(tmp_path):
    html = _base_html().replace("text-decoration:line-through;", "")
    ok, rep = _theme(html, tmp_path)
    assert rep["LINE_THROUGH_COUNT"] == 0
    assert rep["strikethrough_props_ok"] is True
    assert rep["strikethrough_forbidden_rgba_present"] is False


# 附:对比度函数校准(#737373 白底应约 4.74,与 67C/67D 一致)
def test_obs98_contrast_calibration_737373():
    ratio = v_mod._contrast_ratio(v_mod._hex_to_rgb("#737373"))
    assert 4.7 <= ratio <= 4.8, ratio


def test_obs98_contrast_white_text_on_white_is_low():
    ratio = v_mod._contrast_ratio((255, 255, 255))
    assert ratio == 1.0
