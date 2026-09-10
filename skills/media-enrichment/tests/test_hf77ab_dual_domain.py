"""77AB:aihot 域名双前缀适配(OBS-378) + 40164 上传前探针(OBS-379)。

规格 A 测试(①②④+internal_page 接线):
- ①virxact 域条目过三处判定(本文件覆盖分流双校验器+internal_page 接线;
  producers 门在 pipeline 侧 test_hf77ab_guard.py);
- ②aihot.news 域条目同样过(双前缀核心断言——m9coc1 改写场景根除);
- ④media SKILL.md 改写禁令锚点;
- internal_page 判定接线:run_media :1293 重分类判定改用
  AIHOT_SITE_PREFIXES 双前缀(单一真源常量),内联单前缀判定绝版。

规格 B 测试(B.3 +3,真实 probe_token + mock 传输层,在进程内跑真 main()):
- ①mock 40164 探针命中 → FAIL_CLOSED 且文案含 IP+加白指引+「零张上传」;
- ②mock 正常 token → 探针过、批量上传走(断言循环执行);
- ③mock 网络异常 → 不 40164 停机、走既有 token error 路径(不误伤)。

网络边界 mock 说明:探针仅 live 模式触发,故请求 config network_mode=live,
进程内把 fetch_page/download_image/is_safe_url 三入口钉到 fixture 语义
(零真实网络);requests.get/post 由探针/上传自身消费,mock 传输层响应。
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
sys.path.insert(0, str(SKILL_ROOT / "src"))

import run_media_enrichment as runner  # noqa: E402
from validate_media_manifest import validate_manifest  # noqa: E402
from media_enrichment.input_contract import (  # noqa: E402
    compute_file_sha256, validate_request,
)
from media_enrichment.url_security import AIHOT_SITE_PREFIXES  # noqa: E402

VIRXACT = "https://aihot.virxact.com/items/77ab-virxact"
AIHOT_NEWS = "https://aihot.news/items/77ab-news"


# ── 规格 A ①②:分流双校验器(双前缀核心断言)─────────────────────────

def _supplemental_request(permalink) -> dict:
    return {
        "schema_version": "1.0", "run_id": "test-77ab-dual-domain",
        "article": {"path": "article.md", "sha256": "a" * 64},
        "materials": [{
            "material_id": "M-SUP", "aihot_permalink": permalink,
            "source_url": "https://example.org/sup", "title": "T",
            "selected_claim_ids": ["C-01"], "provenance": "supplemental",
        }],
        "claims": [{"claim_id": "C-01", "claim_text": "A", "material_id": "M-SUP",
                    "source_url": "https://example.org/sup", "source_excerpt": "A"}],
        "config": {"network_mode": "offline_fixture", "upload_mode": "dry_run"},
    }


def _input_contract_result(tmp_path: Path, permalink):
    article = tmp_path / "article.md"
    article.write_text("test", encoding="utf-8")
    request = _supplemental_request(permalink)
    request["article"]["sha256"] = compute_file_sha256(article)
    req_path = tmp_path / "request.json"
    req_path.write_text(json.dumps(request, ensure_ascii=False), encoding="utf-8")
    return validate_request(req_path)


def _lane_check(tmp_path: Path, permalink) -> dict:
    manifest_path = tmp_path / "media_manifest.json"
    request_path = tmp_path / "media_request.json"
    article = tmp_path / "final_article.md"
    article.write_text("# 77AB\n\n正文。\n", encoding="utf-8")
    manifest_path.write_text(json.dumps({"schema_version": "1.0"}),
                             encoding="utf-8")
    request_path.write_text(json.dumps(
        {"article": {"path": "final_article.md", "sha256": "a" * 64},
         "materials": [{
             "material_id": "M-SUP", "aihot_permalink": permalink,
             "source_url": "https://example.org/sup", "title": "T",
             "selected_claim_ids": [], "provenance": "supplemental",
         }]}, ensure_ascii=False), encoding="utf-8")
    report = validate_manifest(str(manifest_path), str(request_path))
    return next(c for c in report["checks"]
                if c["check"] == "REQUEST_MATERIAL_PERMALINK_LANE")


def test_77ab_virxact_entry_passes_lane_validators(tmp_path):
    """①virxact 域条目过分流双校验器(input_contract 3f + validate lane)。"""
    result = _input_contract_result(tmp_path, VIRXACT)
    assert result.valid, f"Errors: {result.errors}"
    lane_dir = tmp_path / "lane"
    lane_dir.mkdir()
    check = _lane_check(lane_dir, VIRXACT)
    assert check["status"] == "PASS", check["detail"]


def test_77ab_aihot_news_entry_passes_lane_validators(tmp_path):
    """②aihot.news 域条目同样过(双前缀核心断言——m9coc1 改写场景根除)。"""
    result = _input_contract_result(tmp_path, AIHOT_NEWS)
    assert result.valid, f"Errors: {result.errors}"
    lane_dir = tmp_path / "lane"
    lane_dir.mkdir()
    check = _lane_check(lane_dir, AIHOT_NEWS)
    assert check["status"] == "PASS", check["detail"]


# ── 规格 A ①②:internal_page 判定接线(单一真源常量)─────────────────

def test_77ab_internal_page_gate_dual_prefix_wiring():
    """①②internal_page 判定改双前缀:常量含两域,判定接线到常量,
    三处判定文件内联单前缀字面量绝版。"""
    assert AIHOT_SITE_PREFIXES == (
        "https://aihot.virxact.com/", "https://aihot.news/")
    src = (SKILL_ROOT / "scripts" / "run_media_enrichment.py").read_text(
        encoding="utf-8")
    # 重分类块 :1293 判定接线到常量(双前缀 any 形态)
    assert 'internal_page=any((asset.source_page_url or "").startswith(' in src
    assert "for p in AIHOT_SITE_PREFIXES)," in src
    # 三处判定文件内联单前缀判定绝版(77AB/OBS-378)
    for rel in ("scripts/run_media_enrichment.py",
                "src/media_enrichment/input_contract.py",
                "scripts/validate_media_manifest.py"):
        text = (SKILL_ROOT / rel).read_text(encoding="utf-8")
        assert '"https://aihot.virxact.com/"' not in text, (
            f"{rel} 仍残留内联单前缀判定字面量")


# ── 规格 A ④:media SKILL.md 改写禁令锚点────────────────────────────

def test_77ab_skill_md_domain_rewrite_ban_anchor():
    """④media SKILL.md 含禁改写上游域名明规(77AB/OBS-378 措辞锚点)。"""
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "记录层禁止改写上游返回的域名" in text
    assert "permalink/links 各字段保留上游返回原值" in text
    assert "77AB/OBS-378" in text
    assert "门的职责是兼容双域，不是倒逼改写" in text


# ── 规格 B:40164 上传前探针(B.3 测试 +3)───────────────────────────

class _FakeResp:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def _make_fixture(root: Path, slug: str, image_name: str,
                  color: tuple[int, int, int]) -> None:
    from PIL import Image
    html = root / "html"
    images = root / "images"
    html.mkdir(parents=True, exist_ok=True)
    images.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (1000, 700), color).save(images / image_name, "PNG")
    (html / f"{slug}.html").write_text(
        "<!doctype html><html><body><article>"
        "<p>relevant body figure</p>"
        f'<img src="https://img.example-source.test/{image_name}" '
        'alt="relevant body figure">'
        "</article></body></html>",
        encoding="utf-8",
    )


def _live_request(tmp_path: Path) -> Path:
    article = tmp_path / "final_article.md"
    article.write_text("# title\n\nrelevant body figure\n", encoding="utf-8")
    material = {
        "material_id": "M-001",
        "aihot_permalink": "https://aihot.news/items/77ab-probe",
        "source_url": "https://source.example.test/77ab-probe",
        "title": "77ab", "selected_claim_ids": ["C-01"],
        "copyright_review": {
            "status": "known_allowed", "reviewed_by": "scope-reviewer",
            "reviewed_at": "2026-09-10T00:00:00Z", "evidence": "e" * 64,
            "approval_id": "AP-material", "approved_scope": "material",
        },
    }
    payload = {
        "schema_version": "1.0", "run_id": "77ab-probe-e2e",
        "article": {"path": "final_article.md",
                    "sha256": hashlib.sha256(article.read_bytes()).hexdigest()},
        "materials": [material],
        "claims": [{"claim_id": "C-01", "claim_text": "relevant body figure",
                    "material_id": "M-001",
                    "source_url": material["source_url"],
                    "source_excerpt": "relevant body figure"}],
        "config": {
            # 探针仅 live 触发(77AB/OBS-379 规格:fake/offline 不触网)
            "network_mode": "live", "upload_mode": "wechat_image_host",
            "max_images_per_material": 4, "max_total_images": 8,
            "allow_unknown_license_for_publish": False,
        },
    }
    path = tmp_path / "media_request.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return path


def _pin_offline_network(monkeypatch, fixture: Path):
    """把 live 请求的三处网络入口钉到 fixture 语义(零真实网络)。"""
    from media_enrichment.page_fetcher import fetch_page as _real_fetch
    from media_enrichment.downloader import download_image as _real_download
    from media_enrichment.url_security import URLSecurityResult

    monkeypatch.setattr(
        runner, "fetch_page",
        lambda url, mode="live", fixture_dir=None, timeout=15:
            _real_fetch(url, mode="offline_fixture", fixture_dir=fixture_dir,
                        timeout=timeout))
    monkeypatch.setattr(
        runner, "download_image",
        lambda url, images_dir, max_bytes=15728640, mode="live",
               fixture_dir=None:
            _real_download(url, images_dir, max_bytes=max_bytes,
                           mode="offline_fixture", fixture_dir=fixture_dir))
    monkeypatch.setattr(
        runner, "is_safe_url",
        lambda url, require_dns=True:
            URLSecurityResult(safe=True, url=url, reasons=[]))


def _run_phase(monkeypatch, tmp_path: Path, fixture: Path, request: Path,
               phase: str, frozen: Path | None = None) -> tuple[int, dict, dict]:
    out = tmp_path / f"out-{phase}"
    argv = ["run_media_enrichment.py", "--request", str(request),
            "--output-dir", str(out), "--fixture-dir", str(fixture / "html"),
            "--phase", phase]
    if frozen is not None:
        argv.extend(["--discovery-manifest", str(frozen)])
    monkeypatch.setattr(sys, "argv", argv)
    code = None
    try:
        runner.main()
    except SystemExit as exc:
        code = exc.code
    manifest = json.loads(
        (out / "media_manifest.json").read_text(encoding="utf-8"))
    events = json.loads(
        (out / "upload_events.json").read_text(encoding="utf-8"))
    return code, manifest, events


def _probe_e2e(monkeypatch, tmp_path, get_payload):
    """discover(真实)+continue(探针路径);requests.get 由 payload/异常驱动。"""
    import requests
    fixture = tmp_path / "fixture"
    _make_fixture(fixture, "77ab-probe", "probe-a.png", (210, 40, 40))
    request = _live_request(tmp_path)
    _pin_offline_network(monkeypatch, fixture)
    monkeypatch.setenv("WECHAT_APP_ID", "wx77ab")
    monkeypatch.setenv("WECHAT_APP_SECRET", "sec77ab")

    post_calls: list = []

    def _fake_post(url, files=None, timeout=30, **kw):
        post_calls.append(url)
        return _FakeResp(200, {"url": "https://mmbiz.qpic.cn/mmbiz_png/"
                                     "77abprobe/640?wx_fmt=png"})

    if isinstance(get_payload, Exception):
        def _fake_get(url, params=None, timeout=10, **kw):
            raise get_payload
    else:
        def _fake_get(url, params=None, timeout=10, **kw):
            return _FakeResp(200, get_payload)

    monkeypatch.setattr(requests, "get", _fake_get)
    monkeypatch.setattr(requests, "post", _fake_post)
    # discover(无上传,dry_run 强制)——探针不触发,断基线资产可上传
    code0, _, _ = _run_phase(monkeypatch, tmp_path, fixture, request, "discover")
    assert code0 == 0
    code, manifest, events = _run_phase(
        monkeypatch, tmp_path, fixture, request, "continue",
        tmp_path / "out-discover" / "asset_discovery_manifest.json")
    return code, manifest, events, post_calls


def test_77ab_probe_40164_fail_closed(monkeypatch, tmp_path):
    """B.3①:mock 40164 探针命中 → FAIL_CLOSED,文案含 IP+加白指引+
    「零张上传」;上传循环整体跳过(requests.post 零调用)。"""
    code, manifest, events, post_calls = _probe_e2e(
        monkeypatch, tmp_path,
        {"errcode": 40164,
         "errmsg": "invalid ip 183.221.7.130 ipv6 ::, not in whitelist, "
                   "request from 183.221.7.130"})
    assert code == 1
    errors = manifest.get("errors") or []
    err = next(e for e in errors if "77AB/OBS-379" in e)
    assert "183.221.7.130" in err
    assert "IP 白名单" in err and "设置与开发→基本配置" in err
    assert "零张上传" in err
    assert "errmsg 原文: invalid ip 183.221.7.130" in err
    assert not any("upload failed for" in e for e in errors), errors
    assert events["events"] == []           # 零张上传(事件零条)
    assert post_calls == []                 # 上传端点零调用
    probe = events["token_probe"]
    assert probe["ok"] is False and probe["errcode"] == 40164
    assert probe["ip"] == "183.221.7.130"
    assert probe["endpoint_path"] == "/cgi-bin/token"


def test_77ab_probe_ok_uploads_proceed(monkeypatch, tmp_path):
    """B.3②:mock 正常 token → 探针过(ok=True),批量上传循环照走。"""
    code, manifest, events, post_calls = _probe_e2e(
        monkeypatch, tmp_path, {"access_token": "TK-77ab"})
    assert code == 0, manifest.get("errors")
    assert len(post_calls) == 1             # uploadimg 循环执行(1/1)
    assert [e["asset_id"] for e in events["events"]] == ["A-001"]
    assert events["events"][0]["status"] == "success"
    assert events["token_probe"]["ok"] is True
    asset = next(a for a in manifest["assets"] if a["asset_origin"] == "source")
    assert asset["upload"]["status"] == "success"


def test_77ab_probe_network_error_existing_path(monkeypatch, tmp_path):
    """B.3③:mock 网络异常 → 非 40164 不停机,走既有 per-asset token error
    路径(不误伤):循环执行、错误来自既有 upload failed 通道。"""
    import requests as _requests
    code, manifest, events, post_calls = _probe_e2e(
        monkeypatch, tmp_path,
        _requests.exceptions.ConnectionError("simulated probe network down"))
    assert code == 1
    errors = manifest.get("errors") or []
    assert not any("77AB/OBS-379" in e for e in errors), errors
    assert any("upload failed for A-001" in e for e in errors), errors
    assert len(events["events"]) == 1        # 循环执行(既有路径逐资产报错)
    assert events["events"][0]["status"] == "failed"
    assert events["token_probe"]["ok"] is False
    assert events["token_probe"]["errcode"] is None
    assert "token request failed" in events["token_probe"]["errmsg"]
