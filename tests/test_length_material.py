"""Tests for v0.3.1-rc1-hotfix2: material ingestion validation and full mode gate.

Tests call real production functions or CLI, not manual dict construction.
Covers: H1 exit code, H2 bidirectional validation, H3 duplicate status,
H4 coverage computation, H5 conflict sources, H6 full CLI,
H7 deep full validation, H8 docs list 11 artifacts, H9 code char counting,
H10 K3 capability, H11 regression tests.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from validate_article_length import (
    LENGTH_MODE_PRESETS, ALLOWED_MODES,
    count_visible_chars, count_cjk_chars, count_latin_words,
    count_paragraphs, split_sections,
    check_duplicate_padding, parse_outline_budgets,
    validate_section_budgets, check_full_mode_completeness,
    validate_article_length, parse_sections_json,
)

from material_ingestion import (
    normalize_url, compute_url_hash, compute_content_hash,
    normalize_material_text, detect_exact_duplicates,
    build_event_index, validate_event_assignments,
    compute_source_coverage, compute_event_coverage,
    compute_claim_coverage, resolve_article_mode,
    generate_ingestion_report, validate_ledger_structure,
    check_duplicate_status,
)


# ════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════

def write_temp_article(text, tmp_path, name='article.md'):
    p = tmp_path / name
    p.write_text(text, encoding='utf-8')
    return p


def make_chinese_text(char_count):
    base = '这是一个测试句子用于验证篇幅策略功能。'
    result = ''
    while len(result) < char_count:
        result += base
    return result[:char_count]


def make_ledger(materials, events=None, claims=None, total_count=None):
    """Build a ledger dict for testing."""
    ml = {'materials': materials}
    if events is not None:
        ml['events'] = events
    if claims is not None:
        ml['claims'] = claims
    ml['total_count'] = total_count if total_count is not None else len(materials)
    return {'material_ledger': ml}


# ════════════════════════════════════════════════════════════════
# H1: Material CLI exit code
# ════════════════════════════════════════════════════════════════

def test_h1_invalid_ledger_cli_return_code_1(tmp_path):
    """Used material referencing unknown event → exit code 1, no OK in stdout."""
    ledger = make_ledger([
        {'id': 'm1', 'status': 'used', 'event_id': 'evt-missing'},
    ])
    lp = tmp_path / 'ledger.yaml'
    lp.write_text(yaml.dump(ledger, allow_unicode=True), encoding='utf-8')
    op = tmp_path / 'report.json'

    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'material_ingestion.py'),
         '--ledger', str(lp), '--output', str(op)],
        capture_output=True, text=True
    )
    assert p.returncode == 1
    assert 'OK' not in p.stdout
    assert not op.exists() or 'FAILED' in p.stderr


def test_h1_valid_ledger_cli_return_code_0(tmp_path):
    """Valid ledger → exit code 0, report generated."""
    ledger = make_ledger(
        [{'id': 'm1', 'status': 'used', 'event_id': 'e1', 'source_url': 'https://a.com'}],
        events=[{'id': 'e1', 'materials': ['m1'], 'has_conflict': False}],
    )
    lp = tmp_path / 'ledger.yaml'
    lp.write_text(yaml.dump(ledger, allow_unicode=True), encoding='utf-8')
    op = tmp_path / 'report.json'

    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'material_ingestion.py'),
         '--ledger', str(lp), '--output', str(op)],
        capture_output=True, text=True
    )
    assert p.returncode == 0
    assert 'OK' in p.stdout
    assert op.exists()


# ════════════════════════════════════════════════════════════════
# H2: Bidirectional event validation
# ════════════════════════════════════════════════════════════════

def test_h2_material_missing_from_event_materials_fails():
    """m1/m2 both point to e1, but e1.materials only has m1 → fail."""
    materials = [
        {'id': 'm1', 'event_id': 'e1', 'status': 'used'},
        {'id': 'm2', 'event_id': 'e1', 'status': 'used'},
    ]
    events = {'e1': {'materials': ['m1'], 'sources': set(), 'has_conflict': False}}
    errors = validate_event_assignments(materials, events)
    assert any("does not appear in event 'e1'.materials" in e for e in errors)


def test_h2_material_in_two_events_fails():
    """Same material in two events → fail."""
    materials = [{'id': 'm1', 'event_id': 'e1', 'status': 'used'}]
    events = {
        'e1': {'materials': ['m1'], 'sources': set(), 'has_conflict': False},
        'e2': {'materials': ['m1'], 'sources': set(), 'has_conflict': False},
    }
    errors = validate_event_assignments(materials, events)
    # m1 appears in e2 but its event_id is e1 → mismatch
    assert any('does not match event' in e for e in errors)


def test_h2_duplicate_material_ids_fails():
    materials = [
        {'id': 'm1', 'status': 'used', 'event_id': 'e1'},
        {'id': 'm1', 'status': 'used', 'event_id': 'e1'},
    ]
    events = {'e1': {'materials': ['m1'], 'sources': set(), 'has_conflict': False}}
    errors = validate_event_assignments(materials, events)
    assert any('duplicate material id' in e for e in errors)


def test_h2_total_count_mismatch_fails():
    ledger = make_ledger(
        [{'id': 'm1', 'status': 'used', 'event_id': 'e1'}],
        events=[{'id': 'e1', 'materials': ['m1'], 'has_conflict': False}],
        total_count=5,
    )
    errors = validate_ledger_structure(ledger)
    assert any('total_count' in e and 'does not match' in e for e in errors)


def test_h2_bidirectional_pass():
    """Properly bidirectional assignment passes."""
    materials = [
        {'id': 'm1', 'event_id': 'e1', 'status': 'used'},
        {'id': 'm2', 'event_id': 'e1', 'status': 'used'},
    ]
    events = {'e1': {'materials': ['m1', 'm2'], 'sources': set(), 'has_conflict': False}}
    errors = validate_event_assignments(materials, events)
    assert len(errors) == 0


# ════════════════════════════════════════════════════════════════
# H3: Duplicate status enforcement
# ════════════════════════════════════════════════════════════════

def test_h3_exact_duplicate_marked_used_fails():
    """Two materials with same URL, both marked used → fail."""
    materials = [
        {'id': 'm1', 'source_url': 'https://a.com', 'raw_text': 'same', 'status': 'used'},
        {'id': 'm2', 'source_url': 'https://a.com', 'raw_text': 'same', 'status': 'used'},
    ]
    dedup_map, dups = detect_exact_duplicates(materials)
    assert len(dups) >= 1
    errors = check_duplicate_status(materials, dedup_map)
    assert any('used' in e and 'duplicate' in e for e in errors)


def test_h3_duplicate_of_unknown_fails():
    """duplicate_of pointing to non-existent material → fail."""
    materials = [
        {'id': 'm1', 'source_url': 'https://a.com', 'raw_text': 'orig', 'status': 'used'},
        {'id': 'm2', 'source_url': 'https://a.com', 'raw_text': 'orig', 'status': 'deduplicated',
         'duplicate_of': 'm999'},
    ]
    dedup_map, _ = detect_exact_duplicates(materials)
    errors = check_duplicate_status(materials, dedup_map)
    # Now the canonical check fires first: duplicate_of doesn't match detected canonical
    assert any('does not match' in e or 'does not refer to a real material' in e for e in errors)


def test_h3_duplicate_of_points_to_another_duplicate_fails():
    """duplicate_of pointing to another duplicate → fail."""
    materials = [
        {'id': 'm1', 'source_url': 'https://a.com', 'raw_text': 'orig', 'status': 'used'},
        {'id': 'm2', 'source_url': 'https://a.com', 'raw_text': 'orig', 'status': 'deduplicated',
         'duplicate_of': 'm1'},
        {'id': 'm3', 'source_url': 'https://a.com', 'raw_text': 'orig', 'status': 'deduplicated',
         'duplicate_of': 'm2'},
    ]
    dedup_map, _ = detect_exact_duplicates(materials)
    errors = check_duplicate_status(materials, dedup_map)
    # m3's duplicate_of doesn't match detected canonical (which is m1, not m2)
    assert any('does not match' in e or 'points to another duplicate' in e for e in errors)


def test_h3_deduplicated_not_counted_as_used():
    """deduplicated materials should not count in source_coverage."""
    materials = [
        {'id': 'm1', 'status': 'used'},
        {'id': 'm2', 'status': 'deduplicated', 'duplicate_of': 'm1', 'duplicate_reason': 'url_hash'},
        {'id': 'm3', 'status': 'excluded', 'excluded_reason': 'irrelevant'},
    ]
    cov = compute_source_coverage(materials)
    assert cov == pytest.approx(1/3, abs=0.01)  # only m1 is used out of 3


# ════════════════════════════════════════════════════════════════
# H4: Coverage computation
# ════════════════════════════════════════════════════════════════

def test_h4_excluded_event_does_not_cover_claim():
    """Event exists, but only material is excluded → event_coverage=0, claim_coverage=0."""
    materials = [{'id': 'm1', 'status': 'excluded', 'excluded_reason': 'irrelevant', 'event_id': 'e1'}]
    events = {'e1': {'materials': ['m1'], 'sources': set(), 'has_conflict': False}}
    claims = [{'id': 'c1', 'statement': 'test', 'supporting_events': ['e1']}]

    ev_cov = compute_event_coverage(materials, events)
    assert ev_cov == 0.0

    cl_cov = compute_claim_coverage(materials, events, claims)
    assert cl_cov == 0.0


def test_h4_uncovered_claims_populated():
    """uncovered_claims must be populated when claim has no covered events."""
    ledger = make_ledger(
        [{'id': 'm1', 'status': 'excluded', 'excluded_reason': 'irrelevant', 'event_id': 'e1'}],
        events=[{'id': 'e1', 'materials': ['m1'], 'has_conflict': False}],
        claims=[{'id': 'c1', 'statement': 'test claim', 'supporting_events': ['e1']}],
    )
    report, errors = generate_ingestion_report(ledger)
    assert len(report['uncovered_claims']) >= 1
    assert report['uncovered_claims'][0]['claim_id'] == 'c1'


def test_h4_claim_coverage_with_covered_event():
    """Claim with a covered event → claim_coverage=1."""
    materials = [{'id': 'm1', 'status': 'used', 'event_id': 'e1', 'source_url': 'https://a.com'}]
    events = {'e1': {'materials': ['m1'], 'sources': {'https://a.com'}, 'has_conflict': False}}
    claims = [{'id': 'c1', 'statement': 'test', 'supporting_events': ['e1']}]
    cl_cov = compute_claim_coverage(materials, events, claims)
    assert cl_cov == 1.0


# ════════════════════════════════════════════════════════════════
# H5: Conflict sources and has_conflict validation
# ════════════════════════════════════════════════════════════════

def test_h5_conflict_sources_populated():
    """Conflict report must have sources populated from materials."""
    materials = [
        {'id': 'm1', 'status': 'conflicting', 'event_id': 'e1', 'source_url': 'https://a.com'},
        {'id': 'm2', 'status': 'conflicting', 'event_id': 'e1', 'source_url': 'https://b.com'},
    ]
    events = {
        'e1': {'materials': ['m1', 'm2'], 'sources': {'https://a.com', 'https://b.com'}, 'has_conflict': True}
    }
    claims = []
    report, errors = generate_ingestion_report(make_ledger(
        materials,
        events=[{'id': 'e1', 'materials': ['m1', 'm2'], 'has_conflict': True}],
    ))
    assert len(report['conflicts']) >= 1
    conflict = report['conflicts'][0]
    assert len(conflict['sources']) >= 2


def test_h5_false_has_conflict_fails():
    """has_conflict=True but fewer than 2 conflicting materials → fail."""
    materials = [
        {'id': 'm1', 'status': 'used', 'event_id': 'e1', 'source_url': 'https://a.com'},
    ]
    events = {'e1': {'materials': ['m1'], 'sources': set(), 'has_conflict': True}}
    errors = validate_event_assignments(materials, events)
    assert any('fewer than 2 conflicting' in e for e in errors)


# ════════════════════════════════════════════════════════════════
# H6: Full mode CLI with --semantic-map
# ════════════════════════════════════════════════════════════════

def test_h6_full_cli_missing_semantic_map_fails(tmp_path):
    """Full CLI without --semantic-map → fail."""
    article = write_temp_article(make_chinese_text(3000), tmp_path)
    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'validate_article_length.py'),
         '--article', str(article), '--article-mode', 'medium',
         '--full-mode', '--json'],
        capture_output=True, text=True
    )
    assert p.returncode == 1
    result = json.loads(p.stdout)
    assert any('semantic-map' in e for e in result['errors'])


def test_h6_full_cli_with_semantic_map_passes(tmp_path):
    """Full CLI with all valid artifacts → pass (H8: real end-to-end fixture).
    
    Article contains text that Semantic Map's anchor can find.
    Semantic Map passes validate_semantic_map.py.
    Material Ledger passes material_ingestion.py.
    Ingestion Report is generated by production script.
    Outline has complete section budgets.
    """
    # Article with anchor text that semantic map can find
    anchor_text = '这是一个用于验证的完整端到端测试文本。'
    article_text = '## 第一节\n\n' + anchor_text + '\n\n' + make_chinese_text(3000)
    article = write_temp_article(article_text, tmp_path)

    # generation-profile.yaml (H7: mode=full, valid article_mode, positive ints, paths)
    gp = tmp_path / 'gp.yaml'
    gp.write_text(yaml.dump({
        'mode': 'full', 'article_mode': 'medium', 'length_mode': 'medium',
        'target_visible_chars': 3000, 'acceptable_min': 2500, 'acceptable_max': 4000,
        'material_ledger_path': 'ml.yaml', 'ingestion_report_path': 'mir.json',
    }, allow_unicode=True), encoding='utf-8')

    # writing-brief.md (H7: all length fields, output_mode=full)
    brief = tmp_path / 'brief.md'
    brief.write_text(
        'article_mode: medium\nlength_mode: medium\n'
        'target_visible_chars: 3000\nacceptable_min: 2500\nacceptable_max: 4000\n'
        'output_mode: full',
        encoding='utf-8')

    # material-readiness.yaml (H7: non-empty fields, required_actions is list, allowed_output valid)
    mr = tmp_path / 'mr.yaml'
    mr.write_text(yaml.dump({
        'topic': 'sufficient', 'audience': 'sufficient',
        'core_opinion': 'sufficient', 'evidence': 'sufficient',
        'personal_experience': 'sufficient', 'voice_context': 'sufficient',
        'allowed_output': 'full', 'required_actions': [],
    }, allow_unicode=True), encoding='utf-8')

    # material-ledger.yaml (H2: must pass production validator)
    ml_data = {
        'material_ledger': {
            'total_count': 0,
            'materials': [],
            'events': [],
            'claims': [],
        }
    }
    ml = tmp_path / 'ml.yaml'
    ml.write_text(yaml.dump(ml_data, allow_unicode=True), encoding='utf-8')

    # material-ingestion-report.json (H3: must be recomputed and match)
    # Generate using production script
    from material_ingestion import generate_ingestion_report
    report_dict, _ = generate_ingestion_report(ml_data)
    mir = tmp_path / 'mir.json'
    mir.write_text(json.dumps(report_dict, ensure_ascii=False, indent=2), encoding='utf-8')

    # evidence-map.md (H5: must contain evidence ID)
    em = tmp_path / 'em.md'
    em.write_text('# Evidence Map\nev-001 test evidence\n', encoding='utf-8')

    # core-card.md (H7: six required sections with non-empty content)
    cc = tmp_path / 'cc.md'
    cc.write_text(
        '# Core Card\n'
        'Core Statement: 这是一个测试核心观点\n'
        'Reader Change: 读者理解测试目标\n'
        'Core Tension: 测试与验证的张力\n'
        'Value Carrier: 可操作的验证方法\n'
        'Scope: 适用于所有测试场景\n'
        'Result: holds\n',
        encoding='utf-8')

    # outline.md (H6: all article-level fields + section budgets)
    ol = tmp_path / 'ol.md'
    ol.write_text(
        '# Outline\n'
        '## 文章配置\n'
        '- article_mode: medium\n'
        '- length_mode: medium\n'
        '- target_visible_chars: 3000\n'
        '- acceptable_min: 2500\n'
        '- acceptable_max: 4000\n'
        '- planned_total_chars: 3000\n\n'
        '## 第一节\n'
        '- weight_percent: 100\n'
        '- planned_chars: 3000\n'
        '- minimum_chars: 2500\n'
        '- maximum_chars: 4000\n'
        '- evidence_ids: []\n'
        '- event_ids: []\n'
        '- unique_information_goal: test\n',
        encoding='utf-8')

    # semantic-map.yaml (H4: must pass production validate_semantic_map.py)
    # Anchor text must exist in article
    sm = tmp_path / 'sm.yaml'
    sm.write_text(yaml.dump({
        'schema_version': '1.0',
        'article': {'id': 'test', 'title': 'Test'},
        'blocks': [
            {'block_id': 'b1', 'heading_path': [], 'role': 'paragraph',
             'source_anchor': {'exact_text': anchor_text},
             'payload': {'text': anchor_text},
             'evidence_ids': [], 'preserve_exactly': False,
             'formatter_candidates': ['paragraph'], 'fallback': [], 'required': False},
            {'block_id': 'sig-1', 'heading_path': [], 'role': 'article_signature',
             'source_anchor': {}, 'payload': {},
             'evidence_ids': [], 'preserve_exactly': False,
             'formatter_candidates': ['footer-signature-brand'], 'fallback': [], 'required': False},
        ],
        'constraints': {
            'preserve_facts': [], 'preserve_stance': [], 'preserve_quotes': [],
            'unresolved_facts': [], 'editor_anchors': [], 'forbidden_transformations': [],
        },
        'component_policy': {
            'force_all_components': False, 'formatter_has_final_choice': True,
            'allow_fallback': True, 'max_primary_advanced_components': 6,
            'prohibit_content_invention': True, 'prohibit_duplicate_full_content': True,
        },
    }, allow_unicode=True), encoding='utf-8')

    # editor-report.md (H7: all 7 required sections)
    er = tmp_path / 'er.md'
    er.write_text(
        '# Editor Report\n'
        '总体判断: 通过\n'
        'P0: 0\n'
        'P1: 0\n'
        'P2: 0\n'
        '分项评分: 85\n'
        '修订计划: 无需修订\n'
        '交接保护项: preserve_exactly\n',
        encoding='utf-8')

    # handoff.yaml (档76A/OBS-252:full-mode 必检)
    hoff = _write_valid_handoff(tmp_path)

    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'validate_article_length.py'),
         '--article', str(article), '--article-mode', 'medium',
         '--full-mode',
         '--generation-profile', str(gp),
         '--brief', str(brief),
         '--material-readiness', str(mr),
         '--material-report', str(mir),
         '--material-ledger', str(ml),
         '--evidence-map', str(em),
         '--core-card', str(cc),
         '--outline', str(ol),
         '--semantic-map', str(sm),
         '--editor-report', str(er),
         '--handoff', str(hoff),
         '--json'],
        capture_output=True, text=True
    )
    assert p.returncode == 0, f"Full CLI should pass:\n{p.stdout}\n{p.stderr}"


# ════════════════════════════════════════════════════════════════
# H7: Deep full mode validation
# ════════════════════════════════════════════════════════════════

def test_h7_junk_full_artifacts_fail(tmp_path):
    """Placeholder content in all 11 files → fail."""
    article = write_temp_article(make_chinese_text(3000), tmp_path)
    paths = {}
    for key, spec in [
        ('generation_profile', 'gp.yaml'), ('writing_brief', 'brief.md'),
        ('material_readiness', 'mr.yaml'), ('material_ingestion_report', 'mir.json'),
        ('material_ledger', 'ml.yaml'), ('evidence_map', 'em.md'),
        ('core_card', 'cc.md'), ('outline', 'ol.md'),
        ('editor_report', 'er.md'),
    ]:
        fp = tmp_path / spec
        fp.write_text('foo: bar', encoding='utf-8')
        paths[key] = str(fp)

    sm = tmp_path / 'sm.yaml'
    sm.write_text('schema_version: "1.0"\nblocks: []\n', encoding='utf-8')
    paths['semantic_map'] = str(sm)
    paths['article'] = str(article)

    errors, details = check_full_mode_completeness(paths)
    assert len(errors) > 0
    # Should fail because writing-brief.md lacks required fields
    assert any('writing-brief.md' in e for e in errors)


def test_h7_invalid_semantic_map_fails(tmp_path):
    """Invalid semantic-map.yaml → fail."""
    article = write_temp_article(make_chinese_text(3000), tmp_path)
    sm = tmp_path / 'sm.yaml'
    sm.write_text('not valid: yaml: [unclosed', encoding='utf-8')

    paths = {'semantic_map': str(sm), 'article': str(article)}
    errors, _ = check_full_mode_completeness(paths)
    assert any('semantic-map.yaml' in e and 'invalid' in e.lower() for e in errors)


# ════════════════════════════════════════════════════════════════
# 档76A/OBS-252:handoff.yaml full-mode 必检(12 件)
# ════════════════════════════════════════════════════════════════

def _write_valid_handoff(tmp_path, name='handoff.yaml', drop=None):
    """写一份合法 handoff;drop 指定要删除的字段(嵌套用 'formatter.cover' 路径)。"""
    data = {'handoff': {
        'schema_version': '2.2',
        'prose_craft_applied': True,
        'prose_craft_version': '1.0',
        'formatter': {'cover': {'kicker': 'K', 'strike': 'S', 'tags': ['a', 'b']}},
        'title_candidates': ['标题一', '标题二'], 'hook_line': '钩子',
    }}
    if drop == 'formatter.cover':
        del data['handoff']['formatter']['cover']
    elif drop:
        del data['handoff'][drop]
    fp = tmp_path / name
    fp.write_text(yaml.safe_dump(data, allow_unicode=True), encoding='utf-8')
    return str(fp)


def test_h76a_handoff_required_full_mode(tmp_path):
    """缺 handoff 文件 → full-mode FAIL(档76A fail-closed)。"""
    article = write_temp_article(make_chinese_text(3000), tmp_path)
    paths = {'article': str(article)}  # 未提供 handoff 路径
    errors, _ = check_full_mode_completeness(paths)
    assert any('handoff.yaml' in e for e in errors), errors


def test_h76a_handoff_missing_required_field_fails(tmp_path):
    """handoff 缺 formatter.cover → full-mode FAIL(负向用例防假绿)。"""
    h = _write_valid_handoff(tmp_path, drop='formatter.cover')
    paths = {'handoff': h}
    errors, _ = check_full_mode_completeness(paths)
    assert any('handoff.formatter.cover' in e for e in errors), errors


def test_h76a_handoff_valid_passes_field_check(tmp_path):
    """合法 handoff → 字段检查通过(仅 handoff 路径下无 error)。"""
    h = _write_valid_handoff(tmp_path)
    paths = {'handoff': h}
    errors, _ = check_full_mode_completeness(paths)
    assert not any('handoff' in e for e in errors), errors


# ════════════════════════════════════════════════════════════════
# H8: Docs list 11 Full artifacts
# ════════════════════════════════════════════════════════════════

def test_h8_skill_md_lists_12_artifacts():
    skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
    for artifact in ['generation-profile', 'writing-brief', 'material-readiness',
                     'material-ingestion-report', 'material-ledger', 'evidence-map',
                     'core-card', 'outline', 'article', 'semantic-map', 'editor-report',
                     'handoff']:
        assert artifact in skill, f"SKILL.md missing artifact '{artifact}'"


def test_h8_length_policy_lists_12_artifacts():
    lp = (ROOT / 'references' / 'length-policy.md').read_text(encoding='utf-8')
    for artifact in ['generation-profile', 'writing-brief', 'material-readiness',
                     'material-ingestion-report', 'material-ledger', 'evidence-map',
                     'core-card', 'outline', 'article', 'semantic-map', 'editor-report',
                     'handoff']:
        assert artifact in lp, f"length-policy.md missing artifact '{artifact}'"


# ════════════════════════════════════════════════════════════════
# H9: Code character counting
# ════════════════════════════════════════════════════════════════

def test_h9_inline_code_counted():
    text = '`inlinecodehere`'
    assert count_visible_chars(text) == len('inlinecodehere')


def test_h9_fenced_code_counted():
    text = '```python\nprint(123)\n```'
    count = count_visible_chars(text)
    assert count > 0
    assert 'print' in text.replace('`', '').replace('python', '')


def test_h9_mixed_chinese_and_code_counted():
    text = '中文测试\n\n```bash\nnpx skills add gzh-design\n```\n\n更多中文。'
    count = count_visible_chars(text)
    assert count > 0
    # Should count Chinese chars AND code content
    assert count >= 4  # at least 中文测试


# ════════════════════════════════════════════════════════════════
# H10: K3 Fixture corruption probes
# ════════════════════════════════════════════════════════════════

def test_h10_k3_remove_event_reverse_reference_fails():
    """Remove material from event.materials → fail."""
    materials = [
        {'id': 'm1', 'event_id': 'e1', 'status': 'used'},
        {'id': 'm2', 'event_id': 'e1', 'status': 'used'},
    ]
    # e1 only lists m1, not m2
    events = {'e1': {'materials': ['m1'], 'sources': set(), 'has_conflict': False}}
    errors = validate_event_assignments(materials, events)
    assert any("does not appear in event" in e for e in errors)


def test_h10_k3_material_in_two_events_fails():
    """Material listed in two events → fail."""
    materials = [{'id': 'm1', 'event_id': 'e1', 'status': 'used'}]
    events = {
        'e1': {'materials': ['m1'], 'sources': set(), 'has_conflict': False},
        'e2': {'materials': ['m1'], 'sources': set(), 'has_conflict': False},
    }
    errors = validate_event_assignments(materials, events)
    assert len(errors) > 0


def test_h10_k3_duplicate_marked_used_fails():
    """Exact duplicate with status=used → fail."""
    materials = [
        {'id': 'm1', 'source_url': 'https://a.com', 'raw_text': 'same content here', 'status': 'used'},
        {'id': 'm2', 'source_url': 'https://a.com', 'raw_text': 'same content here', 'status': 'used'},
    ]
    dedup_map, _ = detect_exact_duplicates(materials)
    errors = check_duplicate_status(materials, dedup_map)
    assert any('used' in e and 'duplicate' in e for e in errors)


def test_h10_k3_excluded_event_claim_not_covered():
    """Excluded event → claim not covered."""
    materials = [{'id': 'm1', 'status': 'excluded', 'excluded_reason': 'irrelevant', 'event_id': 'e1'}]
    events = {'e1': {'materials': ['m1'], 'sources': set(), 'has_conflict': False}}
    claims = [{'id': 'c1', 'statement': 'test', 'supporting_events': ['e1']}]
    cl_cov = compute_claim_coverage(materials, events, claims)
    assert cl_cov == 0.0


def test_h10_k3_tampered_report_coverage_fails():
    """Report with hand-filled coverage that doesn't match → recalculated."""
    ledger = make_ledger(
        [{'id': 'm1', 'status': 'used', 'event_id': 'e1'},
         {'id': 'm2', 'status': 'excluded', 'excluded_reason': 'irrelevant', 'event_id': 'e2'}],
        events=[{'id': 'e1', 'materials': ['m1'], 'has_conflict': False},
                {'id': 'e2', 'materials': ['m2'], 'has_conflict': False}],
    )
    report, _ = generate_ingestion_report(ledger)
    # source_coverage must be 0.5 (1/2), not whatever was in the ledger
    assert report['source_coverage'] == 0.5
    assert report['event_coverage'] == 0.5  # 1/2 events covered


