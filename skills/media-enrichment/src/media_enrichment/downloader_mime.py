"""MIME detection from file header (magic bytes)."""

from __future__ import annotations

from pathlib import Path

MAGIC_BYTES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
    b"RIFF": "image/webp",
    b"\x00\x00\x01\x00": "image/x-icon",
    b"\x00\x00\x02\x00": "image/x-icon",
}

WEBP_CHECK = b"WEBP"


def detect_mime(file_path: str | Path) -> str:
    """Detect MIME type from file header (magic bytes)."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(16)

        for magic, mime in MAGIC_BYTES.items():
            if header.startswith(magic):
                if magic == b"RIFF" and len(header) >= 12:
                    if header[8:12] == WEBP_CHECK:
                        return "image/webp"
                return mime

        if header.startswith(b"<?xml") or header.startswith(b"<svg"):
            content = Path(file_path).read_text(encoding="utf-8", errors="ignore")[:500]
            if "<svg" in content.lower():
                return "image/svg+xml"
    except Exception:
        pass
    return "application/octet-stream"
