"""Tests for image extractor, proxy decoder, image processing, offline integration."""

import pytest
from pathlib import Path
from media_enrichment.image_extractor import extract_images
from media_enrichment.proxy_decoder import decode_proxy_url
from media_enrichment.image_inspector import inspect_image, ImageInspection
from media_enrichment.image_deduplicator import deduplicate_asset, DedupState
from media_enrichment.image_classifier import classify_image

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "html"
FIXTURES_IMG = Path(__file__).resolve().parents[1] / "fixtures" / "images"


class TestImgSrc:
    def test_basic_img_src(self):
        html = (FIXTURES / "img-src.html").read_text(encoding="utf-8")
        result = extract_images(html, page_url="https://example.com/page")
        urls = [c.url for c in result.candidates]
        assert "https://example.com/images/photo1.jpg" in urls

    def test_relative_url_resolved(self):
        html = (FIXTURES / "img-src.html").read_text(encoding="utf-8")
        result = extract_images(html, page_url="https://example.com/page")
        assert any("relative/path/photo3.jpg" in u for u in [c.url for c in result.candidates])

    def test_bare_relative_resolved(self):
        html = (FIXTURES / "img-src.html").read_text(encoding="utf-8")
        result = extract_images(html, page_url="https://example.com/page")
        assert any("photo4.jpg" in u for u in [c.url for c in result.candidates])


class TestSrcset:
    def test_srcset_multiple_sizes(self):
        html = (FIXTURES / "srcset.html").read_text(encoding="utf-8")
        result = extract_images(html, page_url="https://example.com/page")
        urls = [c.url for c in result.candidates]
        assert "https://example.com/images/small.jpg" in urls
        assert "https://example.com/images/medium.jpg" in urls

    def test_picture_source_srcset(self):
        html = (FIXTURES / "srcset.html").read_text(encoding="utf-8")
        result = extract_images(html, page_url="https://example.com/page")
        urls = [c.url for c in result.candidates]
        assert "https://example.com/images/webp-small.webp" in urls


class TestLazyLoad:
    def test_data_src(self):
        html = (FIXTURES / "lazy-load.html").read_text(encoding="utf-8")
        result = extract_images(html, page_url="https://example.com/page")
        assert "https://example.com/images/lazy1.jpg" in [c.url for c in result.candidates]

    def test_data_original(self):
        html = (FIXTURES / "lazy-load.html").read_text(encoding="utf-8")
        result = extract_images(html, page_url="https://example.com/page")
        assert "https://example.com/images/lazy2.jpg" in [c.url for c in result.candidates]

    def test_data_lazy_src(self):
        html = (FIXTURES / "lazy-load.html").read_text(encoding="utf-8")
        result = extract_images(html, page_url="https://example.com/page")
        assert "https://example.com/images/lazy3.jpg" in [c.url for c in result.candidates]


class TestMetaImages:
    def test_og_image(self):
        html = (FIXTURES / "og-image.html").read_text(encoding="utf-8")
        result = extract_images(html, page_url="https://example.com/page")
        assert "https://example.com/images/og-image.jpg" in [c.url for c in result.candidates]

    def test_twitter_image(self):
        html = '<meta name="twitter:image" content="https://example.com/images/twitter.jpg">'
        result = extract_images(html, page_url="https://example.com/page")
        assert "https://example.com/images/twitter.jpg" in [c.url for c in result.candidates]


class TestJSONLD:
    def test_json_ld_single(self):
        html = (FIXTURES / "json-ld.html").read_text(encoding="utf-8")
        result = extract_images(html, page_url="https://example.com/page")
        assert "https://example.com/images/json-ld-single.jpg" in [c.url for c in result.candidates]

    def test_json_ld_array(self):
        html = (FIXTURES / "json-ld.html").read_text(encoding="utf-8")
        result = extract_images(html, page_url="https://example.com/page")
        urls = [c.url for c in result.candidates]
        assert "https://example.com/images/json-ld-array1.jpg" in urls


class TestBackgroundImage:
    def test_background_image_extracted(self):
        bg_file = FIXTURES / "background-image.html"
        if bg_file.exists():
            html = bg_file.read_text(encoding="utf-8")
            result = extract_images(html, page_url="https://example.com/page")
            bg = [c for c in result.candidates if c.extraction_method == "background-image"]
            assert len(bg) >= 1


class TestDuplicates:
    def test_duplicate_urls_removed(self):
        html = (FIXTURES / "duplicates.html").read_text(encoding="utf-8")
        result = extract_images(html, page_url="https://example.com/page")
        urls = [c.url for c in result.candidates]
        assert urls.count("https://example.com/images/duplicate1.jpg") == 1


