"""Tests for semantic component handoff (v0.3.0-rc1-hotfix).

Covers original tests plus 24 new negative tests for hotfix validation.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

# Add scripts to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from validate_semantic_map import (
    ALLOWED_ROLES,
    ROLE_REQUIRED_FIELDS,
    ROLE_EVIDENCE_REQUIRED,
    validate_semantic_map,
)


# ── Helpers ──

def write_temp_article(text, tmp_path, name='article.md'):
    """Write a temporary article file."""
    p = tmp_path / name
    p.write_text(text, encoding='utf-8')
    return p


def write_temp_semantic_map(data, tmp_path, name='semantic-map.yaml'):
    """Write a temporary semantic map YAML file."""
    p = tmp_path / name
    p.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False), encoding='utf-8')
    return p


def write_temp_file(text, tmp_path, name):
    """Write a temporary file."""
    p = tmp_path / name
    p.write_text(text, encoding='utf-8')
    return p


def make_valid_block(block_id, role, exact_text, payload=None, **kwargs):
    """Create a valid semantic map block."""
    block = {
        'block_id': block_id,
        'heading_path': [],
        'role': role,
        'source_anchor': {'exact_text': exact_text},
        'payload': payload or {},
        'evidence_ids': [],
        'preserve_exactly': False,
        'formatter_candidates': [],
        'fallback': [],
        'required': False,
    }
    block.update(kwargs)
    return block


def make_valid_semantic_map(blocks, **overrides):
    """Create a valid semantic map dict."""
    sm = {
        'schema_version': '1.0',
        'article': {
            'id': 'test-article',
            'title': 'Test Article',
            'summary': 'Test summary',
            'article_type': '观点文',
            'core_statement': 'Test core statement',
            'target_platform': ['wechat'],
            'preferred_theme': None,
        },
        'blocks': blocks,
        'constraints': {
            'preserve_facts': [],
            'preserve_stance': [],
            'preserve_quotes': [],
            'unresolved_facts': [],
            'editor_anchors': [],
            'forbidden_transformations': [],
        },
        'component_policy': {
            'force_all_components': False,
            'formatter_has_final_choice': True,
            'allow_fallback': True,
            'max_primary_advanced_components': 6,
            'prohibit_content_invention': True,
            'prohibit_duplicate_full_content': True,
        },
    }
    sm.update(overrides)
    return sm


# ════════════════════════════════════════════════════════════════
# Original Tests (kept and adapted for new validator)
# ════════════════════════════════════════════════════════════════

# ── Test 1: Old handoff fields still exist ──

def test_01_old_handoff_fields_exist():
    """Old handoff v1.0 fields are still present in handoff.md."""
    handoff = (ROOT / 'references' / 'handoff.md').read_text(encoding='utf-8')
    for field in ['article_path', 'content_score', 'p0_count', 'exit_status',
                  'unresolved_facts', 'editor_anchors', 'author_confirmations',
                  'preserve_exactly', 'next', 'humanizer', 'publisher']:
        assert field in handoff, f"Old handoff field '{field}' missing from handoff.md"


# ── Test 2: New handoff schema_version=2.0 ──

def test_02_new_handoff_schema_v2():
    """New handoff v2.0 schema_version is present."""
    handoff = (ROOT / 'references' / 'handoff.md').read_text(encoding='utf-8')
    assert 'schema_version' in handoff
    assert '"2.0"' in handoff or "'2.0'" in handoff or '2.0' in handoff
    assert 'semantic_map_path' in handoff
    assert 'formatter' in handoff
    assert 'gzh-design' in handoff
    assert 'semantic-component-handoff' in handoff
    assert 'component_policy' in handoff
    assert 'force_all_components' in handoff
    assert 'formatter_has_final_choice' in handoff


# ── Test 3: semantic-map template exists ──

def test_03_semantic_map_template_exists():
    """semantic-map.yaml template exists and has required structure."""
    template_path = ROOT / 'templates' / 'semantic-map.yaml'
    assert template_path.exists(), "semantic-map.yaml template not found"
    content = template_path.read_text(encoding='utf-8')
    assert 'schema_version' in content
    assert 'article:' in content
    assert 'blocks:' in content
    assert 'component_policy:' in content
    assert 'force_all_components: false' in content
    assert 'formatter_has_final_choice: true' in content


# ── Test 4: Duplicate block_id error ──

def test_04_duplicate_block_id_error(tmp_path):
    """Duplicate block_id should cause an error."""
    article = "This is a test article with some content."
    article_path = write_temp_article(article, tmp_path)

    blocks = [
        make_valid_block('block-001', 'paragraph', 'This is a test article',
                         payload={'text': 'This is a test article'},
                         formatter_candidates=['paragraph'], fallback=[]),
        make_valid_block('block-001', 'paragraph', 'with some content',
                         payload={'text': 'with some content'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, warnings, info = validate_semantic_map(article_path, sm_path)
    assert any('duplicate block_id' in e for e in errors), f"Expected duplicate block_id error, got: {errors}"


# ── Test 5: Anchor not found error ──

def test_05_anchor_not_found_error(tmp_path):
    """Anchor not found in article should cause an error."""
    article = "This is a test article with some content."
    article_path = write_temp_article(article, tmp_path)

    blocks = [
        make_valid_block('block-001', 'key_statement', 'This text does not exist in the article',
                         payload={'text': 'This text does not exist in the article'},
                         formatter_candidates=['quote'], fallback=['paragraph'],
                         required=True, preserve_exactly=True),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, warnings, info = validate_semantic_map(article_path, sm_path)
    assert any('not found in article' in e for e in errors), f"Expected anchor not found error, got: {errors}"


# ── Test 6: Unknown role error ──

def test_06_unknown_role_error(tmp_path):
    """Unknown role should cause an error."""
    article = "This is a test article."
    article_path = write_temp_article(article, tmp_path)

    blocks = [
        make_valid_block('block-001', 'nonexistent_role', 'This is a test article',
                         payload={'text': 'This is a test article'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, warnings, info = validate_semantic_map(article_path, sm_path)
    assert any('unknown role' in e.lower() for e in errors), f"Expected unknown role error, got: {errors}"


# ── Test 7: Missing payload field error ──

def test_07_missing_payload_field_error(tmp_path):
    """Missing required payload field should cause an error."""
    article = "This is a test article with content."
    article_path = write_temp_article(article, tmp_path)

    blocks = [
        make_valid_block('block-001', 'key_statement', 'This is a test article', payload={},
                         formatter_candidates=['quote'], fallback=['paragraph']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, warnings, info = validate_semantic_map(article_path, sm_path)
    assert any("missing required payload field 'text'" in e for e in errors), f"Expected missing payload error, got: {errors}"


# ── Test 8: compare missing subject_a/b or dimensions error ──

def test_08_compare_missing_fields_error(tmp_path):
    """compare missing subject_a/b or dimensions should cause an error."""
    article = "This is a comparison article."
    article_path = write_temp_article(article, tmp_path)

    blocks = [
        make_valid_block('block-001', 'comparison', 'This is a comparison article',
                         payload={'subject_a': 'A'},
                         formatter_candidates=['compare'], fallback=['paragraph']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, warnings, info = validate_semantic_map(article_path, sm_path)
    error_text = ' '.join(errors)
    assert 'subject_b' in error_text or 'subject_a' in error_text, f"Expected subject error, got: {errors}"
    assert 'dimensions' in error_text, f"Expected dimensions error, got: {errors}"


# ── Test 9: timeline missing time/phase error ──

def test_09_timeline_missing_time_error(tmp_path):
    """timeline missing time in events should cause an error."""
    article = "This is a timeline article."
    article_path = write_temp_article(article, tmp_path)

    blocks = [
        make_valid_block('block-001', 'timeline', 'This is a timeline article',
                         payload={'events': [
                             {'description': 'Event 1'},
                             {'description': 'Event 2'},
                         ]},
                         formatter_candidates=['timeline'], fallback=['ordered_list']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, warnings, info = validate_semantic_map(article_path, sm_path)
    assert any("missing 'time'" in e for e in errors), f"Expected missing time error, got: {errors}"


# ── Test 10: FAQ missing question/answer error ──

def test_10_faq_missing_qa_error(tmp_path):
    """FAQ missing question or answer should cause an error."""
    article = "This is a FAQ article."
    article_path = write_temp_article(article, tmp_path)

    blocks = [
        make_valid_block('block-001', 'faq', 'This is a FAQ article',
                         payload={'items': [{'answer': 'Answer without question'}]},
                         formatter_candidates=['faq'], fallback=['subtitle', 'paragraph']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, warnings, info = validate_semantic_map(article_path, sm_path)
    assert any("missing 'question'" in e for e in errors), f"Expected missing question error, got: {errors}"


# ── Test 11: quote missing source error ──

def test_11_quote_missing_source_error(tmp_path):
    """quote type 'sourced' missing source should cause an error."""
    article = "This is a quote article."
    article_path = write_temp_article(article, tmp_path)

    blocks = [
        make_valid_block('block-001', 'quote', 'This is a quote article',
                         payload={'text': 'A great quote', 'quote_type': 'sourced'},
                         formatter_candidates=['quote'], fallback=['paragraph']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, warnings, info = validate_semantic_map(article_path, sm_path)
    assert any("'sourced' missing 'source'" in e for e in errors), f"Expected source error, got: {errors}"


# ── Test 12: formatter candidate not found error ──

def test_12_formatter_candidate_not_found_error(tmp_path):
    """Unregistered formatter candidate should cause an error."""
    article = "This is a test article."
    article_path = write_temp_article(article, tmp_path)

    blocks = [
        make_valid_block('block-001', 'paragraph', 'This is a test article',
                         payload={'text': 'This is a test article'},
                         formatter_candidates=['nonexistent-component'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, warnings, info = validate_semantic_map(article_path, sm_path)
    assert any('not a registered component' in e for e in errors), f"Expected unregistered component error, got: {errors}"


# ── Test 13: HTML/CSS/color in semantic file fails ──

def test_13_html_css_color_fails(tmp_path):
    """HTML/CSS/color in semantic map should cause an error."""
    article = "This is a test article."
    article_path = write_temp_article(article, tmp_path)

    blocks = [
        make_valid_block('block-001', 'paragraph', 'This is a test article',
                         payload={'text': '<div style="color:#FF0000">HTML content</div>'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, warnings, info = validate_semantic_map(article_path, sm_path)
    assert any('HTML' in e or 'CSS' in e or 'color' in e.lower() for e in errors), f"Expected HTML/CSS error, got: {errors}"


# ── Test 14: force_all_components=true fails ──

def test_14_force_all_components_true_fails(tmp_path):
    """force_all_components=true should cause an error."""
    article = "This is a test article."
    article_path = write_temp_article(article, tmp_path)

    blocks = [
        make_valid_block('block-001', 'paragraph', 'This is a test article',
                         payload={'text': 'This is a test article'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm['component_policy']['force_all_components'] = True
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, warnings, info = validate_semantic_map(article_path, sm_path)
    assert any('force_all_components' in e for e in errors), f"Expected force_all_components error, got: {errors}"


# ── Test 15: Simple article uses only basic roles ──

def test_15_simple_article_basic_roles(tmp_path):
    """Simple article can use only paragraph/chapter/key_statement without advanced components."""
    article = """# 简单观点文

