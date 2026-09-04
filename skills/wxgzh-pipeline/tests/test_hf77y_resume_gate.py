"""77Y/OBS-369:无参续发多候选停机门(MULTIPLE_CANDIDATE_RUNS)。

76V/OBS-295 把无参续发改成「取最新未完成 RUN 自动续跑」,实测误续他会话 RUN
(77Y 用户裁决)——多候选停机列全候选,单候选保持自动续,零候选 NO_RESUMABLE_RUN。

hermetic:真 Orchestrator + 真 list_incomplete(读 tmp project_root 的 state 文件),
resume 经 monkeypatch 拦截(多候选断言不被调用;单候选断言以 run_id=None 调用)。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest  # noqa: F401

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wxgzh_pipeline import paths as P  # noqa: E402
from wxgzh_pipeline.cli import main as cli_main  # noqa: E402
from wxgzh_pipeline.orchestrator import Orchestrator  # noqa: E402
from wxgzh_pipeline.state import PipelineState, save_state  # noqa: E402

RUN_A = "20260901T000000-topic-a"
RUN_B = "20260902T000000-topic-b"
TOPIC_A = "选题甲"
TOPIC_B = "选题乙"


def _mk_incomplete_run(project_root: Path, name: str, topic: str) -> None:
    run_dir = P.run_root(project_root) / name
    run_dir.mkdir(parents=True, exist_ok=True)
    save_state(run_dir, PipelineState(run_id=name, topic=topic,
                                      profile="fast_publish"))


def _parse_json_stdout(out_text: str) -> dict:
    """CLI 可能先打印 [76V] 行再打 JSON——取首个 { 起的 JSON 体。"""
    return json.loads(out_text[out_text.index("{"):])


def test_77y_resume_multiple_candidates_stops(tmp_path, monkeypatch, capsys):
    """两个未完成 RUN → MULTIPLE_CANDIDATE_RUNS 停机(return 1),列全 RUN_ID+topic。"""
    _mk_incomplete_run(tmp_path, RUN_A, TOPIC_A)
    _mk_incomplete_run(tmp_path, RUN_B, TOPIC_B)

    def _must_not_resume(self, run_id=None, stop_after=None):
        raise AssertionError("多候选时禁止自动续跑(77Y/OBS-369)")

    monkeypatch.setattr(Orchestrator, "resume", _must_not_resume)
    rc = cli_main(["续发", "--project-root", str(tmp_path)])
    out = _parse_json_stdout(capsys.readouterr().out)
    assert rc == 1
    assert out["status"] == "MULTIPLE_CANDIDATE_RUNS"
    assert {c["run_id"] for c in out["candidates"]} == {RUN_A, RUN_B}
    assert {c["topic"] for c in out["candidates"]} == {TOPIC_A, TOPIC_B}
    assert "77Y/OBS-369" in out["hint"]
    assert "显式 RUN_ID" in out["hint"]


def test_77y_resume_single_candidate_auto_resumes(tmp_path, monkeypatch, capsys):
    """单候选 → 保持自动续(76V 语义),以 run_id=None 调用 resume。"""
    _mk_incomplete_run(tmp_path, RUN_A, TOPIC_A)
    captured = {}

    def fake_resume(self, run_id=None, stop_after=None):
        captured["run_id"] = run_id
        return {"status": "COMPLETE", "run_id": RUN_A}

    monkeypatch.setattr(Orchestrator, "resume", fake_resume)
    rc = cli_main(["续发", "--project-root", str(tmp_path)])
    out = _parse_json_stdout(capsys.readouterr().out)
    assert rc == 0
    assert captured["run_id"] is None
    assert out["resumed_run_id"] == RUN_A
