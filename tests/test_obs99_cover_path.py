"""档70 OBS-99:封面本地文件定位 —— 候选目录集合 + 交叉验证回归测试。

覆盖(档70 第 3.1 条):
a. ★generated 图表作封面(文件在 discover/charts/) -> PASS ← 本次真实场景
b. ★网页图作封面(文件在 discover/images/) -> 仍 PASS(OBS-72 原语义不回退)
c. local_path 指向 RUN 目录之外 -> FAIL_CLOSED
d. 文件不存在 -> FAIL_CLOSED(原语义保留)
e. 文件存在但 sha256 不等于冻结值 -> FAIL_CLOSED
f. 资产未批准 / 无 success 上传记录 -> FAIL_CLOSED(原语义保留)
g. local_path 记录值与实际命中文件不一致 -> FAIL_CLOSED

全部走 live 分支但 monkeypatch run_script,零真实微信副作用。
"""
import hashlib
import json
from pathlib import Path

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
    topic = "OBS-99 cover path test"


def _build_run(tmp_path: Path, *, assets, body_order, upload_success,
               approvals, origins=None, local_paths=None,
               file_missing=False, tampered=False):
    """assets: {asset_id: bytes}; origins: {asset_id: 'generated'|'source'};
    local_paths: {asset_id: str|Path} 可选(写入 media_manifest 记录)。"""
    rd = tmp_path / "run"
    media = rd / "media_enrichment"
    (media / "discover" / "images").mkdir(parents=True, exist_ok=True)
    (media / "discover" / "charts").mkdir(parents=True, exist_ok=True)
    (media / "continue").mkdir(parents=True, exist_ok=True)
    origins = origins or {}
    local_paths = local_paths or {}
    manifest_assets = []
    full_assets = []
    for aid, blob in assets.items():
        sha = _sha(blob)
        origin = origins.get(aid, "source")
        subdir = "charts" if origin == "generated" else "images"
        manifest_assets.append({
            "asset_id": aid, "asset_sha256": sha,
            "asset_identity_sha256": "0" * 64,
            "asset_origin": origin,
            "material_id": "M-01",
            "source_page_url": "https://example.com/a",
            "resolved_original_url": "https://example.com/a",
        })
        full_assets.append({
            "asset_id": aid, "asset_sha256": sha,
            "asset_origin": origin,
            "local_path": str(local_paths.get(aid, media / "discover" / subdir / f"{sha}.png")),
        })
        if not file_missing:
            content = b"tampered bytes" if tampered else blob
            (media / "discover" / subdir / f"{sha}.png").write_bytes(content)
    manifest = {"schema_version": "1.0", "assets": manifest_assets,
                "discovery_manifest_sha256": "9" * 64}
    (media / "discover" / "asset_discovery_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    full = {"schema_version": "1.0", "assets": full_assets}
    (media / "discover" / "media_manifest.json").write_text(
        json.dumps(full, ensure_ascii=False), encoding="utf-8")
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


def _run_wechat(tmp_path, monkeypatch, **kwargs):
    rd, skills_home = _build_run(tmp_path, **kwargs)
    monkeypatch.setattr(PR, "run_script", _fake_run)
    ctx = _Ctx(rd, skills_home, network_mode="live")
    sd = tmp_path / "stage"; sd.mkdir(exist_ok=True)
    return PR._wechat(ctx, "wechat_draft", sd, EM.EXPECTED_OUTPUTS["wechat_draft"],
                      _State())


def _cover_arg(meta):
    cmd = meta["entry_run"]["command"]
    return cmd[cmd.index("--cover") + 1]


# a. ★generated 图表作封面(charts/ 目录) -> PASS
def test_obs99_generated_chart_cover_passes(tmp_path, monkeypatch):
    blob = b"chart png bytes"
    sha = _sha(blob)
    approvals = {"A-5": _make_approval("A-5", sha)}
    outputs, meta = _run_wechat(
        tmp_path, monkeypatch,
        assets={"A-5": blob},
        body_order=["A-5"],
        upload_success=["A-5"],
        approvals=approvals,
        origins={"A-5": "generated"})
    assert meta["cover_asset_id"] == "A-5"
    assert "--cover" in meta["entry_run"]["command"]
    cover = _cover_arg(meta)
    assert "discover" in cover and "charts" in cover
    assert cover.endswith(f"{sha}.png")
    assert meta["entry_run"]["exit_code"] == 0


# b. 网页图作封面(images/ 目录) -> 仍 PASS
def test_obs99_source_image_cover_passes(tmp_path, monkeypatch):
    blob = b"web jpg bytes"
    sha = _sha(blob)
    approvals = {"A-1": _make_approval("A-1", sha)}
    outputs, meta = _run_wechat(
        tmp_path, monkeypatch,
        assets={"A-1": blob},
        body_order=["A-1"],
        upload_success=["A-1"],
        approvals=approvals,
        origins={"A-1": "source"})
    assert meta["cover_asset_id"] == "A-1"
    cover = _cover_arg(meta)
    assert "images" in cover
    assert cover.endswith(f"{sha}.png")
    assert meta["entry_run"]["exit_code"] == 0


# c. local_path 指向 RUN 目录之外 -> FAIL_CLOSED
def test_obs99_local_path_outside_run_fails_closed(tmp_path, monkeypatch):
    blob = b"chart bytes"
    sha = _sha(blob)
    approvals = {"A-5": _make_approval("A-5", sha)}
    outside = tmp_path / "outside" / "chart-001.png"
    outputs, meta = _run_wechat(
        tmp_path, monkeypatch,
        assets={"A-5": blob},
        body_order=["A-5"],
        upload_success=["A-5"],
        approvals=approvals,
        origins={"A-5": "generated"},
        local_paths={"A-5": outside})
    assert meta["entry_run"]["exit_code"] == 2
    assert "local_path outside media_root" in meta["entry_run"]["stderr"]


# d. 文件不存在 -> FAIL_CLOSED
def test_obs99_file_missing_fails_closed(tmp_path, monkeypatch):
    blob = b"chart bytes"
    sha = _sha(blob)
    approvals = {"A-5": _make_approval("A-5", sha)}
    outputs, meta = _run_wechat(
        tmp_path, monkeypatch,
        assets={"A-5": blob},
        body_order=["A-5"],
        upload_success=["A-5"],
        approvals=approvals,
        origins={"A-5": "generated"},
        file_missing=True)
    assert meta["entry_run"]["exit_code"] == 2
    assert "local frozen file missing" in meta["entry_run"]["stderr"]


# e. 文件存在但 sha256 不等于冻结值 -> FAIL_CLOSED
def test_obs99_file_sha_mismatch_fails_closed(tmp_path, monkeypatch):
    blob = b"chart bytes"
    sha = _sha(blob)
    approvals = {"A-5": _make_approval("A-5", sha)}
    outputs, meta = _run_wechat(
        tmp_path, monkeypatch,
        assets={"A-5": blob},
        body_order=["A-5"],
        upload_success=["A-5"],
        approvals=approvals,
        origins={"A-5": "generated"},
        tampered=True)
    assert meta["entry_run"]["exit_code"] == 2
    assert "sha256 mismatch" in meta["entry_run"]["stderr"]


# f1. 资产未批准 -> FAIL_CLOSED
def test_obs99_unapproved_asset_fails_closed(tmp_path, monkeypatch):
    blob = b"chart bytes"
    approvals = {}
    outputs, meta = _run_wechat(
        tmp_path, monkeypatch,
        assets={"A-5": blob},
        body_order=["A-5"],
        upload_success=["A-5"],
        approvals=approvals,
        origins={"A-5": "generated"})
    assert meta["entry_run"]["exit_code"] == 2
    assert "no stable single_asset approval" in meta["entry_run"]["stderr"]


# f2. 无 success 上传记录 -> FAIL_CLOSED
def test_obs99_no_upload_event_fails_closed(tmp_path, monkeypatch):
    blob = b"chart bytes"
    sha = _sha(blob)
    approvals = {"A-5": _make_approval("A-5", sha)}
    outputs, meta = _run_wechat(
        tmp_path, monkeypatch,
        assets={"A-5": blob},
        body_order=["A-5"],
        upload_success=[],
        approvals=approvals,
        origins={"A-5": "generated"})
    assert meta["entry_run"]["exit_code"] == 2
    assert "no successful upload" in meta["entry_run"]["stderr"]


# g. local_path 记录值与实际命中文件不一致 -> FAIL_CLOSED
def test_obs99_local_path_mismatch_hit_file_fails_closed(tmp_path, monkeypatch):
    blob = b"chart bytes"
    sha = _sha(blob)
    approvals = {"A-5": _make_approval("A-5", sha)}
    # 记录 local_path 指向 charts/ 下另一个文件;实际命中 charts/<sha>.png
    other = tmp_path / "run" / "media_enrichment" / "discover" / "charts" / "other.png"
    other.parent.mkdir(parents=True, exist_ok=True)
    other.write_bytes(b"other file bytes")
    outputs, meta = _run_wechat(
        tmp_path, monkeypatch,
        assets={"A-5": blob},
        body_order=["A-5"],
        upload_success=["A-5"],
        approvals=approvals,
        origins={"A-5": "generated"},
        local_paths={"A-5": other})
    assert meta["entry_run"]["exit_code"] == 2
    assert "local_path record does not match hit file" in meta["entry_run"]["stderr"]


# a2. ★真实命名场景:图表文件为 chart-NNN.png(非 <sha> 命名),local_path 定位
def test_obs99_generated_chart_real_naming_passes(tmp_path, monkeypatch):
    blob = b"chart png bytes real naming"
    sha = _sha(blob)
    approvals = {"A-5": _make_approval("A-5", sha)}
    rd, skills_home = _build_run(
        tmp_path,
        assets={"A-5": blob},
        body_order=["A-5"],
        upload_success=["A-5"],
        approvals=approvals,
        origins={"A-5": "generated"},
        local_paths={"A-5": tmp_path / "run" / "media_enrichment" / "discover" / "charts" / "chart-001.png"})
    # 用真实命名:先删掉 <sha>.png,再建 chart-001.png
    (rd / "media_enrichment" / "discover" / "charts" / f"{sha}.png").unlink()
    (rd / "media_enrichment" / "discover" / "charts" / "chart-001.png").write_bytes(blob)
    monkeypatch.setattr(PR, "run_script", _fake_run)
    ctx = _Ctx(rd, skills_home, network_mode="live")
    sd = tmp_path / "stage"; sd.mkdir(exist_ok=True)
    outputs, meta = PR._wechat(ctx, "wechat_draft", sd,
                               EM.EXPECTED_OUTPUTS["wechat_draft"], _State())
    assert meta["cover_asset_id"] == "A-5"
    cover = _cover_arg(meta)
    assert "chart-001.png" in cover
    assert meta["entry_run"]["exit_code"] == 0
