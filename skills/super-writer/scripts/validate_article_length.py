#!/usr/bin/env python3
"""Validate article length against length-policy.

Checks:
  - visible_chars within acceptable_min / acceptable_max
  - section budget deviation <= 5%
  - duplicate detection (exact, punctuation-normalized, n-gram similarity)
  - full mode product completeness (11 files, non-empty, parseable, with required fields)
  - article_mode validation, explicit min/max preservation
  - outline.md budget parsing
  - code content (inline and fenced) counted in visible chars

Usage:
  python scripts/validate_article_length.py \\
    --article article.md \\
    --article-mode medium

  python scripts/validate_article_length.py \\
    --article article.md \\
    --outline outline.md \\
    --full-mode \\
    --generation-profile generation-profile.yaml \\
    --brief writing-brief.md \\
    --material-readiness material-readiness.yaml \\
    --material-ledger material-ledger.yaml \\
    --material-report material-ingestion-report.json \\
    --evidence-map evidence-map.md \\
    --core-card core-card.md \\
    --semantic-map semantic-map.yaml \\
    --editor-report editor-report.md

Output: JSON with complete diagnostics.
"""
import argparse
import difflib
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

# Import production validators from material_ingestion.py
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from material_ingestion import (
        generate_ingestion_report,
        validate_ledger_structure,
        validate_event_assignments,
        check_duplicate_status,
        detect_exact_duplicates,
        build_event_index,
        load_yaml_safe as load_ledger_yaml,
    )
except ImportError:
    generate_ingestion_report = None
    validate_ledger_structure = None
    validate_event_assignments = None
    check_duplicate_status = None
    detect_exact_duplicates = None
    build_event_index = None
    load_ledger_yaml = None


# ── Length mode presets ──

LENGTH_MODE_PRESETS = {
    'short': {'target_visible_chars': 1500, 'acceptable_min': 1200, 'acceptable_max': 2000},
    'medium': {'target_visible_chars': 3000, 'acceptable_min': 2500, 'acceptable_max': 4000},
    'long': {'target_visible_chars': 5000, 'acceptable_min': 4500, 'acceptable_max': 6500},
    'deep': {'target_visible_chars': 8000, 'acceptable_min': 7000, 'acceptable_max': 10000},
    'daily_digest': {'target_visible_chars': 2500, 'acceptable_min': 2000, 'acceptable_max': 3500},
    'weekly_roundup': {'target_visible_chars': 4000, 'acceptable_min': 3500, 'acceptable_max': 5500},
    'material_synthesis': {'target_visible_chars': 6000, 'acceptable_min': 5000, 'acceptable_max': 8000},
}

ALLOWED_MODES = set(LENGTH_MODE_PRESETS.keys())
SECTION_BUDGET_TOLERANCE = 0.05
NGRAM_SIZE = 8
SIMILARITY_THRESHOLD = 0.85


# ════════════════════════════════════════════════════════════════
# Visible character counting
# ════════════════════════════════════════════════════════════════

def count_cjk_chars(text):
    """Count CJK characters."""
    return sum(1 for c in text if '\u4e00' <= c <= '\u9fff' or '\u3400' <= c <= '\u4dbf')


def count_latin_words(text):
    """Count Latin words (sequences of [a-zA-Z]+)."""
    return len(re.findall(r'[a-zA-Z]+', text))


def count_digits(text):
    """Count digit characters."""
    return sum(1 for c in text if c.isdigit())


def count_visible_chars(text):
    """Count visible characters: all non-whitespace after stripping markdown syntax.

    - Links: [text](url) → count 'text', not URL
    - Tables: count cell text, not pipes or separators
    - Images: ![alt](url) → keep alt text
    - Inline code: `code` → keep 'code'
    - Fenced code: ```lang\\ncode\\n``` → keep 'code' content
    - Markdown markers (#, *, >, |, -) are stripped
    """
    if not text:
        return 0

    t = text

    # Remove fenced code blocks but KEEP their content
    # ```python\nprint(123)\n``` → print(123)
    t = re.sub(r'```[a-zA-Z]*\n(.*?)```', r'\1', t, flags=re.DOTALL)
    # Handle ```code``` on single line
    t = re.sub(r'```([^\n`]*)```', r'\1', t)

    # Remove inline code backticks but KEEP content
    # `code` → code
    t = re.sub(r'`([^`]+)`', r'\1', t)

    # Remove images: ![alt](url) -> keep alt text
    t = re.sub(r'!\[([^\]]*)\]\([^)]*\)', r'\1', t)

    # Remove links: [text](url) -> keep text
    t = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', t)

    # Remove table separators: |---|---|
    t = re.sub(r'^\|?[-:| ]+\|?$', '', t, flags=re.MULTILINE)

    # Remove table pipes (keep cell content)
    t = re.sub(r'\|', ' ', t)

    # Remove markdown headings markers
    t = re.sub(r'^#{1,6}\s+', '', t, flags=re.MULTILINE)

    # Remove blockquote markers
    t = re.sub(r'^>\s*', '', t, flags=re.MULTILINE)

    # Remove list markers
    t = re.sub(r'^[-*+]\s+', '', t, flags=re.MULTILINE)
    t = re.sub(r'^\d+\.\s+', '', t, flags=re.MULTILINE)

    # Remove emphasis markers
    t = re.sub(r'\*{1,3}|_{1,3}|~{1,2}', '', t)

    # Remove HTML tags
    t = re.sub(r'<[^>]+>', '', t)

    # Remove footnote markers
    t = re.sub(r'\[\^\d+\]', '', t)

    # Count non-whitespace
    return len(re.sub(r'\s+', '', t))


def count_punctuation(text):
    """Count punctuation characters."""
    return sum(1 for c in text if c in '，。！？；：、\u201c\u201d\u2018\u2019（）【】《》\u2014\u2026\u00b7,.;:!?\'\"()[]{}<>')


def count_paragraphs(text):
    """Count paragraphs (separated by blank lines)."""
    return len([p for p in text.split('\n\n') if p.strip()])


def split_sections(article_text):
    """Split article into sections by markdown headings."""
    lines = article_text.split('\n')
    sections = []
    current_title = '(preamble)'
    current_lines = []
    heading_re = re.compile(r'^(#{1,6})\s+(.+)$')
    for line in lines:
        m = heading_re.match(line)
        if m:
            if current_lines:
                sections.append({'title': current_title, 'text': '\n'.join(current_lines)})
            current_title = m.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_lines:
        sections.append({'title': current_title, 'text': '\n'.join(current_lines)})
    return sections


# ════════════════════════════════════════════════════════════════
# Duplicate detection
# ════════════════════════════════════════════════════════════════

