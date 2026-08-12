"""URL security module.

SSRF protection: only allow http/https, block ALL non-public-routable
addresses (loopback, private, link-local, multicast, reserved,
unspecified, documentation, cloud-metadata), handle IPv4-mapped IPv6,
and provide manual redirect-safe fetching.
"""

from __future__ import annotations

import ipaddress
import re
import socket
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse, urlunparse, urljoin

ALLOWED_SCHEMES = {"http", "https"}

BLOCKED_HOSTS = {
    "localhost",
    "0.0.0.0",
    "metadata.google.internal",
    "169.254.169.254",
    "100.100.100.200",
}

MAX_REDIRECTS = 5

# Cloud metadata IP ranges
CLOUD_METADATA_RANGES = [
    ipaddress.ip_network("169.254.169.254/32"),
    ipaddress.ip_network("100.100.100.200/32"),
    ipaddress.ip_network("fd00:ec2::254/128"),
]

# All non-public-routable ranges
BLOCKED_RANGES = [
    # IPv4
    ipaddress.ip_network("0.0.0.0/8"),          # "This host" / unspecified
    ipaddress.ip_network("10.0.0.0/8"),          # Private A
    ipaddress.ip_network("100.64.0.0/10"),       # Carrier-grade NAT
    ipaddress.ip_network("127.0.0.0/8"),         # Loopback
    ipaddress.ip_network("169.254.0.0/16"),      # Link-local
    ipaddress.ip_network("172.16.0.0/12"),       # Private B
    ipaddress.ip_network("192.0.0.0/24"),        # IETF protocol assignments
    ipaddress.ip_network("192.0.2.0/24"),        # TEST-NET-1 (documentation)
    ipaddress.ip_network("192.88.99.0/24"),      # 6to4 relay anycast (deprecated)
    ipaddress.ip_network("192.168.0.0/16"),       # Private C
    ipaddress.ip_network("198.18.0.0/15"),       # Benchmark testing
    ipaddress.ip_network("198.51.100.0/24"),     # TEST-NET-2 (documentation)
    ipaddress.ip_network("203.0.113.0/24"),      # TEST-NET-3 (documentation)
    ipaddress.ip_network("224.0.0.0/4"),         # Multicast
    ipaddress.ip_network("240.0.0.0/4"),         # Reserved
    # IPv6
    ipaddress.ip_network("::1/128"),              # Loopback
    ipaddress.ip_network("::/128"),               # Unspecified
    ipaddress.ip_network("fc00::/7"),             # Unique local
    ipaddress.ip_network("fe80::/10"),            # Link-local
    ipaddress.ip_network("ff00::/8"),             # Multicast
    ipaddress.ip_network("2001:db8::/32"),        # Documentation
] + CLOUD_METADATA_RANGES


@dataclass
class URLSecurityResult:
    """Result of URL security check."""
    safe: bool
    url: str
    reasons: list[str]
    resolved_ip: str | None = None


def normalize_url(url: str) -> str:
    """Normalize a URL: remove fragment, strip auth info."""
    if not url:
        return url
    parsed = urlparse(url)
    netloc = parsed.hostname or ""
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    return urlunparse((
        parsed.scheme,
        netloc,
        parsed.path or "/",
        parsed.params,
        parsed.query,
        "",  # no fragment
    ))


def _is_blocked_ip(ip: ipaddress._BaseAddress) -> bool:
    """Check if an IP address is in any blocked range.

    Handles IPv4-mapped IPv6 addresses by extracting the IPv4 portion.
    """
    # Handle IPv4-mapped IPv6 (::ffff:127.0.0.1)
    if isinstance(ip, ipaddress.IPv6Address):
        if ip.ipv4_mapped is not None:
            ip = ip.ipv4_mapped

    for network in BLOCKED_RANGES:
        # Also check mapped form against IPv4 ranges
        if ip in network:
            return True
        if isinstance(ip, ipaddress.IPv4Address):
            mapped = ipaddress.IPv6Address(f"::ffff:{ip}")
            if mapped in network:
                return True
    return False