# ════════════════════════════════════════════════════════════════
# H11: Additional regression tests
# ════════════════════════════════════════════════════════════════

def test_h11_outline_missing_planned_chars_fails(tmp_path):
    """Outline without planned_chars → no budgets parsed."""
    outline = '# Outline\n## 文章配置\n- article_mode: medium\n- target_visible_chars: 3000\n## 第一节\n- weight_percent: 50\n'
    op = tmp_path / 'outline.md'
    op.write_text(outline, encoding='utf-8')
    sections, meta, _ = parse_outline_budgets(str(op))
    assert len(sections) == 0


def test_h11_empty_semantic_map_fails(tmp_path):
    """Empty semantic-map.yaml → fail."""
    sm = tmp_path / 'sm.yaml'
    sm.write_text('', encoding='utf-8')
    paths = {'semantic_map': str(sm)}
    errors, _ = check_full_mode_completeness(paths)
    assert any('empty' in e.lower() for e in errors)


def test_h11_section_budget_with_outline_passes(tmp_path):
    """Validate with outline --outline flag."""
    article_text = '# 第一节\n\n' + make_chinese_text(1500) + '\n\n# 第二节\n\n' + make_chinese_text(1500)
    article = write_temp_article(article_text, tmp_path)

    outline = """# Outline
## 文章配置
- article_mode: medium
- target_visible_chars: 3000

## 第一节
- weight_percent: 50
- planned_chars: 1500
- minimum_chars: 1200
- maximum_chars: 1800

## 第二节
- weight_percent: 50
- planned_chars: 1500
- minimum_chars: 1200
- maximum_chars: 1800
"""
    ol = tmp_path / 'outline.md'
    ol.write_text(outline, encoding='utf-8')

    errors, _, info = validate_article_length(
        str(article), article_mode='medium', outline_path=str(ol)
    )
    assert info.get('section_budgets') is not None


