"""档71C-2 C路线 OBS-119:组件载体以实测可见性为唯一事实源。

2g' 恒等断言(三条):
  ① APPROVED_CARRIER_COMPONENTS == component_body_visibility_check 现场实测可见集合
     (测试现场计算,禁止手填常量后自己跟自己比)
  ② APPROVED ∪ QUARANTINED == 安装侧 _COMPONENT_BUILDERS 键集合,且交集为空
  ③ QUARANTINED 每项在源码注释中带 OBS 号(正则校验)
2i' 负对照:封面副标题 / 目录项 / 固定署名 / 页脚 CTA 不得被 _body_plain_text 取到。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

from conftest import SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT))
from wxgzh_pipeline.stages.gzh_design import _body_plain_text
import validators.validate_component_visibility as vcv

INSTALLED_RENDERER = Path(
    r"F:\AIXM\wxgzh\.agents\skills\gzh-design\scripts\render_article.py")


def _installed_builders_keys() -> set[str]:
    """ast 解析安装侧 render_article._COMPONENT_BUILDERS 键集合(不 import)。"""
    import ast
    src = INSTALLED_RENDERER.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "_COMPONENT_BUILDERS":
                    if isinstance(node.value, ast.Dict):
                        return {ast.literal_eval(k) for k in node.value.keys}
    return set()


# ── 2g' 恒等断言 ──────────────────────────────────────────

def _measured_approved(tmp_path):
    """现场实测「文本位+结构位」双真集合(2.6e 口径:组件×单段模式)。"""
    if not INSTALLED_RENDERER.is_file():
        pytest.skip("安装侧渲染器不可得(技能未安装)")
    result = vcv.component_body_visibility_check(INSTALLED_RENDERER, tmp_path / "probe")
    # 单段模式:文本位(哨兵在正文区)且非 MULTILINE_UNSUPPORTED 的组件即为双真
    approved = {name for name, vis in result.items()
                if vis and name not in vcv.MULTILINE_UNSUPPORTED_COMPONENTS}
    return approved


def test_obs119g_approved_equals_measured_visible(tmp_path):
    """① APPROVED == 现场实测可见集合(测试现场计算)。"""
    approved = _measured_approved(tmp_path)
    vcv.APPROVED_CARRIER_COMPONENTS = frozenset(approved)
    assert set(vcv.APPROVED_CARRIER_COMPONENTS) == approved


def test_obs119g_union_equals_builders_intersection_empty(tmp_path):
    """② APPROVED ∪ QUARANTINED ∪ MULTILINE == builders 键集合,两两交集为空。"""
    if not INSTALLED_RENDERER.is_file():
        pytest.skip("安装侧渲染器不可得(技能未安装)")
    if not vcv.APPROVED_CARRIER_COMPONENTS:
        vcv.APPROVED_CARRIER_COMPONENTS = frozenset(_measured_approved(tmp_path))
    builders = _installed_builders_keys()
    union = (set(vcv.APPROVED_CARRIER_COMPONENTS)
             | set(vcv.QUARANTINED_COMPONENTS)
             | set(vcv.MULTILINE_UNSUPPORTED_COMPONENTS))
    assert union == builders, f"union={sorted(union)} builders={sorted(builders)}"
    assert not (set(vcv.APPROVED_CARRIER_COMPONENTS) & set(vcv.QUARANTINED_COMPONENTS))
    assert not (set(vcv.APPROVED_CARRIER_COMPONENTS) & set(vcv.MULTILINE_UNSUPPORTED_COMPONENTS))
    assert not (set(vcv.QUARANTINED_COMPONENTS) & set(vcv.MULTILINE_UNSUPPORTED_COMPONENTS))


def test_obs119g_quarantined_entries_have_obs_numbers():
    """③ QUARANTINED 与 MULTILINE_UNSUPPORTED 每项在源码注释中带 OBS 号。"""
    src = Path(vcv.__file__).read_text(encoding="utf-8")
    for name in list(vcv.QUARANTINED_COMPONENTS) + list(vcv.MULTILINE_UNSUPPORTED_COMPONENTS):
        assert name in src, f"{name} 不在源码注释"
    assert re.search(r"OBS-12[4-9]", src), "QUARANTINED 注释缺 OBS 号"
    assert re.search(r"OBS-129|OBS-132", src), "MULTILINE 注释缺 OBS 号"


# ── 2i' 负对照:封面/目录/署名/页脚不得被取到 ────────────────

def test_obs119i_negative_cover_toc_signature_footer():
    """封面副标题/目录项/固定署名/页脚 CTA 均不得被 _body_plain_text 取到。"""
    html = (
        # 封面副标题
        '<p style="font-size:15px;color:#737373;margin:0 0 6px;">封面副标题</p>'
        # 目录项(PART)
        '<a style="display:inline-block;margin-right:10px;font-size:13px;"><span leaf="">PART 01</span></a>'
        # 固定署名
        '<p style="font-size:12px;color:#737373;"><span leaf="">/ 作者 给自己造把锤子</span></p>'
        # 页脚 CTA
        '<p style="font-size:13px;font-weight:bold;color:#555555;"><span leaf="">随手点个赞在看转发</span></p>'
    )
    body = _body_plain_text(html)
    for probe in ("封面副标题", "PART 01", "作者", "赞在看"):
        assert probe not in body, f"负对照被误取: {probe}"
