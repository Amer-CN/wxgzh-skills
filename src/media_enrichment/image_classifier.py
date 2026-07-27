"""Image classifier module.

Classifies images using deterministic, auditable rules:
- rejected: tracking pixels, favicon, avatar, logo, ad, placeholder,
  social share cards / link preview images (og:image, twitter:image),
  undecodable, too small
- review_required: unknown license, unclear source, possible news photo, SVG, low confidence
- eligible: traceable source, quality pass, clearly relevant, no copyright block

Never treats 'downloadable' as 'publishable'.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from .image_inspector import ImageInspection


@dataclass
class ClassificationResult:
    """Result of image classification."""
    category: str = ""  # tracking_pixel, favicon, avatar, logo, ad, placeholder, social_share_card, photo, chart, unknown
    decision: str = "review_required"  # rejected, review_required, eligible
    rejection_reasons: list[str] = field(default_factory=list)
    relevance_reasons: list[str] = field(default_factory=list)
    confidence: float = 0.0
    requires_human_review: bool = True


# URL patterns for classification
TRACKING_PATTERNS = [
    r"tracker", r"beacon", r"pixel", r"analytics", r"tracking",
    r"doubleclick", r"googletagmanager", r"facebook\.com/tr",
]

FAVICON_PATTERNS = [r"favicon", r"icon\.png", r"icon\.ico", r"apple-touch-icon"]

AVATAR_PATTERNS = [r"avatar", r"headshot", r"profile.*image", r"user.*image", r"gravatar"]

LOGO_PATTERNS = [r"logo", r"brandmark", r"brand.*mark", r"wordmark"]

AD_PATTERNS = [
    r"banner", r"advertisement", r"ad-", r"-ad-", r"ad_", r"_ad",
    r"sponsor", r"promo", r"affiliate",
]

PLACEHOLDER_PATTERNS = [r"placeholder", r"default.*image", r"no-image", r"blank"]

# dev6: social share cards / link preview images.
# Extraction methods that come from <meta> tags (not rendered in the page
# body): og:image, twitter:image. Sites like AI HOT dynamically generate a
# per-item OpenGraph card (title + source + date) at URLs such as
# /items/<id>/opengraph-image-xxxx — these are link previews, not content
# images, and must never be selected for the article body.
SOCIAL_PREVIEW_EXTRACTION_METHODS = {"og:image", "twitter:image"}

# dev7-hotfix1: segment-based detection (NOT bare substring). A bare
# r"og-image" substring on the full URL false-killed normal body images
# whose names merely CONTAIN the substring (blog-image-hero.jpg,
# catalog-image.png, dog-image.jpg). Instead we split urlsplit(url).path
# into segments and only reject when a segment STARTS a known social-card
# endpoint (opengraph-image / twitter-image / og-image), or is a bare
# og.<ext> filename.
SOCIAL_PREVIEW_SEGMENT_PREFIXES = ("opengraph-image", "twitter-image", "og-image")
SOCIAL_PREVIEW_BARE_FILENAMES = {"og.png", "og.jpg", "og.jpeg", "og.webp"}


def is_social_preview_url(url: str) -> bool:
    """True if the URL PATH points to a dynamically generated social share
    card / link preview endpoint.

    Uses path segments from urllib.parse.urlsplit(url).path — never a bare
    substring on the full URL. A segment triggers rejection only when it:
      - equals a prefix (opengraph-image / twitter-image / og-image), or
      - starts with prefix + "-" (e.g. opengraph-image-1az256), or
      - starts with prefix + "." (e.g. og-image.png), or
      - is exactly a bare og.<ext> filename (og.png/jpg/jpeg/webp).

    So /images/blog-image-hero.jpg, /assets/catalog-image.png,
    /photos/dog-image.jpg, /images/my-og-image-example.jpg are NOT rejected
    (their segments start with blog-/catalog-/dog-/my-, not the prefixes).
    """
    try:
        path = urlsplit(url or "").path
    except (ValueError, TypeError):
        return False
    for seg in path.split("/"):
        seg_l = seg.strip().lower()
        if not seg_l:
            continue
        if seg_l in SOCIAL_PREVIEW_BARE_FILENAMES:
            return True
        for prefix in SOCIAL_PREVIEW_SEGMENT_PREFIXES:
            if (seg_l == prefix
                    or seg_l.startswith(prefix + "-")
                    or seg_l.startswith(prefix + ".")):
                return True
    return False


def _match_any(url: str, patterns: list[str]) -> bool:
    """Check if URL matches any of the patterns."""
    url_lower = url.lower()
    for pattern in patterns:
        if re.search(pattern, url_lower):
            return True
    return False


def classify_image(
    url: str,
    inspection: ImageInspection,
    min_width: int = 640,
    min_height: int = 360,
    context: str = "",
    copyright_status: str = "unknown",
    extraction_method: str = "",
) -> ClassificationResult:
    """Classify an image using deterministic rules.

    Args:
        url: The image URL.
        inspection: ImageInspection result with dimensions, MIME, etc.
        min_width: Minimum allowed width.
        min_height: Minimum allowed height.
        context: HTML context around the image (alt text, surrounding text).
        copyright_status: Known copyright status.
        extraction_method: How the candidate was discovered (e.g. img.src,
            og:image, twitter:image). Meta-tag methods mean the image is a
            link preview card not rendered in the page body.

    Returns:
        ClassificationResult with category, decision, and reasons.
    """
    result = ClassificationResult()
    reasons: list[str] = []

    # --- REJECT checks ---

    # 0. Social share card / link preview image (dev6, dev7-hotfix1).
    # Images discovered via og:image / twitter:image meta tags, or whose URL
    # PATH is a dynamic OpenGraph card endpoint (e.g. AI HOT's per-item
    # /opengraph-image-xxxx), are link previews that never render in the
    # page body — reject regardless of size/quality/copyright.
    # dev7-hotfix1: extraction_method normalized; URL match is segment-based.
    method = (extraction_method or "").strip().lower()
    if method in SOCIAL_PREVIEW_EXTRACTION_METHODS:
        result.category = "social_share_card"
        result.decision = "rejected"
        result.rejection_reasons.append(
            f"social share card / link preview image (extraction_method="
            f"{method}) — not rendered in page body")
        result.confidence = 0.95
        result.requires_human_review = False
        return result

    if is_social_preview_url(url):
        result.category = "social_share_card"
        result.decision = "rejected"
        result.rejection_reasons.append(
            f"URL matches dynamically generated social share card pattern: {url}")
        result.confidence = 0.95
        result.requires_human_review = False
        return result

    # 1. Tracking pixel (1x1 or very small) — skip SVG (width/height are 0 for SVG)
    if not inspection.is_svg and inspection.width <= 1 and inspection.height <= 1:
        result.category = "tracking_pixel"
        result.decision = "rejected"
        result.rejection_reasons.append("1x1 or smaller — likely tracking pixel")
        result.confidence = 0.99
        result.requires_human_review = False
        return result

    if inspection.width > 0 and inspection.width < 5 and inspection.height > 0 and inspection.height < 5:
        result.category = "tracking_pixel"
        result.decision = "rejected"
        result.rejection_reasons.append(f"extremely small image ({inspection.width}x{inspection.height}) — likely tracking pixel")
        result.confidence = 0.95
        result.requires_human_review = False
        return result

    # 2. URL-based classification
    if _match_any(url, TRACKING_PATTERNS):
        result.category = "tracking_pixel"
        result.decision = "rejected"
        result.rejection_reasons.append(f"URL matches tracking pattern: {url}")
        result.confidence = 0.9
        result.requires_human_review = False
        return result

    if _match_any(url, FAVICON_PATTERNS):
        result.category = "favicon"
        result.decision = "rejected"
        result.rejection_reasons.append(f"URL matches favicon pattern: {url}")
        result.confidence = 0.9
        result.requires_human_review = False
        return result

    if _match_any(url, AVATAR_PATTERNS):
        result.category = "avatar"
        result.decision = "rejected"
        result.rejection_reasons.append(f"URL matches avatar/headshot pattern: {url}")
        result.confidence = 0.85
        result.requires_human_review = False
        return result

    if _match_any(url, LOGO_PATTERNS):
        result.category = "logo"
        result.decision = "rejected"
        result.rejection_reasons.append(f"URL matches logo/brandmark pattern: {url}")
        result.confidence = 0.85
        result.requires_human_review = False
        return result

    if _match_any(url, AD_PATTERNS):
        result.category = "ad"
        result.decision = "rejected"
        result.rejection_reasons.append(f"URL matches ad/banner/sponsor pattern: {url}")
        result.confidence = 0.85
        result.requires_human_review = False
        return result

    if _match_any(url, PLACEHOLDER_PATTERNS):
        result.category = "placeholder"
        result.decision = "rejected"
        result.rejection_reasons.append(f"URL matches placeholder pattern: {url}")
        result.confidence = 0.85
        result.requires_human_review = False
        return result

    # 3. Context-based classification (alt text, surrounding text)
    context_lower = context.lower()
    if "avatar" in context_lower or "headshot" in context_lower:
        result.category = "avatar"
        result.decision = "rejected"
        result.rejection_reasons.append("context indicates avatar/headshot")
        result.confidence = 0.8
        result.requires_human_review = False
        return result

    if "logo" in context_lower and "catalog" not in context_lower:
        result.category = "logo"
        result.decision = "rejected"
        result.rejection_reasons.append("context indicates logo/brandmark")
        result.confidence = 0.75
        result.requires_human_review = False
        return result

    if any(word in context_lower for word in ["advertisement", "sponsored", "ad-banner"]):
        result.category = "ad"
        result.decision = "rejected"
        result.rejection_reasons.append("context indicates advertisement")
        result.confidence = 0.8
        result.requires_human_review = False
        return result

    # 4. Undecodable
    if not inspection.is_valid and not inspection.is_svg:
        result.category = "unknown"
        result.decision = "rejected"
        result.rejection_reasons.append(f"image cannot be decoded: {inspection.error}")
        result.confidence = 0.9
        result.requires_human_review = False
        return result

    # 5. Decompression bomb
    if inspection.decompression_bomb:
        result.category = "unknown"
        result.decision = "rejected"
        result.rejection_reasons.append("decompression bomb detected")
        result.confidence = 0.99
        result.requires_human_review = False
        return result

    # 6. Size below hard threshold (skip for SVG — checked separately below)
    if not inspection.is_svg and inspection.width > 0 and inspection.height > 0:
        if inspection.width < min_width or inspection.height < min_height:
            result.category = "too_small"
            result.decision = "rejected"
            result.rejection_reasons.append(
                f"dimensions {inspection.width}x{inspection.height} below minimum {min_width}x{min_height}"
            )
            result.confidence = 0.9
            result.requires_human_review = False
            return result

    # --- REVIEW_REQUIRED checks ---

    # Restricted copyright = always reject
    if copyright_status == "restricted":
        result.category = result.category or "restricted"
        result.decision = "rejected"
        result.rejection_reasons.append("copyright status is restricted")
        result.confidence = 0.95
        result.requires_human_review = False
        return result

    review_reasons: list[str] = []

    # SVG — not directly publishable
    if inspection.is_svg:
        result.category = "svg"
        review_reasons.append("SVG images are not directly publishable as photos")
        result.confidence = 0.7

    # Unknown copyright
    if copyright_status == "unknown":
        review_reasons.append("copyright status unknown — cannot auto-approve for publishing")
        result.confidence = max(result.confidence, 0.6)

    # Photo with unknown source context
    if result.category == "" and copyright_status == "unknown":
        result.category = "photo"
        review_reasons.append("appears to be a photograph but source context unclear")
        result.confidence = max(result.confidence, 0.5)

    if review_reasons:
        result.decision = "review_required"
        result.rejection_reasons = []
        result.relevance_reasons = review_reasons
        result.requires_human_review = True
        if not result.category:
            result.category = "unknown"
        return result

    # --- ELIGIBLE ---
    # Only eligible if: traceable source, quality pass, no copyright block
    if (inspection.is_valid
            and (inspection.width >= min_width or inspection.is_svg)
            and copyright_status in ("known_allowed",)):
        result.category = "photo" if not result.category else result.category
        result.decision = "eligible"
        result.relevance_reasons.append("image is valid, quality meets threshold, and copyright is known_allowed")
        result.confidence = 0.8
        result.requires_human_review = False
        return result

    # Default: review required
    if not result.category:
        result.category = "unknown"
    result.decision = "review_required"
    result.relevance_reasons.append("insufficient information to auto-approve")
    result.requires_human_review = True
    result.confidence = max(result.confidence, 0.3)
    return result
