"""档67 OBS-89:视觉内容门槛分级 + 同数据重复检测测试。

覆盖:
1. 分级判据:代码密集(>=2 代码块)-> min 3;新闻(0 代码块)-> min 6(不降低)
2. 有效下限:无 config 用分级;存在 config 时取 max(不降低新闻类)
3. OBS-89 去重:同 chart_group + 同 numbers 收敛 1 张(bar 优先),不同组不误判
4. readiness 集成:6 图表 -> summary approvable=3;visual_tier 块正确
5. 反向验证:a. 本 RUN 形态(3 图表 + 2 代码块,含 6 图表去重)-> 可批准 3,通过
   b. RUN1/RUN2 新闻综述(零代码块)-> 门槛 6 不降低
   c. 电车 RUN(零代码块)-> 门槛 6 不降低
6. 档68 contract 层分级:enforce_contract 对代码密集文章按 3 判定通过;
   新闻文章仍按 6 判定(3 图不通过)。
"""
from __future__ import annotations

import json
from pathlib import Path

from wxgzh_pipeline.approval_evidence import build_approval_readiness
from wxgzh_pipeline.contracts import enforce_contract
from wxgzh_pipeline.visual_threshold import (
    CODE_DENSE_IMAGE_MIN,
    NEWS_IMAGE_MIN,
    compute_visual_tier,
    count_code_blocks,
    dedup_same_data_charts,
    effective_body_images_min,
)

FIX = Path(__file__).parent / "fixtures" / "obs67"
MANIFEST_6 = FIX / "manifest.six_charts.json"
REGISTRY = FIX / "registry.json"
ARTICLE_CODE_DENSE = FIX / "article.code_dense.md"
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


def _generated_records(man):
    """仅 generated 图表进入去重视野(源图 A-001..004 rejected 不在候选)。"""
    gen = [a for a in man["assets"] if a.get("asset_origin") == "generated"]
    return [{"asset_id": a["asset_id"], "decision": a["decision"],
             "approvable": True, "approvable_blockers": []}
            for a in gen]


# ── 1. 分级判据 ─────────────────────────────────────────────

def test_tier_code_dense_min_3():
    tier = compute_visual_tier(ARTICLE_CODE_DENSE.read_text(encoding="utf-8"))
    assert tier["code_blocks"] >= 2
    assert tier["code_dense"] is True
    assert tier["body_images_min"] == CODE_DENSE_IMAGE_MIN == 3
    assert tier["visual_units_min"] == 5
    assert len(tier["evidence"]) == 3  # 档68 三条依据留痕


def test_tier_news_min_6_not_lowered():
    tier = compute_visual_tier(ARTICLE_NEWS.read_text(encoding="utf-8"))
    assert tier["code_blocks"] == 0
    assert tier["code_dense"] is False
    assert tier["body_images_min"] == NEWS_IMAGE_MIN == 6


def test_count_code_blocks_nonempty_only():
    # 空代码块不计数;成对围栏且含非空行才计
    assert count_code_blocks("```\n\n```") == 0
    assert count_code_blocks("```bash\necho hi\n```") == 1
    assert count_code_blocks(ARTICLE_CODE_DENSE.read_text(encoding="utf-8")) == 2


def test_effective_min_no_config_uses_tier():
    assert effective_body_images_min(compute_visual_tier(ARTICLE_NEWS.read_text(encoding="utf-8")), None) == 6


def test_effective_min_config_is_floor_guarded():
    news = compute_visual_tier(ARTICLE_NEWS.read_text(encoding="utf-8"))
    # 新闻类即使存在旧 config=2,也不得低于 6(分级下限)
    assert effective_body_images_min(news, 2) == 6


# ── 2. OBS-89 去重 ──────────────────────────────────────────

def test_dedup_six_charts_to_three_keep_bar():
    man = json.loads(MANIFEST_6.read_text(encoding="utf-8"))
    assets = {a["asset_id"]: a for a in man["assets"]}
    records = _generated_records(man)
    out = dedup_same_data_charts(records, assets, REGISTRY)
    by_id = {r["asset_id"]: r for r in out}
    assert by_id["A-006"]["duplicate_of"] == "A-005"
    assert by_id["A-006"]["approvable"] is False
    assert any("OBS-89" in b for b in by_id["A-006"]["approvable_blockers"])
    assert by_id["A-008"]["duplicate_of"] == "A-007"
    assert by_id["A-010"]["duplicate_of"] == "A-009"
    assert sum(1 for r in out if r["approvable"]) == 3


def test_dedup_different_groups_not_confused():
    man = json.loads(MANIFEST_6.read_text(encoding="utf-8"))
    assets = {a["asset_id"]: a for a in man["assets"]}
    records = _generated_records(man)
    out = dedup_same_data_charts(records, assets, REGISTRY)
    by_id = {r["asset_id"]: r for r in out}
    # 不同组(A-005/006 红线 vs A-007/008 清单)互不误判
    assert by_id["A-006"]["duplicate_of"] != "A-007"
    assert by_id["A-008"]["duplicate_of"] != "A-009"


def test_dedup_single_chart_group_untouched():
    man = json.loads(MANIFEST_6.read_text(encoding="utf-8"))
    man["assets"] = [a for a in man["assets"] if a["asset_id"] in ("A-005", "A-006")]
    assets = {a["asset_id"]: a for a in man["assets"]}
    records = _generated_records(man)
    out = dedup_same_data_charts(records, assets, REGISTRY)
    by_id = {r["asset_id"]: r for r in out}
    assert by_id["A-005"]["duplicate_of"] is None
    assert by_id["A-005"]["approvable"] is True