class TestProtocolRelative:
    def test_protocol_relative(self):
        html = '<img src="//cdn.example.com/image.jpg">'
        result = extract_images(html, page_url="https://example.com/page")
        assert any("cdn.example.com/image.jpg" in u for u in [c.url for c in result.candidates])


class TestProxyDecoder:
    def test_single_url_encoding(self):
        url = "https://aihot.virxact.com/img-proxy?url=https%3A%2F%2Fexample.com%2Fimage.jpg"
        result = decode_proxy_url(url)
        assert result.is_proxy
        assert "https://example.com/image.jpg" in result.decoded_url

    def test_double_url_encoding(self):
        url = "https://aihot.virxact.com/img-proxy?url=https%253A%252F%252Fexample.com%252Fimage.jpg"
        result = decode_proxy_url(url)
        assert result.is_proxy
        assert result.decoded_url == "https://example.com/image.jpg"

    def test_base64_url(self):
        import base64
        original = "https://example.com/images/base64-1.jpg"
        encoded = base64.urlsafe_b64encode(original.encode()).decode().rstrip("=")
        url = f"https://aihot.virxact.com/img-proxy/{encoded}"
        result = decode_proxy_url(url)
        assert result.is_proxy
        assert original in result.decoded_url

    def test_non_proxy_url(self):
        result = decode_proxy_url("https://example.com/image.jpg")
        assert not result.is_proxy

    def test_max_depth_not_exceeded(self):
        url = "https://aihot.virxact.com/img-proxy?url=https%3A%2F%2Fexample.com%2Fimage.jpg"
        result = decode_proxy_url(url)
        assert result.decode_depth <= 5

    def test_no_eval(self):
        result = decode_proxy_url("https://aihot.virxact.com/img-proxy?url=javascript:alert(1)")
        assert result.decoded_url


class TestImageInspector:
    def test_valid_photo(self):
        r = inspect_image(FIXTURES_IMG / "valid-photo.jpg")
        assert r.is_valid
        assert r.width == 800
        assert r.height == 600
        assert r.mime_type == "image/jpeg"

    def test_valid_png(self):
        r = inspect_image(FIXTURES_IMG / "valid-chart.png")
        assert r.is_valid
        assert r.mime_type == "image/png"

    def test_corrupted(self):
        r = inspect_image(FIXTURES_IMG / "corrupted.jpg")
        assert not r.is_valid

    def test_tracking_pixel(self):
        r = inspect_image(FIXTURES_IMG / "tracking-pixel.gif")
        assert r.is_valid
        assert r.width == 1 and r.height == 1


class TestDedup:
    def test_exact_sha256(self):
        state = DedupState()
        r1 = deduplicate_asset("A-001", "abc", "https://example.com/1.jpg", "ph1", state=state)
        r2 = deduplicate_asset("A-002", "abc", "https://example.com/2.jpg", "ph2", state=state)
        assert r2.is_duplicate and r2.dedup_method == "sha256"

    def test_phash_near(self):
        state = DedupState()
        r1 = deduplicate_asset("A-001", "sha1", "https://example.com/1.jpg", "ffff0000ffff0000", state=state)
        r2 = deduplicate_asset("A-002", "sha2", "https://example.com/2.jpg", "ffff0000ffff0000", state=state)
        assert r2.is_duplicate and r2.dedup_method == "phash"

    def test_different_phash_not_dup(self):
        state = DedupState()
        r1 = deduplicate_asset("A-001", "sha1", "https://example.com/1.jpg", "ffff0000ffff0000", state=state)
        r2 = deduplicate_asset("A-002", "sha2", "https://example.com/2.jpg", "0000ffff0000ffff", state=state)
        assert not r2.is_duplicate

    def test_real_image_exact_dedup(self):
        img = inspect_image(FIXTURES_IMG / "valid-photo.jpg")
        state = DedupState()
        r1 = deduplicate_asset("A-001", img.sha256, "https://example.com/1.jpg", img.perceptual_hash, state=state)
        r2 = deduplicate_asset("A-002", img.sha256, "https://example.com/2.jpg", img.perceptual_hash, state=state)
        assert r2.is_duplicate

    def test_resized_dedup(self):
        img1 = inspect_image(FIXTURES_IMG / "valid-photo.jpg")
        img2 = inspect_image(FIXTURES_IMG / "duplicate-resized.jpg")
        state = DedupState()
        r1 = deduplicate_asset("A-001", img1.sha256, "https://example.com/1.jpg", img1.perceptual_hash, state=state)
        r2 = deduplicate_asset("A-002", img2.sha256, "https://example.com/2.jpg", img2.perceptual_hash, state=state)
        assert r2.is_duplicate


