"""77X 杂项收口六件(内容修复)测试:
①WXGZH_SKIP_VERSION_CHECK=1 豁免门零子进程;②env 未设 behind 分支照旧;
③doctor 失败分支 FAIL_CLOSED 不 NameError(OBS-361);④producers basis
透传到 media_request(OBS-363)。
"""
from __future__ import annotations

import hashlib
import json
import subprocess as sp
from pathlib import Path

import pytest  # noqa: F401

from conftest import SKILL_ROOT, SKILLS_HOME

from wxgzh_pipeline import paths as P  # noqa: E402
from wxgzh_pipeline.state import PipelineState  # noqa: E402

import wxgzh_pipeline.producers as PR  # noqa: E402

MEDIA_ROOT = SKILLS_HOME / "media-enrichment"


# ---------- 规格 A:WXGZH_SKIP_VERSION_CHECK 豁免门 ----------

def test_77x_version_check_skip_gate_zero_subprocess(orch, monkeypatch):
    """env=1 时 _version_check_step 返回 (None, skipped) 且零 subprocess 调用。"""
    monkeypatch.setenv("WXGZH_SKIP_VERSION_CHECK", "1")
    calls = []

    def boobytrap(cmd, *args, **kwargs):
        calls.append(cmd)
        raise AssertionError("subprocess must not be called under skip gate")

    monkeypatch.setattr(sp, "run", boobytrap)
    stale, trace = orch._version_check_step()
    assert calls == []
    assert stale is None
    assert trace == {"status": "skipped",
                     "detail": "WXGZH_SKIP_VERSION_CHECK=1 (77X/OBS-360)"}


def test_77x_version_check_env_unset_behind_flow_unchanged(orch, monkeypatch):
    """env 未设时 behind 分支照旧:mock version_check.py 子进程注入 behind JSON。"""
    monkeypatch.delenv("WXGZH_SKIP_VERSION_CHECK", raising=False)
    payload = {"status": "behind", "latest": "v2026.12.31-77x",
               "current": {"baseline_date": "2026-09-02"},
               "detail": "mock behind"}
    real_run = sp.run  # setattr 前捕获原实现,非 version_check.py 调用透传

    def fake_run(cmd, *args, **kwargs):
        if any("version_check.py" in str(x) for x in (cmd or [])):
            return sp.CompletedProcess(cmd, 0,
                                       stdout=json.dumps(payload, ensure_ascii=False) + "\n",
                                       stderr="")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(sp, "run", fake_run)
    stale, trace = orch._version_check_step(allow_stale=False)
    assert trace is None
    assert stale["status"] == "STALE_VERSION"
    assert stale["reason"] == "remote tag newer"
    assert stale["version_check"]["status"] == "behind"
    assert "v2026.12.31-77x" in stale["hint"]


# ---------- 规格 B:doctor 失败分支 st 缺陷(OBS-361) ----------

def test_77x_doctor_fail_closed_no_name_error(orch, monkeypatch):
    """doctor 失败路径 run() 返回 FAIL_CLOSED,不抛 NameError(修复前引用未定义 st)。"""
    monkeypatch.setattr(orch, "doctor",
                        lambda: (False, {"ok": False, "detail": "mock 77X"}))
    out = orch.run("t")
    assert out["status"] == "FAIL_CLOSED"
    assert out["reason"] == "doctor failed"
    assert out["doctor"]["detail"] == "mock 77X"
    assert "run_wall_seconds" not in out  # 77X 修复口径:doctor 失败时无 state 可计时
    assert not P.run_root(orch.project_root).exists()  # RUN 目录未创建


# ---------- 规格 D:producers basis 透传(OBS-363) ----------

