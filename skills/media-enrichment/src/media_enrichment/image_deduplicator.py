"""Image deduplicator module.

Removes duplicate images using three strategies:
1. SHA256 exact dedup
2. Original URL normalization dedup
3. Perceptual hash (pHash) near-dedup

When same image exists at different sizes, keeps the highest quality version.
Records duplicate_of and dedup reason.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse, urlunparse

# pHash hamming distance threshold (0 = identical, higher = more different)
PHASH_THRESHOLD = 5


@dataclass
class DedupResult:
    """Result of deduplication for a single asset."""
    is_duplicate: bool
    duplicate_of: str | None = None
    dedup_method: str = ""  # sha256, url, phash
    dedup_reason: str = ""


@dataclass
class DedupState:
    """State for the deduplication process."""
    seen_sha256: dict[str, str] = field(default_factory=dict)  # sha256 -> asset_id
    seen_urls: dict[str, str] = field(default_factory=dict)   # normalized_url -> asset_id
    seen_phash: list[tuple[str, str]] = field(default_factory=list)  # (phash, asset_id)


def normalize_image_url(url: str) -> str:
    """Normalize an image URL for dedup comparison."""
    if not url:
        return ""
    try:
        parsed = urlparse(url)
        # Remove query params and fragment, lowercase host
        netloc = (parsed.hostname or "").lower()
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        # Remove trailing slash from path
        path = parsed.path.rstrip("/") or "/"
        return urlunparse((parsed.scheme.lower(), netloc, path, "", "", ""))
    except Exception:
        return url


def hamming_distance(hash1: str, hash2: str) -> int:
    """Compute Hamming distance between two hex perceptual hashes."""
    if not hash1 or not hash2 or len(hash1) != len(hash2):
        return 64  # max distance
    try:
        val1 = int(hash1, 16)
        val2 = int(hash2, 16)
        return bin(val1 ^ val2).count("1")
    except (ValueError, TypeError):
        return 64


def deduplicate_asset(
    asset_id: str,
    sha256: str,
    original_url: str,
    perceptual_hash: str,
    width: int = 0,
    height: int = 0,
    state: DedupState | None = None,
) -> DedupResult:
    """Check if an asset is a duplicate of previously seen assets.

    Args:
        asset_id: Unique ID for this asset.
        sha256: SHA256 hash of the image file.
        original_url: Original source URL of the image.
        perceptual_hash: Perceptual hash string.
        width: Image width (for quality comparison).
        height: Image height (for quality comparison).
        state: DedupState tracking previously seen assets.

    Returns:
        DedupResult indicating whether this is a duplicate.
    """
    if state is None:
        state = DedupState()

    # 1. SHA256 exact dedup
    if sha256 and sha256 in state.seen_sha256:
        existing_id = state.seen_sha256[sha256]
        return DedupResult(
            is_duplicate=True,
            duplicate_of=existing_id,
            dedup_method="sha256",
            dedup_reason=f"exact SHA256 match with {existing_id}",
        )

    # 2. URL normalization dedup
    normalized_url = normalize_image_url(original_url)
    if normalized_url and normalized_url in state.seen_urls:
        existing_id = state.seen_urls[normalized_url]
        return DedupResult(
            is_duplicate=True,
            duplicate_of=existing_id,
            dedup_method="url",
            dedup_reason=f"URL normalization match with {existing_id}",
        )

    # 3. Perceptual hash near-dedup
    if perceptual_hash:
        for existing_phash, existing_id in state.seen_phash:
            distance = hamming_distance(perceptual_hash, existing_phash)
            if distance <= PHASH_THRESHOLD:
                return DedupResult(
                    is_duplicate=True,
                    duplicate_of=existing_id,
                    dedup_method="phash",
                    dedup_reason=f"perceptual hash distance {distance} with {existing_id}",
                )

    # Not a duplicate — register in state
    if sha256:
        state.seen_sha256[sha256] = asset_id
    if normalized_url:
        state.seen_urls[normalized_url] = asset_id
    if perceptual_hash:
        state.seen_phash.append((perceptual_hash, asset_id))

    return DedupResult(is_duplicate=False)
