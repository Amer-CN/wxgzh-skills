"""Image inspector module.

Inspects downloaded images for:
- SHA256 hash
- Perceptual hash (pHash)
- MIME type (from file header)
- Width, height, pixel count
- File size
- Animation frame count
- Transparency
- Aspect ratio
- Decode validity
- EXIF presence
- Decompression bomb protection
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image
import imagehash

# Maximum pixel count to prevent decompression bomb attacks
DEFAULT_MAX_PIXELS = 40_000_000  # 40 megapixels


@dataclass
class ImageInspection:
    """Result of image inspection."""
    sha256: str = ""
    perceptual_hash: str = ""
    mime_type: str = ""
    width: int = 0
    height: int = 0
    pixel_count: int = 0
    file_size: int = 0
    frame_count: int = 1
    has_transparency: bool = False
    aspect_ratio: float = 0.0
    is_animated: bool = False
    is_svg: bool = False
    is_valid: bool = False
    has_exif: bool = False
    decompression_bomb: bool = False
    error: str = ""


def compute_sha256(path: str | Path) -> str:
    """Compute SHA256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect_image(path: str | Path, max_pixels: int = DEFAULT_MAX_PIXELS) -> ImageInspection:
    """Inspect an image file.

    Args:
        path: Path to the image file.
        max_pixels: Maximum allowed pixel count (decompression bomb protection).

    Returns:
        ImageInspection with all measured properties.
    """
    result = ImageInspection()
    path = Path(path)

    if not path.exists():
        result.error = f"file not found: {path}"
        return result

    result.file_size = path.stat().st_size
    result.sha256 = compute_sha256(path)

    # Detect SVG (text-based, not a raster image)
    try:
        first_bytes = path.read_bytes()[:200]
        if b"<?xml" in first_bytes or b"<svg" in first_bytes.lower():
            result.is_svg = True
            result.is_valid = True
            result.mime_type = "image/svg+xml"
            # SVG dimensions are not pixel-based; mark as review_required downstream
            result.width = 0
            result.height = 0
            return result
    except Exception:
        pass

    try:
        # Set decompression bomb protection
        Image.MAX_IMAGE_PIXELS = max_pixels

        img = Image.open(path)

        # Check for decompression bomb
        w, h = img.size
        result.pixel_count = w * h
        if result.pixel_count > max_pixels:
            result.decompression_bomb = True
            result.error = f"decompression bomb: {w}x{h} = {result.pixel_count} pixels > {max_pixels}"
            return result

        result.width = w
        result.height = h
        result.aspect_ratio = round(w / h, 4) if h > 0 else 0.0
        result.mime_type = Image.MIME.get(img.format, "application/octet-stream")

        # Check animation
        try:
            frames = getattr(img, "n_frames", 1)
            result.frame_count = frames
            result.is_animated = frames > 1
        except Exception:
            result.frame_count = 1
            result.is_animated = False

        # Check transparency
        if img.mode in ("RGBA", "LA", "P"):
            result.has_transparency = True
        else:
            result.has_transparency = False

        # Check EXIF
        try:
            exif = img.getexif()
            result.has_exif = bool(exif)
        except Exception:
            result.has_exif = False

        # Compute perceptual hash
        try:
            phash = imagehash.phash(img)
            result.perceptual_hash = str(phash)
        except Exception:
            result.perceptual_hash = ""

        result.is_valid = True

    except Image.DecompressionBombError:
        result.decompression_bomb = True
        result.error = "decompression bomb detected by PIL"
    except Exception as exc:
        result.error = f"image inspection failed: {exc}"

    return result