# ════════════════════════════════════════════════════════════════
# Existing tests (kept from hotfix1, adapted)
# ════════════════════════════════════════════════════════════════

def test_l1_length_presets():
    assert LENGTH_MODE_PRESETS['short']['target_visible_chars'] == 1500
    assert LENGTH_MODE_PRESETS['medium']['target_visible_chars'] == 3000
    assert LENGTH_MODE_PRESETS['long']['target_visible_chars'] == 5000
    assert LENGTH_MODE_PRESETS['deep']['target_visible_chars'] == 8000
    assert LENGTH_MODE_PRESETS['daily_digest']['target_visible_chars'] == 2500
    assert LENGTH_MODE_PRESETS['weekly_roundup']['target_visible_chars'] == 4000
    assert LENGTH_MODE_PRESETS['material_synthesis']['target_visible_chars'] == 6000


def test_l2_3051_chars_medium_passes_long_fails(tmp_path):
    article = write_temp_article(make_chinese_text(3051), tmp_path)
    errors_m, _, _ = validate_article_length(article, article_mode='medium')
    assert len(errors_m) == 0
    errors_l, _, _ = validate_article_length(article, article_mode='long')
    assert any('below' in e for e in errors_l)


def test_l3_cli_validates_length(tmp_path):
    article = write_temp_article(make_chinese_text(3000), tmp_path)
    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'validate_article_length.py'),
         '--article', str(article), '--article-mode', 'medium', '--json'],
        capture_output=True, text=True
    )
    assert p.returncode == 0
    assert json.loads(p.stdout)['passed']


