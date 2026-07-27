"""Uploader module.

Pluggable upload with strict security:
- Unknown upload_mode = error (no silent fallback)
- Unknown copyright = no upload
- MIME from actual detection
- access_token scrubbed from error logs
- response_sha256 generated
- No draft creation, no publishing
"""

from __future__ import annotations

import hashlib
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .downloader_mime import detect_mime

SENSITIVE_PATTERNS = [
    "token", "secret", "cookie", "password", "api_key", "apikey",
    "access_key", "secret_key", "bearer", "authorization",
]

SAFE_FIELD_NAMES = {
    "secrets_detected", "secret_scan_passed", "no_secrets_found",
}

VALID_UPLOAD_MODES = {"dry_run", "wechat_image_host", "stable_storage", "mock"}


def _scrub_token(text: str) -> str:
    """Remove access_token query parameters from strings."""
    return re.sub(r'access_token=[^&\s]+', 'access_token=[REDACTED]', text)


@dataclass
class UploadResult:
    """Result of an upload operation."""
    mode: str
    status: str = "not_uploaded"
    remote_url: str | None = None
    response_sha256: str | None = None
    actual_mime: str = ""
    error: str = ""
    uploaded_at: str = ""


def sanitize_response(data: Any) -> Any:
    """Remove sensitive data from upload response."""
    if isinstance(data, dict):
        return {k: ("[REDACTED]" if any(p in k.lower() for p in SENSITIVE_PATTERNS) else sanitize_response(v))
                for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_response(item) for item in data]
    elif isinstance(data, str):
        lower = data.lower()
        for pattern in SENSITIVE_PATTERNS:
            if pattern in lower:
                return "[REDACTED]"
        return data
    return data


def scan_for_secrets(data: Any) -> list[str]:
    """Scan data for potential secrets."""
    findings: list[str] = []
    if isinstance(data, dict):
        for k, v in data.items():
            if any(p in k.lower() for p in SENSITIVE_PATTERNS) and k.lower() not in SAFE_FIELD_NAMES:
                findings.append(f"sensitive key found: {k}")
            findings.extend(scan_for_secrets(v))
    elif isinstance(data, list):
        for item in data:
            findings.extend(scan_for_secrets(item))
    elif isinstance(data, str):
        lower = data.lower()
        for pattern in SENSITIVE_PATTERNS:
            if pattern in lower:
                findings.append(f"potential secret in value: ...{pattern}...")
    return findings


class DryRunUploader:
    """Default uploader — does not upload anything."""

    def upload(self, local_path: str, asset_id: str = "", copyright_status: str = "unknown") -> UploadResult:
        mime = detect_mime(local_path) if Path(local_path).exists() else ""
        return UploadResult(
            mode="dry_run", status="not_uploaded",
            remote_url=None, response_sha256=None, actual_mime=mime,
        )


class MockUploader:
    """Mock uploader for testing."""

    def __init__(self, simulate_failure: bool = False, simulate_timeout: bool = False):
        self.simulate_failure = simulate_failure
        self.simulate_timeout = simulate_timeout
        self.upload_count = 0

    def upload(self, local_path: str, asset_id: str = "", copyright_status: str = "unknown") -> UploadResult:
        if copyright_status != "known_allowed":
            return UploadResult(
                mode="mock", status="skipped",
                error=f"upload skipped: copyright_status={copyright_status} (only known_allowed can upload)",
            )
        if self.simulate_timeout:
            return UploadResult(mode="mock", status="failed", error="simulated timeout")
        if self.simulate_failure:
            return UploadResult(mode="mock", status="failed", error="simulated upload failure")

        self.upload_count += 1
        mime = detect_mime(local_path) if Path(local_path).exists() else ""
        mock_url = f"https://mock-cdn.example.com/images/{asset_id or f'asset-{self.upload_count}'}.png"
        return UploadResult(
            mode="mock", status="success", remote_url=mock_url,
            response_sha256=hashlib.sha256(mock_url.encode()).hexdigest(),
            actual_mime=mime,
            uploaded_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )


