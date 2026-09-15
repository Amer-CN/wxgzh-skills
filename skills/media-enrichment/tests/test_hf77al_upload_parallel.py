"""77AL/OBS-389:批量上传批次并发(批内并发、批间串行)+ 批次标记入账。

- UPLOAD_WORKERS 单一真源,批次划分 = ceil(资产数/上限);
- 批内真并发(实证:批的墙上跨度 < 各条 request_elapsed 之和);
- manifest 与事件表一致(每条成功事件必有一条 eligible+success 的资产回写);
- 旧串行调用兼容(timed_upload 不传批次参数 → 入账形状与 77AL 前逐字一致)。
"""
from __future__ import annotations

import hashlib
import json
import random
import subprocess
import sys
import threading
import time
from pathlib import Path

from PIL import Image

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

from media_enrichment.uploader import (  # noqa: E402
    UPLOAD_WORKERS, MockUploader, timed_upload, upload_assets_parallel)

RUNNER = SKILL_ROOT / "scripts" / "run_media_enrichment.py"
EVIDENCE_SHA = "e" * 64
IMAGE_COUNT = 24


class _SlowUploader:
    """真并发可观测的假 uploader:每次 upload 固定耗时并记录最大同时在跑数。"""

    def __init__(self, latency: float = 0.05):
        self.latency = latency
        self._lock = threading.Lock()
        self._inflight = 0
        self.max_inflight = 0

    def upload(self, local_path: str, asset_id: str = "",
               copyright_status: str = "unknown"):
        with self._lock:
            self._inflight += 1
            self.max_inflight = max(self.max_inflight, self._inflight)
        try:
            time.sleep(self.latency)
            return MockUploader().upload(local_path, asset_id,
                                         copyright_status=copyright_status)
        finally:
            with self._lock:
                self._inflight -= 1


def _batch_spans(events: list[dict]) -> dict[int, float]:
    spans: dict[int, float] = {}
    by_batch: dict[int, list[dict]] = {}
    for event in events:
        by_batch.setdefault(event.get("batch_index"), []).append(event)
    for index, group in by_batch.items():
        spans[index] = (max(e["end_monotonic"] for e in group)
                        - min(e["start_monotonic"] for e in group))
    return spans


def _mk_png(path: Path, seed: int) -> None:
    """生成 24 张互不重复(实测最小感知哈希距离 22 > PHASH_THRESHOLD=5)的图。"""
    rnd = random.Random(1000 + seed)
    data = bytes(rnd.randrange(256) for _ in range(160 * 120 * 3))
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.frombytes("RGB", (160, 120), data).save(path, "PNG")


def test_batches_concurrent_within_and_serial_across(tmp_path):
    """批次划分 + 批内真并发 + 批间不重叠 + 结果同序。"""
    items = []
    for index in range(8):
        img = tmp_path / f"i{index}.png"
        _mk_png(img, index)
        items.append((str(img), f"A-{index + 1:03d}", "known_allowed"))
    uploader = _SlowUploader()
    events: list = []
    results = upload_assets_parallel(uploader, events, items, workers=4)

    assert [r.status for r in results] == ["success"] * 8
    assert [e["asset_id"] for e in events] == [i[1] for i in items]
    assert [e["batch_index"] for e in events] == [0, 0, 0, 0, 1, 1, 1, 1]
    assert {e["batch_size"] for e in events} == {4}
    assert uploader.max_inflight == 4, "批内未真并发"
    # 批间串行:批 1 的起点不早于批 0 的终点
    assert min(e["start_monotonic"] for e in events if e["batch_index"] == 1) \
        >= max(e["end_monotonic"] for e in events if e["batch_index"] == 0)
    # 批内真并发实证:墙上跨度 < 该批各条耗时之和
    for index, span in _batch_spans(events).items():
        elapsed_sum = sum(e["request_elapsed_seconds"]
                          for e in events if e["batch_index"] == index)
        assert span < elapsed_sum or span < uploader.latency * 4, index


def test_legacy_serial_timed_upload_unchanged(tmp_path):
    """旧串行调用兼容:不传批次参数 → 无批次键、形状与 77AL 前一致。"""
    img = tmp_path / "x.png"
    _mk_png(img, 3)
    events: list = []
    result = timed_upload(MockUploader(), events, str(img), "A-001", "known_allowed")
    assert result.status == "success"
    assert len(events) == 1
    assert set(events[0]) == {
        "asset_id", "mode", "status", "started_at", "ended_at",
        "start_monotonic", "end_monotonic", "http_status", "wechat_errcode",
        "wechat_errmsg", "request_elapsed_seconds", "endpoint_path",
        "request_attempt_index", "media_id", "url",
    }
    assert "batch_index" not in events[0] and "batch_size" not in events[0]


