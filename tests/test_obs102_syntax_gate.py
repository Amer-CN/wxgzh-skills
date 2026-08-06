"""档71B'-C OBS-102:未支持语法门禁回归测试(probe 判据,去绝对路径版)。

分层(OBS-112,5d):
- 机制类用例(针体自检/负对照/stub 两向):必跑,不依赖安装侧;
- 依赖安装侧渲染器的用例(真实 RUN 文章/真实渲染器反向):渲染器由
  skill_discovery 定位,定位不到或 RUN 文章不可得时 pytest.skip 并打印理由。
"""
from __future__ import annotations

import hashlib
import os
import sys
from pathlib import Path

import pytest

from conftest import SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT))
from validators.validate_syntax_gate import (
    BASELINE_SAMPLE,
    CATALOG,
    ARTICLE_SCAN,
    needle_self_check,
    probe_syntax_support,
    validate_syntax_gate,
    _SKELETON,
)
from wxgzh_pipeline.stages.gzh_design import _normalize_text, _body_plain_text

FIX = SKILL_ROOT / "tests" / "fixtures" / "obs102"
CURRENT_RUN_ARTICLE = FIX / "current_run_final_article.md"
CURRENT_RUN_SHA256 = "6A03F0CF095A3FF7476D50AFA328A2B8A833A7B2CFFCE9645F51E7A94DD38999"
STUB_RENDERER = FIX / "stub_renderer_supports_fence.py"


def _real_renderer() -> Path | None:
    """经 skill_discovery 定位安装侧渲染器;定位不到返回 None(skip)。"""
    from wxgzh_pipeline import skill_discovery as SD
    from wxgzh_pipeline import paths as P
    try:
        root = P.skills_home(P.resolve_project_root())
    except Exception:
        root = None
    if root is None:
        return None
    cand = Path(root) / "gzh-design" / "scripts" / "render_article.py"
    return cand if cand.is_file() else None


# ── 3C-d 针体可匹配性自检(机制类,必跑) ────────────────────────

def test_obs102_needle_self_check_all_true():
    sc = needle_self_check()
    assert set(sc) == {k for k, *_ in CATALOG}
    for k, ok in sc.items():
        assert ok, f"needle self-check failed for {k}"


# ── 3C-e 负对照(机制类,必跑) ──────────────────────────────────

def test_obs102_baseline_no_needle_hit(tmp_path):
    from validators.validate_syntax_gate import _renderer_sha256
    renderer = _real_renderer()
    if renderer is None:
        pytest.skip("安装侧渲染器不可得(技能未安装)")
    import subprocess
    md = tmp_path / "baseline.md"
    md.write_text(BASELINE_SAMPLE, encoding="utf-8")
    out = tmp_path / "out"; out.mkdir(exist_ok=True)
    subprocess.run([sys.executable, "-X", "utf8", str(renderer),
                    "--article", str(md), "--output-dir", str(out),
                    "--theme", "smartisan"],
                   capture_output=True, text=True, encoding="utf-8",
                   errors="replace", timeout=120)
    html = (out / "final.html").read_text(encoding="utf-8")
    # 5c(档71C-2):去掉双重归一化 —— _body_plain_text 已归一化,再套
    # _normalize_text 属二次归一化(OBS-118 同源),与实现侧修正保持一致。
    body = _body_plain_text(html)
    for key, label, token, needle, _ in CATALOG:
        assert token not in body, f"baseline token pollution: {key}"
        assert needle not in body, f"baseline needle pollution: {key}"


# ── 4c 免悖论两向(机制类,必跑) ────────────────────────────────

def test_obs102_stub_fence_supported(tmp_path):
    """正向:stub 渲染器 -> fence 判「支持」-> 门禁 PASS。"""
    sample = "# 标题\n\n## 章节\n\n:::alert type=\"warning\"\nSENTINEL_A1\n:::\nSENTINEL_A2 结尾。\n"
    p = tmp_path / "a.md"; p.write_text(sample, encoding="utf-8")
    code, rep = validate_syntax_gate(p, STUB_RENDERER, tmp_path / "probe")
    assert code == 0, rep
    assert rep["OBS102_SYNTAX_GATE"] == "PASS"
    assert rep["probe_summary"]["fence"]["unsupported"] is False


def test_obs102_real_renderer_fence_supported(tmp_path):
    """档71C-1 后:真实渲染器已接线 ::: -> fence 判「支持」-> 门禁 PASS。"""
    renderer = _real_renderer()
    if renderer is None:
        pytest.skip("安装侧渲染器不可得(技能未安装)")
    sample = "# 标题\n\n## 章节\n\n:::alert type=\"warning\"\nSENTINEL_A1\n:::\nSENTINEL_A2 结尾。\n"
    p = tmp_path / "b.md"; p.write_text(sample, encoding="utf-8")
    code, rep = validate_syntax_gate(p, renderer, tmp_path / "probe")
    assert code == 0, rep
    assert rep["OBS102_SYNTAX_GATE"] == "PASS"
    assert rep["probe_summary"]["fence"]["unsupported"] is False


