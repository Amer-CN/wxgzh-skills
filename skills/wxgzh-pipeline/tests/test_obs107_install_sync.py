"""档71B OBS-107:安装同步计数比对排除报告类文件回归测试。"""
from __future__ import annotations

import sys
from pathlib import Path

from conftest import SKILL_ROOT

sys.path.insert(0, str(SKILL_ROOT))
from wxgzh_pipeline.observability import (
    _is_report_doc,
    check_pipeline_consistency,
    _runtime_files,
)


def _tree(tmp_path: Path, files: list[str]) -> Path:
    root = tmp_path / "tree"
    for rel in files:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x", encoding="utf-8")
    return root


def test_obs107_report_doc_excluded_from_count():
    """① 新增一份 audit/quality/x.md -> 计数比对仍 MATCH。"""
    assert _is_report_doc("audit/quality/x.md") is True
    assert _is_report_doc("audit/runs/2026/x.md") is False  # runs 严禁排除
    assert _is_report_doc("validators/x.py") is False


def test_obs107_install_sync_match_with_report(tmp_path):
    repo = _tree(tmp_path, [
        "wxgzh_pipeline/a.py", "validators/b.py",
        "audit/quality/report-1.md", "audit/runs/R1/x.json",
    ])
    installed = _tree(tmp_path / "inst", [
        "wxgzh_pipeline/a.py", "validators/b.py",
        "audit/runs/R1/x.json",
    ])
    rep = check_pipeline_consistency(installed, repo)
    # audit/quality/*.md 排除后 -> MATCH
    assert rep["status"] == "MATCH", rep
    assert rep["missing_files"] == []


def test_obs107_runtime_asset_diff_detected(tmp_path):
    """② 新增运行资产(validators/x.py)-> 计数比对 DIFF。"""
    repo = _tree(tmp_path, [
        "wxgzh_pipeline/a.py", "validators/b.py",
    ])
    installed = _tree(tmp_path / "inst", [
        "wxgzh_pipeline/a.py",
    ])
    rep = check_pipeline_consistency(installed, repo)
    assert rep["status"] == "DIFF"
    assert "validators/b.py" in rep["missing_files"]


def test_obs107_quality_dir_only_excluded(tmp_path):
    """排除范围仅限 audit/quality/**/*.md;audit 其他内容仍比对。"""
    repo = _tree(tmp_path, [
        "audit/quality/ok.md", "audit/side-effects/ledger.md",
    ])
    installed = _tree(tmp_path / "inst", [
        "audit/quality/ok.md",
    ])
    rep = check_pipeline_consistency(installed, repo)
    # quality/ok.md 被排除(不产生 missing);side-effects/ledger.md 属 audit 但非
    # quality -> 仍参与比对,repo 有而 installed 无 -> DIFF
    assert rep["status"] == "DIFF"
    assert "audit/side-effects/ledger.md" in rep["missing_files"]