def normalize_for_dedup(text):
    """Normalize text for duplicate detection."""
    t = re.sub(r'\s+', '', text)
    t = re.sub(r'[，。！？；：、\u201c\u201d\u2018\u2019（）【】《》\-\u2014\u2026\u00b7,.;:!?\'\"()\[\]{}<>]', '', t)
    return t.lower()


def get_ngrams(text, n=NGRAM_SIZE):
    """Get n-gram character sequences from normalized text."""
    norm = normalize_for_dedup(text)
    if len(norm) < n:
        return set()
    return {norm[i:i+n] for i in range(len(norm) - n + 1)}


def ngram_similarity(text1, text2):
    """Jaccard similarity of n-gram sets."""
    ng1 = get_ngrams(text1)
    ng2 = get_ngrams(text2)
    if not ng1 or not ng2:
        return 0.0
    return len(ng1 & ng2) / len(ng1 | ng2)


def check_duplicate_padding(article_text):
    """Check for duplicate content.
    Detects: exact duplicates, punctuation-normalized duplicates,
    high-similarity n-gram matches, split paragraph duplicates.
    """
    findings = []
    paragraphs = [p.strip() for p in article_text.split('\n\n') if p.strip()]
    if len(paragraphs) < 2:
        return findings

    EXEMPT_PATTERNS = [
        r'^好了，今天就先聊到这儿。?$',
        r'^编辑锚点',
        r'^\[编辑锚点',
        r'^\[Editor',
    ]

    for i, para in enumerate(paragraphs):
        if len(para) < 30:
            continue
        if any(re.match(p, para) for p in EXEMPT_PATTERNS):
            continue

        norm_i = normalize_for_dedup(para)
        if len(norm_i) < 30:
            continue

        for j in range(i + 1, len(paragraphs)):
            para_j = paragraphs[j]
            if len(para_j) < 30:
                continue
            if any(re.match(p, para_j) for p in EXEMPT_PATTERNS):
                continue

            norm_j = normalize_for_dedup(para_j)

            if norm_i == norm_j:
                findings.append({
                    'type': 'exact_duplicate',
                    'para_a': i + 1, 'para_b': j + 1,
                    'preview': para[:80],
                })
                continue

            sim = ngram_similarity(para, para_j)
            if sim >= SIMILARITY_THRESHOLD:
                findings.append({
                    'type': 'high_similarity',
                    'para_a': i + 1, 'para_b': j + 1,
                    'similarity': round(sim, 3),
                    'preview': para[:80],
                })
                continue

            if i + 1 < len(paragraphs) and i + 1 != j:
                combined = normalize_for_dedup(para + paragraphs[i + 1])
                if combined == norm_j and len(combined) > 60:
                    findings.append({
                        'type': 'split_paragraph',
                        'paras': [i + 1, i + 2], 'matches': j + 1,
                        'preview': para[:80],
                    })

    return findings


# ════════════════════════════════════════════════════════════════
# Section budget
# ════════════════════════════════════════════════════════════════

def parse_outline_budgets(outline_path):
    """Parse outline.md to extract section budget information.
    Returns (sections, meta, errors).
    If section headings exist but lack budget fields → errors.
    """
    errors = []
    meta = {}
    sections = []

    if not outline_path or not Path(outline_path).exists():
        return sections, meta, errors

    text = Path(outline_path).read_text(encoding='utf-8')

    for field in ['article_mode', 'length_mode', 'target_visible_chars',
                  'acceptable_min', 'acceptable_max', 'planned_total_chars']:
        m = re.search(rf'- {field}[：:]\s*(.+)', text)
        if m:
            val = m.group(1).strip()
            if field in ('target_visible_chars', 'acceptable_min', 'acceptable_max', 'planned_total_chars'):
                try:
                    meta[field] = int(val)
                except ValueError:
                    meta[field] = val
            else:
                meta[field] = val

    # Section headings that are NOT content sections (skip these)
    NON_SECTION_HEADINGS = {'文章配置', '权重校验', '语义规划校验', '篇幅校验'}

    REQUIRED_SECTION_FIELDS = [
        'weight_percent', 'planned_chars', 'minimum_chars',
        'maximum_chars', 'evidence_ids', 'event_ids', 'unique_information_goal',
    ]

    # Find all ## headings, then check if the following lines contain budget fields
    heading_re = re.compile(r'^##\s+(.+)$', re.MULTILINE)
    for hm in heading_re.finditer(text):
        title = hm.group(1).strip()
        if title in NON_SECTION_HEADINGS:
            continue

        # Get text from this heading to the next ## or end
        start = hm.end()
        next_heading = text.find('\n##', start)
        if next_heading == -1:
            section_text = text[start:]
        else:
            section_text = text[start:next_heading]

        # F1: Check ALL required fields exist; error on any missing
        field_values = {}
        for rf in REQUIRED_SECTION_FIELDS:
            fm = re.search(rf'-\s*{rf}[\uff1a:]\s*(.+)', section_text)
            if not fm:
                errors.append(
                    f"ERROR: outline section '{title}' missing required field '{rf}'"
                )
            else:
                field_values[rf] = fm.group(1).strip()

        # Only add to sections if ALL fields present
        if all(rf in field_values for rf in REQUIRED_SECTION_FIELDS):
            try:
                weight = float(field_values['weight_percent'])
                planned = int(field_values['planned_chars'])
                min_c = int(field_values['minimum_chars'])
                max_c = int(field_values['maximum_chars'])
            except (ValueError, IndexError):
                errors.append(f"ERROR: outline section '{title}' has non-numeric budget values")
                continue
            sections.append({
                'title': title,
                'weight': weight / 100.0 if weight > 1 else weight,
                'planned_chars': planned,
                'minimum_chars': min_c,
                'maximum_chars': max_c,
            })

    # H6: If section headings exist but no budget fields found → error
    heading_titles = [m.group(1).strip() for m in heading_re.finditer(text)
                      if m.group(1).strip() not in NON_SECTION_HEADINGS]
    if heading_titles and not sections:
        errors.append(
            f"ERROR: outline has {len(heading_titles)} section heading(s) "
            f"but no budget fields (weight_percent, planned_chars, minimum_chars, maximum_chars)"
        )

    return sections, meta, errors


def parse_sections_json(sections_json):
    """Parse sections JSON from command line."""
    if not sections_json:
        return None, []
    try:
        sections = json.loads(sections_json)
    except (json.JSONDecodeError, TypeError):
        return None, ["ERROR: --sections JSON is invalid (not valid JSON)"]
    if not isinstance(sections, list):
        return None, ["ERROR: --sections must be a JSON array"]
    return sections, []