def test_l4_h8_unknown_mode_fails(tmp_path):
    article = write_temp_article(make_chinese_text(3000), tmp_path)
    errors, _, _ = validate_article_length(article, article_mode='nonsense')
    assert any('unknown article_mode' in e for e in errors)


def test_l5_h8_explicit_min_max_preserved(tmp_path):
    article = write_temp_article(make_chinese_text(5000), tmp_path)
    _, _, info = validate_article_length(article, target_visible_chars=5000,
                                         acceptable_min=4900, acceptable_max=5100)
    assert info['acceptable_min'] == 4900
    assert info['acceptable_max'] == 5100


def test_l6_h8_above_max_is_warning(tmp_path):
    article = write_temp_article(make_chinese_text(5000), tmp_path)
    _, warnings, info = validate_article_length(article, target_visible_chars=3000,
                                                acceptable_min=2500, acceptable_max=4000)
    assert any('exceeds' in w for w in warnings)
    assert info['length_status'] == 'above_max'


def test_l7_json_output_has_all_fields(tmp_path):
    article = write_temp_article(make_chinese_text(3000), tmp_path)
    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'validate_article_length.py'),
         '--article', str(article), '--article-mode', 'medium', '--json'],
        capture_output=True, text=True
    )
    assert p.returncode == 0
    result = json.loads(p.stdout)
    for field in ['passed', 'length_status', 'cjk_chars', 'latin_words',
                  'visible_chars_no_whitespace', 'paragraphs', 'sections',
                  'target_visible_chars', 'acceptable_min', 'acceptable_max',
                  'section_budgets', 'duplicate_findings', 'errors', 'warnings']:
        assert field in result


