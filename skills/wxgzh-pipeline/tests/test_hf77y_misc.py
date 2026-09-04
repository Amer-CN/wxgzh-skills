"""77Y 杂项:G version_check 三态留痕(+1)/H aihot 合成条目自检(+1)/D rejected
一等公民守卫(+2,media continue E2E 经 media runner 子进程,零网络零微信)。
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest  # noqa: F401

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import wxgzh_pipeline.producers as PR  # noqa: E402
from conftest import SKILL_ROOT, SKILLS_HOME  # noqa: E402
from wxgzh_pipeline.state import load_state  # noqa: E402

MEDIA_ROOT = SKILLS_HOME / "media-enrichment"
MEDIA_RUNNER = MEDIA_ROOT / "scripts" / "run_media_enrichment.py"

INTERNAL_URL = "https://aihot.example/items/d77y"
SOURCE_URL = "https://www.example-source.test/d77y-original"


# ── 规格 G:version_check 三态留痕(77Y/OBS-372,+1)──────────────────────

def test_77y_version_check_current_recorded_in_state(orch, monkeypatch):
    """current 也留痕:st.version_check.status=current 落 pipeline_state.json
    (三态 current/behind+allow-stale/unknown 与 skipped 全可辨,不再静默)。"""
    monkeypatch.delenv("WXGZH_SKIP_VERSION_CHECK", raising=False)
    payload = {"status": "current", "latest": "v2026.01.01-old",
               "current": {"baseline_date": "2026-09-02"},
               "detail": "mock current"}
    real_run = subprocess.run

    def fake_run(cmd, *args, **kwargs):
        if any("version_check.py" in str(x) for x in (cmd or [])):
            return subprocess.CompletedProcess(
                cmd, 0, stdout=json.dumps(payload, ensure_ascii=False) + "\n",
                stderr="")
        return real_run(cmd, *args, **kwargs)

    monkeypatch.setattr(subprocess, "run", fake_run)
    out = orch.run("t")
    assert out["status"] == "COMPLETE"
    assert out["version_check"]["status"] == "current"
    st = load_state(Path(out["run_dir"]))
    assert st.version_check["status"] == "current"
    raw = json.loads((Path(out["run_dir"]) / "pipeline_state.json")
                     .read_text(encoding="utf-8"))
    assert raw["version_check"]["status"] == "current"


# ── 规格 H:aihot 合成条目契约自检(77Y/OBS-373,+1)──────────────────────

def test_77y_aihot_synthetic_original_story_page_rejected(tmp_path):
    """合成条目 original=aihot story 页 → ACK 前自检拒(列 id+缺什么);
    supplemental null permalink 按 77X 分流放行;非合成缺 original 拒。"""
    items = [
        {"id": "cmok123", "title": "正常条目", "source_url": "https://x.test/a",
         "links": {"aihot": "https://aihot.virxact.com/items/cmok123",
                   "original": "https://x.test/a"}},
        # 0srcql/nlmrly 二咬实证原形:非 cm 前缀合成条目,story 页 URL 冒充 original
        {"id": "story-digest-7cf4cd3a", "title": "合成条目", "provenance": "normal",
         "links": {"aihot": "https://aihot.virxact.com/story/7cf4cd3a",
                   "original": "https://aihot.virxact.com/story/7cf4cd3a"}},
    ]
    (tmp_path / "deduplicated_items.json").write_text(
        json.dumps(items, ensure_ascii=False), encoding="utf-8")
    violations = PR._aihot_synthetic_original_check(tmp_path)
    assert len(violations) == 1
    assert "story-digest-7cf4cd3a" in violations[0]
    assert "冒充" in violations[0] and "77Y/OBS-373" in violations[0]

    # supplemental + permalink null → 77X 分流允许
    ok_dir = tmp_path / "ok"
    ok_dir.mkdir()
    (ok_dir / "deduplicated_items.json").write_text(json.dumps([
        {"id": "story-sup", "provenance": "supplemental",
         "links": {"original": None}},
    ], ensure_ascii=False), encoding="utf-8")
    assert PR._aihot_synthetic_original_check(ok_dir) == []

    # 非 cm 前缀且非 supplemental、缺 links.original → 拒并缺什么
    miss_dir = tmp_path / "miss"
    miss_dir.mkdir()
    (miss_dir / "deduplicated_items.json").write_text(json.dumps([
        {"id": "story-nolink", "provenance": "normal"},
    ], ensure_ascii=False), encoding="utf-8")
    miss = PR._aihot_synthetic_original_check(miss_dir)
    assert len(miss) == 1 and "story-nolink" in miss[0] and "缺 links.original" in miss[0]


# ── 裁决 3(规格 C 闭环):user_action 经 producers 透传到 media_request ──

def test_77y_user_action_retained_in_media_request(tmp_path):
    """77Y/OBS-371 闭环:user 车道+user_action 三要素经 producers 组装后保留进
    media_request(与 77X/OBS-363 basis 条件透传同法);无 user_action 不携带键。"""
    from test_hf77x_misc import _build_continue_request, _single_asset_approval
    ua = {"user": "operator-a", "action": "approved",
          "at": "2026-09-05T12:00:00Z"}
    req = _build_continue_request(tmp_path, [
        _single_asset_approval("A-77Y-1", "user", None) | {"user_action": ua}])
    approvals = req["asset_approvals"]
    assert len(approvals) == 1
    assert approvals[0]["approved_by"] == "user"
    assert approvals[0]["user_action"] == ua
    # user 车道无 user_action:不携带该键、不报错(77X user 无 basis 同型)
    n2 = tmp_path / "n2"
    n2.mkdir()
    req2 = _build_continue_request(n2, [
        _single_asset_approval("A-77Y-2", "user", None)])
    approvals2 = req2["asset_approvals"]
    assert len(approvals2) == 1
    assert "user_action" not in approvals2[0]


# ── 规格 D:rejected 一等公民守卫(77Y/OBS-368,+2;media continue E2E)────

def _mk_media_fixture(tmp_path: Path) -> Path:
    """html=3 图:1 可批(d77y-ok.png)+ 2 必拒(黑名单域 img.ithome.com /
    动态分享卡端点 opengraph-image);images 目录喂离线下载。"""
    root = tmp_path / "mfixture"
    (root / "html").mkdir(parents=True)
    (root / "images").mkdir(parents=True)
    from PIL import Image
    Image.new("RGB", (900, 600), (11, 99, 177)).save(
        root / "images" / "d77y-ok.png", "PNG")
    (root / "html" / "d77y.html").write_text(
        "<!doctype html><html><head><title>77Y D 守卫</title></head>"
        "<body><article><h1>77Y</h1>"
        '<img src="https://img.example-source.test/d77y-ok.png">'
        '<img src="https://img.ithome.com/d77y-bad.png">'
        '<img src="https://aihot.virxact.com/items/d77y/opengraph-image-abc123">'
        "</article></body></html>", encoding="utf-8")
    return root / "html"


def _mk_media_request(tmp_path: Path) -> Path:
    article = tmp_path / "final_article.md"
    article.write_text("# 77Y D 守卫\n\n正文段落。\n", encoding="utf-8")
    req = {
        "schema_version": "1.0", "run_id": "hf77y-rejected-first-class",
        "article": {"path": str(article),
                    "sha256": hashlib.sha256(article.read_bytes()).hexdigest()},
        "materials": [{"material_id": "M-77Y", "aihot_permalink": INTERNAL_URL,
                       "aihot_internal_url": INTERNAL_URL,
                       "source_url": SOURCE_URL, "title": "77Y 素材",
                       "selected_claim_ids": ["C-77Y"],
                       "copyright_review": {"status": "unknown"}}],
        "claims": [{"claim_id": "C-77Y", "claim_text": "77Y D 守卫",
                    "material_id": "M-77Y", "source_url": SOURCE_URL,
                    "source_excerpt": "77Y 素材"}],
        "asset_approvals": [],
        "config": {"network_mode": "offline_fixture", "upload_mode": "wechat_audit",
                   "max_images_per_material": 8, "max_total_images": 8,
                   "min_width": 480, "min_height": 200,
                   "domain_blacklist": ["ithome.com", "img.ithome.com"]},
    }
    p = tmp_path / "media_request.json"
    p.write_text(json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def _run_media(tmp_path: Path, fixture_html: Path, request: Path, phase: str,
               discovery_manifest: Path | None = None):
    out = tmp_path / f"out-{phase}"
    cmd = [sys.executable, "-X", "utf8", str(MEDIA_RUNNER),
           "--request", str(request), "--output-dir", str(out),
           "--fixture-dir", str(fixture_html), "--phase", phase]
    if discovery_manifest is not None:
        cmd.extend(["--discovery-manifest", str(discovery_manifest)])
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=180)
    manifest = json.loads((out / "media_manifest.json").read_text(encoding="utf-8"))
    discovery = json.loads(
        (out / "asset_discovery_manifest.json").read_text(encoding="utf-8"))
    return proc, manifest, discovery


def _auto_rule_approval(discovery: dict, asset_id: str) -> dict:
    asset = next(a for a in discovery["assets"] if a["asset_id"] == asset_id)
    record = dict(asset)
    record.update({
        "discovery_manifest_sha256": discovery["discovery_manifest_sha256"],
        "approval_id": f"AP-{asset_id}", "approved_scope": "single_asset",
        "approved_by": "auto_rule", "approved_at": "2026-09-05T00:00:00Z",
        "approval_evidence_sha256": "e" * 64,
        # 0srcql 式手填 basis(死条款引用)——77Y/OBS-366 机械值应替代之
        "basis": "04 合同 copyright_policy 节 USER_BLANKET_APPROVAL=true",
    })
    return record


def test_77y_partial_reject_partial_approve_no_fail(tmp_path):
    """①3 资产:1 批(auto_rule+手填死条款 basis)2 拒带理由 → 无 FAIL;
    机械 basis 替代手填值留痕(77Y/OBS-366)。"""
    fixture_html = _mk_media_fixture(tmp_path)
    req = _mk_media_request(tmp_path)
    proc, man_d, discovery = _run_media(tmp_path, fixture_html, req, "discover")
    assert proc.returncode == 0, proc.stdout[-1200:] + proc.stderr[-1200:]
    rejected = [a for a in man_d["assets"] if a["decision"] == "rejected"]
    candidates = [a for a in man_d["assets"]
                  if a["decision"] in ("review_required", "eligible")]
    assert len(rejected) == 2 and len(candidates) == 1
    assert all(a["reasons"] for a in rejected), "rejected 必须带理由"
    # 证据链在案:continue 输出目录父级放 approval_readiness.json(approvable=true)
    (tmp_path / "approval_readiness.json").write_text(json.dumps({
        "assets": [{"asset_id": candidates[0]["asset_id"], "approvable": True}],
    }, ensure_ascii=False), encoding="utf-8")
    target_id = candidates[0]["asset_id"]
    reqd = json.loads(req.read_text(encoding="utf-8"))
    reqd["asset_approvals"] = [_auto_rule_approval(discovery, target_id)]
    req.write_text(json.dumps(reqd, ensure_ascii=False, indent=2), encoding="utf-8")
    proc2, man, _ = _run_media(tmp_path, fixture_html, req, "continue",
                               tmp_path / "out-discover" / "asset_discovery_manifest.json")
    assert proc2.returncode == 0, proc2.stdout[-1200:] + proc2.stderr[-1200:]
    assert not any("FAIL_CLOSED" in e for e in man["errors"])
    target = next(a for a in man["assets"] if a["asset_id"] == target_id)
    assert target["asset_approval_consumed"] is True
    assert target["approved_by"] == "auto_rule"
    # 手填死条款 basis 被机械值替代(04 合同实时值入账留痕)
    assert "basis regenerated mechanically (77Y/OBS-366)" in target["reasons"]
    assert any("COPYRIGHT_POLICY=ALLOW_UNLESS_EXPLICITLY_PROHIBITED" in r
               and "USER_BLANKET_APPROVAL=False" in r for r in target["reasons"])


def test_77y_unhandled_candidate_still_fail_closed(tmp_path):
    """②存活未处置(候选无批准无拒绝)→ FAIL_CLOSED,文案指路 77Y/OBS-368。"""
    fixture_html = _mk_media_fixture(tmp_path)
    req = _mk_media_request(tmp_path)
    proc, _, discovery = _run_media(tmp_path, fixture_html, req, "discover")
    assert proc.returncode == 0, proc.stdout[-1200:] + proc.stderr[-1200:]
    proc2, man, _ = _run_media(tmp_path, fixture_html, req, "continue",
                               tmp_path / "out-discover" / "asset_discovery_manifest.json")
    assert proc2.returncode != 0
    joined = "\n".join(man["errors"])
    assert "upload candidates without approval basis (FAIL_CLOSED)" in joined
    assert "77Y/OBS-368" in joined and "存活未处置" in joined