def validate_section_budgets(sections, target_visible_chars, article_text):
    """Validate section budgets."""
    errors = []
    warnings = []
    budget_info = []

    if sections is not None and (not isinstance(sections, list) or len(sections) == 0):
        # If sections was explicitly provided (not None) but is empty → error
        # This happens when --sections '[]' is passed
        errors.append("ERROR: sections must be a non-empty array")
        return errors, warnings, budget_info

    if sections is None:
        return errors, warnings, budget_info

    total_weight = sum(s.get('weight', 0) for s in sections)
    if total_weight <= 0:
        errors.append(f"ERROR: section weights sum to {total_weight}, must be > 0")
    elif abs(total_weight - 1.0) > 0.001:
        errors.append(f"ERROR: section weights sum to {total_weight:.1%}, must be 100% (±0.1%)")

    article_sections = split_sections(article_text) if article_text else []

    for i, sec in enumerate(sections):
        if not isinstance(sec, dict):
            errors.append(f"ERROR: section {i} is not a dict")
            continue

        title = sec.get('title', f'section-{i}')
        weight = sec.get('weight', 0)
        text = sec.get('text', '')

        if weight <= 0:
            errors.append(f"ERROR: section '{title}' has weight={weight}, must be > 0")
            continue

        budget = int(target_visible_chars * weight)
        if budget == 0:
            continue

        if article_sections and text:
            actual_chars = count_visible_chars(text)
        elif article_sections:
            matched = [s for s in article_sections if s['title'] == title]
            if not matched:
                errors.append(f"ERROR: section '{title}' not found in article")
                continue
            actual_chars = count_visible_chars(matched[0]['text'])
        else:
            continue

        deviation = abs(actual_chars - budget) / budget if budget > 0 else 0
        info = {
            'title': title, 'weight': round(weight, 3),
            'budget': budget, 'actual_chars': actual_chars,
            'deviation': round(deviation, 3),
        }
        budget_info.append(info)

        if deviation > SECTION_BUDGET_TOLERANCE:
            errors.append(
                f"ERROR: section budget exceeded for '{title}': "
                f"budget={budget}, actual={actual_chars}, "
                f"deviation={deviation:.1%} (max {SECTION_BUDGET_TOLERANCE:.0%})"
            )

    return errors, warnings, budget_info


# ════════════════════════════════════════════════════════════════
# Full mode completeness — deep validation
# ════════════════════════════════════════════════════════════════

# Required fields for each full mode artifact
FULL_MODE_REQUIRED_FIELDS = {
    'generation_profile': {
        'filename': 'generation-profile.yaml',
        'type': 'yaml',
        'fields': ['mode', 'article_mode', 'length_mode', 'target_visible_chars',
                   'acceptable_min', 'acceptable_max', 'material_ledger_path',
                   'ingestion_report_path'],
    },
    'writing_brief': {
        'filename': 'writing-brief.md',
        'type': 'brief',
        'fields': ['article_mode', 'length_mode', 'target_visible_chars',
                   'acceptable_min', 'acceptable_max'],
    },
    'material_readiness': {
        'filename': 'material-readiness.yaml',
        'type': 'yaml',
        'fields': ['topic', 'audience', 'core_opinion', 'evidence',
                   'personal_experience', 'voice_context', 'allowed_output',
                   'required_actions'],
    },
    'material_ingestion_report': {
        'filename': 'material-ingestion-report.json',
        'type': 'json',
        'fields': ['source_coverage', 'event_coverage', 'claim_coverage'],
    },
    'material_ledger': {
        'filename': 'material-ledger.yaml',
        'type': 'yaml',
        'fields': ['material_ledger'],
    },
    'evidence_map': {
        'filename': 'evidence-map.md',
        'type': 'md',
        'fields': [],
    },
    'core_card': {
        'filename': 'core-card.md',
        'type': 'core_card',
        'fields': ['Core Statement', 'Reader Change', 'Core Tension',
                   'Value Carrier', 'Scope', 'Result'],
    },
    'outline': {
        'filename': 'outline.md',
        'type': 'outline',
        'fields': [],
    },
    'article': {
        'filename': 'article.md',
        'type': 'article',
        'fields': [],
    },
    'semantic_map': {
        'filename': 'semantic-map.yaml',
        'type': 'semantic_map',
        'fields': [],
    },
    'editor_report': {
        'filename': 'editor-report.md',
        'type': 'editor_report',
        'fields': ['P0', 'P1', 'P2'],
    },
    # 档76A/OBS-252:handoff.yaml 从「建议产出」升为 full-mode 必检(12 件)。
    # 必填字段:handoff.schema_version / prose_craft_applied / prose_craft_version /
    # formatter.cover(嵌套路径,见 handoff 检查分支)。
    'handoff': {
        'filename': 'handoff.yaml',
        'type': 'yaml_handoff',
        'fields': ['schema_version', 'prose_craft_applied', 'prose_craft_version',
                   'formatter.cover'],
    },
}


