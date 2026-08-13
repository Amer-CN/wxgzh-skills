#!/usr/bin/env python3
"""dev7-hotfix1 tests: article_image_bindings.json emission + offline wechat_audit
upload mode + validator --bindings pass + CLI compatibility.

These prove the REAL media-enrichment skill (not a downstream shim) produces
bindings and a mmbiz.qpic.cn URL with ZERO network/side effects.
"""
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from media_enrichment.article_bindings import build_bindings, write_bindings
from media_enrichment.uploader import WechatAuditUploader, create_uploader


def _load_validator():
    p = SKILL_ROOT / "scripts" / "validate_media_manifest.py"
    spec = importlib.util.spec_from_file_location("validate_media_manifest", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _asset(asset_id, decision="eligible", status="success",
           remote="https://mmbiz.qpic.cn/mmbiz_png/abc/640?wx_fmt=png", sha="a" * 64):
    return {
        "asset_id": asset_id, "asset_origin": "source",
        "material_ids": ["M-001"], "claim_ids": ["C-01"],
        "sha256": sha, "decision": decision,
        "caption": "图：示例", "alt_text": "示例",
        "placement": {"anchor": "## 一", "position": "after", "confidence": 0.9},
        "upload": {"mode": "wechat_audit", "status": status,
                   "remote_url": remote, "response_sha256": "b" * 64},
    }


def _manifest(assets):
    return {"schema_version": "1.0", "run_id": "test-bind",
            "input": {"article_sha256": "c" * 64},
            "assets": assets, "errors": [], "warnings": [],
            "gate": {"publish_allowed": False}}


class TestBuildBindings:
    def test_eligible_uploaded_wechat_asset_is_bound(self):
        m = _manifest([_asset("A-001")])
        b = build_bindings(m)
        assert b["body_image_count"] == 1
        item = b["body_images"][0]
        assert item["asset_id"] == "A-001"
        assert "mmbiz.qpic.cn" in item["remote_url"]
        assert item["sha256"] == "a" * 64
        assert b["publish_allowed"] is False

    def test_non_eligible_excluded(self):
        m = _manifest([_asset("A-001", decision="review_required")])
        assert build_bindings(m)["body_image_count"] == 0

    def test_not_uploaded_excluded(self):
        m = _manifest([_asset("A-001", status="not_uploaded", remote=None)])
        assert build_bindings(m)["body_image_count"] == 0

    def test_non_wechat_url_excluded(self):
        m = _manifest([_asset("A-001", remote="https://mock-cdn.example.com/x.png")])
        assert build_bindings(m)["body_image_count"] == 0

    def test_binding_sha_copied_from_manifest(self):
        m = _manifest([_asset("A-001", sha="d" * 64)])
        assert build_bindings(m)["body_images"][0]["sha256"] == "d" * 64


class TestValidatorBindingsPass:
    def test_written_bindings_pass_official_validator(self, tmp_path=None):
        td = Path(tempfile.mkdtemp())
        m = _manifest([_asset("A-001"), _asset("A-002", sha="e" * 64,
                       remote="https://mmbiz.qpic.cn/mmbiz_png/def/640?wx_fmt=png")])
        man_p = td / "media_manifest.json"
        man_p.write_text(json.dumps(m), encoding="utf-8")
        bind_p = td / "article_image_bindings.json"
        write_bindings(m, bind_p)
        vm = _load_validator()
        report = vm.validate_bindings(str(man_p), str(bind_p))
        assert report["pass"] is True, report
        assert report["exit_code"] == 0


class TestWechatAuditUploader:
    def test_known_allowed_yields_mmbiz_url_no_network(self):
        fd, path = tempfile.mkstemp(suffix=".png")
        os.write(fd, b"\x89PNG\r\n\x1a\n" + b"0" * 128)
        os.close(fd)
        try:
            up = WechatAuditUploader()
            r = up.upload(path, "A-001", copyright_status="known_allowed")
            assert r.status == "success"
            assert r.mode == "wechat_audit"
            assert r.remote_url.startswith("https://mmbiz.qpic.cn/")
            assert r.response_sha256 == hashlib.sha256(r.remote_url.encode()).hexdigest()
        finally:
            os.unlink(path)

    def test_deterministic(self):
        fd, path = tempfile.mkstemp(suffix=".png")
        os.write(fd, b"same-bytes-1234567890")
        os.close(fd)
        try:
            up = WechatAuditUploader()
            a = up.upload(path, "A-001", copyright_status="known_allowed")
            b = up.upload(path, "A-001", copyright_status="known_allowed")
            assert a.remote_url == b.remote_url
        finally:
            os.unlink(path)

    def test_non_known_allowed_skipped(self):
        up = WechatAuditUploader()
        for status in ("unknown", "restricted"):
            assert up.upload("x.png", "A-001", copyright_status=status).status == "skipped"

    def test_registered_in_factory(self):
        assert isinstance(create_uploader("wechat_audit"), WechatAuditUploader)


class TestCliCompat:
    def test_runner_argparse_flags(self):
        src = (SKILL_ROOT / "scripts" / "run_media_enrichment.py").read_text(encoding="utf-8")
        for flag in ('"--request"', '"--output-dir"', '"--fixture-dir"'):
            assert flag in src, f"run_media_enrichment.py must accept {flag}"

    def test_validator_argparse_flags(self):
        src = (SKILL_ROOT / "scripts" / "validate_media_manifest.py").read_text(encoding="utf-8")
        for flag in ('"--manifest"', '"--request"', '"--bindings"'):
            assert flag in src, f"validate_media_manifest.py must accept {flag}"



def test_build_bindings_max_images_truncates():
    """76G-R:max_total_images 约束最终入文图数——上传 10 张,绑定截断到 8。"""
    assets = [_asset(f"A-{i:03d}") for i in range(10)]
    man = _manifest(assets)
    bnd = build_bindings(man, max_images=8)
    assert bnd["body_image_count"] == 8
    assert [b["asset_id"] for b in bnd["body_images"]] == [f"A-{i:03d}" for i in range(8)]
    # 不传 max_images 行为不变(全绑)
    assert build_bindings(man)["body_image_count"] == 10


def test_build_bindings_max_images_ignored_when_none():
    """76G-R:max_images 缺省/None → 全绑(行为与现状一致)。"""
    assets = [_asset(f"A-{i:03d}") for i in range(3)]
    man = _manifest(assets)
    assert build_bindings(man)["body_image_count"] == 3
