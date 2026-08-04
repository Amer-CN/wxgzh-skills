"""档67 OBS-89:视觉内容门槛分级 + 同数据重复检测测试。

覆盖:
1. 分级判据:代码密集(>=2 代码块)-> min 3;新闻(0 代码块)-> min 6(不降低)
2. effective_body_images_min:无 config = 分级值;有 config 取 max(分级, config)
3. ★反向验证三组:
   a. 本 RUN 形态(3 图表 + 2 代码块,含 6 图表去重)-> 可批准 3,通过
   b. RUN1/RUN2 新闻综述(零代码块)-> 门槛 6 不降低
   c. 电车 RUN(零代码块)-> 门槛 6 不降低
4. OBS-89:同 chart_group + 同 numbers 收敛为 1 张(优先 bar);不同组不误判;
   duplicate approvable=false;duplicate_of 标记正确
5. readiness 集成:6 图表 -> summary approvable=3;visual_tier 块正确
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from wxgzh_pipeline.visual_threshold import (
    compute_visual_tier, effective_body_images_min, dedup_same_data_charts,
    count_code_blocks,
)
from wxgzh_pipeline.approval_evidence import build_approval_readiness

FIX = Path(__file__).parent / "fixtures" / "obs67"
REGISTRY = FIX / "registry.json"
MANIFEST_6 = FIX / "manifest.six_charts.json"
ARTICLE_CODE = FIX / "article.code_dense.md"
ARTICLE_NEWS = FIX / "article.news.md"


def _run_dir(tmp_path, article, manifest=None, registry=None):
    rd = tmp_path / "run"
    d = rd / "media_enrichment" / "discover"
    d.mkdir(parents=True)
    (d / "media_manifest.json").write_text(
        (manifest or MANIFEST_6).read_text(encoding="utf-8"), encoding="utf-8")
    (rd / "super_writer").mkdir(parents=True)
    (rd / "super_writer" / "canonical_claim_registry.json").write_text(
        (registry or REGISTRY).read_text(encoding="utf-8"), encoding="utf-8")
    (rd / "zh_human_writing").mkdir(parents=True)
    (rd / "zh_human_writing" / "final_article.md").write_text(
        article.read_text(encoding="utf-8"), encoding="utf-8")
    return rd


# ── 1. 分级判据 ─────────────────────────────────────────────

def test_tier_code_dense_min_3():
    tier = compute_visual_tier(ARTICLE_CODE.read_text(encoding="utf-8"))
    assert tier["code_blocks"] == 2
    assert tier["code_dense"] is True
    assert tier["body_images_min"] == 3
    assert tier["visual_units_min"] == 5


def test_tier_news_min_6_not_lowered():
    tier = compute_visual_tier(ARTICLE_NEWS.read_text(encoding="utf-8"))
    assert tier["code_blocks"] == 0
    assert tier["code_dense"] is False
    assert tier["body_images_min"] == 6
    assert tier["visual_units_min"] is None


def test_count_code_blocks_nonempty_only():
    assert count_code_blocks("a\n```\n```\n") == 0          # 空围栏不计
    assert count_code_blocks("a\n```bash\nx\n```\n") == 1
    assert count_code_blocks("```\nx\n```\n```y\n\n```") == 1


# ── 2. effective_body_images_min ─────────────────────────────

def test_effective_min_no_config_uses_tier():
    assert effective_body_images_min(compute_visual_tier(ARTICLE_CODE.read_text(encoding="utf-8")), None) == 3
    assert effective_body_images_min(compute_visual_tier(ARTICLE_NEWS.read_text(encoding="utf-8")), None) == 6


def test_effective_min_config_is_floor_guarded():
    news = compute_visual_tier(ARTICLE_NEWS.read_text(encoding="utf-8"))
    # 新闻类即使存在旧 config=2,也不得低于 6(分级下限)
    assert effective_body_images_min(news, 2) == 6
    code = compute_visual_tier(ARTICLE_CODE.read_text(encoding="utf-8"))
    assert effective_body_images_min(code, 1) == 3   # config 不能压到 3 以下
    assert effective_body_images_min(code, 4) == 4   # config 可更严


# ── 3. OBS-89 同数据去重 ────────────────────────────────────

def test_dedup_six_charts_to_three_keep_bar():
    man = json.loads(MANIFEST_6.read_text(encoding="utf-8"))
    assets_by_id = {a["asset_id"]: a for a in man["assets"]}
    records = [
        {"asset_id": a["asset_id"], "decision": a["decision"],
         "approvable": True, "approvable_blockers": []}
        for a in man["assets"] if a["decision"] == "review_required"
    ]
    out = dedup_same_data_charts(records, assets_by_id, REGISTRY)
    by_id = {r["asset_id"]: r for r in out}
    approvable = [r for r in out if r["approvable"]]
    assert sorted(r["asset_id"] for r in approvable) == ["A-005", "A-007", "A-009"]
    # duplicate 标记与不可批准
    assert by_id["A-006"]["duplicate_of"] == "A-005"
    assert by_id["A-008"]["duplicate_of"] == "A-007"
    assert by_id["A-010"]["duplicate_of"] == "A-009"
    assert by_id["A-006"]["approvable"] is False
    assert any("OBS-89" in b for b in by_id["A-006"]["approvable_blockers"])
    # 保留者无 duplicate_of
    assert by_id["A-005"]["duplicate_of"] is None


def test_dedup_different_groups_not_confused():
    man = json.loads(MANIFEST_6.read_text(encoding="utf-8"))
    assets_by_id = {a["asset_id"]: a for a in man["assets"]}
    records = [
        {"asset_id": a["asset_id"], "decision": a["decision"],
         "approvable": True, "approvable_blockers": []}
        for a in man["assets"] if a["decision"] == "review_required"
    ]
    out = dedup_same_data_charts(records, assets_by_id, REGISTRY)
    # 不同组(A-005/006 红线 vs A-007/008 清单)互不误判
    by_id = {r["asset_id"]: r for r in out}
    assert by_id["A-006"]["duplicate_of"] != "A-007"
    assert by_id["A-008"]["duplicate_of"] != "A-005"


def test_dedup_single_chart_group_untouched():
    man = json.loads(MANIFEST_6.read_text(encoding="utf-8"))
    # 只留红线一组(bar + comp)
    man["assets"] = [a for a in man["assets"] if a["asset_id"] in ("A-005", "A-006")]
    assets_by_id = {a["asset_id"]: a for a in man["assets"]}
    records = [{"asset_id": a["asset_id"], "decision": a["decision"],
                "approvable": True, "approvable_blockers": []}
               for a in man["assets"]]
    out = dedup_same_data_charts(records, assets_by_id, REGISTRY)
    approvable = [r for r in out if r["approvable"]]
    assert [r["asset_id"] for r in approvable] == ["A-005"]


# ── 4. readiness 集成 + 反向验证 ────────────────────────────

def test_readiness_six_charts_converge_to_three(tmp_path):
    rd = _run_dir(tmp_path, ARTICLE_CODE)
    readiness = build_approval_readiness(rd, claim_texts=[],
                                         html_provider=lambda u: None)
    assert readiness["visual_tier"]["code_dense"] is True
    assert readiness["summary"]["approvable"] == 3
    by_id = {r["asset_id"]: r for r in readiness["assets"]}
    assert by_id["A-005"]["approvable"] is True
    assert by_id["A-006"]["approvable"] is False
    assert by_id["A-006"]["duplicate_of"] == "A-005"
    assert by_id["A-009"]["approvable"] is True
    assert by_id["A-010"]["approvable"] is False


def test_readiness_news_tier_6_not_lowered(tmp_path):
    """★反向验证 b:RUN1/RUN2 新闻综述(零代码块)门槛保持 6。"""
    rd = _run_dir(tmp_path, ARTICLE_NEWS)
    readiness = build_approval_readiness(rd, claim_texts=[],
                                         html_provider=lambda u: None)
    assert readiness["visual_tier"]["code_dense"] is False
    assert readiness["visual_tier"]["body_images_min"] == 6


def test_readiness_elec_run_tier_6_not_relaxed(tmp_path):
    """★反向验证 c:档60 电车 RUN(零代码块)门槛不因分级放松。"""
    rd = _run_dir(tmp_path, ARTICLE_NEWS)
    readiness = build_approval_readiness(rd, claim_texts=[],
                                         html_provider=lambda u: None)
    assert readiness["visual_tier"]["body_images_min"] == 6
    assert readiness["visual_tier"]["criterion"].startswith("news")


def test_visual_content_met_units(tmp_path):
    """★反向验证 a:3 图表 + 2 代码块 = 5 视觉单元,视觉内容达标。"""
    rd = _run_dir(tmp_path, ARTICLE_CODE)
    readiness = build_approval_readiness(rd, claim_texts=[],
                                         html_provider=lambda u: None)
    # 可批准 3 张图表;加上 2 个代码块 = 5 视觉单元 >= 5
    assert readiness["summary"]["approvable"] == 3
    assert readiness["visual_tier"]["code_blocks"] == 2
    assert readiness["visual_tier"]["visual_units_min"] == 5
