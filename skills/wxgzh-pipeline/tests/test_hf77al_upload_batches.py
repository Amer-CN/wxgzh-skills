"""77AL/OBS-389:上传批次并发的契约侧口径——批次分区重叠判定。

- 旧串行事件表(无批次标记,77AL 前产物):沿用逐对无重叠判定,不得回归;
- 新批次事件表:BATCH_SIZE 解释的批次分区,所需并发道数 <= 声明的批次数 = 通过;
- 超出声明批次数(真无界并发)= upload_no_overlap 拒,并给出并发超限理由。
"""
from __future__ import annotations

import json
from pathlib import Path

from wxgzh_pipeline.contracts import enforce_contract

BATCH_SIZE = 4


def _contract_dir(tmp_path: Path, events: list[dict]) -> Path:
    """最小 media_enrichment 阶段目录:资产全 eligible+已上传成功 + 事件表。"""
    run_dir = tmp_path / "run"
    me = run_dir / "media_enrichment"
    (me / "discover").mkdir(parents=True, exist_ok=True)
    (run_dir / "aihot").mkdir(parents=True, exist_ok=True)
    (run_dir / "zh_human_writing").mkdir(parents=True, exist_ok=True)
    (run_dir / "aihot" / "deduplicated_items.json").write_text("[]", encoding="utf-8")
    (me / "media_discovery_request.json").write_text("{}", encoding="utf-8")
    (run_dir / "zh_human_writing" / "final_article.md").write_text(
        "# t\n\n正文。\n", encoding="utf-8")

    assets, body = [], []
    for index in range(1, len(events) + 1):
        asset_id = f"A-{index:03d}"
        sha = f"{index:064d}"
        assets.append({
            "asset_id": asset_id, "asset_origin": "source", "decision": "eligible",
            "sha256": sha, "upload": {
                "mode": "wechat_image_host", "status": "success",
                "remote_url": f"https://mmbiz.qpic.cn/mmbiz_png/x/{asset_id}",
                "response_sha256": sha},
        })
        body.append({"asset_id": asset_id, "sha256": sha,
                     "remote_url": f"https://mmbiz.qpic.cn/mmbiz_png/x/{asset_id}"})
    manifest = {"run_id": "contract-batch", "input": {},
                "assets": assets, "errors": [], "warnings": []}
    bindings = {"schema_version": "1.0", "article_sha256": "0" * 64,
                "body_image_count": len(body), "body_images": body}
    (me / "media_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (me / "article_image_bindings.json").write_text(
        json.dumps(bindings, ensure_ascii=False, indent=2), encoding="utf-8")
    payload = {"schema_version": "1.0", "serial": True,
               "parallel_workers": BATCH_SIZE, "events": events}
    (me / "upload_events.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return me


def _serial_events(count: int) -> list[dict]:
    """77AL 前产物形状:逐条首尾相接,无批次键。"""
    return [{"asset_id": f"A-{i + 1:03d}", "status": "success",
             "start_monotonic": i, "end_monotonic": i + 1,
             "url": "https://mmbiz.qpic.cn/x"} for i in range(count)]


def _batch_events(count: int, batch_size: int, concurrent: int) -> list[dict]:
    """批次事件表:每 concurrent 条同时起跑、跨组不重叠。"""
    events = []
    for index in range(count):
        start = (index // concurrent) * 10
        events.append({
            "asset_id": f"A-{index + 1:03d}", "status": "success",
            "start_monotonic": start, "end_monotonic": start + 1,
            "batch_index": index // concurrent, "batch_size": batch_size,
            "url": "https://mmbiz.qpic.cn/x"})
    return events


def test_legacy_serial_log_still_enforced(tmp_path):
    """旧串行事件表:无重叠 → 通过;人为重叠 → 拒(口径不回归)。"""
    me = _contract_dir(tmp_path, _serial_events(4))
    _ok, report = enforce_contract("media_enrichment", me)
    assert report["checks"]["upload_no_overlap"]["ok"] is True, report["problems"]

    overlapped = _serial_events(4)
    overlapped[1]["start_monotonic"] = 0.5  # 与第一条重叠
    me2 = _contract_dir(tmp_path / "b", overlapped)
    _ok2, report2 = enforce_contract("media_enrichment", me2)
    assert report2["checks"]["upload_no_overlap"]["ok"] is False
    assert report2["checks"]["upload_no_overlap"]["detail"] == \
        "parallel/overlapping uploads detected"


def test_batch_partition_allows_declared_concurrency(tmp_path):
    """批内并发(4 道 = 声明批次数)→ 通过,且每资产恰一次成功。"""
    me = _contract_dir(tmp_path, _batch_events(8, BATCH_SIZE, BATCH_SIZE))
    _ok, report = enforce_contract("media_enrichment", me)
    assert report["checks"]["upload_no_overlap"]["ok"] is True, report["problems"]
    assert report["checks"]["one_success_per_asset"]["ok"] is True
    assert report["checks"]["every_bound_asset_uploaded_once"]["ok"] is True


def test_batch_partition_rejects_unbounded_concurrency(tmp_path):
    """并发道数 6 > 声明批次数 4(无界并发)→ 拒,理由=并发超限。"""
    me = _contract_dir(tmp_path, _batch_events(6, BATCH_SIZE, 6))
    ok, report = enforce_contract("media_enrichment", me)
    assert ok is False
    assert report["checks"]["upload_no_overlap"]["ok"] is False
    assert report["checks"]["upload_no_overlap"]["detail"] == \
        "concurrent uploads exceed the declared batch size"


def test_declared_workers_must_match_event_log(tmp_path):
    """契约声明值与事件表台账值不一致 → upload_parallel_workers_declared 拒。"""
    me = _contract_dir(tmp_path, _batch_events(4, BATCH_SIZE, BATCH_SIZE))
    payload = json.loads((me / "upload_events.json").read_text(encoding="utf-8"))
    payload["parallel_workers"] = BATCH_SIZE * 4
    (me / "upload_events.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    ok, report = enforce_contract("media_enrichment", me)
    assert ok is False
    assert report["checks"]["upload_parallel_workers_declared"]["ok"] is False
    assert report["checks"]["upload_parallel_workers_declared"]["detail"] == \
        f"contract={BATCH_SIZE} upload_events={BATCH_SIZE * 4}"


def test_legacy_event_log_without_workers_key_not_blocked(tmp_path):
    """77AL 前事件表无 parallel_workers 台账键 → 该项不适用判通过(旧串行日志
    另走逐对无重叠判定,不被当成新并发)。"""
    me = _contract_dir(tmp_path, _serial_events(4))
    payload = json.loads((me / "upload_events.json").read_text(encoding="utf-8"))
    payload.pop("parallel_workers")
    (me / "upload_events.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _ok, report = enforce_contract("media_enrichment", me)
    assert report["checks"]["upload_parallel_workers_declared"]["ok"] is True
    assert report["checks"]["upload_parallel_workers_declared"]["detail"] == \
        f"contract={BATCH_SIZE} upload_events=None"
    assert report["checks"]["upload_no_overlap"]["ok"] is True
    assert not any(p.startswith("upload_parallel_workers_declared")
                   for p in report["problems"])