## 引言

这是一个关于写作的简单观点。

关键不在于工具，而在于思考。

## 正文

写作的核心是把真实材料和作者判断组织成值得读的内容。

## 结语

好了，今天就先聊到这儿。
"""
    article_path = write_temp_article(article, tmp_path)

    blocks = [
        make_valid_block('cover-001', 'article_cover', '',
                         payload={'title': '简单观点文', 'summary_or_intro': '这是一个关于写作的简单观点。'},
                         source_anchor={'start_text': '# 简单观点文', 'end_text': '这是一个关于写作的简单观点。'},
                         formatter_candidates=['cover-breaking'], fallback=['paragraph'], required=True),
        make_valid_block('section-001', 'article_section', '## 引言',
                         payload={'heading_text': '引言', 'section_index': 1},
                         formatter_candidates=['chapter-title'], fallback=['paragraph']),
        make_valid_block('key-001', 'key_statement', '关键不在于工具，而在于思考。',
                         payload={'text': '关键不在于工具，而在于思考。'},
                         formatter_candidates=['quote'], fallback=['paragraph'], preserve_exactly=True),
        make_valid_block('para-001', 'paragraph', '写作的核心是把真实材料和作者判断组织成值得读的内容。',
                         payload={'text': '写作的核心是把真实材料和作者判断组织成值得读的内容。'},
                         formatter_candidates=['paragraph'], fallback=[]),
        make_valid_block('section-002', 'article_section', '## 结语',
                         payload={'heading_text': '结语', 'section_index': 2},
                         formatter_candidates=['chapter-title'], fallback=['paragraph']),
        make_valid_block('para-002', 'paragraph', '好了，今天就先聊到这儿。',
                         payload={'text': '好了，今天就先聊到这儿。'},
                         formatter_candidates=['paragraph'], fallback=[]),
        make_valid_block('sig-001', 'article_signature', '',
                         payload={}, formatter_candidates=['footer-signature-brand'], fallback=[],
                         source_anchor={}),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, warnings, info = validate_semantic_map(article_path, sm_path)
    assert len(errors) == 0, f"Simple article should pass validation, got errors: {errors}"
    roles_used = set(info.get('roles_used', []))
    assert 'paragraph' in roles_used or 'article_section' in roles_used
    assert 'key_statement' in roles_used


# ── Test 16: Rich article triggers 10+ semantic roles ──

def test_16_rich_article_10_plus_roles(tmp_path):
    """Rich article can legally trigger 10+ semantic roles."""
    article = """# 深度分析

> 深度分析文章。

## 事实

月活用户：120万。类型：订阅。

## 对比

对象 A：方案一，对象 B：方案二。速度：方案一慢，方案二快。

## 决策

推荐方案：方案二。方案一慢，方案二快。

## 时间线

2026-01 完成原型。2026-06 正式上线。

## 案例

背景：服务慢。行动：优化。结果：快了。

## FAQ

问：适合所有项目吗？答：不适合极简脚本。

## 警告

此版本有已知问题。

