"""档71G OBS-180:WXGZH_WECHAT_API_ALLOWED 授权键 gate(R58 三态 + 非 live 不受影响)。

取值口径:strip().lower() in ("1","true","yes");读取优先级:env 优先,.env setdefault。
① 未设 + live → doctor FAIL_CLOSED(默认拒绝)
② 设为 1 + live → 放行
③ 设为 0 且 .env 为 1 + live → 拒绝(证明覆盖优先级)
+ 非 live 模式不受影响;+ producers._wechat / _media_two_phase 两落点。
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from wxgzh_pipeline.orchestrator import Orchestrator

REAL_SKILLS = Path(r"F:\AIXM\wxgzh\.agents\skills")


@pytest.fixture(autouse=True)
def _hermetic_wechat_api_key(monkeypatch):
    """R62(档71G-F):读环境键的测试必须 hermetic——显式删除开发机 shell
    可能存在的键,再依赖各测试显式注入。"""
    monkeypatch.delenv("WXGZH_WECHAT_API_ALLOWED", raising=False)


def _orch(tmp_path, mode, env_extra: dict) -> Orchestrator:
    env = {"WECHAT_APP_ID": "wx123456", "WECHAT_APP_SECRET": "abcdef123456"}
    env.update(env_extra)
    return Orchestrator(project_root=tmp_path, network_mode=mode,
                        skills_home=str(REAL_SKILLS), env=env)


# ── 2e① 未设 + live → doctor FAIL_CLOSED ───────────────────

def test_obs180_unset_live_fails_closed(tmp_path):
    o = _orch(tmp_path, "live", {})
    ok, rep = o.doctor()
    assert ok is False
    assert rep["wechat_api_allowed"] is False
    assert "在 .env 中加入 WXGZH_WECHAT_API_ALLOWED=1" in rep["wechat_api_blocked"]
    assert rep["FAIL_CLOSED"] is True


# ── 2e② 设为 1 + live → 放行 ───────────────────────────────

def test_obs180_set_one_live_allowed(tmp_path):
    o = _orch(tmp_path, "live", {"WXGZH_WECHAT_API_ALLOWED": "1"})
    ok, rep = o.doctor()
    assert rep["wechat_api_allowed"] is True
    assert ok is True, rep


# ── 2e③ 设为 0 且 .env 为 1 + live → 拒绝(env 优先)────────

def test_obs180_zero_overrides_dotenv_one(tmp_path):
    (tmp_path / ".env").write_text("WXGZH_WECHAT_API_ALLOWED=1\n", encoding="utf-8")
    o = _orch(tmp_path, "live", {"WXGZH_WECHAT_API_ALLOWED": "0"})
    ok, rep = o.doctor()
    assert rep["wechat_api_allowed"] is False
    assert ok is False
    assert "在 .env 中加入 WXGZH_WECHAT_API_ALLOWED=1" in rep["wechat_api_blocked"]


# ── 非 live 模式不受影响 ───────────────────────────────────

@pytest.mark.parametrize("mode", ["integration", "fake_live", "offline_fixture"])
def test_obs180_non_live_unaffected(tmp_path, mode):
    o = _orch(tmp_path, mode, {})  # 无键
    ok, rep = o.doctor()
    assert rep.get("wechat_api_allowed") is None
    assert ok is True, rep


# ── producers._wechat 落点:live+未允许 → exit_code=2 FAIL_CLOSED ──

def test_obs180_wechat_stage_gate_live_unset(tmp_path):
    from wxgzh_pipeline.producers import _wechat
    run_dir = tmp_path / "r" / "d"
    run_dir.mkdir(parents=True)
    ctx = SimpleNamespace(network_mode="live", create_wechat_draft=True,
                          skills_home=str(REAL_SKILLS), run_dir=str(run_dir), env={})
    out, meta = _wechat(ctx, "wechat_draft", run_dir, [],
                        SimpleNamespace(topic="t"))
    assert out == []
    assert meta["entry_run"]["exit_code"] == 2
    assert "FAIL_CLOSED" in meta["entry_run"]["stderr"]
    assert "在 .env 中加入 WXGZH_WECHAT_API_ALLOWED=1" in meta["entry_run"]["stderr"]


def test_obs180_wechat_stage_gate_zero_overrides_dotenv(tmp_path):
    """OBS-194(档71H,4a):run_dir 改为 tmp_path/a/b/c,使 parents[2]==tmp_path,
    .env 真正被 gate 读到(此前 tmp_path/r/d 的 parents[2]==tmp_path.parent,
    .env 永远读不到,测试假绿)。断言零改动。"""
    from wxgzh_pipeline.producers import _wechat
    run_dir = tmp_path / "a" / "b" / "c"
    run_dir.mkdir(parents=True)
    (tmp_path / ".env").write_text("WXGZH_WECHAT_API_ALLOWED=1\n", encoding="utf-8")
    ctx = SimpleNamespace(network_mode="live", create_wechat_draft=True,
                          skills_home=str(REAL_SKILLS), run_dir=str(run_dir),
                          env={"WXGZH_WECHAT_API_ALLOWED": "0"})
    out, meta = _wechat(ctx, "wechat_draft", run_dir, [],
                        SimpleNamespace(topic="t"))
    assert meta["entry_run"]["exit_code"] == 2
    # 4b(档71H,R83/R84):断言加严到能区分 gate 与 cover 失败——gate 放行后
    # cover 失败同样返回 exit 2,仅靠 exit_code 无法判定守卫;此处断言 stderr
    # 必须含授权键文案(gate 专有)。4a 原「断言一字不改」与 4b「必须变红」实测
    # 不相容,按 R84 例外(本测试即 OBS-194 修复标的)加严,偏差已如实上报。
    assert "WXGZH_WECHAT_API_ALLOWED" in meta["entry_run"]["stderr"]


def test_obs180_wechat_stage_non_live_not_blocked(tmp_path):
    from wxgzh_pipeline.producers import _wechat
    run_dir = tmp_path / "r" / "d"
    run_dir.mkdir(parents=True)
    ctx = SimpleNamespace(network_mode="integration", create_wechat_draft=False,
                          skills_home=str(REAL_SKILLS), run_dir=str(run_dir), env={})
    out, meta = _wechat(ctx, "wechat_draft", run_dir, [],
                        SimpleNamespace(topic="t"))
    assert meta.get("skipped") == "create_wechat_draft=False"


# ── producers._media_two_phase 落点:live continue 前 gate ──

def test_obs180_media_continue_gate_live_unset(tmp_path):
    from wxgzh_pipeline.producers import MediaRequestError, _media_two_phase
    run_dir = tmp_path / "r" / "d"
    sd = run_dir / "media_enrichment"
    (sd / "discover").mkdir(parents=True)
    (sd / "discover" / "asset_discovery_manifest.json").write_text(
        json.dumps({"assets": []}), encoding="utf-8")
    (sd / "approval_precheck.json").write_text(json.dumps({}), encoding="utf-8")
    (sd / "approval_readiness.json").write_text(json.dumps({}), encoding="utf-8")
    (sd / "copyright_approval.json").write_text(json.dumps({"approvals": []}),
                                                encoding="utf-8")
    # 让 discover_paused 判定走通:paused 要求 registry 与 discovery request 的
    # registry sha 一致(否则会重跑 discover 分支,到不了 continue gate)。
    import hashlib
    reg = run_dir / "super_writer"
    reg.mkdir(parents=True)
    reg_p = reg / "canonical_claim_registry.json"
    reg_p.write_text(json.dumps({"claims": [], "materials": []}), encoding="utf-8")
    reg_sha = hashlib.sha256(reg_p.read_bytes()).hexdigest()
    (sd / "media_discovery_request.json").write_text(
        json.dumps({"provenance": {"canonical_registry_sha256": reg_sha}}),
        encoding="utf-8")
    ctx = SimpleNamespace(run_dir=str(run_dir), network_mode="live",
                          skills_home=str(REAL_SKILLS), env={}, discovery={})
    entry = REAL_SKILLS / "media-enrichment" / "scripts" / "run_media_enrichment.py"
    out, meta = _media_two_phase(ctx, sd, [], SimpleNamespace(run_id="x"),
                                 entry, None)
    # gate 抛出的 MediaRequestError 被阶段外层 except 收进 fail-closed meta(exit 2)。
    assert out == []
    assert meta["entry_run"]["exit_code"] == 2
    assert "WXGZH_WECHAT_API_ALLOWED" in meta["media_request_failed"]
    assert "在 .env 中加入 WXGZH_WECHAT_API_ALLOWED=1" in meta["media_request_failed"]


# ── 2e 对照负例(R49):手写 fake ctx 与 test_obs72 同型 ────────

class _NoEnvCtx:
    """与 test_obs72._Ctx 同型但【不带 env 属性】的手写 fake ctx。"""

    def __init__(self, run_dir, skills_home, env_marker="absent"):
        self.run_dir = run_dir
        self.skills_home = skills_home
        self.network_mode = "live"
        self.create_wechat_draft = True
        if env_marker != "absent":
            self.env = env_marker


def test_obs180_wechat_no_env_attr_fails_closed_no_attributeerror(tmp_path):
    """① ctx 不带 env 属性 + live → 不得抛 AttributeError;必须 FAIL_CLOSED(exit_code=2),
    meta 不得复用 skipped 语义。"""
    from wxgzh_pipeline.producers import _wechat
    run_dir = tmp_path / "r" / "d"
    run_dir.mkdir(parents=True)
    ctx = _NoEnvCtx(str(run_dir), str(REAL_SKILLS), env_marker="absent")
    out, meta = _wechat(ctx, "wechat_draft", run_dir, [], SimpleNamespace(topic="t"))
    assert out == []
    assert meta["entry_run"]["exit_code"] == 2
    assert "FAIL_CLOSED" in meta["entry_run"]["stderr"]
    assert meta.get("skipped") is None


def test_obs180_wechat_env_empty_fails_closed(tmp_path):
    """② ctx.env = {} + live → FAIL_CLOSED。"""
    from wxgzh_pipeline.producers import _wechat
    run_dir = tmp_path / "r" / "d"
    run_dir.mkdir(parents=True)
    ctx = _NoEnvCtx(str(run_dir), str(REAL_SKILLS), env_marker={})
    out, meta = _wechat(ctx, "wechat_draft", run_dir, [], SimpleNamespace(topic="t"))
    assert out == []
    assert meta["entry_run"]["exit_code"] == 2
    assert "FAIL_CLOSED" in meta["entry_run"]["stderr"]


def test_obs180_wechat_env_allowed_not_blocked_by_gate(tmp_path):
    """③ ctx.env = {"WXGZH_WECHAT_API_ALLOWED":"1"} + live → 不被 gate 拦。
    (后续可因其他原因失败,但失败原因不得是 gate。)"""
    from wxgzh_pipeline.producers import _wechat
    run_dir = tmp_path / "r" / "d"
    run_dir.mkdir(parents=True)
    ctx = _NoEnvCtx(str(run_dir), str(REAL_SKILLS),
                    env_marker={"WXGZH_WECHAT_API_ALLOWED": "1"})
    out, meta = _wechat(ctx, "wechat_draft", run_dir, [], SimpleNamespace(topic="t"))
    # 未被 gate 拦:不会出现 gate 的 FAIL_CLOSED 文案与 exit 2 形态
    assert "WXGZH_WECHAT_API_ALLOWED" not in str(meta)
    assert meta.get("skipped") is None


# ── 3b:media continue 授权 → 放行(gate 之后才因其他原因失败)──

def test_obs180_media_continue_gate_live_allowed_passes_gate(tmp_path):
    from wxgzh_pipeline.producers import _media_two_phase
    run_dir = tmp_path / "r" / "d"
    sd = run_dir / "media_enrichment"
    (sd / "discover").mkdir(parents=True)
    (sd / "discover" / "asset_discovery_manifest.json").write_text(
        json.dumps({"assets": []}), encoding="utf-8")
    (sd / "approval_precheck.json").write_text(json.dumps({}), encoding="utf-8")
    (sd / "approval_readiness.json").write_text(json.dumps({}), encoding="utf-8")
    (sd / "copyright_approval.json").write_text(json.dumps({"approvals": []}),
                                                encoding="utf-8")
    import hashlib
    reg = run_dir / "super_writer"
    reg.mkdir(parents=True)
    reg_p = reg / "canonical_claim_registry.json"
    reg_p.write_text(json.dumps({"claims": [], "materials": []}), encoding="utf-8")
    reg_sha = hashlib.sha256(reg_p.read_bytes()).hexdigest()
    (sd / "media_discovery_request.json").write_text(
        json.dumps({"provenance": {"canonical_registry_sha256": reg_sha}}),
        encoding="utf-8")
    ctx = SimpleNamespace(run_dir=str(run_dir), network_mode="live",
                          skills_home=str(REAL_SKILLS),
                          env={"WXGZH_WECHAT_API_ALLOWED": "1"}, discovery={})
    entry = REAL_SKILLS / "media-enrichment" / "scripts" / "run_media_enrichment.py"
    out, meta = _media_two_phase(ctx, sd, [], SimpleNamespace(run_id="x"),
                                 entry, None)
    # 已过 gate:失败原因必须是 gate 之后的「frozen discovery manifest sha256 invalid」,
    # 不得是 WXGZH_WECHAT_API_ALLOWED。
    assert "WXGZH_WECHAT_API_ALLOWED" not in meta.get("media_request_failed", "")
    assert "frozen discovery manifest sha256 invalid" in meta.get("media_request_failed", "")


# ── OBS-197(档71H,5c/R82):WXGZH_ALLOW_WARNINGS 只读 ctx.env,不读 .env ──

def test_obs180_allow_warnings_ignores_dotenv(tmp_path, monkeypatch):
    """.env 写 WXGZH_ALLOW_WARNINGS=1 + ctx.env 为空 + live → 最终 argv 不含
    --allow-warnings(放行开关不得被持久化文件静默开启)。"""
    from wxgzh_pipeline import producers as PR
    run_dir = tmp_path / "a" / "b" / "c"
    run_dir.mkdir(parents=True)
    (tmp_path / ".env").write_text(
        "WXGZH_WECHAT_API_ALLOWED=1\nWXGZH_ALLOW_WARNINGS=1\n", encoding="utf-8")
    captured: dict = {}

    def _fake_run(script, argv, timeout=None, env=None, **kw):
        captured["argv"] = list(argv)
        return {"exit_code": 0, "stdout": "", "stderr": "",
                "script_path": str(script), "script_sha256": "0" * 64,
                "stdout_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "stderr_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "command": [str(script)] + list(argv), "elapsed_seconds": 0.0}

    monkeypatch.setattr(PR, "run_script", _fake_run)
    monkeypatch.setattr(PR, "_select_live_cover", lambda ctx: ("cover.png", "A-1"))
    sd = run_dir
    (sd / "gzh_design").mkdir(parents=True)
    (sd / "gzh_design" / "final.html").write_text("<html></html>", encoding="utf-8")
    ctx = SimpleNamespace(network_mode="live", create_wechat_draft=True,
                          skills_home=str(REAL_SKILLS), run_dir=str(run_dir),
                          env={})  # ctx.env 空;.env 有 WXGZH_ALLOW_WARNINGS=1
    out, meta = PR._wechat(ctx, "wechat_draft", sd, [],
                           SimpleNamespace(topic="t"))
    assert captured.get("argv") is not None, meta
    assert "--allow-warnings" not in captured["argv"], captured["argv"]