def check_full_mode_completeness(paths, runtime_policy=None, material_exhausted=False):
    """Check full mode product completeness — deep validation using production validators.
    paths: dict mapping key -> Path or None.
    runtime_policy: dict with article_mode, target_visible_chars, acceptable_min, acceptable_max
    Returns (errors, details).
    """
    errors = []
    details = []

    for key, spec in FULL_MODE_REQUIRED_FIELDS.items():
        filepath = paths.get(key)
        filename = spec['filename']

        if filepath is None:
            errors.append(f"ERROR: full mode requires {filename} but path not provided")
            details.append({'file': filename, 'status': 'missing_path'})
            continue

        fp = Path(filepath)
        if not fp.exists():
            errors.append(f"ERROR: full mode requires {filename} but file not found: {filepath}")
            details.append({'file': filename, 'status': 'not_found'})
            continue

        try:
            content = fp.read_text(encoding='utf-8').strip()
        except Exception:
            errors.append(f"ERROR: {filename} exists but cannot be read as text")
            details.append({'file': filename, 'status': 'unreadable'})
            continue

        if not content:
            errors.append(f"ERROR: {filename} is empty")
            details.append({'file': filename, 'status': 'empty'})
            continue

        ftype = spec['type']
        required_fields = spec.get('fields', [])
        parse_ok = True

        # ── generation-profile.yaml ──
        if ftype == 'yaml' and key == 'generation_profile':
            if yaml is None:
                continue
            try:
                data = yaml.safe_load(content)
                if not isinstance(data, dict):
                    errors.append(f"ERROR: {filename} top-level must be a dict")
                    details.append({'file': filename, 'status': 'not_dict'})
                    continue
                for field in required_fields:
                    if field not in data:
                        errors.append(f"ERROR: {filename} missing required field '{field}'")
                        details.append({'file': filename, 'status': 'missing_field', 'field': field})
                        parse_ok = False
                # H7: mode must be 'full'
                if data.get('mode') != 'full':
                    errors.append(f"ERROR: {filename} mode must be 'full', got '{data.get('mode')}'")
                    details.append({'file': filename, 'status': 'invalid_mode'})
                    parse_ok = False
                # H7: article_mode must be valid
                if data.get('article_mode') and data['article_mode'] not in ALLOWED_MODES:
                    errors.append(f"ERROR: {filename} invalid article_mode '{data['article_mode']}'")
                    parse_ok = False
                # H7: length fields must be positive integers
                for lf in ['target_visible_chars', 'acceptable_min', 'acceptable_max']:
                    val = data.get(lf)
                    if val is not None and (not isinstance(val, int) or val <= 0):
                        errors.append(f"ERROR: {filename} {lf} must be positive integer, got {val}")
                        parse_ok = False
            except yaml.YAMLError as e:
                errors.append(f"ERROR: {filename} has invalid YAML: {e}")
                details.append({'file': filename, 'status': 'invalid_yaml'})
                continue

        # ── material-readiness.yaml ──
        elif ftype == 'yaml' and key == 'material_readiness':
            if yaml is None:
                continue
            try:
                data = yaml.safe_load(content)
                if not isinstance(data, dict):
                    errors.append(f"ERROR: {filename} top-level must be a dict")
                    continue
                for field in required_fields:
                    if field not in data:
                        errors.append(f"ERROR: {filename} missing required field '{field}'")
                        parse_ok = False
                    elif field == 'required_actions':
                        # required_actions can be empty list, just must be a list
                        if not isinstance(data[field], list):
                            errors.append(f"ERROR: {filename} field '{field}' must be a list")
                            parse_ok = False
                    elif not data[field]:
                        errors.append(f"ERROR: {filename} field '{field}' is empty")
                        parse_ok = False
                # required_actions must be list
                ra = data.get('required_actions')
                if ra is not None and not isinstance(ra, list):
                    errors.append(f"ERROR: {filename} required_actions must be a list")
                    parse_ok = False
                # allowed_output must be valid enum
                ao = data.get('allowed_output')
                if ao and ao not in ('idea', 'outline', 'draft', 'review', 'full'):
                    errors.append(f"ERROR: {filename} invalid allowed_output '{ao}'")
                    parse_ok = False
            except yaml.YAMLError as e:
                errors.append(f"ERROR: {filename} has invalid YAML: {e}")
                details.append({'file': filename, 'status': 'invalid_yaml'})
                continue

        # ── material-ledger.yaml: call production validator (H2) ──
        elif ftype == 'yaml' and key == 'material_ledger':
            if load_ledger_yaml is None:
                details.append({'file': filename, 'status': 'ok', 'note': 'material_ingestion not available'})
                continue
            ledger, load_errors = load_ledger_yaml(str(fp))
            if load_errors:
                errors.extend(load_errors)
                details.append({'file': filename, 'status': 'invalid_ledger'})
                continue
            # Call production generate_ingestion_report
            report, report_errors = generate_ingestion_report(ledger)
            if report_errors:
                errors.extend(report_errors)
                details.append({'file': filename, 'status': 'ledger_validation_failed'})
                continue

        # ── material-ingestion-report.json: recompute and compare (H3) ──
        elif ftype == 'json' and key == 'material_ingestion_report':
            try:
                data = json.loads(content)
                if not isinstance(data, dict):
                    errors.append(f"ERROR: {filename} must be a JSON object")
                    continue
                for field in required_fields:
                    if field not in data:
                        errors.append(f"ERROR: {filename} missing required field '{field}'")
                        parse_ok = False
                # Validate coverage is number in 0-1
                for cov_field in ['source_coverage', 'event_coverage', 'claim_coverage']:
                    val = data.get(cov_field)
                    if val is not None:
                        if not isinstance(val, (int, float)):
                            errors.append(f"ERROR: {filename} {cov_field} must be a number, got {type(val).__name__}")
                            parse_ok = False
                        elif val < 0 or val > 1:
                            errors.append(f"ERROR: {filename} {cov_field} must be 0-1, got {val}")
                            parse_ok = False

                # H3: recompute from ledger and compare
                ledger_path = paths.get('material_ledger')
                if ledger_path and load_ledger_yaml is not None:
                    ledger, _ = load_ledger_yaml(ledger_path)
                    if ledger:
                        recomputed, _ = generate_ingestion_report(ledger)
                        if recomputed:
                            compare_fields = ['total_materials', 'total_events', 'total_claims',
                                              'source_coverage', 'event_coverage', 'claim_coverage',
                                              'duplicates_removed', 'conflicts_detected']
                            for cf in compare_fields:
                                if cf in data and cf in recomputed:
                                    if data[cf] != recomputed[cf]:
                                        errors.append(
                                            f"ERROR: {filename} {cf}={data[cf]} "
                                            f"does not match recomputed value {recomputed[cf]}"
                                        )
                                        parse_ok = False
            except json.JSONDecodeError as e:
                errors.append(f"ERROR: {filename} has invalid JSON: {e}")
                details.append({'file': filename, 'status': 'invalid_json'})
                continue

        # ── generic YAML fallback ──
        elif ftype == 'yaml':
            if yaml is None:
                continue
            try:
                data = yaml.safe_load(content)
                if not isinstance(data, dict):
                    errors.append(f"ERROR: {filename} top-level must be a dict")
                    continue
                for field in required_fields:
                    if field not in data:
                        errors.append(f"ERROR: {filename} missing required field '{field}'")
                        parse_ok = False
            except yaml.YAMLError as e:
                errors.append(f"ERROR: {filename} has invalid YAML: {e}")
                details.append({'file': filename, 'status': 'invalid_yaml'})
                continue

        # ── writing-brief.md (F2: parse and validate actual values) ──
        elif ftype == 'brief':
            # Parse each field's value
            brief_fields = ['article_mode', 'length_mode', 'target_visible_chars',
                            'acceptable_min', 'acceptable_max', 'output_mode']
            brief_values = {}
            for field in brief_fields:
                m = re.search(rf'{re.escape(field)}[\uff1a:]\s*(.+)', content)
                if not m:
                    errors.append(f"ERROR: {filename} missing required field '{field}'")
                    parse_ok = False
                else:
                    brief_values[field] = m.group(1).strip()

            # Validate article_mode
            if 'article_mode' in brief_values:
                if brief_values['article_mode'] not in ALLOWED_MODES:
                    errors.append(f"ERROR: {filename} invalid article_mode '{brief_values['article_mode']}'")
                    parse_ok = False

            # Validate length_mode
            if 'length_mode' in brief_values:
                if brief_values['length_mode'] not in ALLOWED_MODES:
                    errors.append(f"ERROR: {filename} invalid length_mode '{brief_values['length_mode']}'")
                    parse_ok = False

            # Validate length fields are positive integers
            for lf in ['target_visible_chars', 'acceptable_min', 'acceptable_max']:
                if lf in brief_values:
                    try:
                        val = int(brief_values[lf])
                        if val <= 0:
                            errors.append(f"ERROR: {filename} {lf} must be positive, got {val}")
                            parse_ok = False
                    except ValueError:
                        errors.append(f"ERROR: {filename} {lf} must be integer, got '{brief_values[lf]}'")
                        parse_ok = False

            # Validate min <= target <= max
            if all(k in brief_values for k in ['target_visible_chars', 'acceptable_min', 'acceptable_max']):
                try:
                    t = int(brief_values['target_visible_chars'])
                    mn = int(brief_values['acceptable_min'])
                    mx = int(brief_values['acceptable_max'])
                    if mn > t:
                        errors.append(f"ERROR: {filename} acceptable_min({mn}) > target({t})")
                        parse_ok = False
                    if t > mx:
                        errors.append(f"ERROR: {filename} target({t}) > acceptable_max({mx})")
                        parse_ok = False
                except ValueError:
                    pass  # Already reported as non-integer

            # Validate output_mode == 'full'
            if 'output_mode' in brief_values:
                if brief_values['output_mode'] != 'full':
                    errors.append(f"ERROR: {filename} output_mode must be 'full', got '{brief_values['output_mode']}'")
                    parse_ok = False

        # ── core-card.md (H7) ──
        elif ftype == 'core_card':
            for field in required_fields:
                if field.lower() not in content.lower():
                    errors.append(f"ERROR: {filename} missing required section '{field}'")
                    details.append({'file': filename, 'status': 'missing_section', 'section': field})
                    parse_ok = False
            # All fields must have non-empty content (not just titles on same line)
            for field in required_fields:
                pattern = re.compile(rf'{re.escape(field)}[:：]\s*(.+)', re.IGNORECASE)
                m = pattern.search(content)
                if not m or not m.group(1).strip():
                    errors.append(f"ERROR: {filename} section '{field}' has no content")
                    parse_ok = False

        # ── editor-report.md (F3: each section must have non-empty content) ──
        elif ftype == 'editor_report':
            required_sections = ['总体判断', 'P0', 'P1', 'P2', '分项评分', '修订计划', '交接保护项']
            for sec in required_sections:
                # Try "标题: 内容" format
                m = re.search(rf'{re.escape(sec)}[\uff1a:]\s*(.+)', content)
                if m and m.group(1).strip():
                    continue
                # Try "## 标题\n内容" format
                m2 = re.search(rf'##\s*{re.escape(sec)}\s*\n+(.+)', content)
                if m2 and m2.group(1).strip():
                    continue
                # Section exists but no content, or section missing entirely
                if sec in content:
                    errors.append(f"ERROR: {filename} section '{sec}' has no content")
                else:
                    errors.append(f"ERROR: {filename} missing required section '{sec}'")
                parse_ok = False

        # ── handoff.yaml (档76A/OBS-252:full-mode 必检,嵌套字段) ──
        elif ftype == 'yaml_handoff':
            if yaml is None:
                continue
            try:
                data = yaml.safe_load(content)
                if not isinstance(data, dict) or not isinstance(data.get('handoff'), dict):
                    errors.append(f"ERROR: {filename} top-level must be {{handoff: {{...}}}}")
                    parse_ok = False
                    continue
                h = data['handoff']
                # 嵌套路径检查:schema_version / prose_craft_applied / prose_craft_version 顶层,
                # formatter.cover 嵌套(缺任一即 fail-closed)。
                for field in ('schema_version', 'prose_craft_applied', 'prose_craft_version'):
                    if h.get(field) in (None, ''):
                        errors.append(f"ERROR: {filename} missing required field 'handoff.{field}'"); parse_ok = False
                cover = (h.get('formatter') or {}).get('cover') if isinstance(h.get('formatter'), dict) else None
                if not isinstance(cover, dict) or not cover:
                    errors.append(f"ERROR: {filename} missing required field 'handoff.formatter.cover'"); parse_ok = False
            except yaml.YAMLError as e:
                errors.append(f"ERROR: {filename} has invalid YAML: {e}")
                continue

        # ── outline.md (H6) ──
        elif ftype == 'outline':
            # Must have article-level budget fields
            article_fields = ['article_mode', 'length_mode', 'target_visible_chars',
                             'acceptable_min', 'acceptable_max', 'planned_total_chars']
            for field in article_fields:
                if field not in content:
                    errors.append(f"ERROR: {filename} missing article-level field '{field}'")
                    parse_ok = False

            # Parse sections — use errors from parse_outline_budgets (F1: don't discard)
            sections, outline_meta, outline_errors = parse_outline_budgets(str(fp))
            if outline_errors:
                errors.extend(outline_errors)
                parse_ok = False
            if not sections and not outline_errors:
                # Check if there ARE headings in the outline
                has_headings = bool(re.search(r'^##\s+\S+', content, re.MULTILINE))
                if has_headings:
                    errors.append(f"ERROR: {filename} has section headings but no budget fields (weight_percent, planned_chars, etc.)")
                    parse_ok = False
            elif sections:
                # Validate section budget fields
                total_weight = sum(s.get('weight', 0) for s in sections)
                if abs(total_weight - 1.0) > 0.001:
                    errors.append(f"ERROR: {filename} section weights sum to {total_weight:.1%}, must be 100%")
                    parse_ok = False
                total_planned = sum(s.get('planned_chars', 0) for s in sections)
                # Check planned vs target
                tvc_match = re.search(r'target_visible_chars[：:]\s*(\d+)', content)
                if tvc_match:
                    tvc = int(tvc_match.group(1))
                    if abs(total_planned - tvc) > tvc * 0.05:
                        errors.append(f"ERROR: {filename} planned_chars total ({total_planned}) deviates from target ({tvc}) by >5%")
                        parse_ok = False
                # Check min <= planned <= max
                for s in sections:
                    pc = s.get('planned_chars', 0)
                    mn = s.get('minimum_chars', 0)
                    mx = s.get('maximum_chars', 0)
                    if mn > pc or pc > mx:
                        errors.append(f"ERROR: {filename} section '{s.get('title', '')}': minimum({mn}) > planned({pc}) or planned > maximum({mx})")
                        parse_ok = False

        # ── semantic-map.yaml: call production validator (H4) ──
        elif ftype == 'semantic_map':
            if yaml is None:
                continue
            try:
                sm_data = yaml.safe_load(content)
                if not isinstance(sm_data, dict):
                    errors.append(f"ERROR: {filename} top-level must be a dict")
                    continue
                if 'schema_version' not in sm_data:
                    errors.append(f"ERROR: {filename} missing 'schema_version'")
                    parse_ok = False
                if 'blocks' not in sm_data:
                    errors.append(f"ERROR: {filename} missing 'blocks'")
                    parse_ok = False
                if not sm_data.get('blocks'):
                    errors.append(f"ERROR: {filename} blocks list is empty")
                    parse_ok = False
                # H4: Call the production semantic map validator
                article_path = paths.get('article')
                evidence_path = paths.get('evidence_map')
                if article_path:
                    try:
                        from validate_semantic_map import validate_semantic_map
                        ev_path = str(evidence_path) if evidence_path else None
                        sm_errors, _, _ = validate_semantic_map(
                            article_path, str(fp),
                            formatter_root=None,
                            evidence_map_path=ev_path,
                        )
                        if sm_errors:
                            for e in sm_errors:
                                errors.append(f"ERROR: {filename} semantic validator: {e}")
                            details.append({'file': filename, 'status': 'semantic_validation_failed'})
                            parse_ok = False
                    except ImportError:
                        details.append({'file': filename, 'status': 'ok', 'note': 'semantic_map validator not available'})
            except yaml.YAMLError as e:
                errors.append(f"ERROR: {filename} has invalid YAML: {e}")
                details.append({'file': filename, 'status': 'invalid_yaml'})
                continue

        # ── evidence-map.md (H5) ──
        elif ftype == 'md' and key == 'evidence_map':
            if len(content) < 10:
                errors.append(f"ERROR: {filename} has insufficient content (< 10 chars)")
                details.append({'file': filename, 'status': 'too_short'})
                continue
            # Must contain at least one evidence ID pattern
            if not re.search(r'(?:ev|EV)[-_]?\d+', content):
                errors.append(f"ERROR: {filename} must contain at least one Evidence ID (e.g. ev-001)")
                details.append({'file': filename, 'status': 'no_evidence_id'})
                parse_ok = False

        # ── article.md ──
        elif ftype == 'article':
            if len(content) < 50:
                errors.append(f"ERROR: {filename} has insufficient content (< 50 chars)")
                details.append({'file': filename, 'status': 'too_short'})
                continue

        # ── generic md fallback ──
        elif ftype == 'md':
            if len(content) < 10:
                errors.append(f"ERROR: {filename} has insufficient content (< 10 chars)")
                details.append({'file': filename, 'status': 'too_short'})
                continue

        if parse_ok:
            details.append({'file': filename, 'status': 'ok'})

    # ── F4: Cross-artifact consistency checks ──
    cross_errors = check_cross_artifact_consistency(paths, errors, runtime_policy)
    errors.extend(cross_errors)

    return errors, details


