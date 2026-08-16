#!/usr/bin/env python3
"""Validate semantic-map.yaml against article.md and formatter registry.

Checks (v0.3.0-rc1-hotfix.2):
  - schema_version present and == "1.0"
  - article section with id/title
  - block_id unique
  - role in allowed vocabulary (41 roles, no article_wrapper)
  - source_anchor required for all non-signature roles (exact_text or start_text/end_text)
  - source_anchor locatable and unique in article.md (within heading_path section)
  - heading_path exists, follows hierarchy, and section contains anchor
  - deep payload validation per role (all 41 roles)
  - payload content provenance: substantive content must come from source span
  - URL provenance: URLs must be in source span or declared in author_assets
  - evidence-map required when evidence-backed roles (fact/statistic/case) are present
  - evidence_required blocks have evidence_ids validated against evidence-map
  - formatter_candidates are registered AND compatible with role
  - fallback exists and is valid
  - no HTML/CSS/theme color
  - component_policy must exist as dict with all 6 required fields
  - key_statement <= 5 per article
  - advanced component types <= max_primary_advanced_components
  - article_signature: at most one, must be last block
  - duplicate exact_text is ERROR (not warning)
  - anchor occurrence count in article (ambiguous = ERROR)
  - start/end uniqueness checked within section (even with heading_path)
  - CTA URL must be HTTPS
  - resource_list URLs must be HTTPS
  - media URLs must be HTTPS or allowed local protocol
  - malformed YAML returns structured error, not traceback

Usage:
  python scripts/validate_semantic_map.py \\
    --article article.md \\
    --semantic-map semantic-map.yaml \\
    --evidence-map evidence-map.md \\
    --formatter-root f:/AIXM/wxgzh/gzh-design-skill/

  # Regenerate formatter-registry.yaml SHA256 hashes:
  python scripts/validate_semantic_map.py \\
    --regenerate-registry \\
    --formatter-root f:/AIXM/wxgzh/gzh-design-skill/

Output: JSON + human-readable summary.
"""
# 72A-F: runtime_manifest 响应性验证，语义中性。
import argparse
import hashlib
import os
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


# ── Allowed semantic roles (41, from references/semantic-components.md) ──

ALLOWED_ROLES = {
    # Article-level (7)
    "article_cover", "article_toc", "article_intro",
    "article_section", "article_conclusion", "article_cta", "article_signature",
    # Body-level: basic (5)
    "paragraph", "key_statement", "secondary_emphasis", "subtitle", "quote",
    # Body-level: data (3)
    "fact", "statistic", "example",
    # Body-level: structure (9)
    "case", "step_sequence", "ordered_list", "pill_list", "process_flow",
    "comparison", "decision", "timeline", "checklist",
    # Body-level: interactive (2)
    "faq", "dialogue",
    # Body-level: alert (3)
    "warning", "tip", "information",
    # Body-level: code (4)
    "code", "command", "prompt", "code_comparison",
    # Body-level: reference (2)
    "resource_list", "footnote",
    # Body-level: media (6)
    "media_text", "image", "image_annotation", "gallery", "long_image", "video",
}

ROLE_REQUIRED_FIELDS = {
    "article_cover": ["title", "summary_or_intro"],
    "article_toc": ["toc_items"],
    "article_intro": ["text"],
    "article_section": ["heading_text", "section_index"],
    "article_conclusion": ["heading_text"],
    "article_cta": ["text", "url"],
    "article_signature": [],
    "paragraph": ["text"],
    "key_statement": ["text"],
    "secondary_emphasis": ["text", "style_type"],
    "subtitle": ["heading_text"],
    "quote": ["text"],
    "fact": ["items"],
    "statistic": ["value", "label"],
    "example": ["text"],
    "case": [],
    "step_sequence": ["steps"],
    "ordered_list": ["items"],
    "pill_list": ["items"],
    "process_flow": ["steps"],
    "comparison": ["subject_a", "subject_b", "dimensions", "rows"],
    "decision": ["recommended", "options"],
    "timeline": ["events"],
    "checklist": ["items"],
    "faq": ["items"],
    "dialogue": ["messages"],
    "warning": ["text"],
    "tip": ["text"],
    "information": ["text"],
    "code": ["code_text"],
    "command": ["code_text"],
    "prompt": ["code_text"],
    "code_comparison": ["before_code", "after_code"],
    "resource_list": ["links"],
    "footnote": ["notes"],
    "media_text": ["image_url", "explanation_text"],
    "image": ["image_url"],
    "image_annotation": ["image_url", "notes"],
    "gallery": ["images"],
    "long_image": ["image_url", "caption"],
    "video": [],
}

ROLE_EVIDENCE_REQUIRED = {"fact", "statistic", "case"}

ADVANCED_COMPONENT_ROLES = {
    "comparison", "decision", "timeline", "checklist", "faq", "dialogue",
    "case", "step_sequence", "process_flow", "fact", "statistic",
    "code_comparison", "resource_list", "footnote",
    "media_text", "image_annotation", "gallery", "long_image", "video",
}

CASE_REQUIRED_SUBFIELDS = ["context", "challenge", "action", "result"]
CASE_MIN_SUBFIELDS = 3

HTML_PATTERN = re.compile(r'<(?:html|head|body|div|span|section|style|script|table|tr|td|th|ul|ol|li|p|h[1-6])\b', re.IGNORECASE)
CSS_PATTERN = re.compile(r'(?:style\s*=|class\s*=|background-color|font-family|margin|padding|border|color\s*:\s*#)', re.IGNORECASE)
HEX_COLOR_PATTERN = re.compile(r'#[0-9a-fA-F]{3,8}\b')

ALLOWED_LOCAL_PROTOCOLS = ('assets/', './assets/', 'file://')

_FULL_TO_HALF = {
    '：': ':', '，': ',', '。': '.', '！': '!', '？': '?',
    '；': ';', '（': '(', '）': ')', '【': '[', '】': ']',
    '\u201c': '"', '\u201d': '"', '\u2018': "'", '\u2019': "'",
    '—': '-', '–': '-', '～': '~', '　': ' ',
}


