"""Downloader module.

Downloads images with manual redirect handling (allow_redirects=False),
per-hop SSRF checks, streaming with size limit, atomic rename, SHA256
filename, Content-Type vs file header verification.
"""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from .url_security import is_safe_url, normalize_url, safe_download_with_redirects, MAX_REDIRECTS
from .downloader_mime import detect_mime

# dev7: downloaded files must keep a real image extension so downstream
# uploaders (e.g. WeChat uploadimg, which rejects extension-less filenames)
# receive a proper filename. Content-Type wins; original URL suffix is the
# fallback; unknown types get no extension (and stay non-uploadable).
MIME_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
URL_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".gif")


def pick_extension(actual_mime: str, content_type: str, url: str) -> str:
    """Choose a file extension: detected MIME > Content-Type > URL suffix."""
    for mime in (actual_mime, content_type):
        ext = MIME_EXTENSIONS.get((mime or "").split(";")[0].strip().lower())
        if ext:
            return ext
    path = url.split("?")[0].split("#")[0].lower()
    for ext in URL_EXTENSIONS:
        if path.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    return ""


@dataclass
class DownloadResult:
    """Result of an image download."""
    success: bool
    url: str
    local_path: str = ""
    sha256: str = ""
    file_size: int = 0
    content_type: str = ""
    actual_mime: str = ""
    mime_mismatch: bool = False
    error: str = ""
    duration_ms: int = 0
    redirect_chain: list[str] = field(default_factory=list)


def download_image(
    url: str,
    output_dir: str | Path,
    max_bytes: int = 15728640,
    timeout: int = 30,
    mode: str = "live",
    fixture_dir: str | Path | None = None,
) -> DownloadResult:
    """Download an image with manual redirect handling and SSRF checks.

    hotfix4: mode="offline_fixture" reads the image from a local fixture dir
    (URL path basename -> <fixture_dir>/<basename>) with ZERO network.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if mode == "offline_fixture":
        return _download_offline(url, output_dir, fixture_dir, max_bytes)
    start_time = time.time()

    # Initial safety check
    sec_result = is_safe_url(url)
    if not sec_result.safe:
        return DownloadResult(
            success=False, url=url,
            error=f"URL security check failed: {', '.join(sec_result.reasons)}",
        )

    # Use a temp path for streaming download
    temp_path = output_dir / f".download_tmp_{os.getpid()}_{int(time.time())}"

    try:
        sha_hex, total_size, content_type, redirect_chain = safe_download_with_redirects(
            url, temp_path, max_bytes=max_bytes, timeout=timeout,
        )

        final_path = output_dir / sha_hex
        actual_mime = detect_mime(temp_path)

        # dev7: keep/append a proper image extension (SHA256 name + ext)
        ext = pick_extension(actual_mime, content_type, url)
        if ext:
            final_path = output_dir / f"{sha_hex}{ext}"

        mime_mismatch = False
        if content_type and content_type != "application/octet-stream":
            ct_normalized = content_type.replace("image/jpg", "image/jpeg")
            actual_normalized = actual_mime.replace("image/jpg", "image/jpeg")
            if ct_normalized != actual_normalized:
                mime_mismatch = True

        # Atomic rename
        if final_path.exists():
            temp_path.unlink(missing_ok=True)
        else:
            temp_path.rename(final_path)

        duration_ms = int((time.time() - start_time) * 1000)
        return DownloadResult(
            success=True, url=url, local_path=str(final_path),
            sha256=sha_hex, file_size=total_size,
            content_type=content_type, actual_mime=actual_mime,
            mime_mismatch=mime_mismatch, duration_ms=duration_ms,
            redirect_chain=redirect_chain,
        )

    except RuntimeError as exc:
        temp_path.unlink(missing_ok=True)
        return DownloadResult(
            success=False, url=url, error=str(exc),
            duration_ms=int((time.time() - start_time) * 1000),
        )
    except Exception as exc:
        temp_path = output_dir / f".download_tmp_{os.getpid()}_{int(time.time())}"
        temp_path.unlink(missing_ok=True)
        return DownloadResult(
            success=False, url=url, error=f"unexpected error: {exc}",
            duration_ms=int((time.time() - start_time) * 1000),
        )


def _download_offline(url: str, output_dir: Path, fixture_dir: str | Path | None,
                      max_bytes: int) -> DownloadResult:
    """hotfix4: offline_fixture image "download" — copies the fixture file whose
    name equals the URL path basename. ZERO network; still size-limited, still
    SHA256-named with a real extension (same downstream contract as live)."""
    if fixture_dir is None:
        return DownloadResult(success=False, url=url,
                              error="fixture_dir required for offline_fixture download")
    from urllib.parse import urlparse
    name = Path(urlparse(url).path).name
    if not name:
        return DownloadResult(success=False, url=url, error="offline: URL has no basename")
    src = Path(fixture_dir) / name
    if not src.is_file():
        return DownloadResult(success=False, url=url,
                              error=f"offline image fixture not found: {src}")
    data = src.read_bytes()
    if len(data) > max_bytes:
        return DownloadResult(success=False, url=url,
                              error=f"file exceeded max size {max_bytes}")
    sha_hex = hashlib.sha256(data).hexdigest()
    final_path = output_dir / f"{sha_hex}{src.suffix.lower()}"
    if not final_path.exists():
        final_path.write_bytes(data)
    actual_mime = detect_mime(final_path)
    return DownloadResult(success=True, url=url, local_path=str(final_path),
                          sha256=sha_hex, file_size=len(data),
                          content_type=actual_mime, actual_mime=actual_mime)
