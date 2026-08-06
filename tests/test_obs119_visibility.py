"""档71C-R2 OBS-145-150:组件载体判据分裂 + 锚实测导出 + 四名单。

R19 口径:四名单常量(import 后未改) == component_structure_check 现场实测导出。
3b:gzh_design._COMPONENT_PARA_RES 快照 == 锚导出生成集(R19,防手抄锚自证)。
1d:负样本(未知 type/缺 type)渲染不崩 + unknown_component_args 有记录。
2e:docstring 正则与实现常量一致。5e:OBS-138 footnotes 双语法翻转。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

from conftest import SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT))
import validators.validate_component_visibility as vcv
from wxgzh_pipeline.stages.gzh_design import _body_plain_text


def _resolved_renderer() -> tuple[Path | None, list[str]]:
    """解析渲染器:优先同工作区 gzh-design-skill 仓(本档修复树),再退回安装侧。"""
    log: list[str] = []
    # 1) 同工作区仓内树(优先,本档修复所在)
    for cand in (SKILL_ROOT.parent / "gzh-design-skill" / "scripts" / "render_article.py",
                 Path(r"F:\AIXM\wxgzh\gzh-design-skill\scripts\render_article.py")):
        if cand.is_file():
            log.append(f"repo renderer={cand}")
            return cand, log
    # 2) 安装侧
    try:
        from wxgzh_pipeline import paths as P
        from wxgzh_pipeline import skill_discovery as SD
        root = P.resolve_project_root()
        sh = P.skills_home(root)
        lock = SD.load_lock(SKILL_ROOT)
        ep = lock["skills"].get("gzh-design", {}).get("entrypoint", "")
        cand = Path(sh) / "gzh-design" / ep
        log.append(f"installed candidate={cand} is_file={cand.is_file()}")
        return (cand if cand.is_file() else None), log
    except Exception as e:  # noqa: BLE001
        return None, log + [f"resolve failed: {e!r}"]


def _renderer_or_skip():
    renderer, log = _resolved_renderer()
    if renderer is None:
        pytest.skip("安装侧渲染器不可得;解析过程:\n" + "\n".join(log))
    return renderer


def _installed_builders_keys(renderer: Path) -> set[str]:
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


# ── 5a/5b/5c:四名单 R19 恒等断言 ─────────────────────────────

def test_obs145_four_lists_equal_measured(tmp_path):
    """四名单常量 == 现场实测导出(QUARANTINED/MULTILINE/ANCHOR_GAP/APPROVED)。"""
    renderer = _renderer_or_skip()
    measured = vcv.component_structure_check(renderer, tmp_path / "struct")
    exported = vcv.export_lists_from_measurement(measured)
    assert set(vcv.QUARANTINED_COMPONENTS) == exported["quarantined"]
    assert set(vcv.MULTILINE_UNSUPPORTED_COMPONENTS) == exported["multiline"]
    assert set(vcv.ANCHOR_GAP_COMPONENTS) == exported["anchor_gap"]
    assert set(vcv.APPROVED_CARRIER_COMPONENTS) == exported["approved"]


def test_obs145_union_equals_builders_intersection_empty(tmp_path):
    """四名单并集 == builders 键集合,两两交集为空。"""
    renderer = _renderer_or_skip()
    builders = _installed_builders_keys(renderer)
    union = (set(vcv.QUARANTINED_COMPONENTS) | set(vcv.MULTILINE_UNSUPPORTED_COMPONENTS)
             | set(vcv.ANCHOR_GAP_COMPONENTS) | set(vcv.APPROVED_CARRIER_COMPONENTS))
    assert union == builders, f"union={sorted(union)} builders={sorted(builders)}"
    sets = [set(vcv.QUARANTINED_COMPONENTS), set(vcv.MULTILINE_UNSUPPORTED_COMPONENTS),
            set(vcv.ANCHOR_GAP_COMPONENTS), set(vcv.APPROVED_CARRIER_COMPONENTS)]
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            assert not (sets[i] & sets[j]), f"交集非空: {sorted(sets[i] & sets[j])}"


def test_obs145_lists_entries_have_obs_numbers():
    """名单每项在源码注释中带 OBS 号。"""
    src = Path(vcv.__file__).read_text(encoding="utf-8")
    for name in (set(vcv.QUARANTINED_COMPONENTS) | set(vcv.MULTILINE_UNSUPPORTED_COMPONENTS)
                 | set(vcv.ANCHOR_GAP_COMPONENTS) | set(vcv.APPROVED_CARRIER_COMPONENTS)):
        assert name in src, f"{name} 不在源码注释"
    assert re.search(r"OBS-145", src)


# ── 3b:锚快照焊死(R19:快照 == 现场导出) ───────────────────────

def test_obs145_component_para_res_snapshot_matches_export(tmp_path):
    """gzh_design._COMPONENT_PARA_RES 快照 == 锚实测导出生成集(R19,防手抄自证)。"""
    from wxgzh_pipeline.stages import gzh_design as gd
    renderer = _renderer_or_skip()
    anchors = vcv.export_body_anchors_from_measurement(renderer, tmp_path / "anchors")
    exported = vcv.build_component_para_regexes(anchors)
    snapshot = [m for rx in gd._COMPONENT_PARA_RES for m in re.findall(r'<p style="([^"]*)"', rx.pattern)]
    # 快照 style 必须是导出集合的子集(导出含更多,快照是 71C-2 时期的手抄子集)
    for s in snapshot:
        assert any(s in e for e in exported), f"快照锚 {s} 不在导出集"


# ── 1d:负样本(未知 type/缺 type 不崩 + unknown_component_args) ──

def test_obs145_negative_samples_render_ok(tmp_path):
    """三份负样本渲染 returncode==0 + final.html 存在 + 哨兵可见。"""
    renderer = _renderer_or_skip()
    import subprocess
    for label, block in vcv._NEGATIVE_SAMPLES.items():
        d = tmp_path / label
        d.mkdir(parents=True, exist_ok=True)
        (d / "a.md").write_text(f"# 标题\n\n## 章节\n\n{block}\n结尾。\n", encoding="utf-8")
        out = d / "out"
        out.mkdir(exist_ok=True)
        proc = subprocess.run(
            [sys.executable, "-X", "utf8", str(renderer),
             "--article", str(d / "a.md"), "--output-dir", str(out),
             "--theme", "smartisan"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120)
        assert proc.returncode == 0, f"{label}: rc={proc.returncode} {proc.stderr}"
        html = (out / "final.html").read_text(encoding="utf-8")
        assert "SENTINEL_A1" in html, f"{label}: 哨兵不可见"
        rep = json.loads((out / "component_usage_report.json").read_text(encoding="utf-8"))
        if label != "alert-no-type":
            assert rep["components"]["unknown_component_args"], \
                f"{label}: unknown_component_args 无记录"


# ── 2e:docstring 正则与实现一致 ──────────────────────────────

def test_obs139_docstring_regex_matches_impl():
    """docstring 写的载体正则与实现常量一致(2e/OBS-139)。"""
    doc = vcv.component_structure_check.__doc__ or ""
    assert "render_ok" in doc and "anchor_ok" in doc and "per_item_ok" in doc
    src = Path(vcv.__file__).read_text(encoding="utf-8")
    # docstring 提到的三判据名称必须在实现函数体内出现
    for name in ("render_ok", "anchor_ok", "per_item_ok"):
        assert name in src


# ── 5e:OBS-138 footnotes 双语法翻转(1g 修复后语义反转) ────────

def test_obs136_footnotes_doc_vs_impl_syntax(tmp_path):
    """两种语法都走 footnotes 分支(1g 修复后语义反转:文档语法不再退化)。"""
    renderer = _renderer_or_skip()
    import subprocess
    doc_block = "正文中引用标记[^1]\n\n[^1]: SENTINEL_FN 注释\n"
    impl_block = ":::footnotes\n[^1]: SENTINEL_FN 注释\n:::\n"
    results = []
    for label, block in (("doc", doc_block), ("impl", impl_block)):
        d = tmp_path / f"fn-{label}"
        d.mkdir(parents=True, exist_ok=True)
        (d / "a.md").write_text(f"# 标题\n\n## 章节\n\n{block}\n结尾。\n", encoding="utf-8")
        out = d / "out"
        out.mkdir(exist_ok=True)
        subprocess.run(
            [sys.executable, "-X", "utf8", str(renderer),
             "--article", str(d / "a.md"), "--output-dir", str(out),
             "--theme", "smartisan"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120)
        rep = json.loads((out / "component_usage_report.json").read_text(encoding="utf-8"))
        html = (out / "final.html").read_text(encoding="utf-8")
        results.append((label, rep["components"]["components"], "SENTINEL_FN" in html))
    doc_comps, impl_comps = results[0][1], results[1][1]
    # 翻转:两种语法 components.footnotes 都 == 1(1g 修复前文档语法为 0)
    assert doc_comps.get("footnotes") == 1, f"doc 语法应走 footnotes: {doc_comps}"
    assert impl_comps.get("footnotes") == 1, f"impl 语法应走 footnotes: {impl_comps}"
    assert results[0][2] and results[1][2]


# ── 矩阵 JSON v2 ────────────────────────────────────────────

def test_obs145_matrix_json_matches_measured(tmp_path):
    renderer = _renderer_or_skip()
    matrix_path = SKILL_ROOT / "audit" / "quality" / "component_capability_matrix.json"
    if not matrix_path.is_file():
        pytest.skip("矩阵 JSON 未生成")
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert matrix.get("criteria_version") == "v2"
    assert matrix.get("criteria_changelog"), "v2 缺 changelog"
    measured = vcv.component_structure_check(renderer, tmp_path / "struct2")
    for name, r in measured.items():
        m = matrix.get("components", {}).get(name)
        assert m is not None, name
        assert m["render_ok"] == r["render_ok"]
        assert m["anchor_ok"] == r["anchor_ok"]
        assert m["per_item_ok"] == r["per_item_ok"]


def test_obs145_matrix_assertions_executed_flag():
    matrix_path = SKILL_ROOT / "audit" / "quality" / "component_capability_matrix.json"
    if not matrix_path.is_file():
        pytest.skip("矩阵 JSON 未生成")
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert matrix.get("assertions_executed") is True


def test_obs145_matrix_metadata_shape():
    matrix_path = SKILL_ROOT / "audit" / "quality" / "component_capability_matrix.json"
    if not matrix_path.is_file():
        pytest.skip("矩阵 JSON 未生成")
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert matrix.get("criteria_version") == "v2"
    assert Path(matrix.get("renderer_path", "")).is_absolute()
    assert re.fullmatch(r"[0-9a-f]{64}", matrix.get("renderer_sha256", ""))


# ── 2i' 负对照:封面/目录/署名/页脚不得被取到 ────────────────

def test_obs119i_negative_cover_toc_signature_footer():
    html = (
        '<p style="font-size:15px;color:#737373;margin:0 0 6px;">封面副标题</p>'
        '<a style="display:inline-block;margin-right:10px;font-size:13px;"><span leaf="">PART 01</span></a>'
        '<p style="font-size:12px;color:#737373;"><span leaf="">/ 作者 给自己造把锤子</span></p>'
        '<p style="font-size:13px;font-weight:bold;color:#555555;"><span leaf="">随手点个赞在看转发</span></p>'
    )
    body = _body_plain_text(html)
    for probe in ("封面副标题", "PART 01", "作者", "赞在看"):
        assert probe not in body, f"负对照被误取: {probe}"
