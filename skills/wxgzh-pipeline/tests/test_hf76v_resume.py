"""76V/OBS-295:无参续发默认取最新未完成 RUN。

- 多积压:取 started_at/名称最新的未完成 RUN,不再报 MULTIPLE_INCOMPLETE;
- 单个:直取;
- 零个:返回 None(NO_RESUMABLE_RUN)。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wxgzh_pipeline.orchestrator import Orchestrator  # noqa: E402
from wxgzh_pipeline import paths as P  # noqa: E402


def _mk_run(project_root: Path, name: str, completed: list[str], draft=False):
    rd = P.run_root(project_root) / name
    rd.mkdir(parents=True, exist_ok=True)
    st = {
        "run_id": name, "topic": f"topic-{name}",
        "completed_stages": completed,
        "draft_created": draft,
        "current_stage": None,
        "failed_stage": None,
        "output_hashes": {},
    }
    (rd / "pipeline_state.json").write_text(
        json.dumps(st, ensure_ascii=False), encoding="utf-8")
    return rd


def test_multiple_incomplete_picks_newest(tmp_path):
    """多积压:无参续发取最新未完成 RUN。"""
    orch = Orchestrator(project_root=tmp_path, network_mode="offline_fixture")
    _mk_run(tmp_path, "20260813T010000-old-run", ["aihot"])
    _mk_run(tmp_path, "20260814T020000-new-run", ["aihot", "super_writer"])
    _mk_run(tmp_path, "20260814T030000-complete", ["aihot", "super_writer",
                                                   "zh_human_writing", "media_enrichment",
                                                   "gzh_design", "wechat_draft"], draft=True)
    # 完成的不算;最新未完成 = 20260814T020000-new-run
    inc = orch.list_incomplete()
    assert sorted(inc) == ["20260813T010000-old-run", "20260814T020000-new-run"]
    picked = orch._find_resume_run(None)
    assert picked is not None and picked.name == "20260814T020000-new-run"


def test_single_incomplete_picks_it(tmp_path):
    """单个未完成:直取。"""
    orch = Orchestrator(project_root=tmp_path, network_mode="offline_fixture")
    _mk_run(tmp_path, "20260814T020000-only-run", ["aihot"])
    picked = orch._find_resume_run(None)
    assert picked is not None and picked.name == "20260814T020000-only-run"


def test_zero_incomplete_returns_none(tmp_path):
    """零个未完成:返回 None(不再有 MULTIPLE_INCOMPLETE)。"""
    orch = Orchestrator(project_root=tmp_path, network_mode="offline_fixture")
    _mk_run(tmp_path, "20260814T030000-complete", ["aihot"], draft=True)
    picked = orch._find_resume_run(None)
    assert picked is None
    assert orch.list_incomplete() == []