class WechatImageHostUploader:
    """WeChat image host uploader. Only uploads images — NO drafts, NO publishing."""

    def __init__(self):
        self.app_id = os.environ.get("WECHAT_APP_ID", "")
        self.app_secret = os.environ.get("WECHAT_APP_SECRET", "")

    def _get_access_token(self) -> tuple[str, str]:
        if not self.app_id or not self.app_secret:
            return "", "WECHAT_APP_ID or WECHAT_APP_SECRET not set"
        try:
            import requests
            url = "https://api.weixin.qq.com/cgi-bin/token"
            params = {"grant_type": "client_credential", "appid": self.app_id, "secret": self.app_secret}
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if "access_token" in data:
                return data["access_token"], ""
            return "", _scrub_token(f"WeChat token error: {data.get('errmsg', 'unknown')}")
        except Exception as exc:
            return "", _scrub_token(f"token request failed: {exc}")

    def upload(self, local_path: str, asset_id: str = "", copyright_status: str = "unknown") -> UploadResult:
        if copyright_status != "known_allowed":
            return UploadResult(
                mode="wechat_image_host", status="skipped",
                error=f"upload skipped: copyright_status={copyright_status}",
            )
        if not self.app_id or not self.app_secret:
            return UploadResult(
                mode="wechat_image_host", status="failed",
                error="WECHAT_APP_ID or WECHAT_APP_SECRET not set",
            )

        mime = detect_mime(local_path) if Path(local_path).exists() else ""
        token, err = self._get_access_token()
        if err:
            return UploadResult(mode="wechat_image_host", status="failed", error=err, actual_mime=mime)

        try:
            import requests
            url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={token}"
            path = Path(local_path)
            # dev7: WeChat uploadimg rejects extension-less filenames.
            # The multipart filename must carry a real image extension —
            # use the file's own suffix, else derive one from detected MIME.
            upload_name = path.name
            if not path.suffix:
                from .downloader import MIME_EXTENSIONS
                upload_name = path.name + MIME_EXTENSIONS.get(
                    (mime or "").split(";")[0].strip().lower(), ".png")
            with open(path, "rb") as f:
                files = {"media": (upload_name, f, mime or "image/png")}
                resp = requests.post(url, files=files, timeout=30)

            data = resp.json()
            sanitized = sanitize_response(data)

            if "url" in data:
                resp_hash = hashlib.sha256(data["url"].encode()).hexdigest()
                return UploadResult(
                    mode="wechat_image_host", status="success",
                    remote_url=data["url"], response_sha256=resp_hash,
                    actual_mime=mime,
                    uploaded_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                )
            else:
                return UploadResult(
                    mode="wechat_image_host", status="failed",
                    error=_scrub_token(f"upload failed: {sanitized}"),
                    actual_mime=mime,
                )
        except Exception as exc:
            return UploadResult(
                mode="wechat_image_host", status="failed",
                error=_scrub_token(f"upload error: {exc}"),
                actual_mime=mime,
            )


class StableStorageUploader:
    """Stable storage uploader."""

    def __init__(self, base_url: str = "", api_key: str = ""):
        self.base_url = base_url or os.environ.get("STABLE_STORAGE_URL", "")
        self.api_key = api_key or os.environ.get("STABLE_STORAGE_KEY", "")

    def upload(self, local_path: str, asset_id: str = "", copyright_status: str = "unknown") -> UploadResult:
        if copyright_status != "known_allowed":
            return UploadResult(
                mode="stable_storage", status="skipped",
                error=f"upload skipped: copyright_status={copyright_status}",
            )
        if not self.base_url:
            return UploadResult(mode="stable_storage", status="failed", error="STABLE_STORAGE_URL not configured")

        mime = detect_mime(local_path) if Path(local_path).exists() else ""
        try:
            import requests
            path = Path(local_path)
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            with open(path, "rb") as f:
                files = {"file": (path.name, f, mime or "application/octet-stream")}
                resp = requests.post(self.base_url, files=files, headers=headers, timeout=30)
            data = resp.json()
            sanitized = sanitize_response(data)
            if "url" in sanitized:
                resp_hash = hashlib.sha256(str(sanitized["url"]).encode()).hexdigest()
                return UploadResult(
                    mode="stable_storage", status="success",
                    remote_url=sanitized["url"], response_sha256=resp_hash,
                    actual_mime=mime,
                    uploaded_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                )
            else:
                return UploadResult(mode="stable_storage", status="failed",
                                    error=f"upload failed: {sanitized}", actual_mime=mime)
        except Exception as exc:
            return UploadResult(mode="stable_storage", status="failed",
                                 error=_scrub_token(f"upload error: {exc}"), actual_mime=mime)


def create_uploader(mode: str, **kwargs: Any):
    """Create uploader. Raises ValueError on unknown mode."""
    if mode not in VALID_UPLOAD_MODES:
        raise ValueError(f"Unknown upload_mode: '{mode}'. Valid modes: {VALID_UPLOAD_MODES}")
    if mode == "dry_run":
        return DryRunUploader()
    elif mode == "mock":
        return MockUploader(**kwargs)
    elif mode == "wechat_image_host":
        return WechatImageHostUploader()
    elif mode == "stable_storage":
        return StableStorageUploader(**kwargs)
    return DryRunUploader()
