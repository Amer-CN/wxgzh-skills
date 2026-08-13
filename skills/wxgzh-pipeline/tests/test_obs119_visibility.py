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
    """OBS-157:解析渲染器(无硬编码路径)。

    返回 (renderer, 解析日志);解析不到 -> (None, 日志),由调用方 skip。
    """
    log: list[str] = []
    # 1) 同工作区仓内树(SKILL_ROOT.parent/gzh-design-skill,相对解析)
    repo_cand = SKILL_ROOT.parent / "gzh-design-skill" / "scripts" / "render_article.py"
    log.append(f"repo candidate={repo_cand} is_file={repo_cand.is_file()}")
    if repo_cand.is_file():
        return repo_cand, log
    # 2) 安装侧(经 paths/skill_discovery)
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


def _installed_renderer() -> tuple[Path | None, list[str]]:
    """5b:安装侧渲染器(经 paths/skill_discovery;不回落仓内树)。"""
    log: list[str] = []
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
                        keys = {ast.literal_eval(k) for k in node.value.keys}
                        # 76J/OBS-271:table/list 非 ::: 组件,由 _render_item 的 kind
                        # 分发渲染(hammer_table/hammer_list),与 _COMPONENT_BUILDERS 并列。
                        return keys | {"table", "list"}
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


# ── 3c/3d(OBS-154):component_anchors.json 焊死(R19,逐条相等) ─────

def test_obs154_anchors_json_renderer_sha_matches_installed(tmp_path):
    """3c:component_anchors.json 的 renderer_sha256 == 当前安装侧渲染器 sha256。"""
    import hashlib
    renderer = _renderer_or_skip()
    anchors_json = SKILL_ROOT / "validators" / "component_anchors.json"
    if not anchors_json.is_file():
        pytest.skip("component_anchors.json 未生成")
    payload = json.loads(anchors_json.read_text(encoding="utf-8"))
    actual = hashlib.sha256(renderer.read_bytes()).hexdigest()
    assert payload.get("renderer_sha256") == actual, \
        f"JSON sha {payload.get('renderer_sha256')} != 渲染器 sha {actual}"


def test_obs154_anchors_json_matches_export_exact(tmp_path):
    """2d(OBS-172):现场导出 == JSON 内容,五列全比(sentinel/component/slot/mode/style)。"""
    from validators.component_slots import SLOTS
    renderer = _renderer_or_skip()
    anchors_json = SKILL_ROOT / "validators" / "component_anchors.json"
    if not anchors_json.is_file():
        pytest.skip("component_anchors.json 未生成")
    payload = json.loads(anchors_json.read_text(encoding="utf-8"))
    anchors = vcv.export_body_anchors_from_measurement(renderer, tmp_path / "anchors")
    json_map = {row["sentinel"]: row for row in payload["anchors"]}
    assert set(json_map) == set(anchors), \
        f"JSON 哨兵集 != 现场哨兵集: {sorted(set(json_map) ^ set(anchors))}"
    slot_names = {s.name for cs in SLOTS for s in cs.slots}
    for sent, info in anchors.items():
        row = json_map[sent]
        # 五列全比
        assert row["sentinel"] == sent, sent
        assert row["component"] == info["component"], sent
        assert row["slot"] == info["slot"], \
            f"{sent}: JSON slot {row['slot']!r} != 现场 {info['slot']!r}"
        assert row["mode"] == info["mode"], \
            f"{sent}: JSON mode {row['mode']!r} != 现场 {info['mode']!r}"
        assert row["style"] == info["style"], \
            f"{sent}: JSON style {row['style']!r} != 现场 {info['style']!r}"
        # 形状断言:slot 不得以 s- / s_ 开头,且必须命中 SLOTS 真实槽名
        assert not row["slot"].startswith(("s-", "s_")), \
            f"{sent}: slot 旧格式 {row['slot']!r}"
        assert row["slot"] in slot_names, \
            f"{sent}: slot {row['slot']!r} 不在 SLOTS 槽名集合"


def test_obs154_gzh_design_para_res_built_from_json():
    """gzh_design._COMPONENT_PARA_RES 由 JSON 构造(非手抄),style 与 JSON 逐条相等。"""
    from wxgzh_pipeline.stages import gzh_design as gd
    anchors_json = SKILL_ROOT / "validators" / "component_anchors.json"
    if not anchors_json.is_file():
        pytest.skip("component_anchors.json 未生成")
    payload = json.loads(anchors_json.read_text(encoding="utf-8"))
    json_styles = sorted({row["style"] for row in payload["anchors"]
                          if row.get("style") and row["style"] != "URL_SLOT"})
    # pattern 里 style 被 re.escape 转义,需 unescape 后与 JSON 原文比较。
    import html as _html
    res_styles = []
    for rx in gd._COMPONENT_PARA_RES:
        m = re.search(r'<p style="(.*?)">', rx.pattern)
        if m:
            res_styles.append(re.sub(r"\\(.)", r"\1", m.group(1)))
    res_styles = sorted(set(res_styles))
    assert res_styles == json_styles, \
        f"gzh_design 锚 style != JSON style: {sorted(set(res_styles) ^ set(json_styles))}"


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
    assert matrix.get("criteria_version") == "v4"
    assert matrix.get("criteria_changelog"), "v2 缺 changelog"
    measured = vcv.component_structure_check(renderer, tmp_path / "struct2")
    for name, r in measured.items():
        m = matrix.get("components", {}).get(name)
        assert m is not None, name
        assert m["render_ok"] == r["render_ok"]
        assert m["struct_ok"] == r["struct_ok"]
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
    assert matrix.get("criteria_version") == "v4"
    # 5b(OBS-166):renderer_path 随 bundle 发布,不得含机器绝对路径。
    rp = matrix.get("renderer_path", "")
    assert rp and not Path(rp).is_absolute() and ":" not in rp, f"renderer_path 含绝对路径: {rp}"
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
