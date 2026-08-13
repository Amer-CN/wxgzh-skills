"""档64 OBS-64:素材注入正门(自有素材)测试。

覆盖:
1. schema 合规通过(与 aihot 产出同构 + 来源留痕必填)
2. 缺必填字段 FAIL_CLOSED
3. ★反向验证:缺 source_provenance 的 items 文件必须被拦下
4. 来源留痕写入 fetch_log(injection 块 + 逐条 provenance)
5. 注入标记正确(mode=items_file_injection,不伪装为检索结果)
6. 旧通道 user_materials_override 已不可用(content_validate FAIL)
7. 注入一致性校验(数量/ID 不匹配 FAIL)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from wxgzh_pipeline import material_injection as MI
from wxgzh_pipeline.stages import aihot as AIHOT_STAGE

FIX = Path(__file__).parent / "fixtures" / "obs64"


def _ctx_state(tmp_path):
    """最小 ctx/state 桩:content_validate 只需 sd/state。"""
    from types import SimpleNamespace
    ctx = SimpleNamespace(run_dir=str(tmp_path), skills_home=str(tmp_path))
    state = SimpleNamespace(topic="t", final_article_sha256=None,
                            items_file=str(FIX / "items.valid.json"))
    return ctx, state


def test_schema_valid_passes():
    items = json.loads((FIX / "items.valid.json").read_text(encoding="utf-8"))
    out = MI.validate_items(items)
    assert len(out) == 2
    assert out[0]["source_provenance"]["source_type"] == "repo_path"


def test_missing_required_field_fail_closed(tmp_path):
    items = json.loads((FIX / "items.valid.json").read_text(encoding="utf-8"))
    del items[0]["title"]
    with pytest.raises(MI.MaterialInjectionError, match="missing required fields"):
        MI.validate_items(items)


def test_missing_provenance_fail_closed(tmp_path):
    """★反向验证:缺来源字段的 items 必须被拦下。"""
    items = json.loads((FIX / "items.missing_provenance.json").read_text(encoding="utf-8"))
    with pytest.raises(MI.MaterialInjectionError, match="source_provenance"):
        MI.validate_items(items)


def test_invalid_provenance_values_fail_closed():
    items = json.loads((FIX / "items.valid.json").read_text(encoding="utf-8"))
    items[0]["source_provenance"]["source_type"] = "invented"
    with pytest.raises(MI.MaterialInjectionError, match="source_type"):
        MI.validate_items(items)
    items = json.loads((FIX / "items.valid.json").read_text(encoding="utf-8"))
    items[0]["source_provenance"]["content_sha256"] = "short"
    with pytest.raises(MI.MaterialInjectionError, match="content_sha256"):
        MI.validate_items(items)


def test_write_injected_aihot_writes_three_files_and_trail(tmp_path):
    sd = tmp_path / "run" / "aihot"
    sd.mkdir(parents=True)
    meta = MI.write_injected_aihot(sd, FIX / "items.valid.json", "run-x", "topic-x")
    assert meta["mode"] == MI.INJECTION_MODE
    for name in ("deduplicated_items.json", "raw_items.json", "fetch_log.json",
                 "items_file.injected.json"):
        assert (sd / name).is_file(), name
    dedup = json.loads((sd / "deduplicated_items.json").read_text(encoding="utf-8"))
    assert len(dedup) == 2
    fetch_log = json.loads((sd / "fetch_log.json").read_text(encoding="utf-8"))
    assert fetch_log["mode"] == "items_file_injection"
    assert fetch_log["aihot_api_skipped"] is True
    inj = fetch_log["injection"]
    assert inj["item_count"] == 2
    assert inj["items_file_sha256"] == meta["items_file_sha256"]
    assert len(inj["provenance"]) == 2
    assert inj["provenance"][0]["original_ref"].endswith("hooks/_common.sh")
    assert inj["provenance"][0]["content_sha256"] == "a" * 64


def test_content_validate_injection_consistent(tmp_path):
    ctx, state = _ctx_state(tmp_path)
    sd = tmp_path / "run" / "aihot"
    sd.mkdir(parents=True)
    MI.write_injected_aihot(sd, FIX / "items.valid.json", "run-x", "topic-x")
    code, report, _, _ = AIHOT_STAGE.content_validate(ctx, sd, state)
    assert code == 0
    assert report["AIHOT"] == "PASS(INJECTED)"
    assert report["injection"]["mode"] == "items_file_injection"


def test_content_validate_injection_inconsistent_fails(tmp_path):
    ctx, state = _ctx_state(tmp_path)
    sd = tmp_path / "run" / "aihot"
    sd.mkdir(parents=True)
    MI.write_injected_aihot(sd, FIX / "items.valid.json", "run-x", "topic-x")
    # 篡改 dedup(数量不一致)
    dedup = json.loads((sd / "deduplicated_items.json").read_text(encoding="utf-8"))
    dedup.append(dict(dedup[0], id="extra"))
    (sd / "deduplicated_items.json").write_text(
        json.dumps(dedup, ensure_ascii=False), encoding="utf-8")
    code, report, _, _ = AIHOT_STAGE.content_validate(ctx, sd, state)
    assert code == 1
    assert "inconsistent" in report["reason"]


def test_legacy_user_materials_override_closed(tmp_path):
    """旧的非正式手写通道必须 FAIL_CLOSED(档64 起不可用)。"""
    ctx, state = _ctx_state(tmp_path)
    sd = tmp_path / "run" / "aihot"
    sd.mkdir(parents=True)
    (sd / "deduplicated_items.json").write_text(
        (FIX / "items.valid.json").read_text(encoding="utf-8"), encoding="utf-8")
    (sd / "fetch_log.json").write_text(json.dumps({
        "mode": "user_materials_override", "aihot_api_skipped": True,
        "raw_count": 2, "deduplicated_count": 2,
    }), encoding="utf-8")
    code, report, _, _ = AIHOT_STAGE.content_validate(ctx, sd, state)
    assert code == 1
    assert "已关闭" in report["reason"]


def test_missing_items_file_fail_closed(tmp_path):
    sd = tmp_path / "run" / "aihot"
    sd.mkdir(parents=True)
    with pytest.raises(MI.MaterialInjectionError, match="items file missing"):
        MI.write_injected_aihot(sd, tmp_path / "nope.json", "run-x", "topic-x")
