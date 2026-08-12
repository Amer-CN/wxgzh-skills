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