def _mk_fixture(root: Path) -> None:
    html = root / "html"
    images = root / "images"
    html.mkdir(parents=True, exist_ok=True)
    images.mkdir(parents=True, exist_ok=True)
    for index in range(IMAGE_COUNT):
        name = f"p{index:02d}.png"
        _mk_png(images / name, index)
        (html / f"m{index:02d}.html").write_text(
            "<!doctype html><html><body><article><h1>页" + str(index) + "</h1>"
            f'<img src="https://img.example-source.test/{name}" '
            'alt="relevant body figure"></article></body></html>',
            encoding="utf-8")


def _mk_request(tmp_path: Path) -> Path:
    article = tmp_path / "final_article.md"
    article.write_text("# 并行上传\n\nrelevant body figure\n", encoding="utf-8")
    materials, claims = [], []
    for index in range(IMAGE_COUNT):
        mid = f"M-{index + 1:03d}"
        materials.append({
            "material_id": mid,
            "aihot_permalink": f"https://aihot.virxact.com/items/aihot-m{index:02d}",
            "source_url": f"https://source.example.test/m{index:02d}",
            "title": f"素材{index}",
            "selected_claim_ids": [f"C-{index + 1:02d}"],
            "copyright_review": {
                "status": "known_allowed", "reviewed_by": "fixture-reviewer",
                "reviewed_at": "2026-09-15T00:00:00Z", "evidence": EVIDENCE_SHA,
                "approval_id": f"AP-material-{index:02d}", "approved_scope": "material",
            },
        })
        claims.append({
            "claim_id": f"C-{index + 1:02d}",
            "claim_text": "relevant body figure",
            "material_id": mid,
            "source_url": f"https://source.example.test/m{index:02d}",
            "source_excerpt": "relevant body figure",
        })
    payload = {
        "schema_version": "1.0", "run_id": "hf77al-upload-parallel",
        "article": {"path": str(article),
                    "sha256": hashlib.sha256(article.read_bytes()).hexdigest()},
        "materials": materials, "claims": claims, "asset_approvals": [],
        "config": {"network_mode": "offline_fixture", "upload_mode": "wechat_audit",
                   "max_images_per_material": 4, "max_total_images": IMAGE_COUNT,
                   "min_width": 100, "min_height": 100,
                   "allow_unknown_license_for_publish": False},
    }
    path = tmp_path / "media_request.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _run(tmp_path: Path, fixture: Path, request: Path, phase: str, out: Path,
         frozen: Path | None = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-X", "utf8", str(RUNNER),
           "--request", str(request), "--output-dir", str(out),
           "--fixture-dir", str(fixture / "html"), "--phase", phase]
    if frozen is not None:
        cmd.extend(["--discovery-manifest", str(frozen)])
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300)


def test_cli_24_images_parallel_upload_and_manifest_consistency(tmp_path):
    """fixture 24 张:并行上传全成功 + 批次标记 + manifest/事件表一致。"""
    fixture = tmp_path / "fixture"
    _mk_fixture(fixture)
    request = _mk_request(tmp_path)
    discover_out = tmp_path / "out-discover"
    discovered = _run(tmp_path, fixture, request, "discover", discover_out)
    assert discovered.returncode == 0, discovered.stdout[-1500:] + discovered.stderr[-1500:]

    continue_out = tmp_path / "out-continue"
    continued = _run(tmp_path, fixture, request, "continue", continue_out,
                     discover_out / "asset_discovery_manifest.json")
    assert continued.returncode == 0, continued.stdout[-2000:] + continued.stderr[-2000:]

    payload = json.loads((continue_out / "upload_events.json").read_text(encoding="utf-8"))
    manifest = json.loads((continue_out / "media_manifest.json").read_text(encoding="utf-8"))
    bindings = json.loads(
        (continue_out / "article_image_bindings.json").read_text(encoding="utf-8"))
    events = payload["events"]
    assert payload["parallel_workers"] == UPLOAD_WORKERS
    assert len(events) == IMAGE_COUNT
    assert [e["status"] for e in events] == ["success"] * IMAGE_COUNT
    assert all(e["batch_size"] == UPLOAD_WORKERS for e in events)
    assert sorted({e["batch_index"] for e in events}) \
        == list(range(-(-IMAGE_COUNT // UPLOAD_WORKERS)))
    assert [e["asset_id"] for e in events] == sorted(e["asset_id"] for e in events)

    # manifest 一致:每条成功事件对应一个 eligible+success 且 remote_url 相同
    by_id = {a["asset_id"]: a for a in manifest["assets"]}
    for event in events:
        asset = by_id[event["asset_id"]]
        assert asset["decision"] == "eligible"
        assert asset["upload"]["status"] == "success"
        assert asset["upload"]["remote_url"] == event["url"]
    success_urls = {e["url"] for e in events}
    assert {b["remote_url"] for b in bindings["body_images"]} <= success_urls
    # manifest 由单写者产出(不因并发出现重复资产行)
    assert len(by_id) == len(manifest["assets"])