def check_cross_artifact_consistency(paths, existing_errors, runtime_policy=None):
    """Check consistency across generation-profile, writing-brief, outline, and CLI runtime policy.
    Returns list of error strings.
    """
    errors = []

    if yaml is None:
        return errors

    # Parse generation-profile.yaml
    gp_path = paths.get('generation_profile')
    gp_data = None
    gp_dir = None
    if gp_path and Path(gp_path).exists():
        try:
            gp_data = yaml.safe_load(Path(gp_path).read_text(encoding='utf-8'))
            gp_dir = Path(gp_path).resolve().parent
        except (yaml.YAMLError, Exception):
            pass

    # Parse writing-brief.md
    brief_path = paths.get('writing_brief')
    brief_data = {}
    if brief_path and Path(brief_path).exists():
        brief_content = Path(brief_path).read_text(encoding='utf-8')
        for field in ['article_mode', 'length_mode', 'target_visible_chars',
                      'acceptable_min', 'acceptable_max']:
            m = re.search(rf'{re.escape(field)}[\uff1a:]\s*(.+)', brief_content)
            if m:
                val = m.group(1).strip()
                try:
                    brief_data[field] = int(val) if field in ('target_visible_chars', 'acceptable_min', 'acceptable_max') else val
                except ValueError:
                    brief_data[field] = val

    # Parse outline.md
    outline_path = paths.get('outline')
    outline_data = {}
    if outline_path and Path(outline_path).exists():
        outline_content = Path(outline_path).read_text(encoding='utf-8')
        for field in ['article_mode', 'length_mode', 'target_visible_chars',
                      'acceptable_min', 'acceptable_max', 'planned_total_chars']:
            m = re.search(rf'-\s*{re.escape(field)}[\uff1a:]\s*(.+)', outline_content)
            if m:
                val = m.group(1).strip()
                try:
                    outline_data[field] = int(val) if field in ('target_visible_chars', 'acceptable_min', 'acceptable_max', 'planned_total_chars') else val
                except ValueError:
                    outline_data[field] = val

    # Check Profile fields
    if gp_data and isinstance(gp_data, dict):
        # F4-1: length_mode must be allowed
        lm = gp_data.get('length_mode')
        if lm and lm not in ALLOWED_MODES:
            errors.append(f"ERROR: generation-profile.yaml invalid length_mode '{lm}'")

        # F4-2: acceptable_min <= target <= acceptable_max
        t = gp_data.get('target_visible_chars')
        mn = gp_data.get('acceptable_min')
        mx = gp_data.get('acceptable_max')
        if all(isinstance(x, int) for x in [t, mn, mx]):
            if mn > t:
                errors.append(f"ERROR: generation-profile.yaml acceptable_min({mn}) > target({t})")
            if t > mx:
                errors.append(f"ERROR: generation-profile.yaml target({t}) > acceptable_max({mx})")

        # F4-3: material_ledger_path resolves to the CLI-provided ledger
        ml_path = gp_data.get('material_ledger_path')
        cli_ml = paths.get('material_ledger')
        if ml_path and cli_ml and gp_dir:
            resolved = (gp_dir / ml_path).resolve()
            cli_resolved = Path(cli_ml).resolve()
            if resolved != cli_resolved:
                errors.append(
                    f"ERROR: generation-profile.yaml material_ledger_path '{ml_path}' "
                    f"does not match CLI-provided ledger path"
                )

        # F4-4: ingestion_report_path resolves to the CLI-provided report
        ir_path = gp_data.get('ingestion_report_path')
        cli_ir = paths.get('material_ingestion_report')
        if ir_path and cli_ir and gp_dir:
            resolved = (gp_dir / ir_path).resolve()
            cli_resolved = Path(cli_ir).resolve()
            if resolved != cli_resolved:
                errors.append(
                    f"ERROR: generation-profile.yaml ingestion_report_path '{ir_path}' "
                    f"does not match CLI-provided report path"
                )

        # F4-5: Cross-check Profile, Brief, Outline fields
        cross_fields = ['article_mode', 'length_mode', 'target_visible_chars',
                        'acceptable_min', 'acceptable_max']
        for field in cross_fields:
            gp_val = gp_data.get(field)
            brief_val = brief_data.get(field)
            outline_val = outline_data.get(field)

            if gp_val is not None and brief_val is not None:
                if gp_val != brief_val:
                    errors.append(
                        f"ERROR: cross-artifact mismatch: generation-profile {field}={gp_val} "
                        f"vs writing-brief {field}={brief_val}"
                    )
            if gp_val is not None and outline_val is not None:
                if gp_val != outline_val:
                    errors.append(
                        f"ERROR: cross-artifact mismatch: generation-profile {field}={gp_val} "
                        f"vs outline {field}={outline_val}"
                    )
            if brief_val is not None and outline_val is not None:
                if brief_val != outline_val:
                    errors.append(
                        f"ERROR: cross-artifact mismatch: writing-brief {field}={brief_val} "
                        f"vs outline {field}={outline_val}"
                    )

    # ── F4/hotfix5: Compare runtime policy against file-based artifacts ──
    if runtime_policy:
        rt_fields = ['article_mode', 'target_visible_chars', 'acceptable_min', 'acceptable_max']
        for field in rt_fields:
            rt_val = runtime_policy.get(field)
            if rt_val is None:
                continue

            # vs generation-profile
            if gp_data and isinstance(gp_data, dict):
                gp_val = gp_data.get(field)
                if gp_val is not None and gp_val != rt_val:
                    errors.append(
                        f"ERROR: cross-artifact mismatch: runtime {field}={rt_val} "
                        f"vs generation-profile {field}={gp_val}"
                    )

            # vs writing-brief
            if brief_data:
                bv = brief_data.get(field)
                if bv is not None and bv != rt_val:
                    errors.append(
                        f"ERROR: cross-artifact mismatch: runtime {field}={rt_val} "
                        f"vs writing-brief {field}={bv}"
                    )

            # vs outline
            if outline_data:
                ov = outline_data.get(field)
                if ov is not None and ov != rt_val:
                    errors.append(
                        f"ERROR: cross-artifact mismatch: runtime {field}={rt_val} "
                        f"vs outline {field}={ov}"
                    )

        # Verify outline planned_total_chars == target_visible_chars
        if outline_data:
            ptc = outline_data.get('planned_total_chars')
            tvc = outline_data.get('target_visible_chars')
            if ptc is not None and tvc is not None and ptc != tvc:
                errors.append(
                    f"ERROR: outline planned_total_chars({ptc}) "
                    f"!= target_visible_chars({tvc})"
                )

    return errors