def is_safe_url(url: str, require_dns: bool = True) -> URLSecurityResult:
    """Check if a URL is safe (no SSRF).

    - Only http/https
    - No localhost, private, link-local, multicast, reserved, documentation, cloud-metadata
    - DNS resolution and IP re-check (including IPv4-mapped IPv6)
    - No auth credentials in URL
    - require_dns=False (hotfix4, offline_fixture only): every static check still
      applies but the DNS resolution step is skipped — offline runs never touch
      the network, so there is nothing to resolve.
    """
    if not url or not url.strip():
        return URLSecurityResult(safe=False, url=url, reasons=["empty URL"])

    try:
        parsed = urlparse(url)
    except Exception as exc:
        return URLSecurityResult(safe=False, url=url, reasons=[f"parse error: {exc}"])

    scheme = (parsed.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        return URLSecurityResult(
            safe=False, url=url,
            reasons=[f"disallowed scheme: {scheme} (only http/https allowed)"],
        )

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return URLSecurityResult(safe=False, url=url, reasons=["missing hostname"])

    # Strip IPv6 brackets for hostname comparison
    bare_hostname = hostname.strip("[]")

    if bare_hostname in BLOCKED_HOSTS:
        return URLSecurityResult(
            safe=False, url=url,
            reasons=[f"blocked hostname: {bare_hostname}"],
        )

    # Check for userinfo in URL (auth credentials)
    if "@" in (parsed.netloc or ""):
        return URLSecurityResult(
            safe=False, url=url,
            reasons=["auth credentials in URL are not allowed"],
        )

    # Try to parse as IP address (handles both IPv4 and IPv6)
    try:
        ip = ipaddress.ip_address(bare_hostname)
        if _is_blocked_ip(ip):
            return URLSecurityResult(
                safe=False, url=url,
                reasons=[f"blocked IP address: {bare_hostname}"],
            )
        # IP is public — safe
        return URLSecurityResult(safe=True, url=url, reasons=[])
    except ValueError:
        pass  # Not an IP, it's a hostname

    # DNS resolution and re-check (skipped only for offline_fixture runs)
    if not require_dns:
        return URLSecurityResult(safe=True, url=url, reasons=[])
    try:
        addrs = socket.getaddrinfo(bare_hostname, None)
        for addr_info in addrs:
            ip_str = addr_info[4][0]
            try:
                ip = ipaddress.ip_address(ip_str)
                if _is_blocked_ip(ip):
                    return URLSecurityResult(
                        safe=False, url=url,
                        reasons=[f"DNS resolves to blocked IP: {ip_str} for hostname {bare_hostname}"],
                        resolved_ip=ip_str,
                    )
            except ValueError:
                continue
    except socket.gaierror:
        return URLSecurityResult(
            safe=False, url=url,
            reasons=[f"DNS resolution failed for hostname: {bare_hostname}"],
        )

    return URLSecurityResult(safe=True, url=url, reasons=[])


def check_redirect(original_url: str, redirect_url: str, redirect_count: int) -> URLSecurityResult:
    """Check if a redirect target is safe (pre-request check)."""
    if redirect_count >= MAX_REDIRECTS:
        return URLSecurityResult(
            safe=False, url=redirect_url,
            reasons=[f"max redirects ({MAX_REDIRECTS}) exceeded"],
        )
    return is_safe_url(redirect_url)


def safe_fetch_with_redirects(
    url: str,
    timeout: int = 15,
    max_bytes: int = 10 * 1024 * 1024,
    headers: dict[str, str] | None = None,
) -> tuple[str, str, int, list[str]]:
    """Manually fetch a URL with per-hop redirect security checks.

    Uses allow_redirects=False and manually follows Location headers.

    Returns (final_content, final_url, status_code, redirect_chain).
    Raises Exception on security violation or network error.
    """
    import requests as _requests

    current_url = normalize_url(url)
    redirect_chain: list[str] = []

    default_headers = {"User-Agent": "media-enrichment/0.1.0-dev17"}
    if headers:
        default_headers.update(headers)
    for hop in range(MAX_REDIRECTS + 1):
        sec = is_safe_url(current_url)
        if not sec.safe:
            raise RuntimeError(f"URL security check failed: {', '.join(sec.reasons)}")

        response = _requests.get(
            current_url,
            timeout=(timeout, timeout),
            allow_redirects=False,
            headers=default_headers,
            stream=True,
        )

        # Handle redirect
        if response.status_code in (301, 302, 303, 307, 308):
            redirect_chain.append(current_url)
            location = response.headers.get("location", "")
            if not location:
                raise RuntimeError(f"redirect with no Location header at {current_url}")
            next_url = urljoin(current_url, location)
            sec = is_safe_url(next_url)
            if not sec.safe:
                raise RuntimeError(
                    f"redirect to unsafe URL: {', '.join(sec.reasons)}"
                )
            current_url = normalize_url(next_url)
            response.close()
            continue

        # Not a redirect — read content with size limit
        if response.status_code != 200:
            response.close()
            raise RuntimeError(f"HTTP {response.status_code}")

        content = b""
        for chunk in response.iter_content(chunk_size=65536):
            content += chunk
            if len(content) > max_bytes:
                response.close()
                raise RuntimeError(f"response exceeded max bytes {max_bytes}")

        response.close()
        redirect_chain.append(current_url)
        return content.decode("utf-8", errors="replace"), current_url, response.status_code, redirect_chain

    raise RuntimeError(f"max redirects ({MAX_REDIRECTS}) exceeded")


def safe_download_with_redirects(
    url: str,
    output_path,
    max_bytes: int = 15728640,
    timeout: int = 30,
    headers: dict[str, str] | None = None,
) -> tuple[str, int, str, list[str]]:
    """Manually download a file with per-hop redirect security checks.

    Uses allow_redirects=False and manually follows Location headers.
    Streams to output_path with size limit.

    Returns (sha256_hex, file_size, content_type, redirect_chain).
    Raises Exception on security violation or network error.
    """
    import requests as _requests
    import hashlib
    from pathlib import Path

    current_url = normalize_url(url)
    redirect_chain: list[str] = []
    output_path = Path(output_path)

    default_headers = {"User-Agent": "media-enrichment/0.1.0-dev17"}
    if headers:
        default_headers.update(headers)
    for hop in range(MAX_REDIRECTS + 1):
        sec = is_safe_url(current_url)
        if not sec.safe:
            raise RuntimeError(f"URL security check failed: {', '.join(sec.reasons)}")

        response = _requests.get(
            current_url,
            timeout=(timeout, timeout),
            allow_redirects=False,
            headers=default_headers,
            stream=True,
        )

        if response.status_code in (301, 302, 303, 307, 308):
            redirect_chain.append(current_url)
            location = response.headers.get("location", "")
            if not location:
                response.close()
                raise RuntimeError(f"redirect with no Location header at {current_url}")
            next_url = urljoin(current_url, location)
            sec = is_safe_url(next_url)
            if not sec.safe:
                response.close()
                raise RuntimeError(f"redirect to unsafe URL: {', '.join(sec.reasons)}")
            current_url = normalize_url(next_url)
            response.close()
            continue

        if response.status_code != 200:
            response.close()
            raise RuntimeError(f"HTTP {response.status_code}")

        content_type = response.headers.get("content-type", "").split(";")[0].strip()

        sha = hashlib.sha256()
        total = 0
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=65536):
                total += len(chunk)
                if total > max_bytes:
                    f.close()
                    output_path.unlink(missing_ok=True)
                    response.close()
                    raise RuntimeError(f"file exceeded max size {max_bytes}")
                sha.update(chunk)
                f.write(chunk)

        response.close()
        redirect_chain.append(current_url)
        return sha.hexdigest(), total, content_type, redirect_chain

    raise RuntimeError(f"max redirects ({MAX_REDIRECTS}) exceeded")


def is_private_network_url(url: str) -> bool:
    """Quick check if URL points to private network."""
    result = is_safe_url(url)
    return not result.safe
