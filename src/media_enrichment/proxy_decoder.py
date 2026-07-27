"""Proxy decoder module.

Decodes AI HOT img-proxy URLs: URL encoding, double URL encoding,
query parameter wrapping, and Base64 URL encoding.

Records decode method and depth. No eval, no dynamic script execution,
no unbounded recursion. Max decode depth enforced.
"""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from urllib.parse import unquote, urlparse, parse_qs, urlunparse

MAX_DECODE_DEPTH = 5

# Patterns that indicate a proxy URL
PROXY_PATTERNS = [
    r"img-proxy",
    r"image-proxy",
    r"proxy.*image",
    r"img\.proxy",
    r"/proxy/",
]

# A URL that looks like it could be a proxy
PROXY_INDICATOR = re.compile("|".join(PROXY_PATTERNS), re.IGNORECASE)


@dataclass
class DecodeResult:
    """Result of proxy URL decoding."""
    encoded_url: str
    decoded_url: str
    decode_method: str
    decode_depth: int
    is_proxy: bool


def _looks_like_url(s: str) -> bool:
    """Heuristic: does the string look like a URL after decoding?"""
    if not s:
        return False
    return s.startswith("http://") or s.startswith("https://")


def _try_url_decode(s: str) -> tuple[str, bool]:
    """Try URL-decoding. Returns (decoded, was_decoded)."""
    try:
        decoded = unquote(s)
        if decoded != s:
            return decoded, True
    except Exception:
        pass
    return s, False


def _try_base64_decode(s: str) -> tuple[str, bool]:
    """Try Base64-decoding. Returns (decoded, was_decoded)."""
    if not s or len(s) < 8:
        return s, False
    # Only try if it looks like Base64
    try:
        # Pad if needed
        padded = s + "=" * (4 - len(s) % 4) if len(s) % 4 else s
        decoded = base64.urlsafe_b64decode(padded).decode("utf-8", errors="ignore")
        if _looks_like_url(decoded):
            return decoded, True
    except Exception:
        pass
    return s, False


def _extract_from_query_param(url: str) -> str | None:
    """Extract a target URL from a query parameter."""
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        for key, values in params.items():
            for val in values:
                if _looks_like_url(val):
                    return val
                # Try decoding the param value
                decoded_val, was_decoded = _try_url_decode(val)
                if _looks_like_url(decoded_val):
                    return decoded_val
                decoded_b64, was_b64 = _try_base64_decode(val)
                if _looks_like_url(decoded_b64):
                    return decoded_b64
    except Exception:
        pass
    return None


def decode_proxy_url(url: str, depth: int = 0) -> DecodeResult:
    """Decode a potentially proxied image URL.

    Supports:
    - Single URL encoding
    - Double URL encoding
    - Query parameter wrapping
    - Base64 URL encoding

    Limits recursion to MAX_DECODE_DEPTH.
    No eval, no dynamic script execution.
    """
    if depth >= MAX_DECODE_DEPTH:
        return DecodeResult(
            encoded_url=url,
            decoded_url=url,
            decode_method="max_depth_reached",
            decode_depth=depth,
            is_proxy=False,
        )

    is_proxy = bool(PROXY_INDICATOR.search(url))

    if not is_proxy:
        # Even if not a proxy, try one round of URL decoding in case it's encoded
        decoded, was_decoded = _try_url_decode(url)
        if was_decoded and _looks_like_url(decoded) and decoded != url:
            # Recurse to check for double encoding
            sub = decode_proxy_url(decoded, depth + 1)
            return DecodeResult(
                encoded_url=url,
                decoded_url=sub.decoded_url,
                decode_method="url_decode" + ("+" + sub.decode_method if sub.decode_method != "none" else ""),
                decode_depth=sub.decode_depth,
                is_proxy=False,
            )
        return DecodeResult(
            encoded_url=url,
            decoded_url=url,
            decode_method="none",
            decode_depth=depth,
            is_proxy=False,
        )

    # It's a proxy URL — try multiple decode strategies

    # Strategy 1: Extract from query parameter
    target = _extract_from_query_param(url)
    if target:
        sub = decode_proxy_url(target, depth + 1)
        return DecodeResult(
            encoded_url=url,
            decoded_url=sub.decoded_url,
            decode_method="query_param_extract" + ("+" + sub.decode_method if sub.decode_method != "none" else ""),
            decode_depth=depth + 1,
            is_proxy=True,
        )

    # Strategy 2: URL decode the whole URL
    decoded, was_decoded = _try_url_decode(url)
    if was_decoded and decoded != url:
        sub = decode_proxy_url(decoded, depth + 1)
        if sub.decoded_url != url:
            return DecodeResult(
                encoded_url=url,
                decoded_url=sub.decoded_url,
                decode_method="url_decode" + ("+" + sub.decode_method if sub.decode_method != "none" else ""),
                decode_depth=depth + 1,
                is_proxy=True,
            )

    # Strategy 3: Try extracting the path component and Base64 decode
    try:
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        last_segment = path.split("/")[-1] if path else ""
        if last_segment:
            decoded_b64, was_b64 = _try_base64_decode(last_segment)
            if was_b64 and _looks_like_url(decoded_b64):
                sub = decode_proxy_url(decoded_b64, depth + 1)
                return DecodeResult(
                    encoded_url=url,
                    decoded_url=sub.decoded_url,
                    decode_method="base64_path" + ("+" + sub.decode_method if sub.decode_method != "none" else ""),
                    decode_depth=depth + 1,
                    is_proxy=True,
                )
    except Exception:
        pass

    # Could not decode further
    return DecodeResult(
        encoded_url=url,
        decoded_url=url,
        decode_method="unresolved_proxy",
        decode_depth=depth,
        is_proxy=True,
    )
