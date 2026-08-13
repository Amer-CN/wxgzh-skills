"""档55 OBS-82:discover 候选可批准性预校验(尺寸硬门槛)测试。

覆盖:
1. 100x100(A-107 同款)与 1x1(A-108 同款)在预校验中被排除,不进 eligible
2. 尺寸边界:479x200 拦 / 480x200 过(档HF-3R2:门槛按用户裁决 480x200 重导;639x360 亦通过)
3. 批准合同消费端:含不达标资产 -> FAIL_CLOSED
4. 批准合同消费端:全部 eligible -> 通过
5. 真实 RUN 数据回归:discover/media_manifest.json 中 A-107 被识别
"""
import json
from pathlib import Path

import pytest

from wxgzh_pipeline import producers as PR


def _manifest(assets):
    return {"schema_version": "1.0", "assets": assets}


def _make_run(tmp_path, manifest):
    rd = tmp_path / "run"
    d = rd / "media_enrichment" / "discover"
    d.mkdir(parents=True)
    (d / "media_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return rd


A107 = {"asset_id": "A-107", "width": 100, "height": 100,
        "decision": "rejected", "quality_status": "pass"}
A108 = {"asset_id": "A-108", "width": 1, "height": 1,
        "decision": "rejected", "quality_status": "pass"}
A109 = {"asset_id": "A-109", "width": 1440, "height": 658,
        "decision": "eligible", "quality_status": "pass"}
A110 = {"asset_id": "A-110", "width": 1080, "height": 1920,
        "decision": "eligible", "quality_status": "pass"}


def test_small_assets_excluded_not_eligible(tmp_path):
    rd = _make_run(tmp_path, _manifest([A107, A108, A109]))
    pre = PR._approval_precheck(rd)
    assert "A-107" not in pre["eligible"]
    assert "A-108" not in pre["eligible"]
    by_id = {a["asset_id"]: a for a in pre["excluded"]}
    assert by_id["A-107"]["width"] == 100 and by_id["A-107"]["height"] == 100
    assert by_id["A-107"]["reason"] == "dimensions below minimum 480x200"
    assert "A-109" in pre["eligible"]


def test_dimension_boundary(tmp_path):
    """档HF-3R2:门槛按用户裁决(2026-08-09)改为 480x200——w<480 or h<200 才拦。
    断言意图不变:低于门槛进 excluded 带 reason、达标进 eligible 清单。"""
    rd = _make_run(tmp_path, _manifest([
        {"asset_id": "X-1", "width": 479, "height": 200},
        {"asset_id": "X-2", "width": 480, "height": 200},
        {"asset_id": "X-3", "width": 480, "height": 199},
        {"asset_id": "X-4", "width": None, "height": None},
        {"asset_id": "X-5", "width": 639, "height": 360},
    ]))
    pre = PR._approval_precheck(rd)
    assert "X-1" not in pre["eligible"] and "X-3" not in pre["eligible"]
    assert "X-2" in pre["eligible"]
    assert "X-5" in pre["eligible"]
    # 尺寸未知:不排除(continue 阶段由 media 侧兜底),如实标注
    assert "X-4" in pre["eligible"]


def test_enforce_blocks_small_approved(tmp_path):
    rd = _make_run(tmp_path, _manifest([A107, A109]))
    pre = PR._approval_precheck(rd)
    pre["checked_approvals"] = [{"asset_id": "A-107"}]
    with pytest.raises(PR.MediaRequestError) as exc:
        PR._enforce_approval_precheck(rd, pre)
    assert "A-107" in str(exc.value) and "100x100" in str(exc.value)


def test_enforce_passes_eligible(tmp_path):
    rd = _make_run(tmp_path, _manifest([A107, A109, A110]))
    pre = PR._approval_precheck(rd)
    pre["checked_approvals"] = [{"asset_id": "A-109"}, {"asset_id": "A-110"}]
    PR._enforce_approval_precheck(rd, pre)  # 不抛异常


def test_real_run_manifest_regression(tmp_path):
    """真实 RUN(档49/50)的 discover media_manifest:A-107 必须被识别排除。"""
    run = Path(r"F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260802T220853-codex-sol-luna-max-m6pyv4")
    manifest_path = run / "media_enrichment" / "discover" / "media_manifest.json"
    if not manifest_path.is_file():
        pytest.skip("real run manifest unavailable")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assets = [a for a in manifest["assets"] if a.get("asset_id")
              in ("A-107", "A-108", "A-109", "A-110")]
    rd = _make_run(tmp_path, manifest=_manifest(assets))
    pre = PR._approval_precheck(rd)
    by_id = {a["asset_id"]: a for a in pre["excluded"]}
    assert "A-107" in by_id and "A-108" in by_id
    assert "A-109" in pre["eligible"] and "A-110" in pre["eligible"]