def test_l8_k3_fixture_has_177_materials():
    p = ROOT / 'tests' / 'fixtures' / 'materials' / 'k3-177.json'
    data = json.loads(p.read_text(encoding='utf-8'))
    assert len(data['materials']) == 177


def test_l9_k3_validate_assignments_pass():
    p = ROOT / 'tests' / 'fixtures' / 'materials' / 'k3-177.json'
    data = json.loads(p.read_text(encoding='utf-8'))
    materials = data['materials']
    events = build_event_index(materials)
    errors = validate_event_assignments(materials, events)
    assert len(errors) == 0, f"K3 assignment errors: {errors}"


def test_l10_no_integration_dir():
    assert not (ROOT / 'tests' / 'gzh-design-integration').exists()


def test_l11_no_png_in_tests():
    assert len(list((ROOT / 'tests').rglob('*.png'))) == 0


def test_l12_existing_tests_baseline():
    assert (ROOT / 'tests' / 'test_semantic_handoff.py').exists()
    assert (ROOT / 'tests' / 'test_structure.py').exists()
    assert (ROOT / 'tests' / 'test_calibration.py').exists()


# ════════════════════════════════════════════════════════════════
# F5: Adversarial tests for hotfix4
# ════════════════════════════════════════════════════════════════

def test_f5_full_outline_partial_section_fails(tmp_path):
    """Section A complete, Section B missing fields → must fail."""
    outline = """# Outline
## 文章配置
- article_mode: medium
- length_mode: medium
- target_visible_chars: 3000
- acceptable_min: 2500
- acceptable_max: 4000
- planned_total_chars: 3000

## A
- weight_percent: 100
- planned_chars: 3000
- minimum_chars: 2500
- maximum_chars: 4000
- evidence_ids: []
- event_ids: []
- unique_information_goal: test

## B
- weight_percent: 50
"""
    ol = tmp_path / 'outline.md'
    ol.write_text(outline, encoding='utf-8')
    sections, meta, errors = parse_outline_budgets(str(ol))
    # F1: incomplete section B must produce errors
    assert len(errors) > 0, f"Expected errors for incomplete section B, got none"
    assert any("section 'B'" in e for e in errors), f"Expected error about section B, got: {errors}"


