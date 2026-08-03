"""档52 OBS-72: live 封面必须从本 RUN 已批准资产的本地冻结文件中选择。

三条件 FAIL_CLOSED（任一条即拦截，exit 2 零副作用）：
  1. 资产不在批准合同内 / 无稳定 single_asset 批准记录
  2. 批准记录与冻结 discovery manifest 的 asset_sha256 不一致
  3. 本地 discover/images/<sha>.* 文件缺失或 sha256 与冻结清单不一致

选择规则（显式，不依赖隐式顺序）：
  article_image_bindings.json body_images 顺序中第一张
  「已批准 + 已成功上传」的资产；取不到任何候选即 FAIL_CLOSED。

本测试全部走 live 分支但 monkeypatch run_script，零真实微信副作用。
"""
import json
import hashlib
from pathlib import Path

import pytest

from wxgzh_pipeline import execmodel as EM
from wxgzh_pipeline import producers as PR


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _make_approval(asset_id: str, sha: str, material_id: str = "M-01",
                   source_url: str = "https://example.com/a") -> dict:
    identity = PR._stable_asset_identity({
        "material_id": material_id, "source_page_url": source_url,
        "resolved_original_url": source_url, "asset_sha256": sha,
    })
    return {
        "approval_id": f"AP-TEST-{asset_id}",
        "approved_scope": "single_asset",
        "approved_by": "independent_reviewer",
        "approved_at": "20260803T00000000+08:00",
        "approval_evidence_sha256": "5" * 64,
        "asset_id": asset_id,
        "asset_sha256": sha,
        "asset_identity_sha256": identity,
        "material_id": material_id,
        "source_page_url": source_url,
        "resolved_original_url": source_url,
        "discovery_manifest_sha256": "9" * 64,
    }


class _Ctx:
    def __init__(self, run_dir: Path, skills_home: Path, network_mode: str = "live"):
        self.run_dir = run_dir
        self.skills_home = skills_home
        self.network_mode = network_mode
        self.create_wechat_draft = True


class _State:
    topic = "OBS-72 cover test"


