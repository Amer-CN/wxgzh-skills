#!/usr/bin/env python3
"""Generate test image fixtures for media-enrichment tests."""

from pathlib import Path
from PIL import Image
import struct
import io

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "images"
FIXTURE_DIR.mkdir(parents=True, exist_ok=True)


def create_valid_photo():
    """Create a valid JPEG photo (800x600)."""
    img = Image.new("RGB", (800, 600), color=(100, 150, 200))
    # Add some variation
    for x in range(100, 700, 50):
        for y in range(100, 500, 50):
            img.putpixel((x, y), (200, 100, 50))
    img.save(FIXTURE_DIR / "valid-photo.jpg", "JPEG", quality=85)


def create_valid_chart_png():
    """Create a valid PNG chart (800x500)."""
    img = Image.new("RGB", (800, 500), color=(255, 255, 255))
    # Draw some bars
    for x in range(100, 200):
        for y in range(100, 400):
            img.putpixel((x, y), (68, 114, 196))
    for x in range(300, 400):
        for y in range(200, 400):
            img.putpixel((x, y), (237, 125, 49))
    img.save(FIXTURE_DIR / "valid-chart.png", "PNG")


def create_duplicate_resized():
    """Create a resized version of valid-photo.jpg."""
    original = Image.open(FIXTURE_DIR / "valid-photo.jpg")
    resized = original.resize((400, 300))
    resized.save(FIXTURE_DIR / "duplicate-resized.jpg", "JPEG", quality=85)


def create_logo():
    """Create a small logo PNG (200x60)."""
    img = Image.new("RGBA", (200, 60), color=(50, 50, 150, 255))
    img.save(FIXTURE_DIR / "logo.png", "PNG")


def create_avatar():
    """Create a small avatar JPG (80x80)."""
    img = Image.new("RGB", (80, 80), color=(200, 200, 200))
    img.save(FIXTURE_DIR / "avatar.jpg", "JPEG", quality=75)


def create_tracking_pixel():
    """Create a 1x1 tracking pixel GIF."""
    img = Image.new("RGB", (1, 1), color=(255, 255, 255))
    img.save(FIXTURE_DIR / "tracking-pixel.gif", "GIF")


def create_corrupted():
    """Create a corrupted JPEG (invalid header)."""
    data = b"NOT_A_VALID_IMAGE_FILE" * 100
    with open(FIXTURE_DIR / "corrupted.jpg", "wb") as f:
        f.write(data)


def create_oversized_metadata():
    """Create a PNG with large metadata but valid structure."""
    img = Image.new("RGB", (640, 360), color=(100, 100, 100))
    img.save(FIXTURE_DIR / "oversized-metadata.png", "PNG")


def create_background_image_html():
    """Create an HTML fixture with background-image."""
    html = """<!DOCTYPE html>
<html>
<head><title>Background Image Test</title></head>
<body style="background-image: url('https://example.com/images/bg-header.jpg')">
  <h1 style="background-image: url(https://example.com/images/bg-title.png)">Title with BG</h1>
  <div style="background-image:url('https://example.com/images/bg-card.jpg')">Card</div>
</body>
</html>
"""
    fixture_dir = Path(__file__).resolve().parents[1] / "fixtures" / "html"
    with open(fixture_dir / "background-image.html", "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    print("Generating test image fixtures...")
    create_valid_photo()
    create_valid_chart_png()
    create_duplicate_resized()
    create_logo()
    create_avatar()
    create_tracking_pixel()
    create_corrupted()
    create_oversized_metadata()
    create_background_image_html()
    print(f"Done. Fixtures in {FIXTURE_DIR}")
