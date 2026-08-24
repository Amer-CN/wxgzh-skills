"""档HF-1/OBS-243:media discover 可恢复降级 → 批准点暂停。

只测 _media_two_phase 的 discover 分支降级路由;既有测试零改动。
判定契约:
  _discover_degraded_recoverable(discover_dir) 全部满足才可恢复——
  manifest 存在可解析 / run_id 正常且 claims_total>0 /
  errors 非空且全为 "Failed to fetch page for " 前缀 /
  eligible+review_required > 0。
可恢复 → meta 追加 discover_degraded/discover_exit_code/discover_errors,
继续既有 paused 路径(precheck/readiness/await_media_approval=True)。
不可恢复 → 维持原样 STAGE_FAILED。
"""

import json
from types import SimpleNamespace

from wxgzh_pipeline import producers as PR

FETCH = "Failed to fetch page for "


def _build_run(tmp_path):
    run_dir = tmp_path / "a" / "b" / "c"
    sd = run_dir / "media_enrichment"
    (sd / "discover").mkdir(parents=True)
    # _build_media_request 依赖:registry(claims+materials)+ dedup 索引
    reg = run_dir / "super_writer"
    reg.mkdir(parents=True)
    (reg / "canonical_claim_registry.json").write_text(json.dumps({
        "claims": [{"claim_id": "c-1", "material_id": "mat-1",
                    "claim_text": "测试 claim"}],
        "materials": [{"material_id": "mat-1", "source_url": "https://example.com/x",
                       "title": "示例材料"}],
    }), encoding="utf-8")
    zh = run_dir / "zh_human_writing"
    zh.mkdir(parents=True)
    (zh / "final_article.md").write_text("# 测试文章\n", encoding="utf-8")
    aihot = run_dir / "aihot"
    aihot.mkdir(parents=True)
    (aihot / "deduplicated_items.json").write_text(json.dumps({
        "items": [{"id": "mat-1", "title": "示例材料",
                   "source_url": "https://example.com/x"}],
    }), encoding="utf-8")
    return run_dir, sd


def _fake_run_factory(sd, exit_code, manifest, frozen, events):
    """fake run_script:写 discover 产物后返回指定退出码(与真实 discover 同效)。"""
    def _fake_run(script_path, args, timeout, env):
        (sd / "discover" / "media_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        (sd / "discover" / "asset_discovery_manifest.json").write_text(
            json.dumps(frozen), encoding="utf-8")
        (sd / "discover" / "upload_events.json").write_text(
            json.dumps({"schema_version": "1.0", "serial": True, "events": events}),
            encoding="utf-8")
        return {
            "script_path": str(script_path), "script_sha256": "1" * 64,
            "command": ["python", str(script_path), *map(str, args)],
            "exit_code": exit_code, "elapsed_seconds": 0.1,
            "stdout_sha256": "2" * 64, "stderr_sha256": "3" * 64,
            "stdout": "", "stderr": "",
        }
    return _fake_run


def _base_manifest(run_id="20260808T220417-x", claims_total=20, errors=None,
                   eligible=0, review_required=2):
    return {
        "run_id": run_id,
        "input": {"claims_total": claims_total},
        "summary": {"eligible_assets": eligible,
                    "review_required_assets": review_required,
                    "candidates_discovered": 0, "downloads_succeeded": 0,
                    "uploaded_assets": 0},
        "errors": errors or [],
        "assets": [],
    }


def _run_discover(tmp_path, monkeypatch, *, exit_code, manifest,
                  frozen=None, events=None):
    run_dir, sd = _build_run(tmp_path)
    frozen = {"assets": [], "discovery_manifest_sha256": "a" * 64} if frozen is None else frozen
    events = [] if events is None else events
    monkeypatch.setattr(PR, "run_script",
                        _fake_run_factory(sd, exit_code, manifest, frozen, events))
    # 不带 skills_home:跳过 _validate_with_fixed_media(fake 环境无固定媒体树)
    ctx = SimpleNamespace(run_dir=str(run_dir), network_mode="integration", env={},
                          discovery={})
    return _media_two_phase_call(ctx, sd)


