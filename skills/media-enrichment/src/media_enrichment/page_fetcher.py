"""Page fetcher module.

Fetches AI HOT permalink HTML in live or offline_fixture mode.
Uses manual redirect handling (allow_redirects=False) with per-hop
security checks. No cookies, tokens, or auth headers recorded.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .url_security import is_safe_url, normalize_url, safe_fetch_with_redirects

# Maximum HTML response size (10 MB)
MAX_PAGE_BYTES = 10 * 1024 * 1024

# Headers that must never be recorded
SENSITIVE_HEADERS = {
    "authorization", "cookie", "set-cookie", "x-api-key",
    "x-auth-token", "x-secret", "api-key", "proxy-authorization",
}

# dev7: explicit no-repost / no-use statements. Per copyright policy
# ALLOW_UNLESS_EXPLICITLY_PROHIBITED, ONLY these explicit phrases on the
# ORIGINAL source page (not the AI HOT detail page) block image use.
NO_REPOST_PHRASES = [
    "禁止转载", "不得转载", "未经许可不得转载", "严禁转载",
    "禁止使用", "不得使用", "禁止复制", "不得复制",
]


def scan_no_repost(html: str) -> list[str]:
    """Return the explicit no-repost phrases found in a page's HTML.

    Must be run against the ORIGINAL source page (source_url); the AI HOT
    detail page alone is not sufficient evidence either way.
    """
    return [p for p in NO_REPOST_PHRASES if p in (html or "")]


@dataclass
class FetchResult:
    """Result of a page fetch."""
    success: bool
    url: str
    final_url: str = ""
    status_code: int = 0
    content: str = ""
    content_sha256: str = ""
    fetched_at: str = ""
    duration_ms: int = 0
    error: str = ""
    redirect_chain: list[str] = field(default_factory=list)
    response_headers_sanitized: dict[str, str] = field(default_factory=dict)


def _sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    """Remove sensitive headers from recorded metadata."""
    return {
        k: "[REDACTED]" if k.lower() in SENSITIVE_HEADERS else v
        for k, v in headers.items()
    }


def fetch_page(
    url: str,
    mode: str = "live",
    fixture_dir: str | Path | None = None,
    timeout: int = 15,
) -> FetchResult:
    """Fetch an HTML page."""
    if mode == "offline_fixture":
        return _fetch_offline(url, fixture_dir)
    elif mode == "live":
        return _fetch_live(url, timeout)
    else:
        return FetchResult(success=False, url=url, error=f"unknown mode: {mode}")


def _fetch_offline(url: str, fixture_dir: str | Path | None) -> FetchResult:
    """Fetch from a local fixture file."""
    if fixture_dir is None:
        return FetchResult(success=False, url=url, error="fixture_dir required for offline mode")

    fixture_dir = Path(fixture_dir)
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        slug = parsed.path.rstrip("/").split("/")[-1] or "index"
        fixture_path = fixture_dir / f"{slug}.html"
    except Exception:
        fixture_path = fixture_dir / "index.html"

    if not fixture_path.exists():
        return FetchResult(success=False, url=url, error=f"fixture not found: {fixture_path}")

    content = fixture_path.read_text(encoding="utf-8")
    return FetchResult(
        success=True, url=url, final_url=url, status_code=200,
        content=content,
        content_sha256=hashlib.sha256(content.encode("utf-8")).hexdigest(),
        fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        duration_ms=0,
        response_headers_sanitized={"content-type": "text/html; charset=utf-8"},
    )


def _fetch_live(url: str, timeout: int) -> FetchResult:
    """Fetch a live URL with manual redirect handling and per-hop SSRF checks."""
    start_time = time.time()

    try:
        content, final_url, status_code, redirect_chain = safe_fetch_with_redirects(
            url, timeout=timeout, max_bytes=MAX_PAGE_BYTES,
        )

        content_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
        duration_ms = int((time.time() - start_time) * 1000)

        return FetchResult(
            success=True, url=url, final_url=final_url, status_code=status_code,
            content=content, content_sha256=content_sha,
            fetched_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            duration_ms=duration_ms, redirect_chain=redirect_chain,
        )

    except RuntimeError as exc:
        return FetchResult(
            success=False, url=url, error=str(exc),
            duration_ms=int((time.time() - start_time) * 1000),
        )
    except Exception as exc:
        return FetchResult(
            success=False, url=url, error=f"unexpected error: {exc}",
            duration_ms=int((time.time() - start_time) * 1000),
        )