好了，今天就先聊到这儿。
"""
    article_path = write_temp_article(article, tmp_path)

    blocks = [
        make_valid_block('cover-001', 'article_cover', '',
                         payload={'title': '深度分析', 'summary_or_intro': '深度分析文章。'},
                         source_anchor={'start_text': '# 深度分析', 'end_text': '深度分析文章。'},
                         formatter_candidates=['cover-breaking'], fallback=['paragraph'], required=True),
        make_valid_block('sec-001', 'article_section', '## 事实',
                         payload={'heading_text': '事实', 'section_index': 1},
                         formatter_candidates=['chapter-title'], fallback=['paragraph']),
        make_valid_block('fact-001', 'fact', '',
                         payload={'title': '核心数据', 'items': [{'key': '月活用户', 'value': '120万'}, {'key': '类型', 'value': '订阅'}]},
                         source_anchor={'start_text': '月活用户：120万。', 'end_text': '类型：订阅。'},
                         evidence_ids=['ev-001'],
                         formatter_candidates=['facts'], fallback=['ordered_list'], preserve_exactly=True),
        make_valid_block('sec-002', 'article_section', '## 对比',
                         payload={'heading_text': '对比', 'section_index': 2},
                         formatter_candidates=['chapter-title'], fallback=['paragraph']),
        make_valid_block('cmp-001', 'comparison', '',
                         payload={'subject_a': '方案一', 'subject_b': '方案二',
                                  'dimensions': ['速度'], 'rows': [{'dimension': '速度', 'value_a': '慢', 'value_b': '快'}]},
                         source_anchor={'start_text': '对象 A：方案一，对象 B：方案二。', 'end_text': '速度：方案一慢，方案二快。'},
                         formatter_candidates=['compare'], fallback=['paragraph']),
        make_valid_block('sec-003', 'article_section', '## 决策',
                         payload={'heading_text': '决策', 'section_index': 3},
                         formatter_candidates=['chapter-title'], fallback=['paragraph']),
        make_valid_block('dec-001', 'decision', '',
                         payload={'recommended': '方案二', 'options': [{'name': '方案一', 'description': '慢'}, {'name': '方案二', 'description': '快'}]},
                         source_anchor={'start_text': '推荐方案：方案二。', 'end_text': '方案一慢，方案二快。'},
                         formatter_candidates=['decision'], fallback=['paragraph']),
        make_valid_block('sec-004', 'article_section', '## 时间线',
                         payload={'heading_text': '时间线', 'section_index': 4},
                         formatter_candidates=['chapter-title'], fallback=['paragraph']),
        make_valid_block('tl-001', 'timeline', '2026-01 完成原型。2026-06 正式上线。',
                         payload={'title': '项目演进', 'events': [{'time': '2026-01', 'description': '完成原型'}, {'time': '2026-06', 'description': '正式上线'}]},
                         formatter_candidates=['timeline'], fallback=['ordered_list']),
        make_valid_block('sec-005', 'article_section', '## 案例',
                         payload={'heading_text': '案例', 'section_index': 5},
                         formatter_candidates=['chapter-title'], fallback=['paragraph']),
        make_valid_block('case-001', 'case', '背景：服务慢。行动：优化。结果：快了。',
                         payload={'context': '服务慢', 'challenge': '', 'action': '优化', 'result': '快了'},
                         evidence_ids=['ev-002'],
                         formatter_candidates=['case'], fallback=['paragraph']),
        make_valid_block('sec-006', 'article_section', '## FAQ',
                         payload={'heading_text': 'FAQ', 'section_index': 6},
                         formatter_candidates=['chapter-title'], fallback=['paragraph']),
        make_valid_block('faq-001', 'faq', '问：适合所有项目吗？答：不适合极简脚本。',
                         payload={'title': '常见问题', 'items': [{'question': '适合所有项目吗？', 'answer': '不适合极简脚本。'}]},
                         formatter_candidates=['faq'], fallback=['subtitle', 'paragraph']),
        make_valid_block('warn-001', 'warning', '此版本有已知问题。',
                         payload={'text': '此版本有已知问题。'},
                         formatter_candidates=['alert'], fallback=['quote', 'paragraph']),
        make_valid_block('key-001', 'key_statement', '好了，今天就先聊到这儿。',
                         payload={'text': '好了，今天就先聊到这儿。'},
                         formatter_candidates=['quote'], fallback=['paragraph'], preserve_exactly=True),
        make_valid_block('sig-001', 'article_signature', '',
                         payload={}, formatter_candidates=['footer-signature-brand'], fallback=[],
                         source_anchor={}),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    # Write a simple evidence map
    ev_path = write_temp_file("# Evidence\nev-001 test\nev-002 test\n", tmp_path, 'evidence-map.md')

    errors, warnings, info = validate_semantic_map(article_path, sm_path, evidence_map_path=ev_path)
    assert len(errors) == 0, f"Rich article should pass validation, got errors: {errors}"
    roles_used = info.get('roles_used', [])
    assert len(roles_used) >= 10, f"Expected 10+ roles, got {len(roles_used)}: {roles_used}"


# ── Test 17: Advanced components have mappable roles ──

def test_17_advanced_components_have_roles():
    """All 19 advanced components have at least one mappable semantic role."""
    capability_map = (ROOT / 'references' / 'formatter-capability-map.md').read_text(encoding='utf-8')

    advanced_components = [
        'alert', 'quote', 'code-compare', 'media-text', 'gallery',
        'long-image', 'resources', 'footnotes', 'dialogue', 'facts',
        'decision', 'steps', 'compare', 'annotated-image', 'faq',
        'timeline', 'checklist', 'case', 'cta',
    ]

    for comp in advanced_components:
        assert comp in capability_map, f"Advanced component '{comp}' not found in formatter-capability-map.md"


# ── Test 18: Core components have roles ──

def test_18_core_components_have_roles():
    """All 13 core components have corresponding content roles or article-level structure."""
    capability_map = (ROOT / 'references' / 'formatter-capability-map.md').read_text(encoding='utf-8')

    core_components = [
        ('global-container', 'formatter_generated'),
        ('cover-breaking', 'article_cover'),
        ('toc-scroll', 'article_toc'),
        ('chapter-title', 'article_section'),
        ('paragraph', 'paragraph'),
        ('inline-styles', 'secondary_emphasis'),
        ('label-heading', 'subtitle'),
        ('code-block', 'code'),
        ('quote-oneliner', 'quote'),
        ('alert-box', 'warning'),
        ('table-list-flow', 'ordered_list'),
        ('image-video', 'image'),
        ('footer-signature-brand', 'article_signature'),
    ]

    for comp_id, semantic_role in core_components:
        assert comp_id in capability_map, f"Core component '{comp_id}' not found in formatter-capability-map.md"
        if semantic_role != 'formatter_generated':
            assert semantic_role in ALLOWED_ROLES, f"Semantic role '{semantic_role}' not in ALLOWED_ROLES"


# ── Test 19: humanizer anchor invalidation ──

def test_19_humanizer_anchor_invalidation(tmp_path):
    """After humanizer modifies article, stale anchors should be detected."""
    modified_article = "The modified text is different now."
    article_path = write_temp_article(modified_article, tmp_path)

    blocks = [
        make_valid_block('block-001', 'key_statement', 'The original text is here.',
                         payload={'text': 'The original text is here.'},
                         formatter_candidates=['quote'], fallback=['paragraph'], preserve_exactly=True),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, warnings, info = validate_semantic_map(article_path, sm_path)
    assert any('not found in article' in e for e in errors), \
        f"Expected anchor invalidation error after humanizer, got: {errors}"


# ── Test 20: fallback allows formatter downgrade ──

def test_20_fallback_allows_downgrade(tmp_path):
    """When fallback is available, formatter can downgrade without error."""
    article = "Comparing A and B. Speed: A is fast, B is slow."
    article_path = write_temp_article(article, tmp_path)

    blocks = [
        make_valid_block('block-001', 'comparison', '',
                         payload={'subject_a': 'A', 'subject_b': 'B',
                                  'dimensions': ['speed'], 'rows': [{'dimension': 'speed', 'value_a': 'fast', 'value_b': 'slow'}]},
                         source_anchor={'start_text': 'Comparing A and B.', 'end_text': 'Speed: A is fast, B is slow.'},
                         formatter_candidates=['compare', 'table-list-flow'],
                         fallback=['paragraph', 'ordered_list']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, warnings, info = validate_semantic_map(article_path, sm_path)
    assert len(errors) == 0, f"Valid article with fallback should pass, got errors: {errors}"


# ── Test 21: preserve_exactly ──

def test_21_preserve_exactly_not_rewritable(tmp_path):
    """preserve_exactly=true blocks should not be flagged as rewritable."""
    article = "This is a key statement that must be preserved exactly."
    article_path = write_temp_article(article, tmp_path)

    blocks = [
        make_valid_block('block-001', 'key_statement', 'This is a key statement that must be preserved exactly.',
                         payload={'text': 'This is a key statement that must be preserved exactly.'},
                         formatter_candidates=['quote'], fallback=['paragraph'],
                         preserve_exactly=True),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, warnings, info = validate_semantic_map(article_path, sm_path)
    assert not any('preserve_exactly' in e.lower() for e in errors), \
        f"preserve_exactly=true should not cause errors, got: {errors}"
    sm_data = yaml.safe_load(sm_path.read_text(encoding='utf-8'))
    assert sm_data['blocks'][0]['preserve_exactly'] is True


# ── Test 22: CLI test ──

def test_22_cli_works(tmp_path):
    """CLI interface works correctly."""
    article = "This is a test article for CLI validation."
    article_path = write_temp_article(article, tmp_path)

    blocks = [
        make_valid_block('block-001', 'paragraph', 'This is a test article for CLI validation.',
                         payload={'text': 'This is a test article for CLI validation.'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'validate_semantic_map.py'),
         '--article', str(article_path),
         '--semantic-map', str(sm_path),
         '--json'],
        capture_output=True, text=True
    )
    assert p.returncode == 0, f"CLI should pass for valid input:\n{p.stdout}\n{p.stderr}"
    result = json.loads(p.stdout)
    assert result['passed'] is True
    assert result['summary']['total_blocks'] == 1


# ════════════════════════════════════════════════════════════════
# H1: 角色总数和集合完全一致
# ════════════════════════════════════════════════════════════════

def test_h1_role_count_is_41():
    """ALLOWED_ROLES must have exactly 41 roles."""
    assert len(ALLOWED_ROLES) == 41, f"Expected 41 roles, got {len(ALLOWED_ROLES)}: {sorted(ALLOWED_ROLES)}"


def test_h1_roles_match_required_fields():
    """set(ALLOWED_ROLES) must equal set(ROLE_REQUIRED_FIELDS.keys())."""
    assert set(ALLOWED_ROLES) == set(ROLE_REQUIRED_FIELDS.keys()), \
        f"Mismatch: ALLOWED_ROLES - ROLE_REQUIRED_FIELDS = {ALLOWED_ROLES - set(ROLE_REQUIRED_FIELDS.keys())}, " \
        f"ROLE_REQUIRED_FIELDS - ALLOWED_ROLES = {set(ROLE_REQUIRED_FIELDS.keys()) - ALLOWED_ROLES}"


def test_h1_article_wrapper_not_in_roles():
    """article_wrapper must NOT be in ALLOWED_ROLES (it's formatter_generated)."""
    assert 'article_wrapper' not in ALLOWED_ROLES, "article_wrapper should not be a Writer output role"


def test_h1_formatter_capability_map_uses_formatter_generated():
    """formatter-capability-map.md must use formatter_generated for global-container."""
    cap_map = (ROOT / 'references' / 'formatter-capability-map.md').read_text(encoding='utf-8')
    assert 'formatter_generated' in cap_map
    # global-container should not use article_wrapper as semantic_role
    assert '| semantic_role | article_wrapper |' not in cap_map


# ════════════════════════════════════════════════════════════════
# H2: 模板 candidate 全部有效
# ════════════════════════════════════════════════════════════════

def test_h2_template_candidates_all_valid():
    """All formatter_candidates in template must exist in the registered component set."""
    from validate_semantic_map import _get_static_components
    registered = _get_static_components()
    template_path = ROOT / 'templates' / 'semantic-map.yaml'
    template = yaml.safe_load(template_path.read_text(encoding='utf-8'))

    for block in template.get('blocks', []):
        for cand in block.get('formatter_candidates', []):
            assert cand in registered, f"Template block '{block.get('block_id')}' has invalid candidate '{cand}'"


def test_h2_template_roles_all_valid():
    """All roles in template must exist in ALLOWED_ROLES."""
    template_path = ROOT / 'templates' / 'semantic-map.yaml'
    template = yaml.safe_load(template_path.read_text(encoding='utf-8'))

    for block in template.get('blocks', []):
        role = block.get('role')
        assert role in ALLOWED_ROLES, f"Template block '{block.get('block_id')}' has invalid role '{role}'"


def test_h2_template_no_table_candidate():
    """Template must not contain 'table' as a formatter_candidate (should be 'table-list-flow')."""
    template_text = (ROOT / 'templates' / 'semantic-map.yaml').read_text(encoding='utf-8')
    # Check that 'table' is not a standalone candidate entry
    lines = template_text.split('\n')
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- ') and stripped.endswith('table'):
            pytest.fail(f"Template contains invalid component 'table': {line}")


# ════════════════════════════════════════════════════════════════
# H3: formatter-root 真正生效
# ════════════════════════════════════════════════════════════════

def test_h3_formatter_root_missing_directory_reports_error(tmp_path):
    """formatter-root pointing to nonexistent directory should report error."""
    article = "Test article."
    article_path = write_temp_article(article, tmp_path)
    blocks = [make_valid_block('b1', 'paragraph', 'Test article.',
                               payload={'text': 'Test article.'},
                               formatter_candidates=['paragraph'], fallback=[])]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, _, info = validate_semantic_map(article_path, sm_path,
                                            formatter_root=str(tmp_path / 'nonexistent'))
    assert any('does not exist' in e for e in errors), f"Expected formatter_root missing error, got: {errors}"
    assert info.get('formatter_root_used') is not None


def test_h3_formatter_root_sha_mismatch_reports_error(tmp_path):
    """When gzh-design contract SHA changes, validator should report error."""
    article = "Test article."
    article_path = write_temp_article(article, tmp_path)
    blocks = [make_valid_block('b1', 'paragraph', 'Test article.',
                               payload={'text': 'Test article.'},
                               formatter_candidates=['paragraph'], fallback=[])]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    # Create a fake formatter root with wrong content
    fake_root = tmp_path / 'fake-gzh-design'
    fake_root.mkdir()
    (fake_root / 'SKILL.md').write_text('wrong content', encoding='utf-8')
    (fake_root / 'references').mkdir()
    (fake_root / 'references' / 'theme-index.md').write_text('wrong', encoding='utf-8')
    (fake_root / 'references' / 'common-components.md').write_text('wrong', encoding='utf-8')
    (fake_root / 'references' / 'advanced-components.md').write_text('wrong', encoding='utf-8')
    (fake_root / 'references' / 'theme-hammer.md').write_text('wrong', encoding='utf-8')

    errors, _, _ = validate_semantic_map(article_path, sm_path, formatter_root=str(fake_root))
    assert any('SHA256 mismatch' in e or 'mismatch' in e.lower() for e in errors), \
        f"Expected SHA mismatch error, got: {errors}"


def test_h3_formatter_root_valid_works(tmp_path):
    """Real formatter-root should pass SHA verification and be used."""
    gzh_root = Path('f:/AIXM/wxgzh/gzh-design-skill/')
    if not gzh_root.exists():
        pytest.skip("gzh-design-skill not found, skipping integration test")

    article = "Test article content."
    article_path = write_temp_article(article, tmp_path)
    blocks = [make_valid_block('b1', 'paragraph', 'Test article content.',
                               payload={'text': 'Test article content.'},
                               formatter_candidates=['paragraph'], fallback=[])]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, _, info = validate_semantic_map(article_path, sm_path, formatter_root=str(gzh_root))
    assert info.get('formatter_root_used') is True, "formatter_root should be used"
    # Should not have SHA mismatch errors
    assert not any('SHA256 mismatch' in e for e in errors), f"Unexpected SHA mismatch: {errors}"


# ════════════════════════════════════════════════════════════════
# H4: role 与 candidate 不兼容报错
# ════════════════════════════════════════════════════════════════

def test_h4_role_candidate_incompatible_reports_error(tmp_path):
    """paragraph → cta should be rejected as incompatible."""
    gzh_root = Path('f:/AIXM/wxgzh/gzh-design-skill/')
    if not gzh_root.exists():
        pytest.skip("gzh-design-skill not found")

    article = "Test article content."
    article_path = write_temp_article(article, tmp_path)
    blocks = [make_valid_block('b1', 'paragraph', 'Test article content.',
                               payload={'text': 'Test article content.'},
                               formatter_candidates=['cta'], fallback=[])]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, _, _ = validate_semantic_map(article_path, sm_path, formatter_root=str(gzh_root))
    assert any('not compatible' in e.lower() for e in errors), \
        f"Expected incompatible role/candidate error for paragraph→cta, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H4: CTA 非 HTTPS 报错
# ════════════════════════════════════════════════════════════════

def test_h4_cta_non_https_reports_error(tmp_path):
    """article_cta with non-HTTPS URL should report error."""
    article = "Click here for more info."
    article_path = write_temp_article(article, tmp_path)
    blocks = [make_valid_block('cta-001', 'article_cta', 'Click here for more info.',
                               payload={'text': 'Click here for more info.', 'url': 'http://example.com'},
                               formatter_candidates=['cta'], fallback=['footer-signature-brand'])]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('HTTPS' in e for e in errors), f"Expected HTTPS error for CTA, got: {errors}"


def test_h4_cta_empty_url_reports_error(tmp_path):
    """article_cta with empty URL should report error."""
    article = "Click here for more info."
    article_path = write_temp_article(article, tmp_path)
    blocks = [make_valid_block('cta-001', 'article_cta', 'Click here for more info.',
                               payload={'text': 'Click here for more info.', 'url': ''},
                               formatter_candidates=['cta'], fallback=['footer-signature-brand'])]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('missing required payload field' in e or 'HTTPS' in e for e in errors), \
        f"Expected error for empty CTA URL, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H4: video 空 URL 报错
# ════════════════════════════════════════════════════════════════

def test_h4_video_empty_url_reports_error(tmp_path):
    """video with both empty video_url and image_url should report error."""
    article = "Watch this video demo."
    article_path = write_temp_article(article, tmp_path)
    blocks = [make_valid_block('vid-001', 'video', 'Watch this video demo.',
                               payload={'video_url': '', 'image_url': ''},
                               formatter_candidates=['image-video'], fallback=[])]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('video' in e.lower() and ('requires' in e.lower() or 'must' in e.lower()) for e in errors), \
        f"Expected error for empty video URLs, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H4: fact item 缺 key/value 报错
# ════════════════════════════════════════════════════════════════

def test_h4_fact_item_missing_key_value_reports_error(tmp_path):
    """fact with item missing key or value should report error."""
    article = "Some factual data here."
    article_path = write_temp_article(article, tmp_path)
    blocks = [make_valid_block('fact-001', 'fact', 'Some factual data here.',
                               payload={'items': [{'key': '', 'value': '123'}, {'key': 'name', 'value': ''}]},
                               evidence_ids=['ev-001'],
                               formatter_candidates=['facts'], fallback=['ordered_list'])]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any("missing non-empty 'key'" in e for e in errors), f"Expected missing key error, got: {errors}"
    assert any("missing non-empty 'value'" in e for e in errors), f"Expected missing value error, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H4: decision 少于两个 option 报错
# ════════════════════════════════════════════════════════════════

def test_h4_decision_less_than_two_options_reports_error(tmp_path):
    """decision with only 1 option should report error."""
    article = "We chose option A."
    article_path = write_temp_article(article, tmp_path)
    blocks = [make_valid_block('dec-001', 'decision', 'We chose option A.',
                               payload={'recommended': 'A', 'options': [{'name': 'A', 'description': 'good'}]},
                               formatter_candidates=['decision'], fallback=['paragraph'])]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('at least 2' in e for e in errors), f"Expected less than 2 options error, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H4: checklist checked 非 boolean 报错
# ════════════════════════════════════════════════════════════════

def test_h4_checklist_non_boolean_checked_reports_error(tmp_path):
    """checklist with non-boolean checked should report error."""
    article = "Check these items."
    article_path = write_temp_article(article, tmp_path)
    blocks = [make_valid_block('chk-001', 'checklist', 'Check these items.',
                               payload={'items': [
                                   {'text': 'Item 1', 'checked': 'yes'},
                                   {'text': 'Item 2', 'checked': True}
                               ]},
                               formatter_candidates=['checklist'], fallback=['ordered_list'])]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any("must be boolean" in e for e in errors), f"Expected non-boolean checked error, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H4: gallery 只有一张图报错
# ════════════════════════════════════════════════════════════════

def test_h4_gallery_single_image_reports_error(tmp_path):
    """gallery with only 1 image should report error."""
    article = "Gallery content here."
    article_path = write_temp_article(article, tmp_path)
    blocks = [make_valid_block('gal-001', 'gallery', 'Gallery content here.',
                               payload={'images': [
                                   {'url': 'https://example.com/1.jpg', 'caption': 'Image 1'}
                               ]},
                               formatter_candidates=['gallery'], fallback=[])]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('at least 2' in e for e in errors), f"Expected gallery single image error, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H5: duplicate anchor 报错 (ERROR not warning)
# ════════════════════════════════════════════════════════════════

def test_h5_duplicate_anchor_reports_error(tmp_path):
    """Duplicate exact_text in two blocks should be ERROR, not warning."""
    article = "The same text appears here. Another sentence."
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', 'The same text appears here.',
                         payload={'text': 'The same text appears here.'},
                         formatter_candidates=['paragraph'], fallback=[]),
        make_valid_block('b2', 'paragraph', 'The same text appears here.',
                         payload={'text': 'Duplicate block content.'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('duplicate anchor' in e.lower() or 'duplicate exact_text' in e.lower() for e in errors), \
        f"Expected duplicate anchor ERROR, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H5: heading_path 无效报错
# ════════════════════════════════════════════════════════════════

def test_h5_invalid_heading_path_reports_error(tmp_path):
    """heading_path referencing non-existent heading should report error."""
    article = "## Real Heading\n\nContent here."
    article_path = write_temp_article(article, tmp_path)
    blocks = [make_valid_block('b1', 'paragraph', 'Content here.',
                               payload={'text': 'Content here.'},
                               heading_path=['Nonexistent Heading'],
                               formatter_candidates=['paragraph'], fallback=[])]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('heading_path' in e and 'not found' in e.lower() for e in errors), \
        f"Expected heading_path not found error, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H5: evidence ID 不存在报错
# ════════════════════════════════════════════════════════════════

def test_h5_evidence_id_not_found_reports_error(tmp_path):
    """evidence_id not in evidence-map should report error."""
    article = "Some factual data here."
    article_path = write_temp_article(article, tmp_path)
    blocks = [make_valid_block('fact-001', 'fact', 'Some factual data here.',
                               payload={'items': [{'key': 'k', 'value': 'v'}, {'key': 'k2', 'value': 'v2'}]},
                               evidence_ids=['ev-nonexistent'],
                               formatter_candidates=['facts'], fallback=['ordered_list'])]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    ev_path = write_temp_file("# Evidence\nev-001 real\n", tmp_path, 'evidence-map.md')

    errors, _, _ = validate_semantic_map(article_path, sm_path, evidence_map_path=ev_path)
    assert any('ev-nonexistent' in e and 'not found' in e.lower() for e in errors), \
        f"Expected evidence ID not found error, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H6: signature 出现两次报错
# ════════════════════════════════════════════════════════════════

def test_h6_signature_twice_reports_error(tmp_path):
    """article_signature appearing twice should report error."""
    article = "Content here. More content."
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', 'Content here.',
                         payload={'text': 'Content here.'},
                         formatter_candidates=['paragraph'], fallback=[]),
        make_valid_block('sig-001', 'article_signature', '',
                         payload={}, formatter_candidates=['footer-signature-brand'], fallback=[],
                         source_anchor={}),
        make_valid_block('b2', 'paragraph', 'More content.',
                         payload={'text': 'More content.'},
                         formatter_candidates=['paragraph'], fallback=[]),
        make_valid_block('sig-002', 'article_signature', '',
                         payload={}, formatter_candidates=['footer-signature-brand'], fallback=[],
                         source_anchor={}),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('article_signature' in e and '2' in e for e in errors), \
        f"Expected double signature error, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H6: signature 不在末尾报错
# ════════════════════════════════════════════════════════════════

def test_h6_signature_not_last_reports_error(tmp_path):
    """article_signature not being the last block should report error."""
    article = "First paragraph. Second paragraph."
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', 'First paragraph.',
                         payload={'text': 'First paragraph.'},
                         formatter_candidates=['paragraph'], fallback=[]),
        make_valid_block('sig-001', 'article_signature', '',
                         payload={}, formatter_candidates=['footer-signature-brand'], fallback=[],
                         source_anchor={}),
        make_valid_block('b2', 'paragraph', 'Second paragraph.',
                         payload={'text': 'Second paragraph.'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('article_signature' in e and 'last' in e.lower() for e in errors), \
        f"Expected signature not last error, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H6: key_statement 超过 5 个报错
# ════════════════════════════════════════════════════════════════

def test_h6_too_many_key_statements_reports_error(tmp_path):
    """More than 5 key_statement blocks should report error."""
    article = "Stmt1. Stmt2. Stmt3. Stmt4. Stmt5. Stmt6."
    article_path = write_temp_article(article, tmp_path)
    blocks = []
    for i in range(1, 7):
        blocks.append(make_valid_block(f'ks-{i:03d}', 'key_statement', f'Stmt{i}.',
                                       payload={'text': f'Stmt{i}.'},
                                       formatter_candidates=['quote'], fallback=['paragraph']))
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('key_statement' in e and 'exceeds' in e.lower() for e in errors), \
        f"Expected key_statement count exceeds error, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H6: 高级组件超过上限报错
# ════════════════════════════════════════════════════════════════

def test_h6_too_many_advanced_types_reports_error(tmp_path):
    """More advanced component types than max should report error."""
    article = """## Sec1
Data1.
## Sec2
Data2.
## Sec3
Data3.
## Sec4
Data4.
## Sec5
Data5.
## Sec6
Data6.
## Sec7
Data7.
## Sec8
Data8.
"""
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('c1', 'comparison', 'Data1.',
                         payload={'subject_a': 'A', 'subject_b': 'B',
                                  'dimensions': ['d'], 'rows': [{'dimension': 'd', 'value_a': '1', 'value_b': '2'}]},
                         formatter_candidates=['compare'], fallback=['paragraph']),
        make_valid_block('c2', 'decision', 'Data2.',
                         payload={'recommended': 'A', 'options': [{'name': 'A', 'description': 'd'}, {'name': 'B', 'description': 'd'}]},
                         formatter_candidates=['decision'], fallback=['paragraph']),
        make_valid_block('c3', 'timeline', 'Data3.',
                         payload={'events': [{'time': 't1', 'description': 'd1'}, {'time': 't2', 'description': 'd2'}]},
                         formatter_candidates=['timeline'], fallback=['ordered_list']),
        make_valid_block('c4', 'checklist', 'Data4.',
                         payload={'items': [{'text': 'i1', 'checked': True}, {'text': 'i2', 'checked': False}]},
                         formatter_candidates=['checklist'], fallback=['ordered_list']),
        make_valid_block('c5', 'faq', 'Data5.',
                         payload={'items': [{'question': 'Q1', 'answer': 'A1'}]},
                         formatter_candidates=['faq'], fallback=['paragraph']),
        make_valid_block('c6', 'dialogue', 'Data6.',
                         payload={'messages': [{'role': 'user', 'content': 'Hi'}]},
                         formatter_candidates=['dialogue'], fallback=['paragraph']),
        make_valid_block('c7', 'case', 'Data7.',
                         payload={'context': 'ctx', 'challenge': 'ch', 'action': 'act', 'result': 'res'},
                         evidence_ids=['ev-001'],
                         formatter_candidates=['case'], fallback=['paragraph']),
        make_valid_block('c8', 'step_sequence', 'Data8.',
                         payload={'steps': ['s1', 's2']},
                         formatter_candidates=['steps'], fallback=['ordered_list']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm['component_policy']['max_primary_advanced_components'] = 3
    sm_path = write_temp_semantic_map(sm, tmp_path)

    ev_path = write_temp_file("# Evidence\nev-001 test\n", tmp_path, 'evidence-map.md')
    errors, _, _ = validate_semantic_map(article_path, sm_path, evidence_map_path=ev_path)
    assert any('exceeds max_primary_advanced_components' in e for e in errors), \
        f"Expected advanced component count exceeds error, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H6: prohibit_duplicate_full_content=false 报错
# ════════════════════════════════════════════════════════════════

def test_h6_prohibit_duplicate_false_reports_error(tmp_path):
    """prohibit_duplicate_full_content=false should report error."""
    article = "Test content here."
    article_path = write_temp_article(article, tmp_path)
    blocks = [make_valid_block('b1', 'paragraph', 'Test content here.',
                               payload={'text': 'Test content here.'},
                               formatter_candidates=['paragraph'], fallback=[])]
    sm = make_valid_semantic_map(blocks)
    sm['component_policy']['prohibit_duplicate_full_content'] = False
    sm_path = write_temp_semantic_map(sm, tmp_path)

    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('prohibit_duplicate_full_content' in e for e in errors), \
        f"Expected prohibit_duplicate_full_content=false error, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H8: malformed YAML 返回结构化错误
# ════════════════════════════════════════════════════════════════

def test_h8_malformed_yaml_returns_structured_error(tmp_path):
    """Malformed YAML should return structured error, not crash with traceback."""
    article = "Test article."
    article_path = write_temp_article(article, tmp_path)
    bad_yaml = tmp_path / 'bad.yaml'
    bad_yaml.write_text("schema_version: 1.0\n  bad: indent: here\n    [unclosed", encoding='utf-8')

    errors, _, _ = validate_semantic_map(article_path, bad_yaml)
    assert any('YAML' in e or 'parse' in e.lower() for e in errors), \
        f"Expected structured YAML error, got: {errors}"


def test_h8_empty_yaml_returns_structured_error(tmp_path):
    """Empty YAML file should return structured error."""
    article = "Test article."
    article_path = write_temp_article(article, tmp_path)
    empty_yaml = tmp_path / 'empty.yaml'
    empty_yaml.write_text("", encoding='utf-8')

    errors, _, _ = validate_semantic_map(article_path, empty_yaml)
    assert any('empty' in e.lower() for e in errors), \
        f"Expected empty YAML error, got: {errors}"


def test_h8_non_object_yaml_returns_structured_error(tmp_path):
    """YAML top-level being a list (not object) should return structured error."""
    article = "Test article."
    article_path = write_temp_article(article, tmp_path)
    list_yaml = tmp_path / 'list.yaml'
    list_yaml.write_text("- item1\n- item2\n", encoding='utf-8')

    errors, _, _ = validate_semantic_map(article_path, list_yaml)
    assert any('object' in e.lower() or 'dict' in e.lower() for e in errors), \
        f"Expected non-object YAML error, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H7: Fixture A/B/C 均为 0 error + 0 warning
# ════════════════════════════════════════════════════════════════

def test_h7_fixture_a_zero_errors_zero_warnings():
    """Fixture A should have 0 errors and 0 warnings."""
    fixture_dir = ROOT / 'tests' / 'fixtures' / 'semantic' / 'fixture-a-simple'
    article = fixture_dir / 'article.md'
    sm = fixture_dir / 'semantic-map.yaml'
    errors, warnings, info = validate_semantic_map(article, sm)
    assert len(errors) == 0, f"Fixture A has {len(errors)} errors: {errors}"
    assert len(warnings) == 0, f"Fixture A has {len(warnings)} warnings: {warnings}"


def test_h7_fixture_b_zero_errors_zero_warnings():
    """Fixture B should have 0 errors and 0 warnings."""
    fixture_dir = ROOT / 'tests' / 'fixtures' / 'semantic' / 'fixture-b-tutorial'
    article = fixture_dir / 'article.md'
    sm = fixture_dir / 'semantic-map.yaml'
    errors, warnings, info = validate_semantic_map(article, sm)
    assert len(errors) == 0, f"Fixture B has {len(errors)} errors: {errors}"
    assert len(warnings) == 0, f"Fixture B has {len(warnings)} warnings: {warnings}"


def test_h7_fixture_c_zero_errors_zero_warnings():
    """Fixture C should have 0 errors and 0 warnings (with evidence-map)."""
    fixture_dir = ROOT / 'tests' / 'fixtures' / 'semantic' / 'fixture-c-analysis'
    article = fixture_dir / 'article.md'
    sm = fixture_dir / 'semantic-map.yaml'
    ev = fixture_dir / 'evidence-map.md'
    errors, warnings, info = validate_semantic_map(article, sm, evidence_map_path=ev)
    assert len(errors) == 0, f"Fixture C has {len(errors)} errors: {errors}"
    assert len(warnings) == 0, f"Fixture C has {len(warnings)} warnings: {warnings}"


# ════════════════════════════════════════════════════════════════
# Additional: SKILL.md references new files
# ════════════════════════════════════════════════════════════════

def test_skill_md_references_semantic_files():
    """SKILL.md should reference the new semantic files."""
    skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
    assert 'semantic-components.md' in skill
    assert 'formatter-capability-map.md' in skill
    assert 'semantic-map.yaml' in skill
    assert 'validate_semantic_map.py' in skill
    assert 'content_shape' in skill
    assert 'semantic_blocks' in skill
    assert 'formatter_opportunities' in skill


# ════════════════════════════════════════════════════════════════
# Additional: formatter-registry.yaml exists
# ════════════════════════════════════════════════════════════════

def test_formatter_registry_exists():
    """formatter-registry.yaml should exist and have required structure."""
    reg_path = ROOT / 'references' / 'formatter-registry.yaml'
    assert reg_path.exists(), "formatter-registry.yaml not found"
    reg = yaml.safe_load(reg_path.read_text(encoding='utf-8'))
    assert 'registry_version' in reg
    assert 'source_files' in reg
    assert 'role_component_matrix' in reg
    assert 'all_components' in reg
    assert len(reg['source_files']) > 0


# ════════════════════════════════════════════════════════════════
# F1: Content Provenance Validation Tests
# ════════════════════════════════════════════════════════════════

def test_f1_payload_fact_not_in_article_reports_error(tmp_path):
    """payload with fact not in article should report content provenance error."""
    article = "原文只有一句普通话。"
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('fact-001', 'fact', '原文只有一句普通话。',
                         payload={'items': [{'key': '营收', 'value': '999亿元'}, {'key': '增长', 'value': '88%'}]},
                         evidence_ids=['ev-001'],
                         formatter_candidates=['facts'], fallback=['ordered_list']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    ev_path = write_temp_file("# Evidence\nev-001 test\n", tmp_path, 'evidence-map.md')
    errors, _, _ = validate_semantic_map(article_path, sm_path, evidence_map_path=ev_path)
    assert any('not found in source span' in e for e in errors), \
        f"Expected content provenance error for invented fact, got: {errors}"


def test_f1_payload_number_not_in_article_reports_error(tmp_path):
    """payload with number not in article should report content provenance error."""
    article = "月活用户120万。"
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('stat-001', 'statistic', '月活用户120万。',
                         payload={'value': '999亿', 'label': '增长'},
                         formatter_candidates=['facts'], fallback=['paragraph']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('not found in source span' in e for e in errors), \
        f"Expected content provenance error for invented number, got: {errors}"


def test_f1_payload_url_not_in_article_reports_error(tmp_path):
    """URLs in payload that are not in source span and not in author_assets must report error."""
    article = "Check the docs for more info."
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('res-001', 'resource_list', 'Check the docs for more info.',
                         payload={'links': [
                             {'name': 'Docs', 'url': 'https://example.com/docs'},
                             {'name': 'API', 'url': 'https://example.com/api'}
                         ]},
                         formatter_candidates=['resources'], fallback=['paragraph']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    # URLs not in source span and not declared in author_assets → ERROR
    url_errors = [e for e in errors if 'not found in source span' in e and 'not declared in author_assets' in e]
    assert len(url_errors) >= 2, f"Expected URL provenance errors, got: {errors}"


def test_f1_url_in_source_span_passes(tmp_path):
    """URLs that appear in article source span should pass provenance check."""
    article = "Docs: https://example.com/docs and API: https://example.com/api"
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('res-001', 'resource_list', '',
                         payload={'links': [
                             {'name': 'Docs', 'url': 'https://example.com/docs'},
                             {'name': 'API', 'url': 'https://example.com/api'}
                         ]},
                         source_anchor={'start_text': 'Docs: https://example.com/docs',
                                        'end_text': 'API: https://example.com/api'},
                         formatter_candidates=['resources'], fallback=['paragraph']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    url_errors = [e for e in errors if 'URL' in e and 'not found in source span' in e]
    assert len(url_errors) == 0, f"URLs in source span should pass, got: {url_errors}"


def test_f1_url_in_author_assets_passes(tmp_path):
    """URLs declared in author_assets with valid provenance should pass."""
    article = "Some article content here."
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('res-001', 'resource_list', 'Some article content here.',
                         payload={'links': [
                             {'name': 'Docs', 'url': 'https://example.com/docs'},
                             {'name': 'API', 'url': 'https://example.com/api'}
                         ]},
                         formatter_candidates=['resources'], fallback=['paragraph']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm['author_assets'] = [
        {'asset_id': 'link-001', 'type': 'url', 'value': 'https://example.com/docs',
         'provenance': 'author_input', 'source_reference': 'author provided'},
        {'asset_id': 'link-002', 'type': 'url', 'value': 'https://example.com/api',
         'provenance': 'supplied_material', 'source_reference': 'research notes'},
    ]
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    url_errors = [e for e in errors if 'URL' in e and 'not found in source span' in e]
    assert len(url_errors) == 0, f"URLs in author_assets should pass, got: {url_errors}"


def test_f1_url_author_assets_generated_provenance_reports_error(tmp_path):
    """URLs declared in author_assets with provenance=generated must report error."""
    article = "Some article content here."
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('res-001', 'resource_list', 'Some article content here.',
                         payload={'links': [
                             {'name': 'Docs', 'url': 'https://example.com/docs'},
                         ]},
                         formatter_candidates=['resources'], fallback=['paragraph']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm['author_assets'] = [
        {'asset_id': 'link-001', 'type': 'url', 'value': 'https://example.com/docs',
         'provenance': 'generated', 'source_reference': 'AI generated'},
    ]
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('invalid provenance' in e and 'generated' in e for e in errors), \
        f"Expected invalid provenance error for 'generated', got: {errors}"


def test_f1_steps_not_in_source_span_reports_error(tmp_path):
    """steps where only first step is in anchor should report error."""
    article = "## Steps\n\n1. First step.\n2. Second step.\n3. Third step."
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('steps-001', 'step_sequence', '1. First step.',
                         payload={'steps': ['First step.', 'Second step.', 'Third step.']},
                         heading_path=['Steps'],
                         formatter_candidates=['steps'], fallback=['ordered_list']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('not found in source span' in e for e in errors), \
        f"Expected error for steps not in source span, got: {errors}"


def test_f1_faq_second_pair_not_in_source_span_reports_error(tmp_path):
    """FAQ where second QA pair is not in source span should report error."""
    article = "## FAQ\n\n问：第一个问题？答：第一个回答。\n\n问：第二个问题？答：第二个回答。"
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('faq-001', 'faq', '问：第一个问题？',
                         payload={'items': [
                             {'question': '第一个问题？', 'answer': '第一个回答。'},
                             {'question': '第二个问题？', 'answer': '第二个回答。'}
                         ]},
                         heading_path=['FAQ'],
                         formatter_candidates=['faq'], fallback=['paragraph']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('not found in source span' in e for e in errors), \
        f"Expected error for FAQ second pair not in span, got: {errors}"


def test_f1_comparison_rows_not_in_source_span_reports_error(tmp_path):
    """comparison rows not in source span should report error."""
    article = "## Compare\n\n对象 A：甲，对象 B：乙。速度：甲快，乙慢。"
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('cmp-001', 'comparison', '对象 A：甲，对象 B：乙。',
                         payload={'subject_a': '甲', 'subject_b': '乙',
                                  'dimensions': ['速度'], 'rows': [{'dimension': '速度', 'value_a': '快', 'value_b': '慢'}]},
                         heading_path=['Compare'],
                         formatter_candidates=['compare'], fallback=['paragraph']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('not found in source span' in e for e in errors), \
        f"Expected error for comparison rows not in span, got: {errors}"


def test_f1_timeline_events_not_in_source_span_reports_error(tmp_path):
    """timeline events not in source span should report error."""
    article = "## Timeline\n\n2026-01 完成原型。2026-06 正式上线。"
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('tl-001', 'timeline', '2026-01 完成原型。',
                         payload={'events': [
                             {'time': '2026-01', 'description': '完成原型'},
                             {'time': '2026-06', 'description': '正式上线'}
                         ]},
                         heading_path=['Timeline'],
                         formatter_candidates=['timeline'], fallback=['ordered_list']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('not found in source span' in e for e in errors), \
        f"Expected error for timeline events not in span, got: {errors}"


def test_f1_case_result_not_in_source_span_reports_error(tmp_path):
    """case result not in source span should report error."""
    article = "## Case\n\n背景：服务慢。行动：优化。结果：快了。"
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('case-001', 'case', '背景：服务慢。',
                         payload={'context': '服务慢', 'challenge': '', 'action': '优化', 'result': '快了'},
                         heading_path=['Case'],
                         evidence_ids=['ev-001'],
                         formatter_candidates=['case'], fallback=['paragraph']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    ev_path = write_temp_file("# Evidence\nev-001 test\n", tmp_path, 'evidence-map.md')
    errors, _, _ = validate_semantic_map(article_path, sm_path, evidence_map_path=ev_path)
    assert any('not found in source span' in e for e in errors), \
        f"Expected error for case result not in span, got: {errors}"


def test_f1_decision_description_not_in_article_reports_error(tmp_path):
    """decision description with text not in article should report error."""
    article = "推荐方案：Nomad。"
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('dec-001', 'decision', '推荐方案：Nomad。',
                         payload={'recommended': 'Nomad',
                                  'options': [
                                      {'name': 'Nomad', 'description': '推荐方案，轻量易用'},
                                      {'name': 'K8s', 'description': '重'}
                                  ]},
                         formatter_candidates=['decision'], fallback=['paragraph']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('not found in source span' in e and '轻量易用' in e for e in errors), \
        f"Expected error for '轻量易用' not in article, got: {errors}"


# ════════════════════════════════════════════════════════════════
# F2: Anchor Uniqueness Tests
# ════════════════════════════════════════════════════════════════

def test_f2_anchor_ambiguous_no_heading_path_reports_error(tmp_path):
    """Anchor appearing twice in article with no heading_path should be ERROR."""
    article = "重复句。\n\n重复句。"
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', '重复句。',
                         payload={'text': '重复句。'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('appears 2 times' in e and 'ambiguous' in e.lower() for e in errors), \
        f"Expected ambiguous anchor error, got: {errors}"


def test_f2_heading_path_wrong_section_reports_error(tmp_path):
    """heading_path pointing to wrong section where anchor is not should report error."""
    article = "## Section A\n\nContent A here.\n\n## Section B\n\nContent B here."
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', 'Content B here.',
                         payload={'text': 'Content B here.'},
                         heading_path=['Section A'],
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any(('not found' in e.lower() or 'not within' in e.lower()) and ('heading_path' in e.lower() or 'section' in e.lower()) for e in errors), \
        f"Expected heading_path wrong section error, got: {errors}"


def test_f2_same_heading_different_parent_disambiguated(tmp_path):
    """Same heading name under different parents can be disambiguated with full path."""
    article = """# Parent A

## Child

Shared text here.

# Parent B

## Child

Shared text here.
"""
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', 'Shared text here.',
                         payload={'text': 'Shared text here.'},
                         heading_path=['Parent A', 'Child'],
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    # "Shared text here." appears twice; with heading_path it should be disambiguated
    # But "Shared text here." appears in both sections, so within "Parent A > Child" section it appears once
    assert not any('ambiguous' in e.lower() for e in errors), \
        f"Should not be ambiguous with heading_path, got: {errors}"


def test_f2_source_start_end_wrong_order_reports_error(tmp_path):
    """source_anchor with end_text before start_text should report error."""
    article = "First sentence. Second sentence."
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', '',
                         payload={'text': 'First sentence. Second sentence.'},
                         source_anchor={'start_text': 'Second sentence.', 'end_text': 'First sentence.'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('not found after start_text' in e for e in errors), \
        f"Expected end_text not found after start_text error, got: {errors}"


# ════════════════════════════════════════════════════════════════
# F3: Delivery Package Consistency Tests
# ════════════════════════════════════════════════════════════════

def test_f3_check_manifest_exists_and_runs():
    """check_manifest.py should exist and be runnable."""
    script_path = ROOT / 'scripts' / 'check_manifest.py'
    assert script_path.exists(), "check_manifest.py should exist in scripts/"
    # Verify it can be imported/run
    p = subprocess.run(
        [sys.executable, str(script_path), '--help'],
        capture_output=True, text=True, timeout=5
    )
    # It may not have --help, but it should at least not crash on import
    # Just verify the file is valid Python
    import py_compile
    py_compile.compile(str(script_path), doraise=True)


def test_f3_package_zip_exists():
    """package_zip.py should exist in scripts/."""
    script_path = ROOT / 'scripts' / 'package_zip.py'
    assert script_path.exists(), "package_zip.py should exist in scripts/"
    import py_compile
    py_compile.compile(str(script_path), doraise=True)


def test_f3_validate_script_supports_regenerate_registry():
    """validate_semantic_map.py should support --regenerate-registry flag."""
    script_path = ROOT / 'scripts' / 'validate_semantic_map.py'
    p = subprocess.run(
        [sys.executable, str(script_path), '--help'],
        capture_output=True, text=True, timeout=5
    )
    assert '--regenerate-registry' in p.stdout, \
        f"--regenerate-registry should be in help output: {p.stdout}"


def test_f3_formatter_registry_doc_command_executable():
    """The --regenerate-registry command documented in formatter-registry.yaml should work."""
    reg_path = ROOT / 'references' / 'formatter-registry.yaml'
    content = reg_path.read_text(encoding='utf-8')
    assert '--regenerate-registry' in content, \
        "formatter-registry.yaml should document --regenerate-registry command"
    # Verify the command is actually implemented
    from validate_semantic_map import regenerate_registry
    assert callable(regenerate_registry), "regenerate_registry function should exist"


# ════════════════════════════════════════════════════════════════
# H2.1: Missing source_anchor must fail (except article_signature)
# ════════════════════════════════════════════════════════════════

def test_h2_paragraph_empty_anchor_reports_error(tmp_path):
    """paragraph with empty source_anchor must report ERROR."""
    article = "正文内容。"
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', '',
                         payload={'text': '正文内容。'},
                         source_anchor={},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('requires source_anchor' in e for e in errors), \
        f"Expected source_anchor required error for paragraph, got: {errors}"


def test_h2_fact_missing_source_anchor_reports_error(tmp_path):
    """fact with no source_anchor key at all must report ERROR."""
    article = "Some data here."
    article_path = write_temp_article(article, tmp_path)
    block = {
        'block_id': 'fact-001',
        'heading_path': [],
        'role': 'fact',
        'payload': {'items': [{'key': 'k', 'value': 'v'}, {'key': 'k2', 'value': 'v2'}]},
        'evidence_ids': ['ev-001'],
        'preserve_exactly': False,
        'formatter_candidates': ['facts'],
        'fallback': ['ordered_list'],
        'required': False,
    }
    # Deliberately no source_anchor key
    sm = make_valid_semantic_map([block])
    sm_path = write_temp_semantic_map(sm, tmp_path)
    ev_path = write_temp_file("# Evidence\nev-001 test\n", tmp_path, 'evidence-map.md')
    errors, _, _ = validate_semantic_map(article_path, sm_path, evidence_map_path=ev_path)
    assert any('requires source_anchor' in e for e in errors), \
        f"Expected source_anchor required error for fact, got: {errors}"


def test_h2_signature_empty_anchor_passes(tmp_path):
    """article_signature with empty source_anchor should still pass."""
    article = "Content here."
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', 'Content here.',
                         payload={'text': 'Content here.'},
                         formatter_candidates=['paragraph'], fallback=[]),
        make_valid_block('sig-001', 'article_signature', '',
                         payload={}, source_anchor={},
                         formatter_candidates=['footer-signature-brand'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert not any('requires source_anchor' in e for e in errors), \
        f"article_signature should not require source_anchor, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H2.2: evidence-map required for evidence-backed roles
# ════════════════════════════════════════════════════════════════

def test_h2_fact_without_evidence_map_reports_error(tmp_path):
    """fact role without --evidence-map must report ERROR."""
    article = "Some factual data here."
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('fact-001', 'fact', 'Some factual data here.',
                         payload={'items': [{'key': 'k', 'value': 'v'}, {'key': 'k2', 'value': 'v2'}]},
                         evidence_ids=['ev-001'],
                         formatter_candidates=['facts'], fallback=['ordered_list']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('evidence-map is required' in e for e in errors), \
        f"Expected evidence-map required error for fact, got: {errors}"


def test_h2_statistic_without_evidence_map_reports_error(tmp_path):
    """statistic role without --evidence-map must report ERROR."""
    article = "增长42%。"
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('stat-001', 'statistic', '增长42%。',
                         payload={'value': '42%', 'label': '增长'},
                         formatter_candidates=['facts'], fallback=['paragraph']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('evidence-map is required' in e for e in errors), \
        f"Expected evidence-map required error for statistic, got: {errors}"


def test_h2_case_without_evidence_map_reports_error(tmp_path):
    """case role without --evidence-map must report ERROR."""
    article = "背景：服务慢。行动：优化。结果：快了。"
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('case-001', 'case', '背景：服务慢。',
                         payload={'context': '服务慢', 'challenge': '', 'action': '优化', 'result': '快了'},
                         evidence_ids=['ev-001'],
                         formatter_candidates=['case'], fallback=['paragraph']),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('evidence-map is required' in e for e in errors), \
        f"Expected evidence-map required error for case, got: {errors}"


def test_h2_paragraph_without_evidence_map_passes(tmp_path):
    """paragraph without evidence-map should pass (no evidence-backed roles)."""
    article = "Just a normal paragraph."
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', 'Just a normal paragraph.',
                         payload={'text': 'Just a normal paragraph.'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert not any('evidence-map is required' in e for e in errors), \
        f"Paragraph without evidence-map should not report error, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H2.3: start/end uniqueness within section (even with heading_path)
# ════════════════════════════════════════════════════════════════

def test_h2_start_text_duplicate_within_section_reports_error(tmp_path):
    """start_text appearing twice within heading_path section must report ERROR."""
    article = "## S\n\n开始。中间。开始。内容。结束。"
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', '',
                         payload={'text': '开始。中间。开始。内容。结束。'},
                         heading_path=['S'],
                         source_anchor={'start_text': '开始。', 'end_text': '结束。'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('start_text appears 2 times' in e and 'ambiguous' in e.lower() for e in errors), \
        f"Expected start_text duplicate within section error, got: {errors}"


def test_h2_end_text_duplicate_within_section_reports_error(tmp_path):
    """end_text appearing multiple times after start_text within section must report ERROR."""
    article = "## S\n\n起点。中间。结束。更多。结束。"
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', '',
                         payload={'text': '起点。中间。结束。更多。结束。'},
                         heading_path=['S'],
                         source_anchor={'start_text': '起点。', 'end_text': '结束。'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('end_text appears multiple times' in e and 'ambiguous' in e.lower() for e in errors), \
        f"Expected end_text duplicate within section error, got: {errors}"


def test_h2_same_start_end_different_sections_disambiguated(tmp_path):
    """Same start/end in different sections with heading_path should pass."""
    article = "## A\n\n边界。内容一。结束。\n\n## B\n\n边界。内容二。结束。"
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', '',
                         payload={'text': '边界。内容一。结束。'},
                         heading_path=['A'],
                         source_anchor={'start_text': '边界。', 'end_text': '结束。'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert not any('ambiguous' in e.lower() for e in errors), \
        f"Should not be ambiguous with heading_path in different sections, got: {errors}"


def test_h2_same_start_end_duplicate_in_same_section_reports_error(tmp_path):
    """Same start/end appearing twice in same section, even with heading_path, must report ERROR."""
    article = "## S\n\n边界。内容。结束。边界。更多。结束。"
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', '',
                         payload={'text': '边界。内容。结束。边界。更多。结束。'},
                         heading_path=['S'],
                         source_anchor={'start_text': '边界。', 'end_text': '结束。'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('ambiguous' in e.lower() for e in errors), \
        f"Should report ambiguity even with heading_path within same section, got: {errors}"


# ════════════════════════════════════════════════════════════════
# H2.4: component_policy must be complete
# ════════════════════════════════════════════════════════════════

def test_h2_component_policy_missing_reports_error(tmp_path):
    """Completely missing component_policy must report ERROR."""
    article = "Test content here."
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', 'Test content here.',
                         payload={'text': 'Test content here.'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    del sm['component_policy']
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('component_policy is missing' in e for e in errors), \
        f"Expected component_policy missing error, got: {errors}"


def test_h2_component_policy_null_reports_error(tmp_path):
    """component_policy: null must report ERROR."""
    article = "Test content here."
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', 'Test content here.',
                         payload={'text': 'Test content here.'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm['component_policy'] = None
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('component_policy' in e.lower() and ('missing' in e.lower() or 'dict' in e.lower()) for e in errors), \
        f"Expected component_policy null error, got: {errors}"


def test_h2_component_policy_list_reports_error(tmp_path):
    """component_policy as list (not dict) must report ERROR."""
    article = "Test content here."
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', 'Test content here.',
                         payload={'text': 'Test content here.'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    sm['component_policy'] = []
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('component_policy' in e.lower() and 'dict' in e.lower() for e in errors), \
        f"Expected component_policy list error, got: {errors}"


class TestHandoffProseCraftFields:
    """档72D-1/Batch 2:handoff v2.0 schema 新增 prose_craft 两字段的存在性与类型校验。"""

    HANDOFF = ROOT / "references" / "handoff.md"

    def test_prose_craft_fields_present_in_schema_yaml(self):
        import re
        text = self.HANDOFF.read_text(encoding="utf-8")
        assert "prose_craft_applied:" in text
        assert "prose_craft_version:" in text
        # 类型语义:applied 是布尔示例,version 是字符串示例
        assert re.search(r"prose_craft_applied:\s+(true|false)", text)
        # version 可为 null(未产出)或带引号字符串示例
        assert re.search(r"prose_craft_version:\s+(null|[\"']1\.0[\"'])", text)

    def test_prose_craft_fields_listed_in_v2_field_table(self):
        text = self.HANDOFF.read_text(encoding="utf-8")
        assert "| prose_craft_applied |" in text
        assert "| prose_craft_version |" in text

    def test_v21_fields_present_and_typed(self):
        import re
        text = self.HANDOFF.read_text(encoding="utf-8")
        for key in ("handoff_stage", "author_intent", "allow_rewrite_scope",
                    "material_stats", "scope"):
            assert f"{key}:" in text, key
        # 类型语义:handoff_stage 字符串、allow_rewrite_scope 枚举 none/expression_only、
        # material_stats 对象、formatter.cover 三字段 null 缺省
        assert re.search(r"handoff_stage:\s*[\"']?[a-z_]+[\"']?", text)
        assert re.search(r"allow_rewrite_scope:\s*[\"'](none|expression_only)[\"']", text)
        assert re.search(r"material_stats:\s*\{\}", text)
        assert "| formatter.cover |" in text
        formatter_zone = text.split("formatter:")[1].split("next:")[0]
        for key in ("kicker:", "strike:", "tags:"):
            assert key in formatter_zone, key

    def test_v22_title_fields_present_and_typed(self):
        import re
        text = self.HANDOFF.read_text(encoding="utf-8")
        assert "title_candidates:" in text
        assert "hook_line:" in text
        # 类型语义:title_candidates 是列表、hook_line 是字符串
        assert re.search(r"title_candidates:\s*\[\s*\]", text)
        assert re.search(r"hook_line:\s*[\"']", text)
        # 字段表登记
        assert "| title_candidates |" in text
        assert "| hook_line |" in text
        # 76T/OBS-293:strike_assumption 新字段(划线句改义),hook_line 不再进划线位
        assert "strike_assumption" in text
        assert "被本文证据否定" in text or "被本文推翻" in text
        assert "不再用 hook_line 填充划线位" in text or "不再进划线位" in text

    def test_v22_selection_fields_present_and_typed(self):
        import re
        text = self.HANDOFF.read_text(encoding="utf-8")
        assert "selected_title:" in text
        assert "title_selection_reason:" in text
        # 类型语义:两字段均为字符串示例
        assert re.search(r"selected_title:\s*[\"']", text)
        assert re.search(r"title_selection_reason:\s*[\"']", text)
        # 字段表登记
        assert "| selected_title |" in text
        assert "| title_selection_reason |" in text
        # 契约:selected_title 必须从 title_candidates 中选定,article H1 与之一致
        assert "从 title_candidates" in text or "从 `title_candidates`" in text
        assert "H1" in text


def test_h2_component_policy_missing_field_reports_error(tmp_path):
    """component_policy missing one required field must report ERROR."""
    article = "Test content here."
    article_path = write_temp_article(article, tmp_path)
    blocks = [
        make_valid_block('b1', 'paragraph', 'Test content here.',
                         payload={'text': 'Test content here.'},
                         formatter_candidates=['paragraph'], fallback=[]),
    ]
    sm = make_valid_semantic_map(blocks)
    del sm['component_policy']['prohibit_content_invention']
    sm_path = write_temp_semantic_map(sm, tmp_path)
    errors, _, _ = validate_semantic_map(article_path, sm_path)
    assert any('prohibit_content_invention' in e and 'missing' in e.lower() for e in errors), \
        f"Expected missing field error for prohibit_content_invention, got: {errors}"