# ── 3. readiness 集成 ───────────────────────────────────────

def test_readiness_six_charts_converge_to_three(tmp_path):
    rd = _run_dir(tmp_path, ARTICLE_CODE_DENSE)
    readiness = build_approval_readiness(rd)
    by_id = {r["asset_id"]: r for r in readiness["assets"]}
    assert by_id["A-006"]["approvable"] is False
    assert by_id["A-006"]["duplicate_of"] == "A-005"
    assert readiness["summary"]["approvable"] == 3
    assert readiness["visual_tier"]["code_dense"] is True
    assert readiness["visual_tier"]["body_images_min"] == 3


def test_readiness_news_tier_6_not_lowered(tmp_path):
    """★反向验证 b:RUN1/RUN2 新闻综述(零代码块)门槛保持 6。"""
    rd = _run_dir(tmp_path, ARTICLE_NEWS)
    readiness = build_approval_readiness(rd)
    assert readiness["visual_tier"]["body_images_min"] == 6


def test_readiness_elec_run_tier_6_not_relaxed(tmp_path):
    """★反向验证 c:档60 电车 RUN(零代码块)门槛不因分级放松。"""
    rd = _run_dir(tmp_path, ARTICLE_NEWS)
    readiness = build_approval_readiness(rd)
    assert readiness["visual_tier"]["body_images_min"] == 6
    assert readiness["visual_tier"]["criterion"].startswith("news")


def test_visual_content_met_units(tmp_path):
    rd = _run_dir(tmp_path, ARTICLE_CODE_DENSE)
    readiness = build_approval_readiness(rd)
    tier = readiness["visual_tier"]
    # 3 图表 + 2 代码块 = 5 视觉单元 >= 5
    assert tier["visual_units_min"] == 5


# ── 4. 档68 contract 层分级(与 content_validate 同口径) ─────

def _contract_dir(tmp_path, article):
    rd = _run_dir(tmp_path, article)
    me = rd / "media_enrichment"
    man = json.loads(MANIFEST_6.read_text(encoding="utf-8"))
    # 仅保留 3 张 bar 资产并标记 eligible + 已上传成功(mmbiz)
    keep = ["A-005", "A-007", "A-009"]
    man["assets"] = [a for a in man["assets"] if a["asset_id"] in keep]
    for a in man["assets"]:
        a["decision"] = "eligible"
        a["upload"] = {"status": "success",
                         "remote_url": f"https://mmbiz.qpic.cn/mmbiz_png/x/{a['asset_id']}"}
    body = [{"asset_id": a["asset_id"], "sha256": a.get("sha256") or ""}
            for a in man["assets"]]
    bnd = {"schema_version": "1.0", "article_sha256": "0" * 64,
           "body_image_count": len(body), "body_images": body}
    (me / "discover" / "media_manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    (me / "media_manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    (me / "article_image_bindings.json").write_text(
        json.dumps(bnd, ensure_ascii=False, indent=2), encoding="utf-8")
    events = {"schema_version": "1.0", "serial": True, "events": [
        {"asset_id": aid, "status": "success",
         "start_monotonic": i, "end_monotonic": i + 1}
        for i, aid in enumerate(keep)]}
    (me / "upload_events.json").write_text(
        json.dumps(events, ensure_ascii=False, indent=2), encoding="utf-8")
    # ctx=None 路径的 contract 输入完备性:上游输入 + 前置 receipt 文件
    (rd / "aihot").mkdir(parents=True, exist_ok=True)
    (rd / "aihot" / "deduplicated_items.json").write_text("[]", encoding="utf-8")
    (me / "media_discovery_request.json").write_text("{}", encoding="utf-8")
    (me / "media_continuation_request.json").write_text("{}", encoding="utf-8")
    (me / "discover" / "asset_discovery_manifest.json").write_text(
        json.dumps({"assets": [], "discovery_manifest_sha256": "0" * 64}), encoding="utf-8")
    (rd / "zh_human_writing" / "stage_receipt.json").write_text("{}", encoding="utf-8")
    return rd, me


def test_contract_code_dense_min_3_passes(tmp_path):
    """档68:代码密集文章 3 图 + 2 代码块 -> contract body_images_min 通过(分级 3)。"""
    rd, me = _contract_dir(tmp_path, ARTICLE_CODE_DENSE)
    ok, report = enforce_contract("media_enrichment", me, ctx=None, state=None)
    assert ok, report["problems"]
    assert report["checks"]["body_images_min"]["ok"] is True


def test_contract_news_3_images_fails_min6(tmp_path):
    """★反向验证:新闻综述 3 图在 contract 层仍按 6 判定 FAIL(门槛不降低)。"""
    rd, me = _contract_dir(tmp_path, ARTICLE_NEWS)
    ok, report = enforce_contract("media_enrichment", me, ctx=None, state=None)
    assert ok is False
    assert report["checks"]["body_images_min"]["ok"] is False


def test_contract_news_config2_still_requires_6(tmp_path):
    """OBS-94 防降阈:新闻类即使 RUN 目录出现 config=2,contract 层仍要求 6。"""
    rd, me = _contract_dir(tmp_path, ARTICLE_NEWS)
    (me / "validation_config.json").write_text(
        json.dumps({"body_images_min": 2}), encoding="utf-8")
    ok, report = enforce_contract("media_enrichment", me, ctx=None, state=None)
    assert ok is False
    assert report["checks"]["body_images_min"]["ok"] is False