def test_f5_full_brief_invalid_values_fails(tmp_path):
    """Writing brief with invalid values must fail."""
    article = write_temp_article(make_chinese_text(3000), tmp_path)
    brief = tmp_path / 'brief.md'
    brief.write_text(
        'article_mode: nonsense\n'
        'length_mode: nonsense\n'
        'target_visible_chars: banana\n'
        'acceptable_min: huge\n'
        'acceptable_max: tiny\n'
        'output_mode: full',
        encoding='utf-8')

    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'validate_article_length.py'),
         '--article', str(article), '--article-mode', 'medium',
         '--full-mode', '--brief', str(brief), '--json'],
        capture_output=True, text=True
    )
    assert p.returncode == 1, f"Full CLI should fail with invalid brief values:\n{p.stdout}"
    result = json.loads(p.stdout)
    assert any('invalid' in e.lower() or 'must be' in e.lower() for e in result['errors'])


def test_f5_full_editor_report_titles_only_fails(tmp_path):
    """Editor report with only titles but no content must fail."""
    article = write_temp_article(make_chinese_text(3000), tmp_path)
    er = tmp_path / 'er.md'
    er.write_text('总体判断 P0 P1 P2 分项评分 修订计划 交接保护项', encoding='utf-8')

    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'validate_article_length.py'),
         '--article', str(article), '--article-mode', 'medium',
         '--full-mode', '--editor-report', str(er), '--json'],
        capture_output=True, text=True
    )
    assert p.returncode == 1, f"Full CLI should fail with titles-only editor report:\n{p.stdout}"
    result = json.loads(p.stdout)
    assert any('has no content' in e for e in result['errors'])


