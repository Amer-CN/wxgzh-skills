"""档71C-R3 OBS-151/152 反证测试(R28/R31)。

假渲染器(测试专用)证明名单"能响":
- fake_collapse.py:多行塌成单 <p> -> component_structure_check 的 struct_ok=False
  -> export_lists_from_measurement 的 multiline 非空。
- fake_empty.py:输出不含哨兵 -> render_ok=False -> quarantined 非空。
- 门禁正向测试:注入假名单 -> multiline_gate / quarantine_gate 返回非空命中且行号正确
  (恢复 R2 删除的"能证明门禁会响"测试,R31 替代物)。
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from conftest import SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT))
import validators.validate_component_visibility as vcv

FAKE_COLLAPSE = SKILL_ROOT / "tests" / "fixtures" / "fake_collapse.py"
FAKE_EMPTY = SKILL_ROOT / "tests" / "fixtures" / "fake_empty.py"


def test_obs151_fake_collapse_multiline_nonempty(tmp_path):
    """R28 反证:塌陷渲染器下 multiline 必须非空且含预期组件。"""
    assert FAKE_COLLAPSE.is_file(), "fake_collapse.py 缺失"
    measured = vcv.component_structure_check(FAKE_COLLAPSE, tmp_path / "c")
    lists = vcv.export_lists_from_measurement(measured)
    assert lists["multiline"], "fake_collapse 下 multiline 应为非空"
    # 至少含一个有相邻文本槽对的组件(media-text: cap+exp)
    assert "media-text" in lists["multiline"], sorted(lists["multiline"])


def test_obs151_fake_empty_quarantined_nonempty(tmp_path):
    """R28 反证:无哨兵渲染器下 quarantined 必须非空。"""
    assert FAKE_EMPTY.is_file(), "fake_empty.py 缺失"
    measured = vcv.component_structure_check(FAKE_EMPTY, tmp_path / "e")
    lists = vcv.export_lists_from_measurement(measured)
    assert lists["quarantined"], "fake_empty 下 quarantined 应为非空"
    assert len(lists["quarantined"]) == 9, sorted(lists["quarantined"])


def test_obs151_multiline_gate_fires_with_injected_list(monkeypatch):
    """R31:注入假名单后 multiline_gate 必须返回非空命中且行号正确。"""
    from validators.validate_component_visibility import multiline_gate
    monkeypatch.setattr(vcv, "MULTILINE_UNSUPPORTED_COMPONENTS",
                        frozenset({"alert", "media-text"}))
    md = "# 标题\n\n## 章节\n\n:::alert type=\"warning\"\nS1\nS2\nS3\n:::\n"
    hits = multiline_gate(md)
    assert hits, "注入名单后 multiline_gate 应命中"
    assert hits[0]["name"] == "alert"
    assert hits[0]["line_count"] == 3


def test_obs151_quarantine_gate_fires_with_injected_list(monkeypatch):
    """R31:注入假名单后 quarantine_gate 必须返回非空命中且行号正确。"""
    from validators.validate_component_visibility import quarantine_gate
    monkeypatch.setattr(vcv, "QUARANTINED_COMPONENTS",
                        frozenset({"code-compare", "long-image"}))
    md = "# 标题\n\n## 章节\n\n:::code-compare\n@before\nx\n@end\n:::\n"
    hits = quarantine_gate(md)
    assert hits, "注入名单后 quarantine_gate 应命中"
    assert hits[0]["name"] == "code-compare"
    assert hits[0]["line"] == 5


def test_obs151_real_renderer_lists(tmp_path):
    """真渲染器四名单实测(防回归;OBS-154 锚闭环后:QUAR/MULTI/GAP 全空,APPROVED 9 类)。"""
    from tests.test_obs119_visibility import _resolved_renderer
    renderer, log = _resolved_renderer()
    if renderer is None:
        pytest.skip("渲染器不可得: " + "|".join(log))
    measured = vcv.component_structure_check(renderer, tmp_path / "r")
    lists = vcv.export_lists_from_measurement(measured)
    assert lists["quarantined"] == frozenset(), sorted(lists["quarantined"])
    assert lists["multiline"] == frozenset(), sorted(lists["multiline"])
    assert lists["anchor_gap"] == frozenset(), sorted(lists["anchor_gap"])
    assert len(lists["approved"]) == 9, sorted(lists["approved"])


# ── 4b(OBS-155):三表并集与 SLOTS 一一对应 ───────────────────

def test_obs155_sentinel_tables_match_slots():
    """三张哨兵表并集 == component_slots.SLOTS 的 (组件,槽,模式) 一一对应。"""
    from validators.component_slots import SLOTS
    gen = {}
    for cs in SLOTS:
        for s in cs.slots:
            key = (cs.component, s.name, s.mode)
            gen.setdefault(key, []).append(vcv._sentinel_name(cs.component, s.name, s.mode))
    # 表并集(每组件)
    table_union = {}
    for comp in set(vcv.REQUIRED_SENTINELS) | set(vcv.OPTIONAL_SENTINELS) | set(vcv.URL_SENTINELS):
        names = (vcv.REQUIRED_SENTINELS.get(comp, [])
                 + vcv.OPTIONAL_SENTINELS.get(comp, [])
                 + vcv.URL_SENTINELS.get(comp, []))
        table_union[comp] = set(names)
    # SLOTS 每组件应生成的哨兵(非 multi 槽 1 个,multi 槽 N=3)
    for cs in SLOTS:
        expected = set()
        for s in cs.slots:
            if s.multi:
                for i in range(3):
                    expected.add(vcv._sentinel_name(cs.component, s.name, s.mode, i))
            else:
                expected.add(vcv._sentinel_name(cs.component, s.name, s.mode))
        got = table_union.get(cs.component, set())
        assert got == expected, \
            f"{cs.component}: 表={sorted(got)} SLOTS={sorted(expected)} 差={sorted(got ^ expected)}"


# ── 4e(R30):语法门禁枚举 == 安装侧渲染器源码字面量(ast) ─────

def test_obs156_enum_drift_assertion(tmp_path):
    """R30:component_slots 枚举 == 安装侧渲染器 _ALERT_TYPES/_QUOTE_TYPES 字面量。"""
    from tests.test_obs119_visibility import _resolved_renderer
    from validators.component_slots import ALERT_TYPES, QUOTE_TYPES
    import ast
    renderer, log = _resolved_renderer()
    if renderer is None:
        pytest.skip("渲染器不可得: " + "|".join(log))
    # 枚举字面量在 generate_advanced_html.py 的 alert()/quote() 函数内。
    builders_src = renderer.parent / "generate_advanced_html.py"
    assert builders_src.is_file(), f"缺少 {builders_src}"
    tree = ast.parse(builders_src.read_text(encoding="utf-8"))
    found = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in ("alert", "quote"):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Assign):
                    for tgt in sub.targets:
                        if (isinstance(tgt, ast.Name)
                                and tgt.id in ("_ALERT_TYPES", "_QUOTE_TYPES")
                                and isinstance(sub.value, ast.Set)):
                            found[tgt.id] = frozenset(
                                ast.literal_eval(e) for e in sub.value.elts)
    assert "_ALERT_TYPES" in found, "渲染器源码无 _ALERT_TYPES"
    assert found["_ALERT_TYPES"] == ALERT_TYPES, \
        f"alert 枚举漂移: 渲染器={sorted(found['_ALERT_TYPES'])} 清单={sorted(ALERT_TYPES)}"
    assert found["_QUOTE_TYPES"] == QUOTE_TYPES, \
        f"quote 枚举漂移: 渲染器={sorted(found['_QUOTE_TYPES'])} 清单={sorted(QUOTE_TYPES)}"


# ── 5b(OBS-157):双跑 —— 安装侧与仓内树结论逐位相等 ─────────

def test_obs157_dual_run_installed_vs_repo(tmp_path):
    """安装侧与仓内树各跑一遍四名单,断言逐位相等;不等 FAIL 并打印两侧 sha256。"""
    from tests.test_obs119_visibility import _resolved_renderer, _installed_renderer
    import hashlib
    repo_renderer, repo_log = _resolved_renderer()
    installed_renderer, inst_log = _installed_renderer()
    if installed_renderer is None:
        pytest.skip("安装侧渲染器不可得: " + "|".join(inst_log))
    if repo_renderer is None:
        pytest.skip("仓内渲染器不可得: " + "|".join(repo_log))
    m_repo = vcv.component_structure_check(repo_renderer, tmp_path / "repo")
    m_inst = vcv.component_structure_check(installed_renderer, tmp_path / "inst")
    l_repo = vcv.export_lists_from_measurement(m_repo)
    l_inst = vcv.export_lists_from_measurement(m_inst)
    sha_repo = hashlib.sha256(repo_renderer.read_bytes()).hexdigest()
    sha_inst = hashlib.sha256(installed_renderer.read_bytes()).hexdigest()
    assert l_repo == l_inst, \
        f"双跑名单不等: repo={l_repo} inst={l_inst}\n" \
        f"repo_sha={sha_repo} inst_sha={sha_inst}"
    # 逐位判据也相等
    for comp in m_repo:
        assert m_repo[comp] == m_inst[comp], \
            f"{comp}: repo={m_repo[comp]} inst={m_inst[comp]}"


# ── 2a/2b(OBS-160,R32/R45):ANCHOR_GAP / QUARANTINED 反证 ────

FAKE_OFFANCHOR = SKILL_ROOT / "tests" / "fixtures" / "fake_offanchor.py"
FAKE_PARTIAL = SKILL_ROOT / "tests" / "fixtures" / "fake_partial.py"


def test_obs160_fake_offanchor_gap_nonempty(tmp_path):
    """反证:哨兵在锚集外 style 里 -> ANCHOR_GAP 非空、APPROVED 不足 9 类。"""
    assert FAKE_OFFANCHOR.is_file()
    measured = vcv.component_structure_check(FAKE_OFFANCHOR, tmp_path / "off")
    lists = vcv.export_lists_from_measurement(measured)
    assert lists["anchor_gap"], "fake_offanchor 下 ANCHOR_GAP 应为非空"
    assert len(lists["approved"]) < 9, f"APPROVED 应不足 9 类: {sorted(lists['approved'])}"


def test_obs160_fake_partial_quarantined_nonempty_and_distinct(tmp_path):
    """反证:只渲染一半哨兵 -> QUARANTINED 非空且不等于全 9 类(有区分度)。"""
    assert FAKE_PARTIAL.is_file()
    measured = vcv.component_structure_check(FAKE_PARTIAL, tmp_path / "part")
    lists = vcv.export_lists_from_measurement(measured)
    assert lists["quarantined"], "fake_partial 下 QUARANTINED 应为非空"
    assert lists["quarantined"] != frozenset(
        {"alert", "code-compare", "dialogue", "footnotes", "gallery",
         "long-image", "media-text", "quote", "resources"}), \
        "QUARANTINED 不应是全 9 类(需有区分度)"
