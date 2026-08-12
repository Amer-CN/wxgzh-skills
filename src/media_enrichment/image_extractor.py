"""Image extractor module.

Parses HTML to discover image candidates from:
- img[src], img[srcset], img[data-src], img[data-original], img[data-lazy-src]
- source[srcset] (inside picture elements)
- meta[property="og:image"], meta[name="twitter:image"]
- JSON-LD image (string and array)
- CSS background-image (safe static forms only)
- AI HOT img-proxy URLs

OBS-86(档62):正文边界判定。提取阶段对每个 img 计算页面区域
(body / peripheral / unknown)与所属章节(文档序前最近 h1/h2/h3):
- peripheral(侧边栏/推荐位/广告/页眉页脚/追踪像素/惰性占位 src)
  在下载前直接排除——零第三方请求;
- unknown(结构无法识别)保留为候选但标记位置未知,由 Pipeline 侧
  OBS-87 批准闸门拦下,不得默认收录;
- URL 模式判定(logo/avatar/ad/tracking)仍归 image_classifier,
  本模块不做 URL 模式判定,避免口径分裂(OBS-31 教训)。
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
    title: str = ""  # 档HF-4/OBS-245:img title 属性(内容描述 page_alt 级证据)
    context: str = ""  # surrounding HTML context for classification
    # OBS-86(档62):正文边界判定。page_region ∈ body / peripheral / unknown;
    # section_heading/section_level 为该图在文档序中前最近 h1/h2/h3(跨章节归属)。
    page_region: str = "unknown"
    section_heading: str = ""
    section_level: str = ""
    # 76G 增补/OBS-266:视频封面标记(og:image+og:video / <video poster> /
    # twitter:player:image / 站内页 img-proxy thumb);视频本体不下载不上传。
    video_poster: bool = False


@dataclass
class ExtractionResult:
    """Result of image extraction from a page."""
    candidates: list[ImageCandidate] = field(default_factory=list)
    page_title: str = ""
    page_url: str = ""
    errors: list[str] = field(default_factory=list)
    # OBS-86(档62):提取阶段排除的页面周边图(下载前排除,零第三方请求)
    excluded: list[dict] = field(default_factory=list)


def _meta_content(soup, prop: str) -> str:
    """档HF-4/OBS-245:取 meta[property=prop] 或 meta[name=prop] 的 content 文本。"""
    for attrs in ({"property": prop}, {"name": prop}):
        for meta in soup.find_all("meta", attrs=attrs):
            text = (meta.get("content") or "").strip()
            if text:
                return text
    return ""


# Pattern for safe static background-image URLs
BG_IMAGE_PATTERN = re.compile(
    r'background-image\s*:\s*url\(\s*[\'"]?(https?://[^\'"\)]+)[\'"]?\s*\)',
    re.IGNORECASE,
)

# Pattern for srcset entries
SRCSET_ENTRY_PATTERN = re.compile(r'(\S+)(?:\s+(\d+)w)?(?:\s+(\d+)x)?')

# OBS-86(档62):正文边界判定启发式(容器语义 + 尺寸属性)。
_SECTION_HEADING_LEVELS = ("h1", "h2", "h3")
_PERIPHERAL_TAGS = {"aside", "nav", "header", "footer"}
_PERIPHERAL_ROLES = {"complementary", "navigation", "banner", "contentinfo"}
_BODY_TAGS = {"article", "main"}
_BODY_ROLES = {"main"}
_PERIPHERAL_HINTS = ("sidebar", "recommend", "related", "ad", "banner", "footer",
                     "header", "nav", "menu", "comment", "avatar", "hot", "rank",
                     "info-list", "advert", "promo", "sponsor")
_BODY_HINTS = ("post_content", "post-content", "article_content", "article-content",
               "news_content", "main-content", "main_content", "content")
# 惰性加载占位 src 特征(data: URI 或已知占位文件名);存在真实 srcset/data-* 时排除
_PLACEHOLDER_SRC_TOKENS = ("t.png", "blank", "placeholder", "1x1", "pixel")


def _tokens_of(text: str) -> set[str]:
    """class/id 提示词匹配用的小写词元。"""
    return {t for t in re.split(r"[^0-9a-z]+", text.lower()) if t}


def _tiny_attr(w, h) -> bool:
    try:
        return int(w) <= 5 and int(h) <= 5
    except (TypeError, ValueError):
        return False


def _peripheral_reason(img) -> str:
    w, h = img.get("width"), img.get("height")
    if _tiny_attr(w, h):
        return f"tiny image attribute {w}x{h} — likely tracking pixel (OBS-86)"
    return ("peripheral page region (aside/nav/header/footer or "
            "sidebar/recommend/ad hints) — excluded before download (OBS-86)")


def _classify_page_region(img) -> str:
    """DOM 容器语义判定:peripheral(周边)> body(正文)> unknown。

    依据:祖先标签(aside/nav/header/footer/article/main)、ARIA role、
    class/id 提示词。peripheral 优先级高于 body(正文容器内的广告仍是广告)。"""
    if _tiny_attr(img.get("width"), img.get("height")):
        return "peripheral"
    node = img.parent
    for _ in range(10):
        if node is None or node.name is None:
            break
        name = node.name.lower()
        role = str(node.get("role", "") or "").lower()
        cls = _tokens_of(" ".join(node.get("class", []) or []))
        nid = _tokens_of(str(node.get("id", "") or ""))
        if name in _PERIPHERAL_TAGS or role in _PERIPHERAL_ROLES:
            return "peripheral"
        if any(t in _PERIPHERAL_HINTS for t in (cls | nid)):
            return "peripheral"
        if name in _BODY_TAGS or role in _BODY_ROLES:
            return "body"
        if any(t in _BODY_HINTS for t in (cls | nid)):
            return "body"
        node = node.parent
    return "unknown"


def _is_placeholder_src(img, src: str) -> bool:
    """惰性加载占位:同一 img 存在真实 srcset/data-* 时,占位 src 不产候选。"""
    has_real = any(img.get(a) for a in ("srcset", "data-src", "data-original",
                                        "data-lazy-src"))
    if not has_real:
        return False
    if src.startswith("data:"):
        return True
    low = src.split("?")[0].rsplit("/", 1)[-1].lower()
    return low in _PLACEHOLDER_SRC_TOKENS


def _apply_region(candidate: ImageCandidate, region_map: dict,
                  peripheral_ids: set,
                  elem) -> bool:
    """把扫描阶段算好的区域/章节归属挂到候选上(source 元素取其 picture/img 祖先)。

    返回 True 保留候选;False 表示该元素属周边区域(扫描阶段已排除),
    调用方不得加入候选——确保周边图在下载前被排除。"""
    key = id(elem)
    if key not in region_map and elem.name == "source":
        ancestor = elem.parent
        for _ in range(4):
            if ancestor is None:
                break
            if ancestor.name == "img" and id(ancestor) in region_map:
                key = id(ancestor)
                break
            ancestor = ancestor.parent
    if key in peripheral_ids:
        return False
    region, heading, level = region_map.get(key, ("unknown", "", ""))
    candidate.page_region = region
    candidate.section_heading = heading
    candidate.section_level = level
    return True


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

    # OBS-86(档62):单遍文档序扫描——页面区域(正文/周边/未知)+ 所属章节
    # (前最近 h1/h2/h3)。周边图在提取阶段直接排除:下载前,零第三方请求。
    region_map: dict[int, tuple[str, str, str]] = {}
    peripheral_ids: set[int] = set()
    last_heading: tuple[str, str] | None = None
    for node in soup.find_all([*_SECTION_HEADING_LEVELS, "img"]):
        if node.name in _SECTION_HEADING_LEVELS:
            text = node.get_text(strip=True)
            if text:
                last_heading = (node.name, text)
        elif node.name == "img":
            region = _classify_page_region(node)
            if region == "peripheral":
                result.excluded.append({"url": (node.get("src", "") or "")[:200],
                                        "region": "peripheral",
                                        "reason": _peripheral_reason(node)})
                peripheral_ids.add(id(node))
                continue
            heading = last_heading[1] if last_heading else ""
            level = last_heading[0] if last_heading else ""
            region_map[id(node)] = (region, heading, level)

    # 1. img[src]
    for img in soup.find_all("img", src=True):
        src = img["src"].strip()
        if src:
            resolved = urljoin(page_url, src) if page_url else src
            if _is_placeholder_src(img, src):
                result.excluded.append({"url": resolved[:200], "region": "peripheral",
                                        "reason": "lazy-load placeholder src (real URL in srcset/data-*) — excluded before download"})
                continue
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
            if not _apply_region(candidate, region_map, peripheral_ids, img):
                result.excluded.append({"url": resolved[:200], "region": "peripheral",
                                        "reason": "peripheral page region — excluded before download (OBS-86)"})
                continue
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
            if not _apply_region(candidate, region_map, peripheral_ids, elem):
                result.excluded.append({"url": url[:200], "region": "peripheral",
                                        "reason": "peripheral page region — excluded before download (OBS-86)"})
                continue
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
                    title=img.get("title", ""),
                    context=str(img)[:200],
                )
                if not _apply_region(candidate, region_map, peripheral_ids, img):
                    result.excluded.append({"url": resolved[:200], "region": "peripheral",
                                            "reason": "peripheral page region — excluded before download (OBS-86)"})
                    continue
                result.candidates.append(candidate)

    # 4. meta[property="og:image"]
    # 档HF-4/OBS-247:meta 通道图对正常 URL 放行(不再因通道被拒)。
    # 档HF-4/OBS-245:meta 通道 content_description 用 og:title/og:description
    # 作 page_context(严禁 claim 文本填充)。
    og_title = _meta_content(soup, "og:title")
    og_desc = _meta_content(soup, "og:description")
    meta_context = " ".join(t for t in (og_title, og_desc) if t).strip()
    for meta in soup.find_all("meta", attrs={"property": "og:image"}):
        content = meta.get("content", "").strip()
        if content:
            resolved = urljoin(page_url, content) if page_url else content
            result.candidates.append(ImageCandidate(
                url=resolved,
                extraction_method="og:image",
                context=meta_context or str(meta)[:200],
            ))

    # 5b. 76G 增补/OBS-266:视频封面通道——页面为视频型(og:video / twitter:player /
    # <video>)时抽取封面:<video poster>、twitter:player:image、og:image(视频页),
    # 以及站内页 img-proxy thumb(img[src] 已提取,此处统一补 video_poster 标记)。
    is_video_page = bool(soup.find("video")) or bool(
        _meta_content(soup, "og:video") or _meta_content(soup, "og:video:url")
        or _meta_content(soup, "twitter:player") or _meta_content(soup, "twitter:player:stream"))
    has_og_video = bool(_meta_content(soup, "og:video") or _meta_content(soup, "og:video:url"))
    if is_video_page:
        for vtag in soup.find_all("video"):
            poster = (vtag.get("poster") or "").strip()
            if poster:
                resolved = urljoin(page_url, poster) if page_url else poster
                result.candidates.append(ImageCandidate(
                    url=resolved, extraction_method="video_poster",
                    video_poster=True, context="<video poster>",
                    page_region="body"))
        for meta in soup.find_all("meta", attrs={"name": "twitter:player:image"}):
            content = meta.get("content", "").strip()
            if content:
                resolved = urljoin(page_url, content) if page_url else content
                result.candidates.append(ImageCandidate(
                    url=resolved, extraction_method="twitter:player:image",
                    video_poster=True, context=str(meta)[:200]))
        # og:image 在视频页 = 视频封面;img-proxy thumb 同为封面形态
        for cand in result.candidates:
            if cand.extraction_method == "og:image" and has_og_video:
                cand.video_poster = True
            if ("img-proxy" in cand.url or "thumb" in cand.url.lower()):
                cand.video_poster = True

    # 5. meta[name="twitter:image"]
    for meta in soup.find_all("meta", attrs={"name": "twitter:image"}):
        content = meta.get("content", "").strip()
        if content:
            resolved = urljoin(page_url, content) if page_url else content
            result.candidates.append(ImageCandidate(
                url=resolved,
                extraction_method="twitter:image",
                context=meta_context or str(meta)[:200],
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