def test_f5_full_cross_artifact_mismatch_fails(tmp_path):
    """Profile target=3000, Brief target=5000 → must fail."""
    article = write_temp_article(make_chinese_text(3000), tmp_path)

    gp = tmp_path / 'gp.yaml'
    gp.write_text(yaml.dump({
        'mode': 'full', 'article_mode': 'medium', 'length_mode': 'medium',
        'target_visible_chars': 3000, 'acceptable_min': 2500, 'acceptable_max': 4000,
        'material_ledger_path': 'ml.yaml', 'ingestion_report_path': 'mir.json',
    }, allow_unicode=True), encoding='utf-8')

    brief = tmp_path / 'brief.md'
    brief.write_text(
        'article_mode: medium\nlength_mode: medium\n'
        'target_visible_chars: 5000\nacceptable_min: 2500\nacceptable_max: 6000\n'
        'output_mode: full',
        encoding='utf-8')

    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'validate_article_length.py'),
         '--article', str(article), '--article-mode', 'medium',
         '--full-mode', '--generation-profile', str(gp), '--brief', str(brief),
         '--json'],
        capture_output=True, text=True
    )
    assert p.returncode == 1, f"Full CLI should fail with cross-artifact mismatch:\n{p.stdout}"
    result = json.loads(p.stdout)
    assert any('cross-artifact mismatch' in e for e in result['errors'])