# ════════════════════════════════════════════════════════════════
# Main validation
# ════════════════════════════════════════════════════════════════

def validate_article_length(article_path, target_visible_chars=None,
                            acceptable_min=None, acceptable_max=None,
                            article_mode=None, sections=None,
                            outline_path=None,
                            full_mode=False, full_mode_paths=None,
                            material_exhausted=False):
    """Validate article length against policy."""
    errors = []
    warnings = []
    info = {}

    # Mode validation
    user_target_explicit = target_visible_chars is not None
    user_min_explicit = acceptable_min is not None
    user_max_explicit = acceptable_max is not None

    if article_mode is not None and article_mode not in ALLOWED_MODES:
        errors.append(
            f"ERROR: unknown article_mode '{article_mode}'. "
            f"Allowed: {', '.join(sorted(ALLOWED_MODES))}"
        )
        article_mode = None

    if article_mode and article_mode in ALLOWED_MODES:
        preset = LENGTH_MODE_PRESETS[article_mode]
        if target_visible_chars is None:
            target_visible_chars = preset['target_visible_chars']
        if acceptable_min is None:
            acceptable_min = preset['acceptable_min']
        if acceptable_max is None:
            acceptable_max = preset['acceptable_max']

    if target_visible_chars is None:
        target_visible_chars = 3000
    if acceptable_min is None:
        acceptable_min = round(target_visible_chars * 0.85)
    if acceptable_max is None:
        acceptable_max = round(target_visible_chars * 1.15)

    if user_target_explicit and not user_min_explicit:
        acceptable_min = round(target_visible_chars * 0.85)
    if user_target_explicit and not user_max_explicit:
        acceptable_max = round(target_visible_chars * 1.15)

    if target_visible_chars <= 0:
        errors.append(f"ERROR: target_visible_chars must be > 0, got {target_visible_chars}")
    if acceptable_min <= 0:
        errors.append(f"ERROR: acceptable_min must be > 0, got {acceptable_min}")
    if acceptable_max <= 0:
        errors.append(f"ERROR: acceptable_max must be > 0, got {acceptable_max}")
    if acceptable_min > target_visible_chars:
        errors.append(f"ERROR: acceptable_min ({acceptable_min}) > target ({target_visible_chars})")
    if target_visible_chars > acceptable_max:
        errors.append(f"ERROR: target ({target_visible_chars}) > acceptable_max ({acceptable_max})")

    info['article_mode'] = article_mode
    info['target_visible_chars'] = target_visible_chars
    info['acceptable_min'] = acceptable_min
    info['acceptable_max'] = acceptable_max

    # Read article
    article_path = Path(article_path)
    if not article_path.exists():
        errors.append(f"ERROR: article file not found: {article_path}")
        return errors, warnings, info
    article_text = article_path.read_text(encoding='utf-8')

    # Character counts
    visible_chars = count_visible_chars(article_text)
    info['visible_chars'] = visible_chars
    info['cjk_chars'] = count_cjk_chars(article_text)
    info['latin_words'] = count_latin_words(article_text)
    info['digits'] = count_digits(article_text)
    info['punctuation_chars'] = count_punctuation(article_text)
    info['visible_chars_no_whitespace'] = visible_chars
    info['paragraphs'] = count_paragraphs(article_text)

    article_sections = split_sections(article_text)
    info['sections'] = len(article_sections)

    # Length gate
    # 76R/OBS-290:素材定长度——注册 claim 全覆盖 + 材料门通过(material_exhausted)
    # 时,长度下限降为 advisory(不足留痕说明,不报错逼扩写);素材充分但文章
    # 单薄(非 material_exhausted)仍 FAIL(质量下限不退让)。
    if visible_chars < acceptable_min:
        if material_exhausted:
            warnings.append(
                f"WARN: article length {visible_chars} chars below acceptable_min "
                f"{acceptable_min} — material exhausted (76R/OBS-290), 素材写干即停,不逼扩写"
            )
            info['length_status'] = 'below_min_material_exhausted'
            info['material_exhausted'] = True
        else:
            errors.append(
                f"ERROR: article length {visible_chars} chars is below "
                f"acceptable_min {acceptable_min}"
            )
            info['length_status'] = 'below_min'
    elif visible_chars > acceptable_max:
        warnings.append(
            f"WARN: article length {visible_chars} chars exceeds "
            f"acceptable_max {acceptable_max}. Check for redundancy."
        )
        info['length_status'] = 'above_max'
    else:
        info['length_status'] = 'within_range'

    # Duplicate detection
    dup_findings = check_duplicate_padding(article_text)
    info['duplicate_findings'] = dup_findings
    for f in dup_findings:
        errors.append(
            f"ERROR: duplicate content detected: "
            f"{f['type']} between paragraphs {f.get('para_a', '?')} and {f.get('para_b', '?')}"
        )

    # Section budgets
    if sections is None and outline_path:
        sections, outline_meta, outline_errors = parse_outline_budgets(outline_path)
        errors.extend(outline_errors)
        if outline_meta:
            info['outline_meta'] = outline_meta

    if sections is not None:
        budget_errors, budget_warnings, budget_info = validate_section_budgets(
            sections, target_visible_chars, article_text
        )
        errors.extend(budget_errors)
        warnings.extend(budget_warnings)
        info['section_budgets'] = budget_info

    # Full mode completeness
    if full_mode:
        if full_mode_paths is None:
            full_mode_paths = {}
        fm_errors, fm_details = check_full_mode_completeness(full_mode_paths, {
            'article_mode': article_mode,
            'target_visible_chars': target_visible_chars,
            'acceptable_min': acceptable_min,
            'acceptable_max': acceptable_max,
        }, material_exhausted=material_exhausted)
        errors.extend(fm_errors)
        info['full_mode_details'] = fm_details

    info['passed'] = len(errors) == 0
    info['error_count'] = len(errors)
    info['warning_count'] = len(warnings)

    if not info.get('length_status'):
        info['length_status'] = 'invalid_policy' if errors else 'within_range'

    return errors, warnings, info


