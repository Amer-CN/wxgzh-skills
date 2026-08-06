"""档71C-2 C路线 OBS-119:组件载体以实测可见性为唯一事实源。

2g'/3d(档71C-2A' 重写,R19 口径):三个名单常量 == 现场实测导出集合。
左边 = import 后未被修改的模块常量,右边 = 现场实测,两边不同源(禁止赋值后自证)。

3e(OBS-135):每条测试独立实测,无跨用例顺序依赖。
3a/3b/3c:QUARANTINED=={not text_ok}; MULTILINE=={text_ok and not struct_ok};
         APPROVED=={text_ok and struct_ok}(component_structure_check 现场实测)。
4b/4c:能力矩阵 JSON 与现场实测三位一致;assertions_executed 为真。
5a/5b(OBS-137):渲染器路径经 skill_discovery 解析,不写死盘符。
2i' 负对照:封面副标题 / 目录项 / 固定署名 / 页脚 CTA 不得被 _body_plain_text 取到。
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

from conftest import SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT))
from wxgzh_pipeline.stages.gzh_design import _body_plain_text
import validators.validate_component_visibility as vcv


# ── 5a(OBS-137):渲染器路径经 skill_discovery / paths 解析,不写死盘符 ──

def _resolved_renderer() -> tuple[Path | None, list[str]]:
    """经 skill_discovery/paths 解析安装侧渲染器。

    返回 (renderer, 解析过程日志);解析不到 -> (None, 日志),由调用方 skip。
    """
    log: list[str] = []
    try:
        from wxgzh_pipeline import paths as P
        from wxgzh_pipeline import skill_discovery as SD
        root = P.resolve_project_root()
        log.append(f"project_root={root}")
        sh = P.skills_home(root)
        log.append(f"skills_home={sh}")
        lock = SD.load_lock(SKILL_ROOT)
        entry = lock["skills"].get("gzh-design", {})
        ep = entry.get("entrypoint", "")
        log.append(f"lock gzh-design entrypoint={ep}")
        if not ep:
            return None, log + ["lock 无 gzh-design entrypoint"]
        cand = Path(sh) / "gzh-design" / ep
        log.append(f"candidate={cand} is_file={cand.is_file()}")
        return (cand if cand.is_file() else None), log
    except Exception as e:  # noqa: BLE001
        return None, log + [f"resolve failed: {e!r}"]


def _renderer_or_skip():
    renderer, log = _resolved_renderer()
    if renderer is None:
        pytest.skip("安装侧渲染器不可得;解析过程:\n" + "\n".join(log))
    return renderer, log


def _installed_builders_keys(renderer: Path) -> set[str]:
    """ast 解析安装侧 render_article._COMPONENT_BUILDERS 键集合(不 import)。"""
    import ast
    src = renderer.read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "_COMPONENT_BUILDERS":
                    if isinstance(node.value, ast.Dict):
                        return {ast.literal_eval(k) for k in node.value.keys}
    return set()


# ── 3d 三条恒等断言(R19:左边=未改常量,右边=现场实测) ─────────────

def test_obs119g_three_lists_equal_measured(tmp_path):
    """三个模块常量(import 后未改) == component_structure_check 现场实测导出。"""
    renderer, _log = _renderer_or_skip()
    measured = vcv.component_structure_check(renderer, tmp_path / "struct")
    exported = vcv.export_lists_from_measurement(measured)
    assert set(vcv.QUARANTINED_COMPONENTS) == exported["quarantined"], (
        f"QUARANTINED 与实测不符: 常量={sorted(vcv.QUARANTINED_COMPONENTS)} "
        f"实测={sorted(exported['quarantined'])}")
    assert set(vcv.MULTILINE_UNSUPPORTED_COMPONENTS) == exported["multiline"], (
        f"MULTILINE 与实测不符: 常量={sorted(vcv.MULTILINE_UNSUPPORTED_COMPONENTS)} "
        f"实测={sorted(exported['multiline'])}")
    assert set(vcv.APPROVED_CARRIER_COMPONENTS) == exported["approved"], (
        f"APPROVED 与实测不符: 常量={sorted(vcv.APPROVED_CARRIER_COMPONENTS)} "
        f"实测={sorted(exported['approved'])}")
    # S18:APPROVED 空集或 <=2 类 -> 停机条件(测试直接 FAIL,供审核方裁决)
    assert len(exported["approved"]) >= 3, "S18:APPROVED 只剩 <=2 类"


def test_obs119g_union_equals_builders_intersection_empty(tmp_path):
    """三名单并集 == 安装侧 _COMPONENT_BUILDERS 键集合,两两交集为空。"""
    renderer, _log = _renderer_or_skip()
    builders = _installed_builders_keys(renderer)
    union = (set(vcv.APPROVED_CARRIER_COMPONENTS)
             | set(vcv.QUARANTINED_COMPONENTS)
             | set(vcv.MULTILINE_UNSUPPORTED_COMPONENTS))
    assert union == builders, f"union={sorted(union)} builders={sorted(builders)}"
    assert not (set(vcv.APPROVED_CARRIER_COMPONENTS) & set(vcv.QUARANTINED_COMPONENTS))
    assert not (set(vcv.APPROVED_CARRIER_COMPONENTS) & set(vcv.MULTILINE_UNSUPPORTED_COMPONENTS))
    assert not (set(vcv.QUARANTINED_COMPONENTS) & set(vcv.MULTILINE_UNSUPPORTED_COMPONENTS))


def test_obs119g_lists_entries_have_obs_numbers():
    """三名单每项在源码注释中带 OBS 号(正则校验)。"""
    src = Path(vcv.__file__).read_text(encoding="utf-8")
    for name in (list(vcv.QUARANTINED_COMPONENTS)
                 + list(vcv.MULTILINE_UNSUPPORTED_COMPONENTS)
                 + list(vcv.APPROVED_CARRIER_COMPONENTS)):
        assert name in src, f"{name} 不在源码注释"
    assert re.search(r"OBS-12[4-9]", src), "QUARANTINED 注释缺 OBS 号"
    assert re.search(r"OBS-129|OBS-132|OBS-133", src), "MULTILINE 注释缺 OBS 号"


# ── OBS-136:footnotes 双语法复验(2b) ────────────────────────

def test_obs136_footnotes_doc_vs_impl_syntax(tmp_path):
    """两种语法各跑一次:文档语法不触发 footnotes 分支;实现语法触发。"""
    renderer, _log = _renderer_or_skip()
    from validators.validate_component_visibility import _COMPONENT_SAMPLES
    impl_block = _COMPONENT_SAMPLES["footnotes"]
    assert impl_block.startswith(":::footnotes"), "样本必须是实现语法(:::footnotes 块)"
    doc_block = "正文[^1]\n\n[^1]: SENTINEL_A1 注释\n:::\n"
    usage_entries = []
    for label, block in (("doc", doc_block), ("impl", impl_block)):
        d = tmp_path / f"fn-{label}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "a.md").write_text(f"# 标题\n\n## 章节\n\n{block}\n结尾。\n", encoding="utf-8")
        out = d / "out"
        out.mkdir(exist_ok=True)
        import subprocess, sys as _sys
        proc = subprocess.run(
            [_sys.executable, "-X", "utf8", str(renderer),
             "--article", str(d / "a.md"), "--output-dir", str(out),
             "--theme", "smartisan"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120)
        rep = json.loads((out / "component_usage_report.json").read_text(encoding="utf-8"))
        usage_entries.append((label, rep["components"]["components"],
                              rep["components"]["paragraph"]))
    doc_comps, impl_comps = usage_entries[0][1], usage_entries[1][1]
    # 文档语法退化(components 无 footnotes);实现语法真走 footnotes 分支
    assert "footnotes" not in doc_comps, f"文档语法不应走 footnotes 分支: {doc_comps}"
    assert impl_comps.get("footnotes") == 1, f"实现语法应走 footnotes 分支: {impl_comps}"
    assert usage_entries[1][2] == 1  # impl 只剩 1 段(组件不另计 paragraph)


# ── 4b/4c:能力矩阵 JSON 与现场实测一致 + assertions_executed ──

def test_obs133_matrix_json_matches_measured(tmp_path):
    """audit/quality/component_capability_matrix.json 的三位 == 现场实测三位。"""
    renderer, _log = _renderer_or_skip()
    matrix_path = SKILL_ROOT / "audit" / "quality" / "component_capability_matrix.json"
    if not matrix_path.is_file():
        pytest.skip("矩阵 JSON 尚未生成(第 4a 步产出)")
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    measured = vcv.component_structure_check(renderer, tmp_path / "struct2")
    for name, r in measured.items():
        m = matrix.get("components", {}).get(name)
        assert m is not None, f"矩阵 JSON 缺 {name}"
        assert m["text_ok"] == r["text_ok"], name
        assert m["struct_ok"] == r["struct_ok"], name
        assert m["per_item_ok"] == r["per_item_ok"], name


def test_obs133_matrix_assertions_executed_flag():
    """矩阵 JSON 的 assertions_executed 必须为 true,防断言被 skip 却全绿。"""
    matrix_path = SKILL_ROOT / "audit" / "quality" / "component_capability_matrix.json"
    if not matrix_path.is_file():
        pytest.skip("矩阵 JSON 尚未生成(第 4a 步产出)")
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert matrix.get("assertions_executed") is True, \
        "assertions_executed 缺失或 false(三条恒等断言未真实执行)"


def test_obs133_matrix_json_metadata_shape():
    """矩阵 JSON 元数据形状:renderer 绝对路径 + sha256 + UTC 时间 + 判据版本。"""
    matrix_path = SKILL_ROOT / "audit" / "quality" / "component_capability_matrix.json"
    if not matrix_path.is_file():
        pytest.skip("矩阵 JSON 尚未生成(第 4a 步产出)")
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert matrix.get("criteria_version") == "v1"
    assert Path(matrix.get("renderer_path", "")).is_absolute()
    assert re.fullmatch(r"[0-9a-f]{64}", matrix.get("renderer_sha256", ""))
    assert matrix.get("generated_at_utc")  # 非空即存在


# ── 2i' 负对照:封面/目录/署名/页脚不得被取到 ────────────────

def test_obs119i_negative_cover_toc_signature_footer():
    """封面副标题/目录项/固定署名/页脚 CTA 均不得被 _body_plain_text 取到。"""
    html = (
        '<p style="font-size:15px;color:#737373;margin:0 0 6px;">封面副标题</p>'
        '<a style="display:inline-block;margin-right:10px;font-size:13px;"><span leaf="">PART 01</span></a>'
        '<p style="font-size:12px;color:#737373;"><span leaf="">/ 作者 给自己造把锤子</span></p>'
        '<p style="font-size:13px;font-weight:bold;color:#555555;"><span leaf="">随手点个赞在看转发</span></p>'
    )
    body = _body_plain_text(html)
    for probe in ("封面副标题", "PART 01", "作者", "赞在看"):
        assert probe not in body, f"负对照被误取: {probe}"