def test_obs102_real_renderer_h3_still_fails(tmp_path):
    """反向(保留):真实渲染器 + 含 ### 样本 -> 仍 FAIL,problems[0] 含行号与片段。"""
    renderer = _real_renderer()
    if renderer is None:
        pytest.skip("安装侧渲染器不可得(技能未安装)")
    sample = "# 标题\n\n## 章节\n\n### SENTINEL_A1\nSENTINEL_A2 结尾。\n"
    p = tmp_path / "c.md"; p.write_text(sample, encoding="utf-8")
    code, rep = validate_syntax_gate(p, renderer, tmp_path / "probe")
    assert code == 1
    assert rep["OBS102_SYNTAX_GATE"] == "FAIL"
    assert rep["hits"], rep
    assert rep["hits"][0]["category"] == "### 及更深标题"
    assert rep["hits"][0]["line"] == 5


# ── 现 RUN 冻结文章(依赖安装侧,可 skip) ────────────────────────

def test_obs102_current_run_article_passes(tmp_path):
    """现 RUN 冻结文章 -> PASS(code_fence 4 命中且受支持,其余 0)。"""
    renderer = _real_renderer()
    if renderer is None:
        pytest.skip("安装侧渲染器不可得(技能未安装)")
    env_article = os.environ.get("WXGZH_OBS102_RUN_ARTICLE")
    if env_article and Path(env_article).is_file():
        article = Path(env_article)
    elif CURRENT_RUN_ARTICLE.is_file():
        article = CURRENT_RUN_ARTICLE
    else:
        pytest.skip("现 RUN 冻结文章不可得(未设置 WXGZH_OBS102_RUN_ARTICLE 且 fixture 缺失)")
    # 断言冻结 fixture 的 sha256(防止 fixture 被静默替换)
    sha = hashlib.sha256(article.read_bytes()).hexdigest()
    assert sha.upper() == CURRENT_RUN_SHA256.upper(), f"fixture sha mismatch: {sha}"
    code, rep = validate_syntax_gate(article, renderer, tmp_path / "probe")
    assert code == 0, rep
    assert rep["hits"] == []


def test_obs102_current_run_scan_hits(tmp_path):
    """3C-h:逐类命中数 —— code_fence 4 次,其余 12 类 0 次。"""
    if not CURRENT_RUN_ARTICLE.is_file():
        pytest.skip("现 RUN 冻结 fixture 缺失")
    md = CURRENT_RUN_ARTICLE.read_text(encoding="utf-8")
    lines = md.splitlines()
    for key, label, token, needle, _ in CATALOG:
        rx = ARTICLE_SCAN[key]
        n = sum(1 for ln in lines if rx.search(ln))
        if key == "code_fence":
            assert n == 4, f"code_fence expected 4, got {n}"
        else:
            assert n == 0, f"{key} expected 0, got {n}"


def test_obs118_no_double_normalization():
    """OBS-118:构造含 &amp;lt; 的 HTML,单次归一化与二次归一化结果不同。"""
    html = ('<p style="margin-bottom:16px;font-size:14px;line-height:1.9;'
            'text-align:justify;">a &amp;lt; b</p>')
    once = _body_plain_text(html)          # 单次归一化
    twice = _normalize_text(once)          # 二次归一化(旧 _probe_single 行为)
    assert once != twice, "单次与二次归一化应不同(证明双归一化分叉真实存在)"


# ── 1e(OBS-145):组件 type 枚举校验 正负样本 ─────────────────────

def test_obs145_type_enum_invalid_fails(tmp_path):
    """未定义 alert type -> 语法门禁 FAIL 且给行号。"""
    from validators.validate_syntax_gate import validate_syntax_gate
    renderer = _real_renderer()
    if renderer is None:
        pytest.skip("安装侧渲染器不可得(技能未安装)")
    sample = '# 标题\n\n## 章节\n\n:::alert type="bogus"\n内容\n:::\n'
    p = tmp_path / "c.md"; p.write_text(sample, encoding="utf-8")
    code, rep = validate_syntax_gate(p, renderer, tmp_path / "probe")
    assert code == 1, rep
    cats = [h["category"] for h in rep.get("hits", [])]
    assert any("type" in c for c in cats), cats


def test_obs145_type_enum_valid_passes(tmp_path):
    """合法 alert type -> 语法门禁不因 type 拦截(其余探针不受影响)。"""
    from validators.validate_syntax_gate import validate_syntax_gate
    renderer = _real_renderer()
    if renderer is None:
        pytest.skip("安装侧渲染器不可得(技能未安装)")
    sample = '# 标题\n\n## 章节\n\n:::alert type="warning"\n内容\n:::\n'
    p = tmp_path / "d.md"; p.write_text(sample, encoding="utf-8")
    code, rep = validate_syntax_gate(p, renderer, tmp_path / "probe")
    # 该样本无其它不支持语法;type 合法 -> 不因 type 拦(门禁整体由探针决定)
    assert code == 0, rep