def _build_run(tmp_path: Path, *, assets, body_order, upload_success,
               approvals, local_ok=True):
    """assets: {asset_id: bytes}; body_order/upload_success: lists of ids."""
    rd = tmp_path / "run"
    media = rd / "media_enrichment"
    (media / "discover" / "images").mkdir(parents=True, exist_ok=True)
    (media / "continue").mkdir(parents=True, exist_ok=True)
    manifest_assets = []
    for aid, blob in assets.items():
        sha = _sha(blob)
        manifest_assets.append({
            "asset_id": aid, "asset_sha256": sha,
            "asset_identity_sha256": "0" * 64,
            "material_id": "M-01",
            "source_page_url": "https://example.com/a",
            "resolved_original_url": "https://example.com/a",
        })
        # local_ok=False 时文件仍存在但内容被篡改：sha 不匹配（不是缺失）
        (media / "discover" / "images" / f"{sha}.png").write_bytes(blob if local_ok else b"tampered bytes")
    manifest = {"schema_version": "1.0", "assets": manifest_assets,
                "discovery_manifest_sha256": "9" * 64}
    (media / "discover" / "asset_discovery_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    events = [{"asset_id": aid, "status": "success"} for aid in upload_success]
    (media / "continue" / "upload_events.json").write_text(
        json.dumps({"schema_version": "1.0", "events": events}, ensure_ascii=False),
        encoding="utf-8")
    bindings = {"body_images": [{"asset_id": aid} for aid in body_order]}
    (media / "article_image_bindings.json").write_text(
        json.dumps(bindings, ensure_ascii=False), encoding="utf-8")
    (media / "copyright_approval.json").write_text(
        json.dumps({"approvals": list(approvals.values())}, ensure_ascii=False),
        encoding="utf-8")
    # 占位入口：成功路径不执行脚本（run_script 被 monkeypatch），
    # 失败路径 sha256_file(entry) 需要文件存在。
    entry = tmp_path / "skills_home" / "gzh-design" / "scripts" / "publish_wechat_draft.py"
    entry.parent.mkdir(parents=True, exist_ok=True)
    entry.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
    return rd, tmp_path / "skills_home"


def _fake_run(script_path, args, timeout):
    return {
        "script_path": str(script_path), "script_sha256": "1" * 64,
        "command": ["python", str(script_path), *map(str, args)],
        "exit_code": 0, "elapsed_seconds": 0.1,
        "stdout_sha256": "2" * 64, "stderr_sha256": "3" * 64,
        "stdout": "", "stderr": "",
    }


def _run_wechat(tmp_path, monkeypatch, *, assets, body_order, upload_success,
                approvals, local_ok=True):
    rd, skills_home = _build_run(
        tmp_path, assets=assets, body_order=body_order,
        upload_success=upload_success, approvals=approvals, local_ok=local_ok)
    monkeypatch.setattr(PR, "run_script", _fake_run)
    ctx = _Ctx(rd, skills_home, network_mode="live")
    sd = tmp_path / "stage"; sd.mkdir(exist_ok=True)
    return PR._wechat(ctx, "wechat_draft", sd, EM.EXPECTED_OUTPUTS["wechat_draft"],
                      _State())


def test_live_cover_is_first_approved_uploaded_body_asset(tmp_path, monkeypatch):
    blob_a = b"asset A"
    blob_b = b"asset B"
    sha_a = _sha(blob_a)
    approvals = {"A-1": _make_approval("A-1", sha_a)}
    outputs, meta = _run_wechat(
        tmp_path, monkeypatch,
        assets={"A-1": blob_a, "A-2": blob_b},
        body_order=["A-1", "A-2"],
        upload_success=["A-1", "A-2"],
        approvals=approvals)
    assert meta["cover_asset_id"] == "A-1"
    assert "--cover" in meta["entry_run"]["command"]
    cover_arg = meta["entry_run"]["command"][meta["entry_run"]["command"].index("--cover") + 1]
    assert cover_arg.endswith(f"{sha_a}.png")
    assert outputs == []  # 无 draft 产物（run_script 被替换）


def test_live_cover_skips_unapproved_but_blocks_when_only_unapproved(tmp_path, monkeypatch):
    blob_a = b"asset A"
    blob_b = b"asset B"
    sha_b = _sha(blob_b)
    approvals = {"B-2": _make_approval("B-2", sha_b)}
    # A-1 未批准：不在候选池；B-2 批准：成为封面
    outputs, meta = _run_wechat(
        tmp_path, monkeypatch,
        assets={"A-1": blob_a, "B-2": blob_b},
        body_order=["A-1", "B-2"],
        upload_success=["A-1", "B-2"],
        approvals=approvals)
    assert meta["cover_asset_id"] == "B-2"
    # 反向：唯一候选是未批准资产 -> FAIL_CLOSED
    outputs2, meta2 = _run_wechat(
        tmp_path, monkeypatch,
        assets={"A-1": blob_a},
        body_order=["A-1"],
        upload_success=["A-1"],
        approvals=approvals)
    assert meta2["entry_run"]["exit_code"] == 2
    assert "FAIL_CLOSED" in meta2["entry_run"]["stderr"]
    assert "no approved and uploaded asset" in meta2["entry_run"]["stderr"]


def test_live_cover_local_sha_mismatch_fails_closed(tmp_path, monkeypatch):
    blob = b"asset A"
    sha = _sha(blob)
    approvals = {"A-1": _make_approval("A-1", sha)}
    # local_ok=False：本地文件写入的是另一份内容，sha 不匹配
    outputs, meta = _run_wechat(
        tmp_path, monkeypatch,
        assets={"A-1": blob},
        body_order=["A-1"],
        upload_success=["A-1"],
        approvals=approvals,
        local_ok=False)
    assert meta["entry_run"]["exit_code"] == 2
    assert "sha256 mismatch" in meta["entry_run"]["stderr"]


def test_live_cover_approval_sha_diverges_from_manifest_fails_closed(tmp_path, monkeypatch):
    blob = b"asset A"
    approvals = {"A-1": _make_approval("A-1", "d" * 64)}  # 批准记录 sha 与 manifest 不同
    outputs, meta = _run_wechat(
        tmp_path, monkeypatch,
        assets={"A-1": blob},
        body_order=["A-1"],
        upload_success=["A-1"],
        approvals=approvals)
    assert meta["entry_run"]["exit_code"] == 2
    assert "diverges from frozen manifest" in meta["entry_run"]["stderr"]


def test_live_cover_missing_contract_fails_closed(tmp_path, monkeypatch):
    blob = b"asset A"
    sha = _sha(blob)
    outputs, meta = _run_wechat(
        tmp_path, monkeypatch,
        assets={"A-1": blob},
        body_order=["A-1"],
        upload_success=["A-1"],
        approvals={})  # 空批准合同
    assert meta["entry_run"]["exit_code"] == 2
    assert "no stable single_asset approval" in meta["entry_run"]["stderr"]
    # 批准记录存在但上传事件缺失 -> FAIL_CLOSED
    approvals = {"A-1": _make_approval("A-1", sha)}
    outputs2, meta2 = _run_wechat(
        tmp_path, monkeypatch,
        assets={"A-1": blob},
        body_order=["A-1"],
        upload_success=[],
        approvals=approvals)
    assert meta2["entry_run"]["exit_code"] == 2
    assert "no successful upload" in meta2["entry_run"]["stderr"]


def test_fake_live_never_adds_cover_arg(tmp_path, monkeypatch):
    """fake_live 路径行为不变：不加 --cover，保持 --dry-run。"""
    rd, skills_home = _build_run(
        tmp_path, assets={"A-1": b"x"}, body_order=["A-1"],
        upload_success=["A-1"], approvals={})
    monkeypatch.setattr(PR, "run_script", _fake_run)
    ctx = _Ctx(rd, skills_home, network_mode="fake_live")
    sd = tmp_path / "stage"; sd.mkdir()
    outputs, meta = PR._wechat(ctx, "wechat_draft", sd,
                               EM.EXPECTED_OUTPUTS["wechat_draft"], _State())
    assert "--dry-run" in meta["entry_run"]["command"]
    assert "--cover" not in meta["entry_run"]["command"]
    assert "cover_asset_id" not in meta
