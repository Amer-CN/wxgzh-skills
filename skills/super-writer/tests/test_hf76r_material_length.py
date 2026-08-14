"""76R 任务 4/OBS-290:素材定长度——长度门与素材量脱钩,禁止逼扩写。

函数级直测 validate_article_length:
- 素材耗尽(material_exhausted=True)→ 长度下限降 advisory(PASS 留痕);
- 素材充分但文章单薄(material_exhausted=False)→ 仍 FAIL(质量下限不退让);
- 常规路径(字数达标)行为不变。
"""
from __future__ import annotations

from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from validate_article_length import validate_article_length  # noqa: E402


def _article(text: str) -> Path:
    d = Path(tempfile.mkdtemp())
    p = d / "article.md"
    p.write_text(text, encoding="utf-8")
    return p


SHORT = "# 标题\n\n" + "素材写出的简短正文。" * 30  # ~900 chars < min 2500
LONG = "# 标题\n\n" + "正常篇幅的正文内容。" * 280  # ~2800 chars within 2500-4000


def test_material_exhausted_short_passes_with_note():
    """素材耗尽 → 短文 PASS,length_status=below_min_material_exhausted 留痕。"""
    errors, warnings, info = validate_article_length(
        str(_article(SHORT)), target_visible_chars=3000,
        acceptable_min=2500, acceptable_max=4000,
        article_mode="medium", material_exhausted=True)
    assert not errors, errors
    assert info["length_status"] == "below_min_material_exhausted"
    assert info.get("material_exhausted") is True
    assert any("素材写干即停" in w for w in warnings), warnings


def test_material_sufficient_thin_still_fails():
    """素材充分但文章单薄 → 仍 FAIL(质量下限不退让)。"""
    errors, warnings, info = validate_article_length(
        str(_article(SHORT)), target_visible_chars=3000,
        acceptable_min=2500, acceptable_max=4000,
        article_mode="medium", material_exhausted=False)
    assert errors, "素材充分但短文必须 FAIL"
    assert any("below" in e or "acceptable_min" in e for e in errors)
    assert info["length_status"] == "below_min"


def test_normal_length_unchanged():
    """常规路径(字数达标)→ PASS,无 material_exhausted 标记。"""
    errors, warnings, info = validate_article_length(
        str(_article(LONG)), target_visible_chars=3000,
        acceptable_min=2500, acceptable_max=4000,
        article_mode="medium", material_exhausted=False)
    assert not errors, errors
    assert info["length_status"] == "within_range"
    assert info.get("material_exhausted") is not True
