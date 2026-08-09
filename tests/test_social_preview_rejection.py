"""dev6 tests: social share card / link preview image rejection.

Rule under test (user requirement, 2026-07-27):
- Images discovered via og:image / twitter:image meta tags (link preview
  cards not rendered in the page body) must be rejected.
- Dynamically generated social share cards, e.g. AI HOT's per-item
  /items/<id>/opengraph-image-xxxx endpoint, must be rejected even when
  discovered through other paths (URL pattern fallback).
- Normal in-body images (img.src etc.) are unaffected.
"""

import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "src"))

from media_enrichment.image_classifier import (
    SOCIAL_PREVIEW_EXTRACTION_METHODS,
    classify_image,
)
from media_enrichment.image_inspector import ImageInspection

# real-world regression: the AI HOT og card picked up in the Qwen3.8 run
# (asset A-003, 1200x630, would previously classify eligible)
REAL_AIHOT_OG_URL = ("https://aihot.virxact.com/items/cmrxkj0zi00cdro7w1s7hr2rm/"
                     "opengraph-image-1az256?75c8895f7ec1441b")


def _inspection(width=1200, height=630):
    return ImageInspection(
        sha256="a" * 64, perceptual_hash="b" * 16, width=width, height=height,
        mime_type="image/png", file_size=63322, is_valid=True,
        decompression_bomb=False, error="",
    )


class TestSocialPreviewRejection:
    @pytest.mark.parametrize("method", sorted(SOCIAL_PREVIEW_EXTRACTION_METHODS))
    def test_meta_tag_extraction_not_rejected_by_channel(self, method):
        """档HF-4/OBS-247:meta 通道本身不再一票否决——正常 URL 的
        og:image/twitter:image 发现不再因通道被拒(进入后续安全/尺寸/质量/
        去重关卡,按版权给 review_required/eligible)。"""
        result = classify_image("https://example.com/some/large-photo.png",
                                _inspection(), copyright_status="unknown",
                                extraction_method=method)
        assert result.decision == "review_required"
        assert result.category != "social_share_card"
        result2 = classify_image("https://example.com/some/large-photo.png",
                                 _inspection(), copyright_status="known_allowed",
                                 extraction_method=method)
        assert result2.decision == "eligible"

    def test_real_aihot_og_card_url_rejected(self):
        """Regression: the exact AI HOT opengraph card URL from the Qwen3.8
        run is rejected via URL pattern even without extraction_method."""
        result = classify_image(REAL_AIHOT_OG_URL, _inspection(),
                                copyright_status="known_allowed")
        assert result.decision == "rejected"
        assert result.category == "social_share_card"

    def test_og_url_pattern_beats_eligibility(self):
        """URL pattern applies regardless of extraction method."""
        result = classify_image(REAL_AIHOT_OG_URL, _inspection(),
                                copyright_status="known_allowed",
                                extraction_method="img.src")
        assert result.decision == "rejected"

    def test_normal_body_image_unaffected(self):
        """A normal in-body image stays eligible under known_allowed."""
        result = classify_image("https://example.com/photos/event-shot.jpg",
                                _inspection(), copyright_status="known_allowed",
                                extraction_method="img.src")
        assert result.decision == "eligible"

    def test_default_extraction_method_unaffected(self):
        """Callers not passing extraction_method keep prior behavior."""
        result = classify_image("https://example.com/photos/event-shot.jpg",
                                _inspection(), copyright_status="known_allowed")
        assert result.decision == "eligible"

    def test_runner_passes_extraction_method(self):
        """run_media_enrichment.py must thread candidate.extraction_method
        into classify_image."""
        runner = (SKILL_ROOT / "scripts" / "run_media_enrichment.py").read_text(
            encoding="utf-8")
        block = runner.split("classification = classify_image(")[1][:400]
        assert "extraction_method=candidate.extraction_method," in block


# dev7-hotfix1: segment-based URL detection must NOT false-kill normal body
# images whose names merely contain "og-image" as a substring.
NORMAL_BODY_URLS = [
    "https://example.com/images/blog-image-hero.jpg",
    "https://example.com/assets/catalog-image.png",
    "https://example.com/photos/dog-image.jpg",
    "https://example.com/photos/event-shot.jpg",
    # contains 'og-image' but as a mid-segment substring -> NOT a card
    "https://example.com/images/my-og-image-example.jpg",
]

