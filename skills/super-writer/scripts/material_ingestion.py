#!/usr/bin/env python3
"""Material ingestion: dedup, event routing, coverage, and ingestion report.

Functions:
  - normalize_url, compute_url_hash, compute_content_hash
  - detect_exact_duplicates, check_duplicate_status
  - build_event_index, validate_event_assignments
  - compute_source_coverage, compute_event_coverage, compute_claim_coverage
  - resolve_article_mode, generate_ingestion_report

CLI:
  python scripts/material_ingestion.py \\
    --ledger material-ledger.yaml \\
    --output material-ingestion-report.json

Exit codes:
  0 = success, report generated
  1 = ledger structure or consistency errors
  2 = dependency or runtime error
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(2)


# ── Allowed article modes ──

ALLOWED_MODES = {
    'short', 'medium', 'long', 'deep',
    'daily_digest', 'weekly_roundup', 'material_synthesis',
}

# ── Allowed material statuses ──

ALLOWED_STATUSES = {'used', 'deduplicated', 'conflicting', 'excluded'}

# ── Allowed exclusion reasons ──

ALLOWED_EXCLUDE_REASONS = {
    'duplicate', 'irrelevant', 'outdated', 'superseded', 'conflicting_kept',
}


# ════════════════════════════════════════════════════════════════
# URL normalization
# ════════════════════════════════════════════════════════════════

def normalize_url(url):
    """Normalize URL for comparison: lowercase, strip fragment, trailing slash, www."""
    if not url:
        return ''
    u = url.strip().lower()
    u = re.sub(r'#.*$', '', u)
    u = u.rstrip('/')
    u = re.sub(r'^(https?://)www\.', r'\1', u)
    return u


def compute_url_hash(url):
    """SHA256 of normalized URL."""
    return hashlib.sha256(normalize_url(url).encode('utf-8')).hexdigest()


def normalize_material_text(text):
    """Normalize text for content comparison."""
    if not text:
        return ''
    t = text.strip()
    t = re.sub(r'\s+', ' ', t)
    return t.lower()


def compute_content_hash(text):
    """SHA256 of first 500 chars of normalized text."""
    return hashlib.sha256(normalize_material_text(text)[:500].encode('utf-8')).hexdigest()


# ════════════════════════════════════════════════════════════════
# Duplicate detection
# ════════════════════════════════════════════════════════════════

def detect_exact_duplicates(materials):
    """Find materials with identical URL hash or content hash.
    Returns (dedup_map, duplicates) where dedup_map maps duplicate_id -> canonical_id.
    """
    url_map = {}
    content_map = {}
    dedup_map = {}
    duplicates = []

    for m in materials:
        mid = m.get('id', '')
        url = m.get('source_url', '')
        text = m.get('raw_text', '')

        url_hash = compute_url_hash(url) if url else None
        content_hash = compute_content_hash(text) if text else None

        if url_hash and url_hash in url_map:
            canonical = url_map[url_hash]
            dedup_map[mid] = canonical
            duplicates.append({'id': mid, 'duplicate_of': canonical, 'reason': 'url_hash'})
            continue

        if content_hash and content_hash in content_map:
            canonical = content_map[content_hash]
            dedup_map[mid] = canonical
            duplicates.append({'id': mid, 'duplicate_of': canonical, 'reason': 'content_hash'})
            continue

        if url_hash:
            url_map[url_hash] = mid
        if content_hash:
            content_map[content_hash] = mid

    return dedup_map, duplicates


def check_duplicate_status(materials, dedup_map):
    """Check that duplicate materials have correct status and non-duplicates
    are not falsely marked as deduplicated.
    Returns list of error strings.
    """
    errors = []
    dup_ids = set(dedup_map.keys())
    all_ids = {m.get('id', '') for m in materials}
    mat_by_id = {m.get('id', ''): m for m in materials if m.get('id')}

    # Check every detected duplicate
    for m in materials:
        mid = m.get('id', '')
        status = m.get('status', '')

        if mid in dup_ids:
            # Rule 1: detected duplicate must have status == 'deduplicated'
            if status != 'deduplicated':
                errors.append(
                    f"ERROR: material '{mid}' is detected as exact duplicate "
                    f"but has status '{status}' (must be 'deduplicated')"
                )
                continue

            # Rule 3: deduplicated material must have duplicate_of
            dup_of = m.get('duplicate_of', '')
            if not dup_of:
                errors.append(
                    f"ERROR: material '{mid}' has status 'deduplicated' "
                    f"but no 'duplicate_of' field"
                )
                continue

            # duplicate_of must match dedup_map[mid]
            expected_canonical = dedup_map.get(mid)
            if dup_of != expected_canonical:
                errors.append(
                    f"ERROR: material '{mid}' duplicate_of='{dup_of}' "
                    f"does not match detected canonical '{expected_canonical}'"
                )
                continue

            # duplicate_of must be a real material
            if dup_of not in all_ids:
                errors.append(
                    f"ERROR: material '{mid}' duplicate_of='{dup_of}' "
                    f"does not refer to a real material"
                )
                continue

            # duplicate_of must not be another duplicate
            if dup_of in dup_ids:
                errors.append(
                    f"ERROR: material '{mid}' duplicate_of='{dup_of}' "
                    f"points to another duplicate, must point to canonical"
                )
                continue

            # duplicate_of must not be self-reference
            if dup_of == mid:
                errors.append(
                    f"ERROR: material '{mid}' duplicate_of points to itself"
                )
                continue

        else:
            # Rule 4: non-duplicate must NOT have status 'deduplicated'
            if status == 'deduplicated':
                errors.append(
                    f"ERROR: material '{mid}' has status 'deduplicated' "
                    f"but was not detected as a duplicate"
                )

    return errors


# ════════════════════════════════════════════════════════════════
# Event index
# ════════════════════════════════════════════════════════════════

def build_event_index(materials):
    """Build event index from materials with event_id.
    Returns dict: event_id -> {materials: [id, ...], sources: set(urls), has_conflict: bool}
    Sources are derived from the actual materials' source_url fields.
    """
    events = {}
    for m in materials:
        eid = m.get('event_id', '')
        if not eid:
            continue
        if eid not in events:
            events[eid] = {'materials': [], 'sources': set(), 'has_conflict': False}
        events[eid]['materials'].append(m['id'])
        if m.get('source_url'):
            events[eid]['sources'].add(m['source_url'])
        if m.get('status') == 'conflicting':
            events[eid]['has_conflict'] = True
    return events


def validate_event_assignments(materials, events):
    """Validate bidirectional consistency between materials and events.
    Checks:
      1. Event references valid material IDs
      2. Material.event_id points to existing event
      3. Event.materials contains material whose event_id matches
      4. Every material with event_id appears in that event's materials list
      5. Same material not in two events
      6. Event IDs not duplicated
      7. Material IDs not duplicated
      8. Event.materials has no duplicate IDs
      9. used/conflicting materials have event_id
      10. total_count matches actual count
    Returns list of error strings.
    """
    errors = []

    # Check duplicate material IDs
    seen_mat_ids = set()
    for m in materials:
        mid = m.get('id', '')
        if mid in seen_mat_ids:
            errors.append(f"ERROR: duplicate material id '{mid}'")
        seen_mat_ids.add(mid)

    mat_by_id = {m.get('id', ''): m for m in materials if m.get('id')}

    # Check each event's materials exist and have consistent event_id
    for eid, evt in events.items():
        evt_mats = evt.get('materials', [])
        # Check duplicate IDs in event.materials
        if len(evt_mats) != len(set(evt_mats)):
            errors.append(f"ERROR: event '{eid}' has duplicate material IDs in its materials list")

        for mid in evt_mats:
            if mid not in mat_by_id:
                errors.append(f"ERROR: event '{eid}' references unknown material '{mid}'")
                continue
            mat = mat_by_id[mid]
            mat_eid = mat.get('event_id', '')
            if mat_eid != eid:
                errors.append(
                    f"ERROR: material '{mid}' event_id='{mat_eid}' "
                    f"does not match event '{eid}' that lists it"
                )

    # Check each material with event_id:
    #   - event exists
    #   - material appears in event.materials
    mat_to_events = {}  # mid -> set of event_ids
    for m in materials:
        mid = m.get('id', '')
        eid = m.get('event_id', '')
        if not eid:
            # used/conflicting must have event_id
            if m.get('status') in ('used', 'conflicting'):
                errors.append(
                    f"ERROR: material '{mid}' has status '{m.get('status')}' "
                    f"but no event_id"
                )
            continue

        # Check event exists
        if eid not in events:
            errors.append(f"ERROR: material '{mid}' references unknown event '{eid}'")
            continue

        # Check material appears in event.materials (reverse direction)
        if mid not in events[eid].get('materials', []):
            errors.append(
                f"ERROR: material '{mid}' has event_id='{eid}' "
                f"but does not appear in event '{eid}'.materials"
            )

        # Track which events each material belongs to
        if mid not in mat_to_events:
            mat_to_events[mid] = set()
        mat_to_events[mid].add(eid)

    # Check no material in two events
    for mid, eids in mat_to_events.items():
        if len(eids) > 1:
            errors.append(
                f"ERROR: material '{mid}' appears in multiple events: {', '.join(sorted(eids))}"
            )

    # Check conflicting status matches has_conflict
    for m in materials:
        if m.get('status') == 'conflicting':
            eid = m.get('event_id', '')
            if eid in events and not events[eid]['has_conflict']:
                errors.append(
                    f"ERROR: material '{m['id']}' is 'conflicting' but "
                    f"event '{eid}' has has_conflict=False"
                )

    # Check has_conflict=true requires at least 2 conflicting materials
    for eid, evt in events.items():
        if evt['has_conflict']:
            conflicting_mats = [
                mid for mid in evt['materials']
                if mid in mat_by_id and mat_by_id[mid].get('status') == 'conflicting'
            ]
            if len(conflicting_mats) < 2:
                errors.append(
                    f"ERROR: event '{eid}' has has_conflict=True "
                    f"but has fewer than 2 conflicting materials ({len(conflicting_mats)})"
                )

    # Check excluded materials have valid reason
    for m in materials:
        if m.get('status') == 'excluded':
            reason = m.get('excluded_reason', '')
            if not reason:
                errors.append(f"ERROR: material '{m.get('id', '')}' is 'excluded' but has no excluded_reason")
            elif reason not in ALLOWED_EXCLUDE_REASONS:
                errors.append(
                    f"ERROR: material '{m.get('id', '')}' has invalid excluded_reason '{reason}'. "
                    f"Allowed: {', '.join(sorted(ALLOWED_EXCLUDE_REASONS))}"
                )

    return errors


def validate_ledger_structure(ledger):
    """Validate ledger structure: total_count, IDs, event IDs not duplicated."""
    errors = []
    ml = ledger.get('material_ledger', {})

    materials = ml.get('materials', [])
    events = ml.get('events', [])
    claims = ml.get('claims', [])

    # Check total_count
    total_count = ml.get('total_count', -1)
    if total_count != len(materials):
        errors.append(
            f"ERROR: material_ledger.total_count={total_count} "
            f"does not match actual materials count {len(materials)}"
        )

    # Check duplicate event IDs in events list
    if isinstance(events, list):
        seen_event_ids = set()
        for e in events:
            if not isinstance(e, dict):
                continue
            eid = e.get('id', '')
            if eid in seen_event_ids:
                errors.append(f"ERROR: duplicate event id '{eid}'")
            seen_event_ids.add(eid)

    return errors


# ════════════════════════════════════════════════════════════════
# Coverage
# ════════════════════════════════════════════════════════════════

def compute_source_coverage(materials):
    """Compute source coverage: used materials / total materials.
    deduplicated and excluded do NOT count as used.
    """
    if not materials:
        return 0.0
    total = len(materials)
    used = sum(1 for m in materials if m.get('status') == 'used')
    return used / total if total > 0 else 0.0


def compute_event_coverage(materials, events):
    """Compute event coverage: covered events / total events.
    An event is covered if at least one of its materials has status 'used' or 'conflicting'.
    """
    if not events:
        return 0.0
    total = len(events)
    active_ids = {m['id'] for m in materials if m.get('status') in ('used', 'conflicting')}
    covered = 0
    for eid, evt in events.items():
        if any(mid in active_ids for mid in evt.get('materials', [])):
            covered += 1
    return covered / total if total > 0 else 0.0


def compute_claim_coverage(materials, events, claims):
    """Compute claim coverage: covered claims / total claims.
    A claim is covered only if at least one supporting event has
    at least one used/conflicting material.
    """
    if not claims:
        return 0.0
    total = len(claims)
    active_ids = {m['id'] for m in materials if m.get('status') in ('used', 'conflicting')}
    covered_events = set()
    for eid, evt in events.items():
        if any(mid in active_ids for mid in evt.get('materials', [])):
            covered_events.add(eid)

    covered = 0
    for c in claims:
        sup_events = c.get('supporting_events', [])
        if any(eid in covered_events for eid in sup_events):
            covered += 1
    return covered / total if total > 0 else 0.0


# ════════════════════════════════════════════════════════════════
# Mode resolution
# ════════════════════════════════════════════════════════════════

def resolve_article_mode(material_count, user_mode=None):
    """Resolve article_mode based on material count and user preference.
    Returns (mode, errors, needs_selection).
    """
    errors = []

    if user_mode is not None:
        if not isinstance(user_mode, str) or not user_mode.strip():
            errors.append("ERROR: user_mode is empty")
            return None, errors, False
        if user_mode not in ALLOWED_MODES:
            errors.append(
                f"ERROR: unknown article_mode '{user_mode}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_MODES))}"
            )
            return None, errors, False
        return user_mode, errors, False

    if material_count > 100:
        return None, errors, True  # needs_mode_selection

    if material_count >= 50:
        return 'long', errors, False

    return 'medium', errors, False


# ════════════════════════════════════════════════════════════════
# Ingestion report
# ════════════════════════════════════════════════════════════════

def generate_ingestion_report(ledger):
    """Generate material-ingestion-report from ledger.
    Returns (report_dict, errors).
    If errors is non-empty, report is for diagnostic purposes only.
    """
    errors = []
    ml = ledger.get('material_ledger', {})
    materials = ml.get('materials', [])
    events_list = ml.get('events', [])
    claims = ml.get('claims', [])

    if not isinstance(materials, list):
        errors.append("ERROR: material_ledger.materials must be a list")
        return None, errors

    # Validate materials
    for i, m in enumerate(materials):
        if not isinstance(m, dict):
            errors.append(f"ERROR: material {i} is not a dict")
            continue
        if not m.get('id'):
            errors.append(f"ERROR: material {i} has no id")
        if m.get('status') and m['status'] not in ALLOWED_STATUSES:
            errors.append(
                f"ERROR: material '{m.get('id', i)}' has invalid status '{m['status']}'"
            )

    # Validate ledger structure
    struct_errors = validate_ledger_structure(ledger)
    errors.extend(struct_errors)

    # Build event index from materials (canonical source of truth)
    event_index = build_event_index(materials)

    # If events list is provided, use it as the canonical event definitions
    # but merge with material-derived index for validation
    if isinstance(events_list, list):
        declared_events = {}
        for e in events_list:
            if not isinstance(e, dict):
                continue
            eid = e.get('id', '')
            if eid:
                declared_events[eid] = {
                    'materials': e.get('materials', []),
                    'sources': set(),
                    'has_conflict': e.get('has_conflict', False),
                }
                # Populate sources from the materials listed in this event
                for mid in declared_events[eid]['materials']:
                    mat = next((m for m in materials if m.get('id') == mid), None)
                    if mat and mat.get('source_url'):
                        declared_events[eid]['sources'].add(mat['source_url'])
        # Use declared events as the canonical index for validation
        events_for_validation = declared_events
    else:
        events_for_validation = event_index

    # Validate event assignments
    assign_errors = validate_event_assignments(materials, events_for_validation)
    errors.extend(assign_errors)

    # Detect duplicates
    dedup_map, duplicates = detect_exact_duplicates(materials)

    # Check duplicate status consistency
    dup_errors = check_duplicate_status(materials, dedup_map)
    errors.extend(dup_errors)

    # Compute coverage (must be recalculated, not from hand-filled values)
    source_cov = compute_source_coverage(materials)
    event_cov = compute_event_coverage(materials, events_for_validation)
    claim_cov = compute_claim_coverage(materials, events_for_validation, claims)

    # Find uncovered events
    active_ids = {m['id'] for m in materials if m.get('status') in ('used', 'conflicting')}
    uncovered_events = [
        {'event_id': eid, 'reason': 'no used or conflicting materials'}
        for eid, evt in events_for_validation.items()
        if not any(mid in active_ids for mid in evt.get('materials', []))
    ]

    # Find uncovered claims
    covered_event_ids = set()
    for eid, evt in events_for_validation.items():
        if any(mid in active_ids for mid in evt.get('materials', [])):
            covered_event_ids.add(eid)

    uncovered_claims = []
    if isinstance(claims, list):
        for c in claims:
            if not isinstance(c, dict):
                continue
            sup_events = c.get('supporting_events', [])
            if not any(eid in covered_event_ids for eid in sup_events):
                covered_sup = [eid for eid in sup_events if eid in covered_event_ids]
                uncovered_claims.append({
                    'claim_id': c.get('id', ''),
                    'statement': c.get('statement', ''),
                    'reason': 'no supporting event has used/conflicting materials',
                    'supporting_events': sup_events,
                    'covered_events': covered_sup,
                })

    excluded_materials = [
        {'id': m.get('id', ''), 'reason': m.get('excluded_reason', '')}
        for m in materials if m.get('status') == 'excluded'
    ]

    # Conflicts with full data
    conflicts = []
    for eid, evt in events_for_validation.items():
        if evt['has_conflict']:
            conflicting_mats = [
                mid for mid in evt.get('materials', [])
                if mid in {m['id'] for m in materials if m.get('status') == 'conflicting'}
            ]
            conflicts.append({
                'event_id': eid,
                'materials': conflicting_mats,
                'sources': sorted(evt['sources']),
                'resolution_status': 'unresolved',
            })

    report = {
        'total_materials': len(materials),
        'total_events': len(events_for_validation),
        'total_claims': len(claims) if isinstance(claims, list) else 0,
        'source_coverage': round(source_cov, 4),
        'event_coverage': round(event_cov, 4),
        'claim_coverage': round(claim_cov, 4),
        'duplicates_removed': len(duplicates),
        'conflicts_detected': len(conflicts),
        'excluded_materials': excluded_materials,
        'uncovered_events': uncovered_events,
        'uncovered_claims': uncovered_claims,
        'conflicts': conflicts,
        'duplicates': duplicates,
    }

    return report, errors


# ════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════

def load_yaml_safe(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return None, [f"ERROR: YAML parse error in {path}: {e}"]
    except Exception as e:
        return None, [f"ERROR: Cannot read {path}: {e}"]
    if data is None:
        return None, [f"ERROR: YAML file is empty: {path}"]
    if not isinstance(data, dict):
        return None, [f"ERROR: YAML top-level must be dict, got {type(data).__name__}"]
    return data, []


def main():
    parser = argparse.ArgumentParser(description='Material ingestion: validate ledger and generate report')
    parser.add_argument('--ledger', required=True, help='Path to material-ledger.yaml')
    parser.add_argument('--output', required=True, help='Path to output material-ingestion-report.json')
    parser.add_argument('--diagnostic-output', default=None,
                        help='Save diagnostic report even when errors exist')
    parser.add_argument('--json', action='store_true', help='Print report to stdout as JSON')
    args = parser.parse_args()

    ledger, load_errors = load_yaml_safe(args.ledger)
    if load_errors:
        for e in load_errors:
            print(e, file=sys.stderr)
        sys.exit(1)

    report, errors = generate_ingestion_report(ledger)

    if errors:
        for e in errors:
            print(e, file=sys.stderr)

        if report is not None and args.diagnostic_output:
            # Save diagnostic report
            output = json.dumps(report, ensure_ascii=False, indent=2)
            with open(args.diagnostic_output, 'w', encoding='utf-8', newline='\n') as f:
                f.write(output)
            print(f"Diagnostic report saved to {args.diagnostic_output}", file=sys.stderr)

        if report is None:
            sys.exit(1)

        # Has report but also has errors → do NOT write success report
        print(f"FAILED: {len(errors)} validation errors found", file=sys.stderr)
        sys.exit(1)

    # No errors → write report
    output = json.dumps(report, ensure_ascii=False, indent=2)
    with open(args.output, 'w', encoding='utf-8', newline='\n') as f:
        f.write(output)

    if args.json:
        print(output)

    print(f"OK: ingestion report written to {args.output}")
    print(f"  source_coverage: {report['source_coverage']:.2%}")
    print(f"  event_coverage: {report['event_coverage']:.2%}")
    print(f"  claim_coverage: {report['claim_coverage']:.2%}")
    print(f"  duplicates: {report['duplicates_removed']}")
    print(f"  conflicts: {report['conflicts_detected']}")

    sys.exit(0)


if __name__ == '__main__':
    main()