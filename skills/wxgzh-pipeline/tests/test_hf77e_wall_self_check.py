"""77E/OBS-312:墙钟口径自证行测试。

分段 receipt wall 合计 vs run_wall 并列;差值超限标 WARNING(重叠累计语义),
run_wall 基线=(now - started_at)不因续发重置。
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from wxgzh_pipeline.orchestrator import Orchestrator


def test_wall_self_check_parallel_total_with_warning(tmp_path):
    rd = tmp_path / "run"
    walls = {"aihot": 1000.0, "super_writer": 800.0}
    for stage, w in walls.items():
        sd = rd / stage
        sd.mkdir(parents=True)
        (sd / "stage_receipt.json").write_text(
            json.dumps({"stage": stage, "wall_seconds": w}), encoding="utf-8")
    st = SimpleNamespace(started_at=(
        datetime.now(timezone.utc).replace(microsecond=0).replace(tzinfo=None)
    ).strftime("%Y-%m-%dT%H:%M:%SZ"))
    out = Orchestrator.wall_self_check(rd, st)
    assert out["stage_wall_total_seconds"] == 1800.0
    assert out["stages"] == [("aihot", 1000.0), ("super_writer", 800.0)]
    assert isinstance(out["run_wall_seconds"], float)
    assert out["delta_seconds"] == round(1800.0 - out["run_wall_seconds"], 3)
    # run_wall 很小(刚刚开始)→ 分段合计远超 → WARNING
    assert out["warning"] is not None
    assert "重叠" in out["warning"] and "run_wall 为准" in out["warning"]


def test_wall_self_check_small_delta_no_warning(tmp_path):
    rd = tmp_path / "run"
    st = SimpleNamespace(started_at=(
        datetime.now(timezone.utc).replace(microsecond=0).replace(tzinfo=None)
    ).strftime("%Y-%m-%dT%H:%M:%SZ"))
    (rd / "aihot").mkdir(parents=True)
    (rd / "aihot" / "stage_receipt.json").write_text(
        json.dumps({"stage": "aihot", "wall_seconds": 0.0}), encoding="utf-8")
    out = Orchestrator.wall_self_check(rd, st)
    assert out["stage_wall_total_seconds"] == 0.0
    assert out["warning"] is None
