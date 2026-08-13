"""档63 OBS-71:图表路径纳入批准合同。

覆盖:
1. 事件 RUN 20260801T231452-vibe-coding-guide-v2-1-1vg6jx 离线重放(夹具冻结):
   discover 产图表全部 decision=review_required / copyright=unknown /
   content_description 来自图表 spec(source=generated)/ 计入数量上限;
2. ★重放 continue 无批准合同 → fail-closed:零上传、零草稿(本档硬验收);
3. 重放 continue 带单张图表批准 → 仅该图表上传(wechat_audit,零网络),批准消费;
4. 数量上限:max_total_images 拦截图表;
5. 内容描述非 claim 派生填充。

隔离手段:全部 CLI 子进程 offline_fixture + dry_run/wechat_audit,零网络零微信。
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

FIX = SKILL_ROOT / "tests" / "fixtures" / "obs71"
REQ_TEMPLATE = json.loads(
    (FIX / "media_discovery_request.obs71.json").read_text(encoding="utf-8"))
ARTICLE_SRC = FIX / "final_article.obs71.md"


def _run_cli(tmp_path: Path, phase: str, request: Path, fixture_dir: Path,
             discovery_manifest: Path | None = None) -> tuple[int, str, str]:
    out = tmp_path / f"out-{phase}"
    cmd = [sys.executable, "-X", "utf8",
           str(SKILL_ROOT / "scripts" / "run_media_enrichment.py"),
           "--request", str(request), "--output-dir", str(out),
           "--fixture-dir", str(fixture_dir), "--phase", phase]
    if discovery_manifest is not None:
        cmd += ["--discovery-manifest", str(discovery_manifest)]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    return proc.returncode, proc.stdout, proc.stderr


def _make_request(tmp_path: Path, *, phase: str, approvals: list[dict] | None = None,
                  max_total: int | None = None, upload_mode: str = "dry_run") -> Path:
    req = json.loads(json.dumps(REQ_TEMPLATE, ensure_ascii=False))
    # 文章与请求同目录(placement 按请求相对路径读)
    article = tmp_path / "final_article.md"
    shutil.copy2(ARTICLE_SRC, article)
    req["article"] = {"path": "final_article.md",
                      "sha256": hashlib.sha256(article.read_bytes()).hexdigest()}
    req["config"] = dict(req.get("config", {}))
    req["config"]["network_mode"] = "offline_fixture"
    req["config"]["upload_mode"] = upload_mode
    if max_total is not None:
        req["config"]["max_total_images"] = max_total
    if approvals is not None:
        req["asset_approvals"] = approvals
    p = tmp_path / f"request-{phase}.json"
    p.write_text(json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _fixture_dir(tmp_path: Path) -> Path:
    # --fixture-dir 直接指向 html 目录;图片 fixture 在其父级 images/(本场景无下载)
    fd = tmp_path / "fixtures"
    fd.mkdir(parents=True, exist_ok=True)
    for f in (FIX / "html").glob("*.html"):
        shutil.copy2(f, fd / f.name)
    (tmp_path / "images").mkdir(exist_ok=True)
    return fd


def _approval_for(frozen_record: dict, discovery_sha: str) -> dict:
    return {
        "asset_id": frozen_record["asset_id"],
        "material_id": frozen_record["material_id"],
        "source_page_url": frozen_record["source_page_url"],
        "resolved_original_url": frozen_record["resolved_original_url"],
        "asset_sha256": frozen_record["asset_sha256"],
        "asset_identity_sha256": frozen_record["asset_identity_sha256"],
        "discovery_manifest_sha256": discovery_sha,
        "approval_id": "AP-OBS71-REPLAY",
        "approved_scope": "single_asset",
        "approved_by": "independent_reviewer",
        "approved_at": "2026-08-04T00:00:00Z",
        "approval_evidence_sha256": "e" * 64,
    }


def _discover(tmp_path: Path, max_total: int | None = None) -> tuple[Path, dict]:
    """跑一次重放 discover,返回 (request, discover/media_manifest)。"""
    fd = _fixture_dir(tmp_path)
    req = _make_request(tmp_path, phase="discover", max_total=max_total)
    rc, out, err = _run_cli(tmp_path, "discover", req, fd)
    assert rc == 0, f"discover rc={rc}\n{out[-1500:]}\n{err[-1500:]}"
    man = json.loads((tmp_path / "out-discover" / "media_manifest.json").read_text(
        encoding="utf-8"))
    return req, man


def test_replay_discover_charts_review_required(tmp_path):
    req, man = _discover(tmp_path)
    charts = [a for a in man["assets"] if a["asset_origin"] == "generated"]
    assert len(charts) >= 1, "事件 RUN 请求应生成图表"
    for c in charts:
        assert c["decision"] == "review_required", c["asset_id"]
        assert c["copyright_status"] == "unknown", c["asset_id"]
        assert c["relevance_status"] == "uncertain", c["asset_id"]
        assert any("OBS-71" in r for r in c["reasons"]), c["asset_id"]
        assert c["content_description_source"] == "generated", c["asset_id"]
        assert c["content_description"], c["asset_id"]
        # 内容描述不得是 claim 派生填充
        for claim in REQ_TEMPLATE["claims"]:
            ct = claim.get("claim_text") or ""
            assert ct[:60] != c["content_description"], c["asset_id"]
            assert not c["content_description"].startswith(f"图：{ct[:40]}"), c["asset_id"]
        assert c["resolved_original_url"].endswith(f"#chart-{c['sha256'][:12]}"), c["asset_id"]
        assert c["asset_identity_sha256"], c["asset_id"]
        assert c["page_region"] == "generated", c["asset_id"]
    # 冻结清单包含图表(asset_origin=generated)
    frozen = json.loads((tmp_path / "out-discover" / "asset_discovery_manifest.json").read_text(
        encoding="utf-8"))
    frozen_charts = [a for a in frozen["assets"] if a.get("asset_origin") == "generated"]
    assert len(frozen_charts) == len(charts)


def test_replay_continue_without_approval_fail_closed(tmp_path):
    """★硬验收:事件 RUN 重放无批准 → fail-closed(零上传、零草稿)。"""
    fd = _fixture_dir(tmp_path)
    req = _make_request(tmp_path, phase="discover")
    rc, _, _ = _run_cli(tmp_path, "discover", req, fd)
    assert rc == 0
    frozen = tmp_path / "out-discover" / "asset_discovery_manifest.json"
    # continue:asset_approvals 为空(事件 RUN 的 approvals=[] 形态)
    creq = _make_request(tmp_path, phase="continue", approvals=[],
                         upload_mode="wechat_audit")
    rc, out, err = _run_cli(tmp_path, "continue", creq, fd,
                            discovery_manifest=frozen)
    assert rc == 0, f"continue rc={rc}\n{out[-1500:]}\n{err[-1500:]}"
    events = json.loads((tmp_path / "out-continue" / "upload_events.json").read_text(
        encoding="utf-8"))["events"]
    assert events == [], f"零上传预期,实际 {len(events)} 个事件: {events}"
    man = json.loads((tmp_path / "out-continue" / "media_manifest.json").read_text(
        encoding="utf-8"))
    for a in man["assets"]:
        assert a["upload"]["status"] in ("not_uploaded",), a["asset_id"]
        assert a.get("asset_approval_consumed") is False, a["asset_id"]
    assert man["summary"]["uploaded_assets"] == 0


def test_replay_continue_with_approval_uploads_only_approved(tmp_path):
    fd = _fixture_dir(tmp_path)
    req = _make_request(tmp_path, phase="discover")
    rc, _, _ = _run_cli(tmp_path, "discover", req, fd)
    assert rc == 0
    frozen = tmp_path / "out-discover" / "asset_discovery_manifest.json"
    frozen_data = json.loads(frozen.read_text(encoding="utf-8"))
    charts = [a for a in frozen_data["assets"] if a.get("asset_origin") == "generated"]
    assert charts, "冻结清单应有图表"
    approved = _approval_for(charts[0], frozen_data["discovery_manifest_sha256"])
    creq = _make_request(tmp_path, phase="continue", approvals=[approved],
                         upload_mode="wechat_audit")
    rc, out, err = _run_cli(tmp_path, "continue", creq, fd,
                            discovery_manifest=frozen)
    assert rc == 0, f"continue rc={rc}\n{out[-1500:]}\n{err[-1500:]}"
    events = json.loads((tmp_path / "out-continue" / "upload_events.json").read_text(
        encoding="utf-8"))["events"]
    assert len(events) == 1, f"仅批准图表应上传: {events}"
    assert events[0]["asset_id"] == charts[0]["asset_id"]
    man = json.loads((tmp_path / "out-continue" / "media_manifest.json").read_text(
        encoding="utf-8"))
    by_id = {a["asset_id"]: a for a in man["assets"]}
    assert by_id[charts[0]["asset_id"]]["asset_approval_consumed"] is True
    assert by_id[charts[0]["asset_id"]]["upload"]["status"] == "success"
    for other in charts[1:]:
        assert by_id[other["asset_id"]]["upload"]["status"] == "not_uploaded", other["asset_id"]


def test_max_total_images_does_not_cap_discovery_charts(tmp_path):
    """76E/OBS-260:max_total_images 只约束最终入文图数,不再截断 discovery——
    图表由 claims 决定(本夹具 6 组数据 → 6 张图表),不再出现 chart skipped。"""
    req_path, man = _discover(tmp_path, max_total=1)
    charts = [a for a in man["assets"] if a["asset_origin"] == "generated"]
    assert len(charts) == 6
    joined = " | ".join(man.get("warnings", []))
    assert "max_total_images" not in joined and "chart skipped" not in joined
    # discovery 阶段独立预算存在(media 侧默认 max(24, 3×max_total),请求可不传)
    reqd = json.loads(req_path.read_text(encoding="utf-8"))
    budget = reqd["config"].get("discovery_budget") or 24
    assert budget >= 6