def _media_two_phase_call(ctx, sd):
    entry = tmp_entry(sd)
    state = SimpleNamespace(run_id="x", final_article_sha256=None)
    return PR._media_two_phase(ctx, sd, [], state, entry, None)


def tmp_entry(sd):
    import shutil
    from pathlib import Path
    p = sd / "entry.py"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    return p


def test_hf1_discover_fetch_only_errors_degrades_to_approval(tmp_path, monkeypatch):
    """签名全齐:fetch-only errors + 有 review_required 候选 → 进暂停。"""
    errors = [FETCH + "M-005: HTTP 404",
              FETCH + "M-021: unexpected error: timeout"]
    manifest = _base_manifest(errors=errors)
    out, meta = _run_discover(tmp_path, monkeypatch, exit_code=1, manifest=manifest)
    assert out == []
    assert meta.get("discover_degraded") is True
    assert meta.get("discover_exit_code") == 1
    assert meta.get("discover_errors") == errors
    assert meta.get("await_media_approval") is True
    sd = tmp_path / "a" / "b" / "c" / "media_enrichment"
    assert (sd / "approval_precheck.json").is_file()
    assert (sd / "approval_readiness.json").is_file()


def test_hf1_discover_non_fetch_error_stays_failed(tmp_path, monkeypatch):
    """errors 含非 fetch 前缀条目(如 SECRET_DETECTED)→ 维持 STAGE_FAILED。"""
    errors = [FETCH + "M-005: HTTP 404", "SECRET_DETECTED: token leaked"]
    manifest = _base_manifest(errors=errors)
    out, meta = _run_discover(tmp_path, monkeypatch, exit_code=1, manifest=manifest)
    assert out == []
    assert "discover_degraded" not in meta
    assert meta["entry_run"]["exit_code"] == 1
    assert meta.get("await_media_approval") is None


    """errors 全为 fetch 前缀但可批准候选为 0 → 降级无意义,维持 STAGE_FAILED。"""
def test_hf1_discover_no_candidates_arms_zero_image_fallback(tmp_path, monkeypatch):
    """77G:fetch-only + 零可批准候选 → 空合同降级，不再硬停。"""
    errors = [FETCH + "M-005: HTTP 404"]
    manifest = _base_manifest(errors=errors, eligible=0, review_required=0)
    out, meta = _run_discover(tmp_path, monkeypatch, exit_code=1, manifest=manifest)
    assert out == []
    assert meta.get("discover_degraded") is True
    assert meta.get("zero_image_fallback") is True
    assert meta.get("await_media_approval") is True
    contract = json.loads((tmp_path / "a" / "b" / "c" / "media_enrichment" /
                          "copyright_approval.json").read_text(encoding="utf-8"))
    assert contract["mode"] == "zero_image_shortfall"
    assert contract["approvals"] == []


def test_hf1_discover_validation_failed_stays_failed(tmp_path, monkeypatch):
    """run_id="validation_failed" → 维持 STAGE_FAILED。"""
    errors = [FETCH + "M-005: HTTP 404"]
    manifest = _base_manifest(run_id="validation_failed", errors=errors)
    out, meta = _run_discover(tmp_path, monkeypatch, exit_code=1, manifest=manifest)
    assert out == []
    assert "discover_degraded" not in meta
    assert meta["entry_run"]["exit_code"] == 1


def test_hf1_discover_exit0_paused_path_unchanged(tmp_path, monkeypatch):
    """正常 exit 0 → 既有 paused 路径行为不变(无 discover_degraded)。"""
    manifest = _base_manifest(errors=[])
    out, meta = _run_discover(tmp_path, monkeypatch, exit_code=0, manifest=manifest)
    assert out == []
    assert "discover_degraded" not in meta
    assert meta.get("await_media_approval") is True
    sd = tmp_path / "a" / "b" / "c" / "media_enrichment"
    assert (sd / "approval_precheck.json").is_file()
    assert (sd / "approval_readiness.json").is_file()