def load_yaml_safe(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return None, f"ERROR: Cannot read file {path}: {e}"
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        return None, f"ERROR: YAML parse error in {path}: {e}"
    if data is None:
        return None, f"ERROR: YAML file is empty: {path}"
    if not isinstance(data, dict):
        return None, f"ERROR: YAML top-level must be an object/dict, got {type(data).__name__} in {path}"
    return data, None


def check_html_css(text, location):
    errors = []
    if HTML_PATTERN.search(text):
        errors.append(f"ERROR: HTML tag found in {location}")
    if CSS_PATTERN.search(text):
        errors.append(f"ERROR: CSS/style attribute found in {location}")
    if HEX_COLOR_PATTERN.search(text):
        errors.append(f"ERROR: Hex color found in {location}")
    return errors


def is_valid_url(url):
    if not url or not isinstance(url, str):
        return False
    if url.startswith('https://'):
        return True
    for proto in ALLOWED_LOCAL_PROTOCOLS:
        if url.startswith(proto):
            return True
    return False


def is_https_url(url):
    if not url or not isinstance(url, str):
        return False
    return url.startswith('https://')


def normalize_for_comparison(text):
    """Normalize text for content provenance comparison.
    - Strip markdown markers
    - Convert full-width punctuation to half-width
    - Remove all whitespace
    - Convert to lowercase
    Does NOT do semantic rewriting.
    """
    if not text:
        return ''
    result = text
    result = re.sub(r'[*_`~#>|]', '', result)
    for fw, hw in _FULL_TO_HALF.items():
        result = result.replace(fw, hw)
    result = re.sub(r'\s+', '', result)
    return result.lower()


def parse_headings(article_text):
    """Parse all markdown headings with level, text, and section range."""
    headings = []
    lines = article_text.split('\n')
    heading_re = re.compile(r'^(#{1,6})\s+(.+)$')
    # Build character offsets for each line start; offset[i] = char position of line i
    offsets = [0]
    for idx, line in enumerate(lines):
        # Add len(line) + 1 for newline, but last line may not have trailing newline
        if idx < len(lines) - 1:
            offsets.append(offsets[-1] + len(line) + 1)
        else:
            offsets.append(offsets[-1] + len(line))
    total_len = len(article_text)
    for i, line in enumerate(lines):
        m = heading_re.match(line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            headings.append({
                'level': level, 'text': text,
                'start_pos': offsets[i], 'line': i,
            })
    for j, h in enumerate(headings):
        end_line = len(lines)
        for k in range(j + 1, len(headings)):
            if headings[k]['level'] <= h['level']:
                end_line = headings[k]['line']
                break
        h['end_pos'] = min(offsets[end_line], total_len) if end_line < len(offsets) else total_len
    return headings


def resolve_heading_section(article_text, heading_path, block_id):
    """Resolve heading_path to the section text of the final heading.
    Verifies hierarchy (levels strictly increasing) and uniqueness.
    Returns (section_text, section_start, section_end, errors).
    """
    errors = []
    loc = f"block '{block_id}'"
    if not heading_path:
        return article_text, 0, len(article_text), errors
    headings = parse_headings(article_text)
    search_start = 0
    search_end = len(article_text)
    parent_level = 0
    for i, target in enumerate(heading_path):
        if not isinstance(target, str) or not target.strip():
            errors.append(f"ERROR: {loc} heading_path[{i}] is empty or not a string")
            return None, 0, 0, errors
        matches = [h for h in headings
                   if h['text'] == target
                   and h['start_pos'] >= search_start
                   and h['end_pos'] <= search_end
                   and h['level'] > parent_level]
        if not matches:
            errors.append(
                f"ERROR: {loc} heading_path[{i}] '{target}' not found "
                f"in article hierarchy (level > {parent_level}, within parent section)"
            )
            return None, 0, 0, errors
        if len(matches) > 1:
            errors.append(
                f"ERROR: {loc} heading_path[{i}] '{target}' is ambiguous: "
                f"{len(matches)} matches at this level within parent section"
            )
            return None, 0, 0, errors
        found = matches[0]
        if i == len(heading_path) - 1:
            section_text = article_text[found['start_pos']:found['end_pos']]
            return section_text, found['start_pos'], found['end_pos'], errors
        search_start = found['start_pos']
        search_end = found['end_pos']
        parent_level = found['level']
    return None, 0, 0, errors


# Roles that are formatter-generated and don't need source_anchor
ANCHOR_EXEMPT_ROLES = {'article_signature'}


def extract_source_span(anchor, article_text, heading_path, block_id):
    """Extract source span text from anchor.
    Supports exact_text and start_text/end_text.
    Returns (span_text, errors). span_text is None on failure.
    """
    errors = []
    loc = f"block '{block_id}'"
    if not anchor or not isinstance(anchor, dict) or not anchor:
        return None, errors
    exact_text = anchor.get('exact_text', '')
    start_text = anchor.get('start_text', '')
    end_text = anchor.get('end_text', '')

    section_text = article_text
    if heading_path:
        section_text, _, _, hp_errors = resolve_heading_section(article_text, heading_path, block_id)
        errors.extend(hp_errors)
        if section_text is None:
            return None, errors

    if exact_text:
        count = section_text.count(exact_text)
        if count == 0:
            full_count = article_text.count(exact_text)
            if full_count > 0 and heading_path:
                errors.append(f"ERROR: {loc} source_anchor.exact_text found in article but not within heading_path section")
            else:
                errors.append(f"ERROR: {loc} source_anchor.exact_text not found in article")
            return None, errors
        if count == 1:
            return exact_text, errors
        if not heading_path:
            errors.append(f"ERROR: {loc} source_anchor.exact_text appears {count} times in article (ambiguous: use heading_path to disambiguate)")
        else:
            errors.append(f"ERROR: {loc} source_anchor.exact_text appears {count} times within heading_path section (still ambiguous)")
        return None, errors

    if start_text and end_text:
        start_count = section_text.count(start_text)
        if start_count == 0:
            errors.append(f"ERROR: {loc} source_anchor.start_text not found in article")
            return None, errors
        if start_count > 1:
            if heading_path:
                errors.append(f"ERROR: {loc} source_anchor.start_text appears {start_count} times within heading_path section (ambiguous)")
            else:
                errors.append(f"ERROR: {loc} source_anchor.start_text appears {start_count} times in article (ambiguous: use heading_path to disambiguate)")
            return None, errors
        start_pos = section_text.find(start_text)
        end_pos = section_text.find(end_text, start_pos + len(start_text))
        if end_pos == -1:
            errors.append(f"ERROR: {loc} source_anchor.end_text not found after start_text in article")
            return None, errors
        # Check end_text uniqueness after start_text (always, even with heading_path)
        next_end = section_text.find(end_text, end_pos + len(end_text))
        if next_end != -1:
            if heading_path:
                errors.append(f"ERROR: {loc} source_anchor.end_text appears multiple times after start_text within heading_path section (ambiguous)")
            else:
                errors.append(f"ERROR: {loc} source_anchor.end_text appears multiple times after start_text (ambiguous: use heading_path to disambiguate)")
            return None, errors
        span = section_text[start_pos:end_pos + len(end_text)]
        return span, errors

    if start_text and not end_text:
        errors.append(f"ERROR: {loc} source_anchor has start_text but missing end_text")
        return None, errors
    if end_text and not start_text:
        errors.append(f"ERROR: {loc} source_anchor has end_text but missing start_text")
        return None, errors
    return None, errors


def get_content_leaves(role, payload):
    """Extract substantive content strings from payload that must be sourced from article.
    Returns list of (field_description, value) tuples.
    """
    leaves = []
    def add(desc, val):
        if isinstance(val, str) and val.strip():
            leaves.append((desc, val))

    if role in ('paragraph', 'key_statement', 'secondary_emphasis', 'example',
                'warning', 'tip', 'information', 'article_intro'):
        add(f"{role}.text", payload.get('text', ''))
    elif role == 'article_cover':
        add("article_cover.summary_or_intro", payload.get('summary_or_intro', ''))
    elif role == 'article_cta':
        add("article_cta.text", payload.get('text', ''))
    elif role == 'quote':
        add("quote.text", payload.get('text', ''))
        add("quote.source", payload.get('source', ''))
    elif role == 'subtitle':
        add("subtitle.heading_text", payload.get('heading_text', ''))
    elif role in ('code', 'command', 'prompt'):
        add(f"{role}.code_text", payload.get('code_text', ''))
    elif role == 'code_comparison':
        add("code_comparison.before_code", payload.get('before_code', ''))
        add("code_comparison.after_code", payload.get('after_code', ''))
    elif role == 'fact':
        for i, item in enumerate(payload.get('items', [])):
            if isinstance(item, dict):
                add(f"fact.items[{i}].key", item.get('key', ''))
                add(f"fact.items[{i}].value", item.get('value', ''))
    elif role == 'statistic':
        add("statistic.value", payload.get('value', ''))
        add("statistic.label", payload.get('label', ''))
    elif role == 'case':
        for f in ('context', 'challenge', 'action', 'result'):
            add(f"case.{f}", payload.get(f, ''))
    elif role in ('step_sequence', 'process_flow'):
        for i, step in enumerate(payload.get('steps', [])):
            add(f"{role}.steps[{i}]", step)
    elif role in ('ordered_list', 'pill_list'):
        for i, item in enumerate(payload.get('items', [])):
            add(f"{role}.items[{i}]", item)
    elif role == 'comparison':
        add("comparison.subject_a", payload.get('subject_a', ''))
        add("comparison.subject_b", payload.get('subject_b', ''))
        for i, dim in enumerate(payload.get('dimensions', [])):
            add(f"comparison.dimensions[{i}]", dim)
        for i, row in enumerate(payload.get('rows', [])):
            if isinstance(row, dict):
                add(f"comparison.rows[{i}].dimension", row.get('dimension', ''))
                add(f"comparison.rows[{i}].value_a", row.get('value_a', ''))
                add(f"comparison.rows[{i}].value_b", row.get('value_b', ''))
    elif role == 'decision':
        add("decision.recommended", payload.get('recommended', ''))
        for i, opt in enumerate(payload.get('options', [])):
            if isinstance(opt, dict):
                add(f"decision.options[{i}].name", opt.get('name', ''))
                add(f"decision.options[{i}].description", opt.get('description', ''))
    elif role == 'timeline':
        for i, evt in enumerate(payload.get('events', [])):
            if isinstance(evt, dict):
                add(f"timeline.events[{i}].time", evt.get('time', ''))
                add(f"timeline.events[{i}].description", evt.get('description', ''))
    elif role == 'checklist':
        for i, item in enumerate(payload.get('items', [])):
            if isinstance(item, dict):
                add(f"checklist.items[{i}].text", item.get('text', ''))
    elif role == 'faq':
        for i, item in enumerate(payload.get('items', [])):
            if isinstance(item, dict):
                add(f"faq.items[{i}].question", item.get('question', ''))
                add(f"faq.items[{i}].answer", item.get('answer', ''))
    elif role == 'dialogue':
        for i, msg in enumerate(payload.get('messages', [])):
            if isinstance(msg, dict):
                add(f"dialogue.messages[{i}].role", msg.get('role', ''))
                add(f"dialogue.messages[{i}].content", msg.get('content', ''))
    elif role == 'resource_list':
        for i, link in enumerate(payload.get('links', [])):
            if isinstance(link, dict):
                add(f"resource_list.links[{i}].name", link.get('name', ''))
    elif role == 'footnote':
        for i, note in enumerate(payload.get('notes', [])):
            if isinstance(note, dict):
                add(f"footnote.notes[{i}].content", note.get('content', ''))
    elif role == 'media_text':
        add("media_text.explanation_text", payload.get('explanation_text', ''))
    elif role == 'image_annotation':
        for i, note in enumerate(payload.get('notes', [])):
            if isinstance(note, dict):
                add(f"image_annotation.notes[{i}].description", note.get('description', ''))
    elif role == 'gallery':
        for i, img in enumerate(payload.get('images', [])):
            if isinstance(img, dict):
                add(f"gallery.images[{i}].caption", img.get('caption', ''))
    elif role == 'long_image':
        add("long_image.caption", payload.get('caption', ''))
    return leaves


# Roles whose URL fields need provenance checking
URL_BEARING_ROLES = {'article_cta', 'resource_list', 'image', 'gallery', 'video',
                     'media_text', 'long_image'}

VALID_ASSET_PROVENANCE = {'author_input', 'supplied_material'}


def extract_payload_urls(role, payload):
    """Extract all URLs from payload that need provenance checking.
    Returns list of (field_description, url_value) tuples.
    """
    urls = []
    if role == 'article_cta':
        url = payload.get('url', '')
        if url:
            urls.append(('article_cta.url', url))
    elif role == 'resource_list':
        for i, link in enumerate(payload.get('links', [])):
            if isinstance(link, dict):
                url = link.get('url', '')
                if url:
                    urls.append((f'resource_list.links[{i}].url', url))
    elif role == 'image':
        url = payload.get('image_url', '')
        if url:
            urls.append(('image.image_url', url))
    elif role == 'gallery':
        for i, img in enumerate(payload.get('images', [])):
            if isinstance(img, dict):
                url = img.get('url', '')
                if url:
                    urls.append((f'gallery.images[{i}].url', url))
    elif role == 'video':
        for field in ('video_url', 'image_url'):
            url = payload.get(field, '')
            if url:
                urls.append((f'video.{field}', url))
    elif role == 'media_text':
        url = payload.get('image_url', '')
        if url:
            urls.append(('media_text.image_url', url))
    elif role == 'long_image':
        url = payload.get('image_url', '')
        if url:
            urls.append(('long_image.image_url', url))
    return urls


def collect_author_asset_urls(sm):
    """Collect all declared author/external asset URLs from semantic map.
    Looks for 'author_assets' or 'external_assets' at top level.
    Returns dict: url -> asset_dict
    """
    result = {}
    for key in ('author_assets', 'external_assets'):
        assets = sm.get(key, [])
        if not isinstance(assets, list):
            continue
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            url = asset.get('value', '') or asset.get('url', '')
            if url:
                result[url] = asset
    return result


def validate_url_provenance(role, payload, source_span_text, author_assets, block_id):
    """Validate that URLs in payload are either in source span or declared in author_assets."""
    errors = []
    loc = f"block '{block_id}'"
    if role not in URL_BEARING_ROLES:
        return errors
    url_entries = extract_payload_urls(role, payload)
    if not url_entries:
        return errors
    normalized_span = normalize_for_comparison(source_span_text) if source_span_text else ''
    for desc, url in url_entries:
        # Skip local protocol URLs (assets/ etc.) - they come from the article
        if any(url.startswith(p) for p in ALLOWED_LOCAL_PROTOCOLS):
            continue
        normalized_url = normalize_for_comparison(url)
        # Check if URL is in source span
        if normalized_span and normalized_url in normalized_span:
            continue
        # Check if URL is declared in author_assets
        asset = author_assets.get(url)
        if asset:
            provenance = asset.get('provenance', '')
            if provenance in VALID_ASSET_PROVENANCE:
                continue
            else:
                errors.append(
                    f"ERROR: {loc} URL in {desc}='{url}' declared in author_assets "
                    f"but has invalid provenance '{provenance}' "
                    f"(must be one of: {', '.join(sorted(VALID_ASSET_PROVENANCE))})"
                )
                continue
        # URL not in source span and not in author_assets
        errors.append(
            f"ERROR: {loc} URL in {desc}='{url}' not found in source span "
            f"and not declared in author_assets/external_assets"
        )
    return errors


def validate_payload_provenance(role, payload, source_span_text, block_id):
    """Validate that payload content comes from the source span."""
    errors = []
    loc = f"block '{block_id}'"
    if not source_span_text:
        return errors
    if role in ('article_signature', 'article_toc', 'article_section', 'article_conclusion',
                'image', 'video'):
        return errors
    leaves = get_content_leaves(role, payload)
    normalized_span = normalize_for_comparison(source_span_text)
    for desc, value in leaves:
        normalized_value = normalize_for_comparison(value)
        if not normalized_value:
            continue
        if normalized_value not in normalized_span:
            display = value[:80] + ('...' if len(value) > 80 else '')
            errors.append(
                f"ERROR: {loc} payload content not found in source span: "
                f"{desc}='{display}'"
            )
    return errors


def load_formatter_registry(formatter_root):
    errors = []
    formatter_root = Path(formatter_root)
    if not formatter_root.exists():
        errors.append(f"ERROR: formatter_root directory does not exist: {formatter_root}")
        return None, errors
    registry_path = Path(__file__).parent.parent / 'references' / 'formatter-registry.yaml'
    if not registry_path.exists():
        errors.append(f"ERROR: formatter-registry.yaml not found: {registry_path}")
        return None, errors
    registry, reg_err = load_yaml_safe(registry_path)
    if reg_err:
        errors.append(reg_err)
        return None, errors
    source_files = registry.get('source_files', [])
    for sf in source_files:
        rel_path = sf.get('path', '')
        expected_sha = sf.get('sha256', '')
        actual_path = formatter_root / rel_path
        if not actual_path.exists():
            errors.append(f"ERROR: formatter contract file missing: {rel_path} (expected at {actual_path})")
            continue
        actual_sha = hashlib.sha256(actual_path.read_bytes()).hexdigest()
        if actual_sha != expected_sha:
            errors.append(
                f"ERROR: formatter contract file SHA256 mismatch for {rel_path}: "
                f"expected {expected_sha}, got {actual_sha}. "
                f"gzh-design contract has changed — regenerate formatter-registry.yaml."
            )
    return registry, errors


def extract_evidence_ids(evidence_map_text):
    if not evidence_map_text:
        return set()
    matches = re.findall(r'(?:ev|EV)[-_]?(\d+)', evidence_map_text)
    return {f'ev-{m}' for m in matches} | {f'ev_{m}' for m in matches} | {f'EV-{m}' for m in matches}


def validate_block_payload(role, payload, block_id, article_text):
    """Deep validation of payload fields per role. Returns list of errors."""
    errors = []
    loc = f"block '{block_id}'"
    if payload is None:
        payload = {}
    required_fields = ROLE_REQUIRED_FIELDS.get(role, [])

    if role == 'video':
        video_url = payload.get('video_url', '')
        image_url = payload.get('image_url', '')
        if not video_url and not image_url:
            errors.append(f"ERROR: {loc} role 'video' requires 'video_url' or 'image_url' in payload (at least one non-empty)")
        if video_url and not is_valid_url(video_url):
            errors.append(f"ERROR: {loc} role 'video' video_url must be HTTPS or allowed local protocol, got: {video_url}")
        if image_url and not is_valid_url(image_url):
            errors.append(f"ERROR: {loc} role 'video' image_url must be HTTPS or allowed local protocol, got: {image_url}")
    else:
        for field in required_fields:
            val = payload.get(field)
            if val is None or val == '' or val == []:
                if role == 'article_signature':
                    continue
                errors.append(f"ERROR: {loc} role '{role}' missing required payload field '{field}'")

    if role == 'article_toc':
        items = payload.get('toc_items', [])
        if not isinstance(items, list) or len(items) < 1 or len(items) > 3:
            errors.append(f"ERROR: {loc} role 'article_toc' toc_items must have 1-3 items, got {len(items) if isinstance(items, list) else 'non-list'}")
    elif role == 'fact':
        items = payload.get('items', [])
        if not isinstance(items, list) or len(items) < 2:
            errors.append(f"ERROR: {loc} role 'fact' items must have at least 2 items")
        else:
            for j, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append(f"ERROR: {loc} role 'fact' item {j} is not a dict")
                    continue
                if not item.get('key') or not isinstance(item.get('key'), str):
                    errors.append(f"ERROR: {loc} role 'fact' item {j} missing non-empty 'key'")
                if not item.get('value') or not isinstance(item.get('value'), str):
                    errors.append(f"ERROR: {loc} role 'fact' item {j} missing non-empty 'value'")
    elif role == 'step_sequence':
        steps = payload.get('steps', [])
        if not isinstance(steps, list) or len(steps) < 2:
            errors.append(f"ERROR: {loc} role 'step_sequence' steps must have at least 2 items")
        else:
            for j, step in enumerate(steps):
                if not step or (isinstance(step, str) and not step.strip()):
                    errors.append(f"ERROR: {loc} role 'step_sequence' step {j} is empty")
    elif role == 'ordered_list':
        items = payload.get('items', [])
        if not isinstance(items, list) or len(items) < 2:
            errors.append(f"ERROR: {loc} role 'ordered_list' items must have at least 2 items")
    elif role == 'pill_list':
        items = payload.get('items', [])
        if not isinstance(items, list) or len(items) < 2:
            errors.append(f"ERROR: {loc} role 'pill_list' items must have at least 2 items")
    elif role == 'process_flow':
        steps = payload.get('steps', [])
        if not isinstance(steps, list) or len(steps) < 2:
            errors.append(f"ERROR: {loc} role 'process_flow' steps must have at least 2 items")
    elif role == 'comparison':
        dims = payload.get('dimensions', [])
        rows = payload.get('rows', [])
        if not isinstance(dims, list) or len(dims) < 1:
            errors.append(f"ERROR: {loc} role 'comparison' dimensions must be a non-empty list")
        if not isinstance(rows, list) or len(rows) < 1:
            errors.append(f"ERROR: {loc} role 'comparison' rows must be a non-empty list")
        if isinstance(dims, list) and isinstance(rows, list):
            if len(rows) != len(dims):
                errors.append(f"ERROR: {loc} role 'comparison' rows count ({len(rows)}) must match dimensions count ({len(dims)})")
            for j, row in enumerate(rows):
                if not isinstance(row, dict):
                    errors.append(f"ERROR: {loc} role 'comparison' row {j} is not a dict")
                    continue
                if not row.get('dimension'):
                    errors.append(f"ERROR: {loc} role 'comparison' row {j} missing 'dimension'")
                if not row.get('value_a') and row.get('value_a') != 0:
                    errors.append(f"ERROR: {loc} role 'comparison' row {j} missing 'value_a'")
                if not row.get('value_b') and row.get('value_b') != 0:
                    errors.append(f"ERROR: {loc} role 'comparison' row {j} missing 'value_b'")
    elif role == 'decision':
        options = payload.get('options', [])
        if not isinstance(options, list) or len(options) < 2:
            errors.append(f"ERROR: {loc} role 'decision' options must have at least 2 items")
        else:
            for j, opt in enumerate(options):
                if not isinstance(opt, dict):
                    errors.append(f"ERROR: {loc} role 'decision' option {j} is not a dict")
                    continue
                if not opt.get('name'):
                    errors.append(f"ERROR: {loc} role 'decision' option {j} missing 'name'")
                if not opt.get('description'):
                    errors.append(f"ERROR: {loc} role 'decision' option {j} missing 'description'")
        recommended = payload.get('recommended', '')
        if recommended:
            option_names = [opt.get('name', '') for opt in options if isinstance(opt, dict)]
            if recommended not in option_names:
                errors.append(f"ERROR: {loc} role 'decision' recommended '{recommended}' does not match any option name")
    elif role == 'timeline':
        events = payload.get('events', [])
        if not isinstance(events, list) or len(events) < 2:
            errors.append(f"ERROR: {loc} role 'timeline' events must have at least 2 items")
        else:
            for j, evt in enumerate(events):
                if not isinstance(evt, dict):
                    errors.append(f"ERROR: {loc} role 'timeline' event {j} is not a dict")
                    continue
                if not evt.get('time'):
                    errors.append(f"ERROR: {loc} role 'timeline' event {j} missing 'time'")
                if not evt.get('description'):
                    errors.append(f"ERROR: {loc} role 'timeline' event {j} missing 'description'")
    elif role == 'checklist':
        items = payload.get('items', [])
        if not isinstance(items, list) or len(items) < 2:
            errors.append(f"ERROR: {loc} role 'checklist' items must have at least 2 items")
        else:
            for j, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append(f"ERROR: {loc} role 'checklist' item {j} is not a dict")
                    continue
                if not item.get('text'):
                    errors.append(f"ERROR: {loc} role 'checklist' item {j} missing 'text'")
                if 'checked' not in item:
                    errors.append(f"ERROR: {loc} role 'checklist' item {j} missing 'checked'")
                elif not isinstance(item['checked'], bool):
                    errors.append(f"ERROR: {loc} role 'checklist' item {j} 'checked' must be boolean, got {type(item['checked']).__name__}")
    elif role == 'faq':
        items = payload.get('items', [])
        if not isinstance(items, list) or len(items) < 1:
            errors.append(f"ERROR: {loc} role 'faq' items must have at least 1 item")
        else:
            for j, item in enumerate(items):
                if not isinstance(item, dict):
                    errors.append(f"ERROR: {loc} role 'faq' item {j} is not a dict")
                    continue
                if not item.get('question'):
                    errors.append(f"ERROR: {loc} role 'faq' item {j} missing 'question'")
                if not item.get('answer'):
                    errors.append(f"ERROR: {loc} role 'faq' item {j} missing 'answer'")
    elif role == 'dialogue':
        messages = payload.get('messages', [])
        if not isinstance(messages, list) or len(messages) < 1:
            errors.append(f"ERROR: {loc} role 'dialogue' messages must be non-empty")
        else:
            for j, msg in enumerate(messages):
                if not isinstance(msg, dict):
                    errors.append(f"ERROR: {loc} role 'dialogue' message {j} is not a dict")
                    continue
                if not msg.get('role'):
                    errors.append(f"ERROR: {loc} role 'dialogue' message {j} missing 'role'")
                if not msg.get('content'):
                    errors.append(f"ERROR: {loc} role 'dialogue' message {j} missing 'content'")
    elif role == 'case':
        present = sum(1 for f in CASE_REQUIRED_SUBFIELDS if payload.get(f))
        if present < CASE_MIN_SUBFIELDS:
            errors.append(f"ERROR: {loc} role 'case' needs at least {CASE_MIN_SUBFIELDS} of {CASE_REQUIRED_SUBFIELDS}, found {present}")
    elif role == 'resource_list':
        links = payload.get('links', [])
        if not isinstance(links, list) or len(links) < 2:
            errors.append(f"ERROR: {loc} role 'resource_list' links must have at least 2 items")
        else:
            for j, link in enumerate(links):
                if not isinstance(link, dict):
                    errors.append(f"ERROR: {loc} role 'resource_list' link {j} is not a dict")
                    continue
                if not link.get('name'):
                    errors.append(f"ERROR: {loc} role 'resource_list' link {j} missing 'name'")
                url = link.get('url', '')
                if not url:
                    errors.append(f"ERROR: {loc} role 'resource_list' link {j} missing 'url'")
                elif not is_https_url(url):
                    errors.append(f"ERROR: {loc} role 'resource_list' link {j} url must be HTTPS, got: {url}")
    elif role == 'footnote':
        notes = payload.get('notes', [])
        if not isinstance(notes, list) or len(notes) < 1:
            errors.append(f"ERROR: {loc} role 'footnote' notes must be non-empty")
        else:
            seen_ids = set()
            for j, note in enumerate(notes):
                if not isinstance(note, dict):
                    errors.append(f"ERROR: {loc} role 'footnote' note {j} is not a dict")
                    continue
                if not note.get('id'):
                    errors.append(f"ERROR: {loc} role 'footnote' note {j} missing 'id'")
                elif note['id'] in seen_ids:
                    errors.append(f"ERROR: {loc} role 'footnote' note {j} duplicate id '{note['id']}'")
                else:
                    seen_ids.add(note['id'])
                if not note.get('content'):
                    errors.append(f"ERROR: {loc} role 'footnote' note {j} missing 'content'")
    elif role == 'article_cta':
        url = payload.get('url', '')
        if url and not is_https_url(url):
            errors.append(f"ERROR: {loc} role 'article_cta' url must be HTTPS, got: {url}")
        if not payload.get('text'):
            errors.append(f"ERROR: {loc} role 'article_cta' text must be non-empty")
    elif role == 'gallery':
        images = payload.get('images', [])
        if not isinstance(images, list) or len(images) < 2:
            errors.append(f"ERROR: {loc} role 'gallery' images must have at least 2 items")
        else:
            for j, img in enumerate(images):
                if not isinstance(img, dict):
                    errors.append(f"ERROR: {loc} role 'gallery' image {j} is not a dict")
                    continue
                if not img.get('url'):
                    errors.append(f"ERROR: {loc} role 'gallery' image {j} missing 'url'")
                elif not is_valid_url(img['url']):
                    errors.append(f"ERROR: {loc} role 'gallery' image {j} url must be HTTPS or local, got: {img['url']}")
                if not img.get('caption'):
                    errors.append(f"ERROR: {loc} role 'gallery' image {j} missing 'caption'")
    elif role == 'image_annotation':
        notes = payload.get('notes', [])
        if not isinstance(notes, list) or len(notes) < 1:
            errors.append(f"ERROR: {loc} role 'image_annotation' notes must have at least 1 item")
        else:
            for j, note in enumerate(notes):
                if not isinstance(note, dict):
                    errors.append(f"ERROR: {loc} role 'image_annotation' note {j} is not a dict")
                    continue
                if 'number' not in note:
                    errors.append(f"ERROR: {loc} role 'image_annotation' note {j} missing 'number'")
                if not note.get('description'):
                    errors.append(f"ERROR: {loc} role 'image_annotation' note {j} missing 'description'")
    elif role in ('media_text', 'image', 'long_image'):
        url_field = 'image_url'
        url = payload.get(url_field, '')
        if url and not is_valid_url(url):
            errors.append(f"ERROR: {loc} role '{role}' {url_field} must be HTTPS or local, got: {url}")
    elif role == 'quote':
        qt = payload.get('quote_type', '')
        if qt == 'sourced':
            if not payload.get('source'):
                errors.append(f"ERROR: {loc} role 'quote' type 'sourced' missing 'source'")

    for key, val in payload.items():
        if isinstance(val, str):
            errors.extend(check_html_css(val, f"{loc}.payload.{key}"))
        elif isinstance(val, list):
            for j, item in enumerate(val):
                if isinstance(item, str):
                    errors.extend(check_html_css(item, f"{loc}.payload.{key}[{j}]"))
                elif isinstance(item, dict):
                    for k, v in item.items():
                        if isinstance(v, str):
                            errors.extend(check_html_css(v, f"{loc}.payload.{key}[{j}].{k}"))
    return errors


def validate_semantic_map(article_path, semantic_map_path, formatter_root=None, evidence_map_path=None):
    """Validate semantic map against article. Returns (errors, warnings, info)."""
    errors = []
    warnings = []
    info = {}

    article_path = Path(article_path)
    if not article_path.exists():
        errors.append(f"ERROR: article_path does not exist: {article_path}")
        return errors, warnings, info
    article_text = article_path.read_text(encoding='utf-8')

    semantic_map_path = Path(semantic_map_path)
    if not semantic_map_path.exists():
        errors.append(f"ERROR: semantic_map_path does not exist: {semantic_map_path}")
        return errors, warnings, info

    sm, sm_err = load_yaml_safe(semantic_map_path)
    if sm_err:
        errors.append(sm_err)
        return errors, warnings, info

    evidence_ids_set = set()
    evidence_map_text = ''
    if evidence_map_path:
        evidence_map_path = Path(evidence_map_path)
        if evidence_map_path.exists():
            evidence_map_text = evidence_map_path.read_text(encoding='utf-8')
            evidence_ids_set = extract_evidence_ids(evidence_map_text)
        else:
            errors.append(f"ERROR: evidence_map_path does not exist: {evidence_map_path}")

    registry = None
    role_component_matrix = None
    if formatter_root:
        registry, reg_errors = load_formatter_registry(formatter_root)
        errors.extend(reg_errors)
        if registry:
            role_component_matrix = registry.get('role_component_matrix', {})

    sv = sm.get('schema_version')
    if not sv:
        errors.append("ERROR: schema_version is missing")
    elif sv != "1.0":
        errors.append(f"ERROR: schema_version must be '1.0', got '{sv}'")

    article_info = sm.get('article', {})
    if not article_info:
        errors.append("ERROR: article section is missing")
    else:
        if not article_info.get('id'):
            warnings.append("WARN: article.id is empty")
        if not article_info.get('title'):
            errors.append("ERROR: article.title is missing")

    blocks = sm.get('blocks', [])
    if not blocks:
        errors.append("ERROR: blocks list is empty")
        return errors, warnings, info

    # ── Check: evidence-backed roles require evidence-map ──
    has_evidence_roles = any(b.get('role') in ROLE_EVIDENCE_REQUIRED for b in blocks)
    if has_evidence_roles and not evidence_map_path:
        errors.append(
            "ERROR: evidence-map is required when blocks contain evidence-backed roles "
            f"({', '.join(sorted(ROLE_EVIDENCE_REQUIRED))})"
        )

    # ── Collect author/external assets for URL provenance ──
    author_assets = collect_author_asset_urls(sm)

    block_ids = []
    for i, block in enumerate(blocks):
        bid = block.get('block_id')
        if not bid:
            errors.append(f"ERROR: block at index {i} has no block_id")
            continue
        if bid in block_ids:
            errors.append(f"ERROR: duplicate block_id: {bid}")
        block_ids.append(bid)

    exact_text_usage = {}
    key_statement_count = 0
    advanced_types_used = set()
    signature_indices = []

    for i, block in enumerate(blocks):
        bid = block.get('block_id', f'index-{i}')
        role = block.get('role')
        location = f"block '{bid}'"

        if not role:
            errors.append(f"ERROR: {location} has no role")
            continue
        if role not in ALLOWED_ROLES:
            errors.append(f"ERROR: {location} has unknown role '{role}'. Allowed roles: {', '.join(sorted(ALLOWED_ROLES))}")
            continue

        if role == 'key_statement':
            key_statement_count += 1
        if role in ADVANCED_COMPONENT_ROLES:
            advanced_types_used.add(role)
        if role == 'article_signature':
            signature_indices.append(i)

        anchor = block.get('source_anchor', {})
        if anchor is None:
            anchor = {}
        heading_path = block.get('heading_path', [])
        if heading_path is None:
            heading_path = []

        # ── Require source_anchor for non-exempt roles ──
        source_span_text = None
        if role not in ANCHOR_EXEMPT_ROLES:
            if not anchor or not isinstance(anchor, dict) or not anchor:
                errors.append(f"ERROR: {location} role '{role}' requires source_anchor (exact_text or start_text/end_text)")
            else:
                # ── Extract source span (includes heading_path validation and uniqueness) ──
                source_span_text, span_errors = extract_source_span(anchor, article_text, heading_path, bid)
                errors.extend(span_errors)

                # Track duplicate usage across blocks
                exact_text = anchor.get('exact_text', '') if isinstance(anchor, dict) else ''
                start_text = anchor.get('start_text', '') if isinstance(anchor, dict) else ''
                track_key = exact_text or start_text
                if track_key:
                    if track_key not in exact_text_usage:
                        exact_text_usage[track_key] = []
                    exact_text_usage[track_key].append(bid)
        else:
            # article_signature: no anchor needed
            pass

        # ── Deep payload validation ──
        payload = block.get('payload', {})
        if payload is None:
            payload = {}
        errors.extend(validate_block_payload(role, payload, bid, article_text))

        # ── Content provenance validation ──
        if source_span_text is not None:
            errors.extend(validate_payload_provenance(role, payload, source_span_text, bid))

        # ── URL provenance validation ──
        errors.extend(validate_url_provenance(role, payload, source_span_text, author_assets, bid))

        # ── Check evidence_required ──
        if role in ROLE_EVIDENCE_REQUIRED:
            evidence_ids = block.get('evidence_ids', [])
            if not evidence_ids:
                errors.append(f"ERROR: {location} role '{role}' requires evidence_ids but has none")
            elif evidence_map_path and evidence_ids_set:
                for eid in evidence_ids:
                    if eid not in evidence_ids_set:
                        errors.append(f"ERROR: {location} evidence_id '{eid}' not found in evidence-map")

        # ── Check formatter_candidates ──
        candidates = block.get('formatter_candidates', [])
        if not candidates:
            warnings.append(f"WARN: {location} has no formatter_candidates")
        else:
            if registry:
                registered = set(registry.get('all_components', []))
            else:
                registered = _get_static_components()
            for cand in candidates:
                if cand not in registered:
                    errors.append(f"ERROR: {location} formatter_candidate '{cand}' is not a registered component.")
                if role_component_matrix:
                    compatible = role_component_matrix.get(role, [])
                    if cand not in compatible:
                        errors.append(f"ERROR: {location} formatter_candidate '{cand}' is not compatible with role '{role}'. Compatible components: {', '.join(compatible) if compatible else 'none'}")

        # ── Check fallback ──
        fallback = block.get('fallback', [])
        if not fallback and role not in ('article_signature', 'article_toc', 'footnote', 'paragraph'):
            if not block.get('required', False):
                warnings.append(f"WARN: {location} has no fallback")
        if fallback and registry:
            registered = set(registry.get('all_components', []))
            for fb in fallback:
                if fb not in registered and fb not in ALLOWED_ROLES:
                    errors.append(f"ERROR: {location} fallback '{fb}' is not a registered component or valid role")

        pe = block.get('preserve_exactly')
        if pe is not None and not isinstance(pe, bool):
            errors.append(f"ERROR: {location} preserve_exactly must be boolean, got {type(pe).__name__}")

    # ── Cross-block validation ──
    for text_key, bids in exact_text_usage.items():
        if len(bids) > 1:
            errors.append(f"ERROR: duplicate anchor '{text_key[:50]}' used by multiple blocks: {', '.join(bids)}")

    if key_statement_count > 5:
        errors.append(f"ERROR: key_statement count ({key_statement_count}) exceeds maximum of 5 per article")

    # ── component_policy must exist and be complete ──
    REQUIRED_CP_FIELDS = {
        'force_all_components': False,
        'formatter_has_final_choice': True,
        'allow_fallback': True,
        'prohibit_content_invention': True,
        'prohibit_duplicate_full_content': True,
    }
    cp = sm.get('component_policy')
    if cp is None:
        errors.append("ERROR: component_policy is missing (must be a dict with all required fields)")
        cp = {}
    elif not isinstance(cp, dict):
        errors.append(f"ERROR: component_policy must be a dict, got {type(cp).__name__}")
        cp = {}
    else:
        # Check all required fields exist
        for field, expected_val in REQUIRED_CP_FIELDS.items():
            if field not in cp:
                errors.append(f"ERROR: component_policy.{field} is missing (required field)")
            elif cp.get(field) is not expected_val:
                errors.append(f"ERROR: component_policy.{field} must be {expected_val}, got {cp.get(field)}")
        # max_primary_advanced_components
        max_advanced = cp.get('max_primary_advanced_components')
        if 'max_primary_advanced_components' not in cp:
            errors.append("ERROR: component_policy.max_primary_advanced_components is missing (required field)")
        elif not isinstance(max_advanced, int) or max_advanced < 0 or max_advanced > 6:
            errors.append(f"ERROR: component_policy.max_primary_advanced_components must be 0-6 integer, got {max_advanced}")
        elif len(advanced_types_used) > max_advanced:
            errors.append(f"ERROR: advanced component types ({len(advanced_types_used)}) exceeds max_primary_advanced_components ({max_advanced}). Types used: {', '.join(sorted(advanced_types_used))}")

    if len(signature_indices) > 1:
        errors.append(f"ERROR: article_signature appears {len(signature_indices)} times, must be at most 1")
    elif len(signature_indices) == 1:
        if signature_indices[0] != len(blocks) - 1:
            errors.append(f"ERROR: article_signature must be the last block, found at index {signature_indices[0]} of {len(blocks)}")

    raw_text = semantic_map_path.read_text(encoding='utf-8')
    code_lines = [line for line in raw_text.split('\n') if not line.strip().startswith('#')]
    code_text = '\n'.join(code_lines)
    errors.extend(check_html_css(code_text, "semantic-map.yaml (non-comment)"))

    info['total_blocks'] = len(blocks)
    info['unique_roles'] = len(set(b.get('role', '') for b in blocks if b.get('role')))
    info['roles_used'] = sorted(set(b.get('role', '') for b in blocks if b.get('role')))
    info['errors_count'] = len(errors)
    info['warnings_count'] = len(warnings)
    info['passed'] = len(errors) == 0
    info['formatter_root_used'] = registry is not None
    info['evidence_map_used'] = evidence_map_path is not None
    return errors, warnings, info


def _get_static_components():
    return {
        "global-container", "cover-breaking", "toc-scroll", "chapter-title",
        "paragraph", "inline-styles", "label-heading", "code-block",
        "quote-oneliner", "alert-box", "table-list-flow", "image-video",
        "footer-signature-brand",
        "alert", "quote", "code-compare", "media-text", "gallery",
        "long-image", "resources", "footnotes", "dialogue", "facts",
        "decision", "steps", "compare", "annotated-image", "faq",
        "timeline", "checklist", "case", "cta",
    }


REGISTERED_COMPONENTS = _get_static_components()


def regenerate_registry(formatter_root):
    """Regenerate SHA256 hashes in formatter-registry.yaml.

    76Y-R/OBS-305:formatter-registry.yaml 是锁钉 runtime_manifest 覆盖文件,RUN 中
    agent 误执行本命令会写穿 skill 树致哈希漂移(jsffln 越权 relock 事件根因)。
    现加守卫:须显式 env WXGZH_REGENERATE_REGISTRY_ALLOWED=1(仅开发期维护用)
    才写回;否则拒绝并提示停机报告,禁止 RUN 中自行重锁。
    """
    if os.environ.get("WXGZH_REGENERATE_REGISTRY_ALLOWED", "0").strip().lower() not in ("1", "true", "yes"):
        print("ERROR: --regenerate-registry 写 references/formatter-registry.yaml(锁钉文件)需显式授权"
              " env WXGZH_REGENERATE_REGISTRY_ALLOWED=1;RUN 中遇锁 FAIL_CLOSED 应停机报告等档,"
              "禁止自行 relock/重生成(76Y-R/OBS-305)", file=sys.stderr)
        sys.exit(3)
    formatter_root = Path(formatter_root)
    registry_path = Path(__file__).parent.parent / 'references' / 'formatter-registry.yaml'
    if not registry_path.exists():
        print(f"ERROR: formatter-registry.yaml not found: {registry_path}", file=sys.stderr)
        sys.exit(1)
    registry, err = load_yaml_safe(registry_path)
    if err:
        print(err, file=sys.stderr)
        sys.exit(1)
    updated = 0
    unchanged = 0
    missing = 0
    for sf in registry.get('source_files', []):
        rel_path = sf.get('path', '')
        actual_path = formatter_root / rel_path
        if not actual_path.exists():
            print(f"  WARN: file not found: {rel_path}", file=sys.stderr)
            missing += 1
            continue
        actual_sha = hashlib.sha256(actual_path.read_bytes()).hexdigest()
        old_sha = sf.get('sha256', '')
        if actual_sha != old_sha:
            sf['sha256'] = actual_sha
            updated += 1
            print(f"  UPDATED: {rel_path}")
        else:
            unchanged += 1
            print(f"  OK: {rel_path}")
    # Write back with comments preserved as much as possible
    with open(registry_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write("# Formatter Registry Snapshot\n")
        f.write("# Super Writer v0.3.0-rc1-hotfix.1\n")
        f.write("#\n")
        f.write("# This file is a cryptographic snapshot of gzh-design's component contract.\n")
        f.write("# The validator uses it to detect when gzh-design's components change.\n")
        f.write("# When gzh-design updates, regenerate this file using:\n")
        f.write("#   python scripts/validate_semantic_map.py --regenerate-registry --formatter-root <path>\n")
        f.write("#\n")
        f.write(f"# Source: {formatter_root}\n\n")
        yaml.dump(registry, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"\nRegenerated: {registry_path}")
    print(f"Updated: {updated}, Unchanged: {unchanged}, Missing: {missing}")


def main():
    parser = argparse.ArgumentParser(description='Validate semantic-map.yaml against article.md')
    parser.add_argument('--article', default=None, help='Path to article.md')
    parser.add_argument('--semantic-map', default=None, help='Path to semantic-map.yaml')
    parser.add_argument('--formatter-root', default=None, help='Path to gzh-design skill root')
    parser.add_argument('--evidence-map', default=None, help='Path to evidence-map.md')
    parser.add_argument('--json', action='store_true', help='Output JSON only')
    parser.add_argument('--regenerate-registry', action='store_true',
                        help='Regenerate formatter-registry.yaml SHA256 hashes (requires --formatter-root)')
    args = parser.parse_args()

    if args.regenerate_registry:
        if not args.formatter_root:
            print("ERROR: --formatter-root is required for --regenerate-registry", file=sys.stderr)
            sys.exit(2)
        regenerate_registry(args.formatter_root)
        sys.exit(0)

    if not args.article or not args.semantic_map:
        parser.error("--article and --semantic-map are required (unless --regenerate-registry is used)")

    errors, warnings, info = validate_semantic_map(
        args.article, args.semantic_map, args.formatter_root, args.evidence_map
    )

    result = {
        'passed': info.get('passed', False),
        'errors': errors,
        'warnings': warnings,
        'summary': info,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print("Semantic Map Validation Report")
        print("=" * 60)
        print(f"\nArticle: {args.article}")
        print(f"Semantic Map: {args.semantic_map}")
        if args.formatter_root:
            print(f"Formatter Root: {args.formatter_root}")
            print(f"Formatter Root Used: {info.get('formatter_root_used', False)}")
        if args.evidence_map:
            print(f"Evidence Map: {args.evidence_map}")
            print(f"Evidence Map Used: {info.get('evidence_map_used', False)}")
        print(f"\nTotal blocks: {info.get('total_blocks', 0)}")
        print(f"Unique roles: {info.get('unique_roles', 0)}")
        print(f"Roles used: {', '.join(info.get('roles_used', []))}")
        print(f"\nErrors: {len(errors)}")
        for e in errors:
            print(f"  {e}")
        print(f"\nWarnings: {len(warnings)}")
        for w in warnings:
            print(f"  {w}")
        print(f"\n{'PASSED' if info.get('passed') else 'FAILED'}")
        print("=" * 60)

    sys.exit(0 if info.get('passed') else 1)


if __name__ == '__main__':
    main()