SOCIAL_CARD_URLS = [
    "https://aihot.virxact.com/items/id/opengraph-image-1az256?75c8895f",
    "https://x.com/opengraph-image",
    "https://x.com/opengraph-image-xxxx",
    "https://x.com/twitter-image",
    "https://x.com/twitter-image-xxxx",
    "https://x.com/og-image",
    "https://x.com/og-image-xxxx",
    "https://x.com/og.png",
    "https://x.com/og.jpg",
    "https://x.com/og.jpeg",
    "https://x.com/og.webp",
]


class TestSegmentBasedUrlDetection:
    """dev7-hotfix1 blocker fix: bare r'og-image' substring must not match."""

    @pytest.mark.parametrize("url", NORMAL_BODY_URLS)
    def test_normal_body_url_img_src_eligible(self, url):
        result = classify_image(url, _inspection(),
                                copyright_status="known_allowed",
                                extraction_method="img.src")
        assert result.decision == "eligible", f"{url} wrongly {result.decision}"
        assert result.category != "social_share_card"

    @pytest.mark.parametrize("url", SOCIAL_CARD_URLS)
    def test_social_card_url_rejected(self, url):
        result = classify_image(url, _inspection(),
                                copyright_status="known_allowed",
                                extraction_method="img.src")
        assert result.decision == "rejected", f"{url} wrongly {result.decision}"
        assert result.category == "social_share_card"

    def test_my_og_image_not_rejected_when_url_is_normal(self):
        """档HF-4/OBS-247:body 样 URL 即使 extraction_method 是
        og:image/twitter:image 也不再被拒(通道不再一票否决);仅 URL 命中
        动态伪卡片端点时拒绝(见 test_social_card_url_rejected)。"""
        result = classify_image(
            "https://example.com/images/my-og-image-example.jpg",
            _inspection(), copyright_status="known_allowed",
            extraction_method="og:image")
        assert result.decision == "eligible"
        assert result.category != "social_share_card"

    @pytest.mark.parametrize("method", ["  OG:IMAGE ", "Twitter:Image", "og:image"])
    def test_extraction_method_normalized(self, method):
        """extraction_method is normalized (strip + lower) before matching;
        档HF-4/OBS-247:归一化后 meta 通道 + 正常 URL 不再被拒(伪卡片 URL
        仍需归一化后命中才拒,见下一条)。"""
        result = classify_image("https://example.com/photos/real.png",
                                _inspection(), copyright_status="known_allowed",
                                extraction_method=method)
        assert result.decision == "eligible"
        assert result.category != "social_share_card"
        card = classify_image("https://x.com/opengraph-image-xxxx",
                              _inspection(), copyright_status="known_allowed",
                              extraction_method=method)
        assert card.decision == "rejected"
        assert card.category == "social_share_card"


class TestHtmlExtractionIntegration:
    """dev7-hotfix1: when the SAME url appears both as a body <img src> and as
    <meta og:image>, the body img.src candidate is discovered first and must
    survive (not be misclassified as a share card)."""

    def test_img_src_discovered_before_og_meta(self):
        from media_enrichment.image_extractor import extract_images
        shared = "https://example.com/photos/launch-shot.png"
        html = (
            "<html><head>"
            f'<meta property="og:image" content="{shared}">'
            "</head><body>"
            f'<img src="{shared}" alt="launch">'
            "</body></html>"
        )
        result = extract_images(html, page_url="https://example.com/post")
        cands = [c for c in result.candidates if c.url == shared]
        assert cands, "shared URL must be discovered"
        first = cands[0]
        assert first.extraction_method == "img.src", (
            f"body img.src must be discovered first, got {first.extraction_method}")
        r = classify_image(first.url, _inspection(),
                           copyright_status="known_allowed",
                           extraction_method=first.extraction_method)
        assert r.decision == "eligible"
        assert r.category != "social_share_card"
