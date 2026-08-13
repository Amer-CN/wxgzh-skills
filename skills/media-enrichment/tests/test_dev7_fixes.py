"""dev7 tests: source-image upload & discovery routing fixes.

1. Downloaded files keep/append a real image extension
   (Content-Type > detected MIME > URL suffix).
2. WeChat uploader multipart filename always carries an extension.
3. Explicit no-repost scan helper (targets ORIGINAL source page).
4. Runner prefers materials[].source_url; aihot_permalink is fallback only.
5. validate_media_manifest --bindings checks every final bound asset.
"""

import json
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from media_enrichment.downloader import pick_extension
from media_enrichment.page_fetcher import NO_REPOST_PHRASES, scan_no_repost


class TestPickExtension:
    def test_content_type_png(self):
        assert pick_extension("image/png", "", "https://x/img") == ".png"

    def test_content_type_jpeg_normalized(self):
        assert pick_extension("", "image/jpeg", "https://x/img") == ".jpg"

    def test_url_suffix_fallback(self):
        assert pick_extension("", "", "https://x/a/photo.webp?v=1") == ".webp"

    def test_jpeg_url_suffix_maps_to_jpg(self):
        assert pick_extension("", "", "https://x/a/photo.jpeg") == ".jpg"

    def test_unknown_stays_empty(self):
        assert pick_extension("application/octet-stream", "", "https://x/blob") == ""

    def test_detected_mime_wins_over_url(self):
        assert pick_extension("image/png", "", "https://x/a.jpg") == ".png"


class TestUploaderFilename:
    def test_upload_name_derivation_source(self):
        """Uploader source must derive an extensioned multipart filename for
        extension-less local files."""
        src = (SKILL_ROOT / "src" / "media_enrichment" / "uploader.py").read_text(
            encoding="utf-8")
        assert "upload_name = path.name + MIME_EXTENSIONS.get(" in src
        assert 'files = {"media": (upload_name, f, mime or "image/png")}' in src


class TestNoRepostScan:
    @pytest.mark.parametrize("idx", range(len(NO_REPOST_PHRASES)),
                             ids=[f"phrase_{i:02d}" for i in
                                  range(len(NO_REPOST_PHRASES))])
    def test_each_phrase_detected(self, idx):
        phrase = NO_REPOST_PHRASES[idx]
        hits = scan_no_repost(f"<p>本文{phrase}，谢绝一切使用</p>")
        # overlapping phrases (e.g. 未经许可不得转载 contains 不得转载) may
        # both hit — the required phrase must be among the hits
        assert phrase in hits

    def test_clean_page_empty(self):
        assert scan_no_repost("<p>欢迎转载，注明出处即可</p>") == []

    def test_empty_html(self):
        assert scan_no_repost("") == []


class TestRunnerRouting:
    def test_runner_prefers_aihot_internal_then_source_url(self):
        """76E/OBS-260:抓图优先级=AI HOT 站内页(aihot_internal_url)优先 →
        原始来源页(source_url)兜底 + no-repost 扫描保留;permalink 仅追溯兜底。"""
        runner = (SKILL_ROOT / "scripts" / "run_media_enrichment.py").read_text(
            encoding="utf-8")
        # ① 站内页优先
        assert "fetch_page(internal_url, mode=network_mode" in runner
        assert '"aihot_internal"' in runner
        # ② 原始来源页兜底 + no-repost 扫描(变量名为 fr_src)
        assert "fetch_page(source_url, mode=network_mode" in runner
        assert "falling back to" in runner
        assert "scan_no_repost(fr_src.content)" in runner
        assert 'mat_copyright_status = "restricted"' in runner
        # ③ permalink 追溯兜底
        assert "fetch_page(permalink, mode=network_mode" in runner
        # source_page_url records the actually fetched page
        assert "source_page_url=page_url" in runner
        assert "source_page_url=permalink" not in runner


class TestValidateBindings:
    def _mk(self, tmp_path, upload_status="success",
            remote="https://mmbiz.qpic.cn/x/y", decision="eligible",
            sha="c" * 64, bind_sha=None):
        manifest = {"assets": [{"asset_id": "A-001", "decision": decision,
                                "sha256": sha,
                                "upload": {"status": upload_status,
                                           "remote_url": remote}}]}
        bindings = {"body_images": [{"asset_id": "A-001",
                                     "sha256": bind_sha or sha}]}
        mp = tmp_path / "m.json"
        bp = tmp_path / "b.json"
        mp.write_text(json.dumps(manifest), encoding="utf-8")
        bp.write_text(json.dumps(bindings), encoding="utf-8")
        return str(mp), str(bp)

    def test_all_good_passes(self, tmp_path):
        from validate_media_manifest import validate_bindings
        mp, bp = self._mk(tmp_path)
        assert validate_bindings(mp, bp)["pass"] is True

    def test_failed_upload_fails(self, tmp_path):
        from validate_media_manifest import validate_bindings
        mp, bp = self._mk(tmp_path, upload_status="failed", remote="")
        assert validate_bindings(mp, bp)["pass"] is False

    def test_non_wechat_url_fails(self, tmp_path):
        from validate_media_manifest import validate_bindings
        mp, bp = self._mk(tmp_path, remote="https://example.com/a.png")
        assert validate_bindings(mp, bp)["pass"] is False

    def test_missing_asset_fails(self, tmp_path):
        from validate_media_manifest import validate_bindings
        mp, bp = self._mk(tmp_path)
        bindings = {"body_images": [{"asset_id": "A-999"}]}
        (tmp_path / "b.json").write_text(json.dumps(bindings), encoding="utf-8")
        assert validate_bindings(mp, bp)["pass"] is False

    def test_sha_mismatch_fails(self, tmp_path):
        from validate_media_manifest import validate_bindings
        mp, bp = self._mk(tmp_path, bind_sha="d" * 64)
        assert validate_bindings(mp, bp)["pass"] is False
