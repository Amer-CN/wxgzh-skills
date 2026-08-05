"""档71B OBS-102:未支持语法门禁回归测试(probe 判据)。"""
from __future__ import annotations

import sys
from pathlib import Path

from conftest import SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT))
from validators.validate_syntax_gate import validate_syntax_gate

# 安装侧渲染器(与 skills.lock 锁定版本一致;测试在安装侧存在时运行)
_INSTALLED_RENDERER = Path(
    r"F:\AIXM\wxgzh\.agents\skills\gzh-design\scripts\render_article.py")

RUN_ARTICLE = Path(
    r"F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260804T174355-vibe-coding-guide-v2-1-6-by4s00"
    r"\zh_human_writing\final_article.md")


def _renderer():
    assert _INSTALLED_RENDERER.is_file(), f"renderer missing: {_INSTALLED_RENDERER}"
    return _INSTALLED_RENDERER


def _run_gate(article: Path, tmp_path):
    return validate_syntax_gate(
        article, _renderer(), tmp_path / "probe", tmp_path / "cache.json")


def test_obs102_current_run_article_passes(tmp_path):
    """① 本 RUN 冻结文章 -> PASS(十类全 0 命中)。"""
    assert RUN_ARTICLE.is_file(), "RUN article missing"
    code, rep = _run_gate(RUN_ARTICLE, tmp_path)
    assert code == 0, rep
    assert rep["OBS102_SYNTAX_GATE"] == "PASS"
    assert rep["hits"] == []


def test_obs102_alert_fence_fails_with_line(tmp_path):
    """② 含 :::alert 的 fixture -> FAIL_CLOSED,报出正确行号。"""
    md = "# 标题\n\n## 章节\n\n:::alert type=\"warning\"\nSENTINEL_A1\n:::\n"
    p = tmp_path / "alert.md"
    p.write_text(md, encoding="utf-8")
    code, rep = _run_gate(p, tmp_path)
    assert code == 1
    assert rep["OBS102_SYNTAX_GATE"] == "FAIL"
    hits = [h for h in rep["hits"] if h["category"] == "::: 围栏"]
    assert hits, rep
    assert hits[0]["line"] == 5  # :::alert 所在行


def test_obs102_h3_fails(tmp_path):
    """③ 含 ### 三级标题 -> FAIL_CLOSED。"""
    md = "# 标题\n\n## 章节\n\n### 三级\n"
    p = tmp_path / "h3.md"
    p.write_text(md, encoding="utf-8")
    code, rep = _run_gate(p, tmp_path)
    assert code == 1
    hits = [h for h in rep["hits"] if h["category"] == "### 及更深标题"]
    assert hits, rep
    assert hits[0]["line"] == 5


def test_obs102_quote_and_list_fail(tmp_path):
    """④ 含 > 引用 + - 列表 -> FAIL_CLOSED。"""
    md = "# 标题\n\n## 章节\n\n> 引用\n\n- 项一\n"
    p = tmp_path / "ql.md"
    p.write_text(md, encoding="utf-8")
    code, rep = _run_gate(p, tmp_path)
    assert code == 1
    cats = {h["category"] for h in rep["hits"]}
    assert "行首 > 引用" in cats
    assert "行首 - 无序列表" in cats


def test_obs102_body_region_reuses_gzh_design(tmp_path):
    """⑤ probe 正文区口径来自 gzh_design._body_plain_text(同源,不复制)。"""
    from wxgzh_pipeline.stages.gzh_design import _body_plain_text as gzh_body
    from validators.validate_syntax_gate import _probe_single
    import inspect
    src = inspect.getsource(_probe_single)
    assert "from wxgzh_pipeline.stages.gzh_design import _body_plain_text" in src
    assert callable(gzh_body)
