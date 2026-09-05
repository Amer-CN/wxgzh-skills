"""76E/OBS-260/261:媒体请求范围=registry ∪ material-ledger used + 站内页 URL。"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

import wxgzh_pipeline.producers as PR

from wxgzh_pipeline.state import PipelineState

from conftest import SKILL_ROOT


class _Ctx:
    def __init__(self, run_dir, env=None):
        self.run_dir = str(run_dir)
        self.skills_home = r"F:\AIXM\wxgzh\.agents\skills"
        self.env = dict(env or {})
        self.network_mode = "offline_fixture"


def _mk_run(tmp_path) -> Path:
    rd = tmp_path
    # aihot dedup(50 风格:source_url + links.aihot 站内页)
    dedup = [
        {"id": "aihot-1", "title": "素材A", "source_url": "https://x.com/a",
         "links": {"aihot": "https://aihot.example/items/aihot-1", "original": "https://x.com/a"}},
        {"id": "aihot-2", "title": "M-25 Maestro", "source_url": "https://x.com/b",
         "links": {"aihot": "https://aihot.example/items/aihot-2", "original": "https://x.com/b"}},
    ]
    (rd / "aihot").mkdir()
    (rd / "aihot" / "deduplicated_items.json").write_text(
        json.dumps(dedup, ensure_ascii=False), encoding="utf-8")
    # canonical registry:只有 M-R1(绑定 aiho-1)
    reg = {
        "materials": [{"material_id": "M-R1", "dedup_id": "aihot-1",
                       "source_url": "https://x.com/a", "title": "素材A"}],
        "claims": [{"claim_id": "C-1", "claim_text": "素材A 的声明",
                    "material_id": "M-R1", "source_url": "https://x.com/a",
                    "source_excerpt": "素材A"}]}
    (rd / "super_writer").mkdir()
    (rd / "super_writer" / "canonical_claim_registry.json").write_text(
        json.dumps(reg, ensure_ascii=False), encoding="utf-8")
    # material-ledger:used = M-R1 + M-25(后者无 claim 绑定)
    ledger = {"material_ledger": {"total_count": 2, "materials": [
        {"id": "M-R1", "title": "素材A", "source_url": "https://x.com/a",
         "aihot_permalink": "https://x.com/a", "status": "used"},
        {"id": "M-25", "title": "M-25 Maestro", "source_url": "https://x.com/b",
         "aihot_permalink": "https://x.com/b", "status": "used"},
    ]}}
    (rd / "super_writer" / "material-ledger.yaml").write_text(
        yaml.safe_dump(ledger, allow_unicode=True), encoding="utf-8")
    (rd / "zh_human_writing").mkdir()
    (rd / "zh_human_writing" / "final_article.md").write_text(
        "# 标题\n\n导语。\n## 第一章\n\n正文。\n", encoding="utf-8")
    return rd


def _build(tmp_path) -> dict:
    rd = _mk_run(tmp_path)
    ctx = _Ctx(rd)
    sd = rd / "media_enrichment"
    sd.mkdir()
    st = PipelineState(run_id="r76e", topic="测试")
    req_path = PR._build_media_request(ctx, sd, st, phase="discover")
    return json.loads(req_path.read_text(encoding="utf-8"))


def test_request_materials_union_with_ledger_used(tmp_path):
    req = _build(tmp_path)
    mids = [m["material_id"] for m in req["materials"]]
    assert mids == ["M-R1", "M-25"], mids


def test_ledger_only_material_carries_internal_url_and_dedup_id(tmp_path):
    req = _build(tmp_path)
    m25 = next(m for m in req["materials"] if m["material_id"] == "M-25")
    assert m25["dedup_id"] == "aihot-2"
    assert m25["aihot_internal_url"] == "https://aihot.example/items/aihot-2"
    assert m25["source_url"] == "https://x.com/b"
    assert m25["selected_claim_ids"] == []
    # registry 素材也带站内页 URL
    mr1 = next(m for m in req["materials"] if m["material_id"] == "M-R1")
    assert mr1["aihot_internal_url"] == "https://aihot.example/items/aihot-1"


def test_discovery_budget_env_passthrough(tmp_path):
    rd = _mk_run(tmp_path)
    ctx = _Ctx(rd, env={"WXGZH_MEDIA_DISCOVERY_BUDGET": "48"})
    sd = rd / "media_enrichment"
    sd.mkdir()
    st = PipelineState(run_id="r76e", topic="测试")
    req_path = PR._build_media_request(ctx, sd, st, phase="discover")
    req = json.loads(req_path.read_text(encoding="utf-8"))
    assert req["config"]["discovery_budget"] == 48
    # 未设 env → 不传键(media 侧默认)
    ctx2 = _Ctx(rd)
    req_path2 = PR._build_media_request(ctx2, sd, st, phase="discover")
    req2 = json.loads(req_path2.read_text(encoding="utf-8"))
    assert "discovery_budget" not in req2["config"]



def _mk_supp_run(tmp_path) -> Path:
    """registry 含 supplemental 素材(官方博客,不在 dedup)+ ledger used 同素材。"""
    rd = tmp_path
    dedup = [{"id": "aihot-1", "title": "素材A", "source_url": "https://x.com/a",
              "links": {"aihot": "https://aihot.example/items/aihot-1", "original": "https://x.com/a"}}]
    (rd / "aihot").mkdir()
    (rd / "aihot" / "deduplicated_items.json").write_text(
        json.dumps(dedup, ensure_ascii=False), encoding="utf-8")
    reg = {
        "materials": [
            {"material_id": "M-R1", "dedup_id": "aihot-1",
             "source_url": "https://x.com/a", "title": "素材A"},
            {"material_id": "M-SUP", "provenance": "supplemental",
             "source_url": "https://official.example.com/blog/h3-release",
             "aihot_permalink": "https://aihot.virxact.com/items/supp-h3",
             "title": "官方公告:H3 发布",
             "selected_claim_ids": ["C-2"]},
        ],
        "claims": [
            {"claim_id": "C-1", "claim_text": "素材A 声明", "material_id": "M-R1",
             "source_url": "https://x.com/a", "source_excerpt": "素材A"},
            {"claim_id": "C-2", "claim_text": "官方公告声明", "material_id": "M-SUP",
             "source_url": "https://official.example.com/blog/h3-release",
             "source_excerpt": "官方公告"},
        ]}
    (rd / "super_writer").mkdir()
    (rd / "super_writer" / "canonical_claim_registry.json").write_text(
        json.dumps(reg, ensure_ascii=False), encoding="utf-8")
    ledger = {"material_ledger": {"total_count": 2, "materials": [
        {"id": "M-R1", "title": "素材A", "source_url": "https://x.com/a",
         "aihot_permalink": "https://x.com/a", "status": "used"},
        {"id": "M-SUP", "title": "官方公告:H3 发布",
         "source_url": "https://official.example.com/blog/h3-release",
         "aihot_permalink": None,
         "status": "used", "provenance": "supplemental"},
    ]}}
    (rd / "super_writer" / "material-ledger.yaml").write_text(
        yaml.safe_dump(ledger, allow_unicode=True), encoding="utf-8")
    (rd / "zh_human_writing").mkdir()
    (rd / "zh_human_writing" / "final_article.md").write_text(
        "# 标题\n\n导语。\n## 第一章\n\n正文。\n", encoding="utf-8")
    return rd


def _build_supp(tmp_path) -> dict:
    rd = _mk_supp_run(tmp_path)
    ctx = _Ctx(rd)
    sd = rd / "media_enrichment"
    sd.mkdir()
    st = PipelineState(run_id="r76h", topic="测试")
    req_path = PR._build_media_request(ctx, sd, st, phase="discover")
    return json.loads(req_path.read_text(encoding="utf-8"))


def test_supplemental_material_accepted(tmp_path):
    """76H/OBS-268:provenance=supplemental 素材不在 dedup 池也接受(官方来源注册)。"""
    req = _build_supp(tmp_path)
    sup = [m for m in req["materials"] if m.get("provenance") == "supplemental"]
    assert len(sup) == 1
    assert sup[0]["material_id"] == "M-SUP"
    assert sup[0]["source_url"] == "https://official.example.com/blog/h3-release"
    assert "dedup_id" not in sup[0]
    # normal 素材照旧映射 dedup
    norm = [m for m in req["materials"] if m.get("material_id") == "M-R1"]
    assert norm and norm[0].get("dedup_id") == "aihot-1"


def test_unregistered_source_still_fail_closed(tmp_path):
    """76H/OBS-268:未注册(无 provenance)且不在 dedup 的素材仍 FAIL_CLOSED。"""
    rd = _mk_supp_run(tmp_path)
    # ledger 加一条无 provenance 且不在 dedup 的 used 素材
    lp = rd / "super_writer" / "material-ledger.yaml"
    led = yaml.safe_load(lp.read_text(encoding="utf-8"))
    led["material_ledger"]["materials"].append({
        "id": "M-NOSUP", "title": "未注册来源", "source_url": "https://rogue.example.com/x",
        "aihot_permalink": "https://rogue.example.com/x", "status": "used"})
    lp.write_text(yaml.safe_dump(led, allow_unicode=True), encoding="utf-8")
    ctx = _Ctx(rd)
    sd = rd / "media_enrichment"
    sd.mkdir()
    st = PipelineState(run_id="r76h", topic="测试")
    import pytest as _pytest
    with _pytest.raises(PR.MediaRequestError) as ei:
        PR._build_media_request(ctx, sd, st, phase="discover")
    assert "not found in dedup" in str(ei.value)
