"""档71E OBS-175:配图章节亲和判据测试(独立 CLI,不挂主门禁,S65/3d 例外)。

判据:每张正文图在 final.html 中的章节 == 其数字对在 final_article.md 中
首次出现的 ## 章节。
正例 图与数字线同章 → PASS
反例 ★把图挪到别的章节 → 必须 FAIL 且 reason 命中(本判据唯一存在理由)
边界 bindings 缺 chart_group → 不静默跳过,判 FAIL 并打印缺字段名
"""
from __future__ import annotations

import json
from pathlib import Path

from validators.validate_image_section_affinity import (
    REASON, main, validate_affinity,
)

ARTICLE = """# 测试文章

导语段落,不含数字对比。

## 一、数字线

从 8 条扩到 11 条。

## 二、其它

没有数字的段落。
"""

TOC = '<p>TOC <span>一、数字线</span> <span>二、其它</span></p>'
CH1 = '<section><p><span>一、数字线</span></p></section>'
CH2 = '<section><p><span>二、其它</span></p></section>'
IMG = '<img src="https://example.com/img1.png">'


def _html(img_after: str) -> str:
    parts = [TOC, CH1]
    if img_after == "ch1":
        parts.append(IMG)
    parts.append(CH2)
    if img_after == "ch2":
        parts.append(IMG)
    return "<body>" + "".join(parts) + "</body>"


def _bindings(chart_group=None, caption="红线数量：8 条对 11 条") -> dict:
    entry = {
        "asset_id": "A-005",
        "caption": caption,
        "remote_url": "https://example.com/img1.png",
        "sha256": "a" * 64,
    }
    if chart_group is not None:
        entry["chart_group"] = chart_group
    return {"body_images": [entry]}


def _write(tmp_path, article=None, html=None, bindings=None):
    p = tmp_path
    p.mkdir(parents=True, exist_ok=True)
    (p / "article.md").write_text(article or ARTICLE, encoding="utf-8")
    (p / "final.html").write_text(html or _html("ch1"), encoding="utf-8")
    (p / "bindings.json").write_text(
        json.dumps(bindings or _bindings(), ensure_ascii=False), encoding="utf-8")
    return p


# ── 正例:图与数字线同章 → PASS ─────────────────────────────

def test_obs175_positive_same_chapter_pass(tmp_path):
    p = _write(tmp_path, html=_html("ch1"), bindings=_bindings(chart_group={"start": 8, "end": 11}))
    rep = validate_affinity(p / "article.md", p / "final.html", p / "bindings.json")
    assert rep["ok"] is True, rep
    assert rep["per_image"][0]["image_section"] == "一、数字线"
    assert rep["per_image"][0]["number_section"] == "一、数字线"
    assert rep["per_image"][0]["same_chapter"] is True


# ── 反例:图挪到别的章节 → FAIL 且 reason 命中 ───────────────

def test_obs175_negative_cross_chapter_fails(tmp_path):
    p = _write(tmp_path, html=_html("ch2"), bindings=_bindings(chart_group={"start": 8, "end": 11}))
    rep = validate_affinity(p / "article.md", p / "final.html", p / "bindings.json")
    assert rep["ok"] is False
    assert rep["reason"] == REASON
    img = rep["per_image"][0]
    assert img["ok"] is False
    assert img["image_section"] == "二、其它"
    assert img["number_section"] == "一、数字线"
    assert img["same_chapter"] is False


# ── 边界:bindings 缺 chart_group → FAIL 且打印缺字段名 ─────

def test_obs175_boundary_missing_chart_group_fails(tmp_path):
    p = _write(tmp_path, html=_html("ch1"), bindings=_bindings(chart_group=None))
    rep = validate_affinity(p / "article.md", p / "final.html", p / "bindings.json")
    assert rep["ok"] is False
    assert rep["reason"] == REASON
    assert "missing field: chart_group" in rep["per_image"][0]["reason"]


# ── CLI 退出码:0 = PASS,1 = FAIL(直接调 main,不走子进程)────

def test_obs175_main_exit_codes(tmp_path, capsys):
    ok_dir = _write(tmp_path / "ok", html=_html("ch1"), bindings=_bindings(chart_group={"start": 8, "end": 11}))
    code_ok = main(["--article", str(ok_dir / "article.md"),
                    "--html", str(ok_dir / "final.html"),
                    "--bindings", str(ok_dir / "bindings.json"),
                    "--out-dir", str(tmp_path / "out-ok")])
    assert code_ok == 0
    assert "OBS175_IMAGE_SECTION_AFFINITY=PASS" in capsys.readouterr().out
    bad_dir = _write(tmp_path / "bad", html=_html("ch2"), bindings=_bindings(chart_group={"start": 8, "end": 11}))
    code_bad = main(["--article", str(bad_dir / "article.md"),
                     "--html", str(bad_dir / "final.html"),
                     "--bindings", str(bad_dir / "bindings.json"),
                     "--out-dir", str(tmp_path / "out-bad")])
    assert code_bad == 1
    assert REASON in capsys.readouterr().out
    report = json.loads((tmp_path / "out-bad" / "validate_image_section_affinity.json")
                        .read_text(encoding="utf-8"))
    assert report["reason"] == REASON
