"""77Z 规格 B:upstream_drift 官方刷新通道——请求信封复用判定含 upstream 时效。

零删文件重签:_agent 内 request_frozen=False 分支的既有覆盖写即官方刷新通道;
verify_ack 的 upstream_drift 在重签后自然消失(新信封绑新 hash)。
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest  # noqa: F401

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import wxgzh_pipeline.agent_handshake as AH  # noqa: E402
import wxgzh_pipeline.producers as PR  # noqa: E402

SKILL_ROOT = Path(__file__).resolve().parents[1]
SW_REFERENCES = SKILL_ROOT.parent / "super-writer" / "references"
# execmodel.UPSTREAM_INPUTS["super_writer"] 的真实上游(相对 run_dir)
UPSTREAM_REL = "aihot/deduplicated_items.json"


def _sha(text: str) -> str:
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _make_ctx(tmp_path: Path) -> SimpleNamespace:
    return SimpleNamespace(run_dir=tmp_path, network_mode="live",
                           skills_home=tmp_path, env={}, fake_agent=None)


def _make_state(run_id: str = "run-77z") -> SimpleNamespace:
    return SimpleNamespace(run_id=run_id, topic="77Z 主题",
                           final_article_sha256=None, items_file=None)


def _agent_call(ctx, sd, expected, state, monkeypatch):
    """最小 _agent 直调:upstream/identity/contract/validators 全 mock,零子进程。"""
    monkeypatch.setattr(PR, "_skill_identity",
                        lambda ctx, stage: {"skill_name": "super-writer"})
    monkeypatch.setattr(PR, "_contract_sha", lambda stage: "contract")
    monkeypatch.setattr(PR, "_agent_validator_args", lambda stage, ctx, sd: [])
    return PR._agent(ctx, "super_writer", sd, expected, expected, state)


# ---------- ① 上游合法修正后不复用 → 新 request upstream_hashes=新值(重签实证) ----------

def test_77z_upstream_change_forces_resign(tmp_path, monkeypatch):
    """上游文件内容合法修正 → _reusable_agent_request 返回 False(不复用)
    → _agent 覆盖写新 request,新信封 upstream_hashes=当前盘上新值。"""
    sd = tmp_path / "super_writer"
    sd.mkdir()
    (sd / "stage_request.json").write_text("{}", encoding="utf-8")
    upstream_file = tmp_path / UPSTREAM_REL
    upstream_file.parent.mkdir(parents=True)
    upstream_file.write_text("上游原文", encoding="utf-8")

    ctx = _make_ctx(tmp_path)
    state = _make_state()
    expected = ["out.txt"]

    outputs, meta = _agent_call(ctx, sd, expected, state, monkeypatch)
    assert meta["handshake"]["HANDSHAKE"] == "AWAITING_AGENT"
    first_req = json.loads((sd / AH.REQUEST_FILE).read_text(encoding="utf-8"))
    first_sha = _sha("上游原文")
    assert first_req["upstream_hashes"][UPSTREAM_REL] == first_sha

    # 上游合法修正(新内容,不删任何文件)
    upstream_file.write_text("上游修正后的新内容", encoding="utf-8")
    assert PR._reusable_agent_request(
        sd, state.run_id, "super_writer", expected,
        PR._upstream_hashes(ctx, "super_writer")) is False

    outputs, meta = _agent_call(ctx, sd, expected, state, monkeypatch)
    second_req = json.loads((sd / AH.REQUEST_FILE).read_text(encoding="utf-8"))
    new_sha = _sha("上游修正后的新内容")
    assert second_req["upstream_hashes"][UPSTREAM_REL] == new_sha  # 重签实证
    assert second_req["upstream_hashes"] != first_req["upstream_hashes"]


# ---------- ② 上游未变 → 复用 True(77I 语义不回退) ----------

def test_77z_upstream_unchanged_reuses_frozen_request(tmp_path, monkeypatch):
    """上游未变 → 复用 True;_agent 第二次调用不重写 request(字节不变)。"""
    sd = tmp_path / "super_writer"
    sd.mkdir()
    (sd / "stage_request.json").write_text("{}", encoding="utf-8")
    upstream_file = tmp_path / UPSTREAM_REL
    upstream_file.parent.mkdir(parents=True)
    upstream_file.write_text("上游原文", encoding="utf-8")

    ctx = _make_ctx(tmp_path)
    state = _make_state()
    expected = ["out.txt"]

    _agent_call(ctx, sd, expected, state, monkeypatch)
    before_bytes = (sd / AH.REQUEST_FILE).read_bytes()

    upstream = PR._upstream_hashes(ctx, "super_writer")
    assert PR._reusable_agent_request(
        sd, state.run_id, "super_writer", expected, upstream) is True

    (sd / "out.txt").write_text("output", encoding="utf-8")
    AH.write_ack(sd, "super_writer", expected)
    outputs, meta = _agent_call(ctx, sd, expected, state, monkeypatch)
    assert meta["handshake"]["HANDSHAKE"] == "PASS"
    assert (sd / AH.REQUEST_FILE).read_bytes() == before_bytes  # 未重签


# ---------- ③ 重签后 verify_ack PASS(upstream_drift 空)且零删文件 ----------

def test_77z_resign_then_verify_ack_pass_zero_deletion(tmp_path, monkeypatch):
    """上游修正→ACK 阶段漂移 FAIL→_agent 重签→重新 ACK 后 verify_ack PASS:
    upstream_drift 空且零删文件(请求/产物文件全部仍在盘)。"""
    sd = tmp_path / "super_writer"
    sd.mkdir()
    (sd / "stage_request.json").write_text("{}", encoding="utf-8")
    upstream_file = tmp_path / UPSTREAM_REL
    upstream_file.parent.mkdir(parents=True)
    upstream_file.write_text("上游原文", encoding="utf-8")

    ctx = _make_ctx(tmp_path)
    state = _make_state()
    expected = ["out.txt"]

    _agent_call(ctx, sd, expected, state, monkeypatch)
    (sd / "out.txt").write_text("output", encoding="utf-8")
    AH.write_ack(sd, "super_writer", expected)

    # 上游合法修正 → 旧 ACK 的信封绑旧 hash → upstream_drift FAIL
    upstream_file.write_text("上游修正后的新内容", encoding="utf-8")
    ok, hs = AH.verify_ack(sd, "super_writer", expected, run_dir=tmp_path)
    assert ok is False
    assert hs["upstream_drift"] == [UPSTREAM_REL]

    # 编排器官方重签(_agent 覆盖写新 request)+ 重新 ACK → PASS
    _agent_call(ctx, sd, expected, state, monkeypatch)
    AH.write_ack(sd, "super_writer", expected)
    ok, hs = AH.verify_ack(sd, "super_writer", expected, run_dir=tmp_path)
    assert ok is True, hs
    assert hs["upstream_drift"] == []
    # 零删文件:请求信封/ACK/产物/上游文件全部仍在盘
    for p in (sd / AH.REQUEST_FILE, sd / AH.ACK_FILE, sd / "out.txt",
              upstream_file, sd / "stage_request.json"):
        assert p.is_file(), f"{p} 不应被删除"


# ---------- 指令明路落 _COMMON_RULES ----------

def test_77z_instruction_states_official_resign_channel():
    """77Z/OBS-375 指令明路:_COMMON_RULES 含明路,拼接其上的 aihot/zh 阶段指令
    均携带(super_writer 指令为独立串,明路由 _COMMON_RULES 单一真源承载,
    76F 恢复 SOP 语义由其既有 276 段保留)。"""
    assert "77Z/OBS-375" in PR._COMMON_RULES
    assert "请求信封重签系官方动作不在禁列" in PR._COMMON_RULES
    assert "agent 无需也无权手动重签" in PR._COMMON_RULES
    for stage in ("aihot", "zh_human_writing"):
        assert "77Z/OBS-375" in PR.AGENT_INSTRUCTIONS[stage], stage
    # sw 指令面保留 76F 恢复 SOP;77Z 标题硬措辞(OBS-376)由规格 C 落 sw 标题段。
    assert "76F/OBS-276" in PR.AGENT_INSTRUCTIONS["super_writer"]
