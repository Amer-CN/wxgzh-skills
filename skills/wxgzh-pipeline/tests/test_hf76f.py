"""76F 效率批测试。

- OBS-274(receipt 墙钟):stage receipt 含 validation_seconds + wall_seconds 两套,
  wall_mark 跨调用持久化(握手/返工等待计入);orchestrator 顶层 run_wall_seconds;
- OBS-276(ACK/request 幂等):request_id 稳定、重写不换 id、重 ACK 幂等、
  ACK 绑定 request_id、指令含恢复 SOP;
- OBS-279(编码):读 JSON 容忍 BOM、写 JSON 无 BOM。
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from wxgzh_pipeline import agent_handshake as AH
from wxgzh_pipeline import producers as PR
from wxgzh_pipeline.stages import StageContext, execute_stage
from wxgzh_pipeline.state import PipelineState, atomic_write_json, read_json

from conftest import SKILL_ROOT


# ── OBS-274 墙钟 ───────────────────────────────────────────────

def _run_success_stage(tmp_path, monkeypatch, run_id="hf76f-wall"):
    import wxgzh_pipeline.stages as stages
    monkeypatch.setitem(stages.STAGE_SKILL, "hf76f_test", "gzh-design")
    monkeypatch.setattr(stages, "schema_validate", lambda obj, schema: [])
    monkeypatch.setattr(stages, "enforce_contract",
                        lambda *args, **kwargs: (True, {"CONTRACT": "PASS"}))
    captured = {}
    monkeypatch.setattr(stages, "write_receipt",
                        lambda run_dir, stage, receipt: captured.update(receipt))
    module = SimpleNamespace(
        STAGE="hf76f_test", STAGE_CONFIG={},
        stage_inputs=lambda ctx, state: {},
        run_live=lambda ctx, state: ([], {
            "entrypoint_path": "entry.py",
            "entry_run": {"command": ["python", "entry.py"], "exit_code": 0,
                          "stdout": "ok", "stderr": "", "elapsed_seconds": 0.1},
        }),
        content_validate=lambda ctx, sd, state: (0, {}, None, None),
        side_effects=lambda ctx, state: [],
        invoked_entrypoint=lambda ctx: "entry.py",
        post=lambda ctx, sd, state, exit_code, report: None,
    )
    ctx = StageContext(run_dir=tmp_path, skills_home=tmp_path, discovery={},
                       network_mode="live")
    state = SimpleNamespace(run_id=run_id, started_at=datetime.now(
        timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    execute_stage(ctx, module, state)
    return captured


def test_receipt_wall_and_validation_seconds(tmp_path, monkeypatch):
    receipt = _run_success_stage(tmp_path, monkeypatch)
    assert "validation_seconds" in receipt, receipt.keys()
    assert "wall_seconds" in receipt, receipt.keys()
    # 首次执行:validation == elapsed;wall >= validation(同一进程内)
    assert receipt["validation_seconds"] == receipt["elapsed_seconds"]
    assert receipt["wall_seconds"] >= receipt["validation_seconds"] >= 0


def test_wall_mark_persists_across_attempts(tmp_path, monkeypatch):
    """握手等待后 resume:wall_seconds 从首次尝试起算(含等待),validation 只算本次。"""
    import wxgzh_pipeline.stages as stages
    sd = tmp_path / "hf76f_test"
    sd.mkdir(parents=True, exist_ok=True)
    past = (datetime.now(timezone.utc) - timedelta(seconds=300)
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
    # 模拟首次尝试已落 wall_mark(300 秒前)
    (sd / ".wall_started_at").write_text(past, encoding="utf-8", newline="\n")
    receipt = _run_success_stage(tmp_path, monkeypatch)
    assert receipt["wall_seconds"] >= 300, receipt["wall_seconds"]
    assert receipt["validation_seconds"] < 300


def test_run_wall_seconds_helper():
    st = PipelineState(run_id="x", topic="t",
                       started_at=(datetime.now(timezone.utc)
                                   - timedelta(seconds=120))
                       .strftime("%Y-%m-%dT%H:%M:%SZ"))
    from wxgzh_pipeline.orchestrator import Orchestrator
    w = Orchestrator._wall_seconds(st)
    assert w >= 120


# ── OBS-276 ACK/request 幂等 ───────────────────────────────────

def _mk_request_dir(tmp_path):
    sd = tmp_path / "super_writer"
    sd.mkdir(parents=True, exist_ok=True)
    (sd / "article.md").write_text("# 标题\n\n正文。\n", encoding="utf-8")
    (sd / "stage_request.json").write_text(json.dumps({"x": 1}), encoding="utf-8")
    return sd


def test_request_id_stable_across_rewrites(tmp_path):
    sd = _mk_request_dir(tmp_path)
    outputs = ["article.md"]
    AH.write_request(sd, "super_writer", "super-writer", "instr", outputs,
                     {"topic": "t"}, run_id="r1",
                     stage_request_sha256="a" * 64)
    req1 = read_json(sd / AH.REQUEST_FILE)
    # 同阶段同意图重写(模拟 resume 重跑)
    AH.write_request(sd, "super_writer", "super-writer", "instr", outputs,
                     {"topic": "t"}, run_id="r1",
                     stage_request_sha256="a" * 64)
    req2 = read_json(sd / AH.REQUEST_FILE)
    assert req1["request_id"] == req2["request_id"] == "r1:super_writer"


def test_ack_idempotent_and_binds_request_id(tmp_path):
    sd = _mk_request_dir(tmp_path)
    outputs = ["article.md"]
    AH.write_request(sd, "super_writer", "super-writer", "instr", outputs,
                     {"topic": "t"}, run_id="r1",
                     stage_request_sha256="a" * 64)
    ack1 = AH.write_ack(sd, "super_writer", outputs, agent_id="agent")
    ack2 = AH.write_ack(sd, "super_writer", outputs, agent_id="agent")  # 重 ACK 幂等
    assert ack1["request_id"] == "r1:super_writer"
    assert ack1 == ack2
    ok, rep = AH.verify_ack(sd, "super_writer", outputs)
    assert ok and rep["request_id_ok"] is True


def test_stale_ack_rejected_with_sop_reason(tmp_path):
    sd = _mk_request_dir(tmp_path)
    outputs = ["article.md"]
    AH.write_request(sd, "super_writer", "super-writer", "instr", outputs,
                     {"topic": "t"}, run_id="r1",
                     stage_request_sha256="a" * 64)
    AH.write_ack(sd, "super_writer", outputs)
    ack_p = sd / AH.ACK_FILE
    ack = read_json(ack_p)
    ack["request_id"] = "stale:super_writer"  # 模拟绑定旧 request 的 ACK
    atomic_write_json(ack_p, ack)
    ok, rep = AH.verify_ack(sd, "super_writer", outputs)
    assert not ok
    assert rep["request_id_ok"] is False
    assert "re-ACK against the latest request" in rep.get("reason", "")


# ── OBS-279 BOM / 编码 ─────────────────────────────────────────

def test_read_json_tolerates_bom(tmp_path):
    p = tmp_path / "with_bom.json"
    p.write_bytes(b"\xef\xbb\xbf" + json.dumps({"k": "v"}, ensure_ascii=False).encode("utf-8"))
    assert read_json(p) == {"k": "v"}
    p2 = tmp_path / "no_bom.json"
    atomic_write_json(p2, {"k": "v"})
    raw = p2.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), "写 JSON 必须无 BOM"


def test_instructions_contain_recovery_sop():
    for key in ("aihot", "super_writer", "zh_human_writing"):
        instr = PR.AGENT_INSTRUCTIONS[key]
        # 77C 压缩后 sw 措辞有别(合并 276+279),aihot/zh 未动
        ack_anchor = ("按最新 agent_handshake_request.json 重新 ACK" if key == "super_writer"
                     else "以当前最新 agent_handshake_request.json 为准重新 ACK")
        del_anchor = "禁删文件重来" if key == "super_writer" else "禁止删除文件重来"
        assert ack_anchor in instr, key
        assert "POSIX 正斜杠" in instr, key
        assert del_anchor in instr, key


def test_sw_instruction_contains_tool_guidance():
    instr = PR.AGENT_INSTRUCTIONS["super_writer"]
    assert "align_outline_budget.py" in instr
    assert "validate_single_product.py" in instr
