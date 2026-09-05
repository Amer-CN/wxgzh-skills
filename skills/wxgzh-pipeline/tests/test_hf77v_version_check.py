"""77V:版本新鲜度检查三形态(current/behind/unknown)+ 编排器第 0 步。

不真实联网:ls-remote 一律 monkeypatch;编排器侧只拦截 version_check.py 的
subprocess 调用并注入三形态 JSON,其余 subprocess 调用透传真实实现
(fake_live 机制不受影响)。真实离线跑(main + mock rc=1)恒 exit 0。
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest  # noqa: F401

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from wxgzh_pipeline import paths as P  # noqa: E402
from wxgzh_pipeline.state import load_state  # noqa: E402

SKILL_ROOT = Path(__file__).resolve().parents[1]


def _load_vcheck():
    """把 scripts/version_check.py 当独立脚本加载(非包内模块)。"""
    spec = importlib.util.spec_from_file_location(
        "wxgzh_version_check_77v", SKILL_ROOT / "scripts" / "version_check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _vc_payload(status: str, latest=None, overridden: bool = False) -> dict:
    payload = {"status": status, "latest": latest,
               "current": {"baseline_date": "2026-09-02"},
               "detail": f"mock {status}"}
    if overridden:
        payload["overridden"] = True
    return payload


def _fake_run(payload: dict):
    """只拦 version_check.py,其余 subprocess 调用透传真实实现。"""
    real = subprocess.run  # setattr 前捕获原实现,避免递归

    def fake_run(cmd, *args, **kwargs):
        if any("version_check.py" in str(x) for x in (cmd or [])):
            return subprocess.CompletedProcess(
                cmd, 0, stdout=json.dumps(payload, ensure_ascii=False) + "\n",
                stderr="")
        return real(cmd, *args, **kwargs)
    return fake_run


# ---------- 形态 1:current ----------

def test_77v_version_check_current(monkeypatch):
    """mock 远端旧日期 tag → 本地基线(repo history 2026-09-02)较新 → current。"""
    vc = _load_vcheck()
    monkeypatch.setattr(vc, "_ls_remote_tags",
                        lambda remote: (["v2026.01.01-old"], None))
    out = vc.check(skills_home=SKILL_ROOT.parent)
    assert out["status"] == "current"
    assert out["latest"] == "v2026.01.01-old"
    # 77Y-F/OBS-372:baseline_date 从 history 最后一条 recorded_at 动态读取
    # (hotfix7/77O-F 单一真源同法),不再硬编码——77X relock 后日期推进即过期
    import json as _json
    from pathlib import Path as _Path
    _hp = SKILL_ROOT / "skills.lock.history.json"
    _last = _json.loads(_hp.read_text(encoding="utf-8"))[-1]
    _expected_date = str(_last.get("recorded_at") or "")[:10]
    assert out["current"]["baseline_date"] == _expected_date
    assert out["current"]["baseline_source"] == "skills.lock.history.json"
    # 同日取字典序最大、日期为主序
    assert vc._latest_vtag(
        ["v2026.09.01-a", "v2026.09.01-b", "v2026.08.30-z", "not-v-tag"])[0] \
        == "v2026.09.01-b"


# ---------- 形态 2:behind ----------

def test_77v_version_check_behind(monkeypatch):
    vc = _load_vcheck()
    monkeypatch.setattr(vc, "_ls_remote_tags",
                        lambda remote: (["v2026.12.31-new"], None))
    out = vc.check(skills_home=SKILL_ROOT.parent)
    assert out["status"] == "behind"
    assert out["latest"] == "v2026.12.31-new"
    assert "--allow-stale" in out["detail"]


def test_77v_orchestrator_behind_stops_before_run_dir(orch, monkeypatch):
    """编排器 run() behind → STALE_VERSION 停机,RUN 目录未创建。"""
    # 77X:豁免门落地后本测试显式退出套件级豁免,恢复 mock 原语义
    monkeypatch.delenv("WXGZH_SKIP_VERSION_CHECK", raising=False)
    import subprocess as sp
    monkeypatch.setattr(sp, "run", _fake_run(_vc_payload("behind", "v2026.12.31-new")))
    out = orch.run("t")
    assert out["status"] == "STALE_VERSION"
    assert out["reason"] == "remote tag newer"
    assert out["version_check"]["status"] == "behind"
    assert "v2026.12.31-new" in out["hint"]
    assert not P.run_root(orch.project_root).exists()  # RUN 创建之前停机


def test_77v_orchestrator_behind_allow_stale_continues(orch, monkeypatch):
    """--allow-stale:behind 留痕(overridden=true)继续跑完。"""
    # 77X:豁免门落地后本测试显式退出套件级豁免,恢复 mock 原语义
    monkeypatch.delenv("WXGZH_SKIP_VERSION_CHECK", raising=False)
    import subprocess as sp
    monkeypatch.setattr(sp, "run", _fake_run(_vc_payload("behind", "v2026.12.31-new")))
    out = orch.run("t", allow_stale=True)
    assert out["status"] == "COMPLETE"
    assert out["version_check"]["overridden"] is True
    st = load_state(Path(out["run_dir"]))
    assert st.version_check["overridden"] is True  # 写进 pipeline_state.json


# ---------- 形态 3:unknown ----------

def test_77v_version_check_unknown_lsremote_fail(monkeypatch, capsys):
    """mock ls-remote rc=1 → status=unknown,main 恒 exit 0(真实离线跑)。"""
    vc = _load_vcheck()

    def fake_git(*args, **kwargs):
        return subprocess.CompletedProcess(["git"], 1, stdout="",
                                           stderr="mock: offline")
    monkeypatch.setattr(vc.subprocess, "run", fake_git)
    rc = vc.main(["--skills-home", str(SKILL_ROOT.parent)])
    assert rc == 0  # 建议性工具:永远 exit 0
    out = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert out["status"] == "unknown"
    assert out["latest"] is None
    assert "rc=1" in out["detail"]


def test_77v_orchestrator_unknown_keeps_running_and_records(orch, monkeypatch):
    """unknown → 继续跑,st.version_check 留痕进 pipeline_state.json + run 结果。"""
    # 77X:豁免门落地后本测试显式退出套件级豁免,恢复 mock 原语义
    monkeypatch.delenv("WXGZH_SKIP_VERSION_CHECK", raising=False)
    import subprocess as sp
    monkeypatch.setattr(sp, "run", _fake_run(_vc_payload("unknown")))
    out = orch.run("t")
    assert out["status"] == "COMPLETE"  # unknown 不阻断
    assert out["version_check"]["status"] == "unknown"
    st = load_state(Path(out["run_dir"]))
    assert st.version_check["status"] == "unknown"
    raw = json.loads((Path(out["run_dir"]) / "pipeline_state.json")
                     .read_text(encoding="utf-8"))
    assert raw["version_check"]["status"] == "unknown"


# ---------- 向后兼容 ----------

def test_77v_state_backward_compat_without_version_check(tmp_path):
    """旧 state(无 version_check 键)反序列化不崩,字段默认 None。"""
    rd = tmp_path / "run-old"
    rd.mkdir()
    (rd / "pipeline_state.json").write_text(json.dumps(
        {"run_id": "run-old", "topic": "旧 state", "completed_stages": ["aihot"],
         "draft_created": False}, ensure_ascii=False), encoding="utf-8")
    st = load_state(rd)
    assert st.version_check is None
    assert st.to_dict()["version_check"] is None
    assert st.is_complete() is False  # 其余语义零变化
