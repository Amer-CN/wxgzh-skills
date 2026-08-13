#!/usr/bin/env python3
"""dev2-hotfix2 tests: EXACT WeChat host gate + upload event log.

Negative host cases that MUST fail everywhere (bindings builder, official
validator, uploader normalization):
  https://evil.example/?x=mmbiz.qpic.cn
  https://mmbiz.qpic.cn.evil.example/a.png
  https://evil.example/mmbiz.qlogo.cn/a.png
  https://mmbiz.qpic.cn@evil.example/a.png
  http://mmbiz.qpic.cn/a.png
"""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from media_enrichment.article_bindings import _is_wechat_url, build_bindings
from media_enrichment.uploader import (MockUploader, normalize_wechat_url,
                                       timed_upload)

EVIL_URLS = [
    "https://evil.example/?x=mmbiz.qpic.cn",
    "https://mmbiz.qpic.cn.evil.example/a.png",
    "https://evil.example/mmbiz.qlogo.cn/a.png",
    "https://mmbiz.qpic.cn@evil.example/a.png",
    "http://mmbiz.qpic.cn/a.png",
]
GOOD_URLS = [
    "https://mmbiz.qpic.cn/mmbiz_png/abc/640?wx_fmt=png",
    "https://mmbiz.qlogo.cn/x/0",
]


def _load_validator():
    p = SKILL_ROOT / "scripts" / "validate_media_manifest.py"
    spec = importlib.util.spec_from_file_location("validate_media_manifest", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _asset(remote):
    return {"asset_id": "A-001", "asset_origin": "source", "decision": "eligible",
            "sha256": "a" * 64, "material_ids": ["M-001"], "claim_ids": ["C-01"],
            "placement": {"anchor": "## 一", "position": "after", "confidence": 0.9},
            "upload": {"mode": "wechat_audit", "status": "success",
                       "remote_url": remote, "response_sha256": "b" * 64}}


class TestExactHostGate:
    def test_bindings_builder_rejects_evil_urls(self):
        for url in EVIL_URLS:
            assert _is_wechat_url(url) is False, url
            man = {"run_id": "t", "input": {"article_sha256": "c" * 64},
                   "assets": [_asset(url)]}
            assert build_bindings(man)["body_image_count"] == 0, url

    def test_bindings_builder_accepts_exact_https_hosts(self):
        for url in GOOD_URLS:
            assert _is_wechat_url(url) is True, url

    def test_official_validator_rejects_evil_urls(self):
        vm = _load_validator()
        for url in EVIL_URLS:
            assert vm._is_exact_wechat_url(url) is False, url
        for url in GOOD_URLS:
            assert vm._is_exact_wechat_url(url) is True, url

    def test_official_validator_bindings_fail_on_evil_host(self):
        vm = _load_validator()
        td = Path(tempfile.mkdtemp())
        url = EVIL_URLS[1]
        man = {"run_id": "t", "input": {"article_sha256": "c" * 64},
               "assets": [_asset(url)]}
        (td / "m.json").write_text(json.dumps(man), encoding="utf-8")
        bnd = {"body_images": [{"asset_id": "A-001", "sha256": "a" * 64,
                                "remote_url": url}]}
        (td / "b.json").write_text(json.dumps(bnd), encoding="utf-8")
        rep = vm.validate_bindings(str(td / "m.json"), str(td / "b.json"))
        assert rep["pass"] is False


class TestNormalizeWechatUrl:
    def test_http_mmbiz_upgraded_to_https(self):
        assert normalize_wechat_url("http://mmbiz.qpic.cn/a/0") == "https://mmbiz.qpic.cn/a/0"

    def test_evil_urls_rejected(self):
        for url in EVIL_URLS[:-1]:  # last one upgrades to a GOOD https url
            assert normalize_wechat_url(url) is None, url

    def test_non_wechat_host_rejected(self):
        assert normalize_wechat_url("https://mock-cdn.example.com/x.png") is None


class TestUploadEvents:
    def test_serial_events_no_overlap_one_per_asset(self, tmp_path=None):
        td = Path(tempfile.mkdtemp())
        img = td / "x.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
        up = MockUploader()
        events = []
        r1 = timed_upload(up, events, str(img), "A-001", "known_allowed")
        r2 = timed_upload(up, events, str(img), "A-002", "known_allowed")
        assert r1.status == r2.status == "success"
        assert [e["asset_id"] for e in events] == ["A-001", "A-002"]
        for e in events:
            assert e["end_monotonic"] >= e["start_monotonic"]
            assert set(e) >= {"asset_id", "mode", "status", "started_at",
                              "ended_at", "start_monotonic", "end_monotonic"}
        # serial: next start must not precede previous end
        assert events[1]["start_monotonic"] >= events[0]["end_monotonic"]