# ════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Validate article length against length-policy')
    parser.add_argument('--article', required=True, help='Path to article.md')
    parser.add_argument('--target-visible-chars', type=int, default=None)
    parser.add_argument('--acceptable-min', type=int, default=None)
    parser.add_argument('--acceptable-max', type=int, default=None)
    parser.add_argument('--article-mode', default=None, help='Length mode preset')
    parser.add_argument('--sections', default=None, help='JSON array of sections')
    parser.add_argument('--outline', default=None, help='Path to outline.md for budget parsing')
    parser.add_argument('--full-mode', action='store_true', help='Check full mode product completeness')
    parser.add_argument('--brief', default=None)
    parser.add_argument('--evidence-map', default=None)
    parser.add_argument('--core-card', default=None)
    parser.add_argument('--editor-report', default=None)
    parser.add_argument('--generation-profile', default=None)
    parser.add_argument('--material-readiness', default=None)
    parser.add_argument('--material-ledger', default=None)
    parser.add_argument('--material-report', default=None)
    parser.add_argument('--semantic-map', default=None, help='Path to semantic-map.yaml')
    parser.add_argument('--json', action='store_true', help='Output JSON only')
    parser.add_argument('--handoff', default=None, help='Path to handoff.yaml (档76A full-mode 必检)')
    args = parser.parse_args()

    sections = None
    if args.sections:
        sections, sec_errors = parse_sections_json(args.sections)
        if sec_errors:
            for e in sec_errors:
                print(e, file=sys.stderr)
            sys.exit(1)

    full_mode_paths = {}
    if args.full_mode:
        full_mode_paths = {
            'generation_profile': args.generation_profile,
            'writing_brief': args.brief,
            'material_readiness': args.material_readiness,
            'material_ingestion_report': args.material_report,
            'material_ledger': args.material_ledger,
            'evidence_map': args.evidence_map,
            'core_card': args.core_card,
            'outline': args.outline,
            'article': args.article,
            'semantic_map': args.semantic_map,
            'editor_report': args.editor_report,
            'handoff': args.handoff,
        }

    # 76R/OBS-290:素材定长度——full-mode 时读 material-readiness,注册 claim
    # 全覆盖(claim_coverage==1.0)且材料门允许 full(allowed_output=full)视为
    # 素材耗尽:长度下限降 advisory(不足留痕),不再逼扩写。
    material_exhausted = False
    if args.full_mode and args.material_readiness:
        try:
            _mr = yaml.safe_load(Path(args.material_readiness).read_text(encoding="utf-8")) or {}
            _cov = _mr.get("claim_coverage")
            _ao = _mr.get("allowed_output")
            if (isinstance(_cov, (int, float)) and _cov >= 1.0
                    and _ao == "full"):
                material_exhausted = True
        except (OSError, yaml.YAMLError):
            material_exhausted = False

    errors, warnings, info = validate_article_length(
        args.article,
        target_visible_chars=args.target_visible_chars,
        acceptable_min=args.acceptable_min,
        acceptable_max=args.acceptable_max,
        article_mode=args.article_mode,
        sections=sections,
        outline_path=args.outline,
        full_mode=args.full_mode,
        full_mode_paths=full_mode_paths if args.full_mode else None,
        material_exhausted=material_exhausted,
    )

    result = {
        'passed': info.get('passed', False),
        'length_status': info.get('length_status', 'invalid_policy'),
        'article_mode': info.get('article_mode'),
        'cjk_chars': info.get('cjk_chars', 0),
        'latin_words': info.get('latin_words', 0),
        'visible_chars_no_whitespace': info.get('visible_chars_no_whitespace', 0),
        'paragraphs': info.get('paragraphs', 0),
        'sections': info.get('sections', 0),
        'target_visible_chars': info.get('target_visible_chars', 0),
        'acceptable_min': info.get('acceptable_min', 0),
        'acceptable_max': info.get('acceptable_max', 0),
        'section_budgets': info.get('section_budgets', []),
        'duplicate_findings': info.get('duplicate_findings', []),
        'errors': errors,
        'warnings': warnings,
    }

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("=" * 60)
        print("Article Length Validation Report")
        print("=" * 60)
        print(f"\nArticle: {args.article}")
        print(f"Article mode: {info.get('article_mode', 'N/A')}")
        print(f"Length status: {info.get('length_status', 'N/A')}")
        print(f"CJK chars: {info.get('cjk_chars', 0)}")
        print(f"Latin words: {info.get('latin_words', 0)}")
        print(f"Visible chars: {info.get('visible_chars', 0)}")
        print(f"Paragraphs: {info.get('paragraphs', 0)}")
        print(f"Target: {info.get('target_visible_chars', 'N/A')}")
        print(f"Acceptable range: {info.get('acceptable_min', 'N/A')} - {info.get('acceptable_max', 'N/A')}")
        if info.get('section_budgets'):
            print(f"\nSection budgets:")
            for b in info['section_budgets']:
                print(f"  {b['title']}: budget={b['budget']}, actual={b['actual_chars']}, deviation={b['deviation']:.1%}")
        if info.get('duplicate_findings'):
            print(f"\nDuplicate findings: {len(info['duplicate_findings'])}")
            for f in info['duplicate_findings']:
                print(f"  {f['type']}: {f.get('preview', '')[:60]}")
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