class TestClassifier:
    def test_tracking_pixel_rejected(self):
        insp = ImageInspection(is_valid=True, width=1, height=1, mime_type="image/gif", sha256="a", perceptual_hash="p")
        assert classify_image("https://analytics.example.com/pixel.gif", insp).decision == "rejected"

    def test_logo_rejected(self):
        insp = ImageInspection(is_valid=True, width=200, height=60, mime_type="image/png", sha256="a", perceptual_hash="p")
        assert classify_image("https://example.com/images/logo.png", insp).decision == "rejected"

    def test_avatar_rejected(self):
        insp = ImageInspection(is_valid=True, width=80, height=80, mime_type="image/jpeg", sha256="a", perceptual_hash="p")
        assert classify_image("https://example.com/images/avatar/user123.jpg", insp).decision == "rejected"

    def test_ad_rejected(self):
        insp = ImageInspection(is_valid=True, width=728, height=90, mime_type="image/jpeg", sha256="a", perceptual_hash="p")
        assert classify_image("https://example.com/images/banner-ad-728x90.jpg", insp).decision == "rejected"

    def test_too_small_rejected(self):
        insp = ImageInspection(is_valid=True, width=100, height=50, mime_type="image/jpeg", sha256="a", perceptual_hash="p")
        assert classify_image("https://example.com/images/small.jpg", insp, min_width=640, min_height=360).decision == "rejected"

    def test_corrupted_rejected(self):
        insp = ImageInspection(is_valid=False, error="cannot decode")
        assert classify_image("https://example.com/images/broken.jpg", insp).decision == "rejected"

    def test_unknown_copyright_review(self):
        insp = ImageInspection(is_valid=True, width=800, height=600, mime_type="image/jpeg", sha256="a", perceptual_hash="p")
        result = classify_image("https://example.com/images/photo.jpg", insp, copyright_status="unknown")
        assert result.decision == "review_required"

    def test_restricted_rejected(self):
        insp = ImageInspection(is_valid=True, width=800, height=600, mime_type="image/jpeg", sha256="a", perceptual_hash="p")
        result = classify_image("https://example.com/images/photo.jpg", insp, copyright_status="restricted")
        assert result.decision == "rejected"

    def test_known_allowed_eligible(self):
        insp = ImageInspection(is_valid=True, width=800, height=600, mime_type="image/jpeg", sha256="a", perceptual_hash="p")
        result = classify_image("https://example.com/images/photo.jpg", insp, copyright_status="known_allowed")
        assert result.decision == "eligible"

    def test_svg_review(self):
        insp = ImageInspection(is_valid=True, is_svg=True, mime_type="image/svg+xml", sha256="a", perceptual_hash="")
        result = classify_image("https://example.com/images/diagram.svg", insp, copyright_status="known_allowed")
        assert result.decision == "review_required"


class TestOfflineIntegration:
    def test_offline_fetch_stable_hash(self):
        from media_enrichment.page_fetcher import fetch_page
        r1 = fetch_page("https://aihot.virxact.com/items/img-src", mode="offline_fixture", fixture_dir=FIXTURES)
        r2 = fetch_page("https://aihot.virxact.com/items/img-src", mode="offline_fixture", fixture_dir=FIXTURES)
        assert r1.content_sha256 == r2.content_sha256

    def test_ssrf_urls_all_blocked(self):
        html = (FIXTURES / "malicious-ssrf.html").read_text(encoding="utf-8")
        result = extract_images(html, page_url="https://example.com/page")
        from media_enrichment.url_security import is_safe_url
        for c in result.candidates:
            if c.url.startswith("http"):
                assert not is_safe_url(c.url).safe

    def test_manifest_deterministic(self):
        from media_enrichment.manifest_builder import ManifestBuilder, AssetRecord
        import json
        def build():
            b = ManifestBuilder(run_id="t", request_sha256="a"*64, article_sha256="b"*64, claims_total=1, materials_total=1)
            b.add_asset(AssetRecord(asset_id="A-001", asset_origin="source", material_ids=["M-001"], claim_ids=["C-01"],
                                    decision="eligible", reasons=["test"], sha256="c"*64, source_page_url="https://example.com"))
            return b.build()
        assert json.dumps(build(), sort_keys=True) == json.dumps(build(), sort_keys=True)
