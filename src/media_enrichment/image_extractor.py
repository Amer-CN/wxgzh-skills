"""Image extractor module.

Parses HTML to discover image candidates from:
- img[src], img[srcset], img[data-src], img[data-original], img[data-lazy-src]
- source[srcset] (inside picture elements)
- meta[property="og:image"], meta[name="twitter:image"]
- JSON-LD image (string and array)
- CSS background-image (safe static forms only)
- AI HOT img-proxy URLs
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup


@dataclass
class ImageCandidate:
    """A discovered image candidate."""
    url: str
    extraction_method: str
    raw_srcset: str = ""
    width_hint: int | None = None
    height_hint: int | None = None
    alt: str = ""
    context: str = ""  # surrounding HTML context for classification


@dataclass
class ExtractionResult:
    """Result of image extraction from a page."""
    candidates: list[ImageCandidate] = field(default_factory=list)
    page_title: str = ""
    page_url: str = ""
    errors: list[str] = field(default_factory=list)


# Pattern for safe static background-image URLs
BG_IMAGE_PATTERN = re.compile(
    r'background-image\s*:\s*url\(\s*[\'"]?(https?://[^\'"\)]+)[\'"]?\s*\)',
    re.IGNORECASE,
)

# Pattern for srcset entries
SRCSET_ENTRY_PATTERN = re.compile(r'(\S+)(?:\s+(\d+)w)?(?:\s+(\d+)x)?')


def extract_images(html: str, page_url: str = "") -> ExtractionResult:
    """Extract all image candidates from HTML.

    Args:
        html: HTML content string.
        page_url: Base URL for resolving relative URLs.

    Returns:
        ExtractionResult with all discovered candidates.
    """
    result = ExtractionResult(page_url=page_url)

    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception as exc:
        result.errors.append(f"HTML parse error: {exc}")
        return result

    result.page_title = soup.title.string.strip() if soup.title and soup.title.string else ""

    # 1. img[src]
    for img in soup.find_all("img", src=True):
        src = img["src"].strip()
        if src:
            resolved = urljoin(page_url, src) if page_url else src
            candidate = ImageCandidate(
                url=resolved,
                extraction_method="img.src",
                alt=img.get("alt", ""),
                context=str(img)[:200],
            )
            # Check for width/height attributes
            if img.get("width"):
                try:
                    candidate.width_hint = int(img["width"])
                except ValueError:
                    pass
            if img.get("height"):
                try:
                    candidate.height_hint = int(img["height"])
                except ValueError:
                    pass
            result.candidates.append(candidate)

    # 2. img[srcset] and source[srcset]
    for elem in soup.find_all(attrs={"srcset": True}):
        srcset = elem["srcset"]
        method = "img.srcset" if elem.name == "img" else "source.srcset"
        entries = _parse_srcset(srcset, page_url)
        for url, width, dpr in entries:
            candidate = ImageCandidate(
                url=url,
                extraction_method=method,
                raw_srcset=srcset[:200],
                width_hint=width,
                context=str(elem)[:200],
            )
            result.candidates.append(candidate)

    # 3. img[data-src], img[data-original], img[data-lazy-src]
    for attr in ("data-src", "data-original", "data-lazy-src"):
        for img in soup.find_all("img", attrs={attr: True}):
            src = img[attr].strip()
            if src:
                resolved = urljoin(page_url, src) if page_url else src
                candidate = ImageCandidate(
                    url=resolved,
                    extraction_method=f"img.{attr}",
                    alt=img.get("alt", ""),
                    context=str(img)[:200],
                )
                result.candidates.append(candidate)

    # 4. meta[property="og:image"]
    for meta in soup.find_all("meta", attrs={"property": "og:image"}):
        content = meta.get("content", "").strip()
        if content:
            resolved = urljoin(page_url, content) if page_url else content
            result.candidates.append(ImageCandidate(
                url=resolved,
                extraction_method="og:image",
                context=str(meta)[:200],
            ))

    # 5. meta[name="twitter:image"]
    for meta in soup.find_all("meta", attrs={"name": "twitter:image"}):
        content = meta.get("content", "").strip()
        if content:
            resolved = urljoin(page_url, content) if page_url else content
            result.candidates.append(ImageCandidate(
                url=resolved,
                extraction_method="twitter:image",
                context=str(meta)[:200],
            ))

    # 6. JSON-LD image
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            _extract_json_ld_images(data, page_url, result)
        except (json.JSONDecodeError, TypeError):
            pass

    # 7. CSS background-image (safe static forms only)
    for match in BG_IMAGE_PATTERN.finditer(html):
        url = match.group(1).strip()
        if url:
            resolved = urljoin(page_url, url) if page_url else url
            result.candidates.append(ImageCandidate(
                url=resolved,
                extraction_method="background-image",
                context=match.group(0)[:200],
            ))

    # Deduplicate by URL while preserving first occurrence
    seen_urls: set[str] = set()
    unique: list[ImageCandidate] = []
    for c in result.candidates:
        if c.url not in seen_urls:
            seen_urls.add(c.url)
            unique.append(c)
    result.candidates = unique

    return result


def _parse_srcset(srcset: str, page_url: str = "") -> list[tuple[str, int | None, int | None]]:
    """Parse a srcset attribute into (url, width, dpr) tuples."""
    entries = []
    for part in srcset.split(","):
        part = part.strip()
        if not part:
            continue
        m = SRCSET_ENTRY_PATTERN.match(part)
        if m:
            url = m.group(1)
            width = int(m.group(2)) if m.group(2) else None
            dpr = int(m.group(3)) if m.group(3) else None
            resolved = urljoin(page_url, url) if page_url else url
            entries.append((resolved, width, dpr))
    return entries


def _extract_json_ld_images(data: Any, page_url: str, result: ExtractionResult) -> None:
    """Recursively extract image URLs from JSON-LD data."""
    if isinstance(data, dict):
        # Direct image field
        image = data.get("image")
        if isinstance(image, str):
            resolved = urljoin(page_url, image) if page_url else image
            result.candidates.append(ImageCandidate(
                url=resolved,
                extraction_method="json-ld.image",
                context=json.dumps(data)[:200],
            ))
        elif isinstance(image, list):
            for img_url in image:
                if isinstance(img_url, str):
                    resolved = urljoin(page_url, img_url) if page_url else img_url
                    result.candidates.append(ImageCandidate(
                        url=resolved,
                        extraction_method="json-ld.image",
                        context=json.dumps(data)[:200],
                    ))
        # Recurse into nested objects
        for key, val in data.items():
            if key != "image" and isinstance(val, (dict, list)):
                _extract_json_ld_images(val, page_url, result)
    elif isinstance(data, list):
        for item in data:
            _extract_json_ld_images(item, page_url, result)