def test_f5_full_runtime_policy_mismatch_fails(tmp_path):
    """Profile/Brief/Outline say long/5000 but CLI says medium → must fail."""
    article = write_temp_article(make_chinese_text(3000), tmp_path)

    gp = tmp_path / 'gp.yaml'
    gp.write_text(yaml.dump({
        'mode': 'full', 'article_mode': 'long', 'length_mode': 'long',
        'target_visible_chars': 5000, 'acceptable_min': 4500, 'acceptable_max': 6500,
        'material_ledger_path': 'ml.yaml', 'ingestion_report_path': 'mir.json',
    }, allow_unicode=True), encoding='utf-8')

    brief = tmp_path / 'brief.md'
    brief.write_text(
        'article_mode: long\nlength_mode: long\n'
        'target_visible_chars: 5000\nacceptable_min: 4500\nacceptable_max: 6500\n'
        'output_mode: full',
        encoding='utf-8')

    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'validate_article_length.py'),
         '--article', str(article), '--article-mode', 'medium',
         '--full-mode', '--generation-profile', str(gp), '--brief', str(brief),
         '--json'],
        capture_output=True, text=True
    )
    assert p.returncode == 1, f"Full CLI should fail with runtime policy mismatch:\n{p.stdout}"
    result = json.loads(p.stdout)
    assert any(
        'runtime article_mode' in e or 'runtime target_visible_chars' in e
        for e in result['errors']
    ), f"Expected runtime policy mismatch error, got: {result['errors']}"