def _mk_run(tmp_path: Path) -> Path:
    """最小 RUN 形状(76E 同构):dedup + canonical registry + ledger + 冻结文章。"""
    rd = tmp_path
    dedup = [
        {"id": "aihot-1", "title": "素材A", "source_url": "https://x.com/a",
         "links": {"aihot": "https://aihot.example/items/aihot-1",
                   "original": "https://x.com/a"}},
        {"id": "aihot-2", "title": "M-25 Maestro", "source_url": "https://x.com/b",
         "links": {"aihot": "https://aihot.example/items/aihot-2",
                   "original": "https://x.com/b"}},
    ]
    (rd / "aihot").mkdir()
    (rd / "aihot" / "deduplicated_items.json").write_text(
        json.dumps(dedup, ensure_ascii=False), encoding="utf-8")
    reg = {
        "materials": [{"material_id": "M-R1", "dedup_id": "aihot-1",
                       "source_url": "https://x.com/a", "title": "素材A"}],
        "claims": [{"claim_id": "C-1", "claim_text": "素材A 的声明",
                    "material_id": "M-R1", "source_url": "https://x.com/a",
                    "source_excerpt": "素材A"}]}
    (rd / "super_writer").mkdir()
    (rd / "super_writer" / "canonical_claim_registry.json").write_text(
        json.dumps(reg, ensure_ascii=False), encoding="utf-8")
    (rd / "zh_human_writing").mkdir()
    (rd / "zh_human_writing" / "final_article.md").write_text(
        "# 标题\n\n导语。\n## 第一章\n\n正文。\n", encoding="utf-8")
    return rd


def _single_asset_approval(asset_id: str, approved_by: str,
                           basis: str | None) -> dict:
    rec = {
        "asset_id": asset_id,
        "material_id": "M-R1",
        "source_page_url": "https://x.com/a/asset",
        "resolved_original_url": "https://x.com/a/asset/original",
        "asset_sha256": "b" * 64,
        "asset_identity_sha256": hashlib.sha256("\n".join((
            "M-R1", "https://x.com/a/asset",
            "https://x.com/a/asset/original", "b" * 64,
        )).encode("utf-8")).hexdigest(),
        "discovery_manifest_sha256": "c" * 64,
        "approval_id": f"APR-77X-{asset_id}",
        "approved_scope": "single_asset",
        "approved_by": approved_by,
        "approved_at": "2026-09-03T00:00:00Z",
        "approval_evidence_sha256": "d" * 64,
    }
    if basis is not None:
        rec["basis"] = basis
    return rec


def _build_continue_request(tmp_path: Path, approvals: list[dict]) -> dict:
    rd = _mk_run(tmp_path)
    sd = rd / "media_enrichment"
    sd.mkdir()
    (sd / "copyright_approval.json").write_text(
        json.dumps({"approvals": approvals}, ensure_ascii=False), encoding="utf-8")

    class _Ctx:
        run_dir = str(rd)
        skills_home = str(SKILLS_HOME)
        env = {"WXGZH_FIXED_MEDIA_ROOT": str(MEDIA_ROOT)}
        network_mode = "offline_fixture"

    req_path = PR._build_media_request(_Ctx(), sd, PipelineState(run_id="r77x", topic="t"),
                                       phase="continue")
    return json.loads(req_path.read_text(encoding="utf-8"))


def test_77x_auto_rule_basis_retained_in_media_request(tmp_path):
    """auto_rule+basis 的 single_asset approval:basis 保留进 media_request。"""
    req = _build_continue_request(tmp_path, [
        _single_asset_approval("A-77X-1", "auto_rule", "76R/OBS-289")])
    approvals = req["asset_approvals"]
    assert len(approvals) == 1
    assert approvals[0]["approved_by"] == "auto_rule"
    assert approvals[0]["basis"] == "76R/OBS-289"
    assert approvals[0]["asset_id"] == "A-77X-1"


def test_77x_user_lane_without_basis_carries_no_key(tmp_path):
    """user 车道无 basis:不携带 basis 键、不报错。"""
    req = _build_continue_request(tmp_path, [
        _single_asset_approval("A-77X-2", "user", None)])
    approvals = req["asset_approvals"]
    assert len(approvals) == 1
    assert approvals[0]["approved_by"] == "user"
    assert "basis" not in approvals[0]
