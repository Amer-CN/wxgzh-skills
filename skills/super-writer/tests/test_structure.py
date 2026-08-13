from pathlib import Path
import subprocess, sys, json, tempfile

ROOT = Path(__file__).resolve().parents[1]

def test_validator():
    p = subprocess.run([sys.executable, str(ROOT/'scripts/validate_skill.py')], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr

def test_boundaries_present():
    skill = (ROOT/'SKILL.md').read_text(encoding='utf-8')
    for term in ['不得编造', '去 AI 味', 'Phase 3', 'P0', 'handoff']:
        assert term in skill

def test_material_readiness_gate():
    """素材充分性检查门禁存在"""
    skill = (ROOT/'SKILL.md').read_text(encoding='utf-8')
    assert 'Phase 1.5' in skill
    assert 'material_readiness' in skill
    research = (ROOT/'references/research-evidence.md').read_text(encoding='utf-8')
    assert 'material_readiness' in research
    assert 'allowed_output' in research
    assert 'required_actions' in research

def test_two_layer_topic_scoring():
    """两层选题评分存在"""
    core = (ROOT/'references/core-finding.md').read_text(encoding='utf-8')
    assert 'HKR' in core
    assert 'UEPT' in core
    assert 'Unique' in core
    assert 'Evidence' in core
    assert 'Personal' in core
    assert 'Timely' in core
    assert 'decision' in core

def test_research_stop_conditions():
    """研究停止条件三层结构存在"""
    research = (ROOT/'references/research-evidence.md').read_text(encoding='utf-8')
    assert '研究停止条件' in research
    assert '必须满足' in research
    assert '尽量满足' in research
    assert '无法满足时退出' in research
    assert 'research_limited' in research
    assert '个人经历型' in research
    assert '全部满足时即可结束研究阶段' not in research

def test_exclusion_analysis():
    """排斥分析存在"""
    research = (ROOT/'references/research-evidence.md').read_text(encoding='utf-8')
    assert '排斥分析' in research

def test_pain_point_depth():
    """痛点深度检查存在"""
    research = (ROOT/'references/research-evidence.md').read_text(encoding='utf-8')
    assert '痛点深度' in research
    assert 'Layer 3' in research
    assert '不得编造' in research

def test_four_shovels():
    """四铲深化存在"""
    core = (ROOT/'references/core-finding.md').read_text(encoding='utf-8')
    assert '四铲' in core
    assert '反转' in core
    assert '追问前提' in core
    assert '追问情绪' in core
    assert '翻转定义' in core

def test_evidence_map_enhanced():
    """证据地图增强字段存在"""
    evidence = (ROOT/'templates/evidence-map.md').read_text(encoding='utf-8')
    assert 'Reader Tension Statement' in evidence
    assert '来源日期' in evidence
    assert '是否原始来源' in evidence
    assert '支持/反对' in evidence
    assert '适用边界' in evidence
    assert '目标章节' in evidence
    assert '核验状态' in evidence
    assert '使用状态' in evidence

def test_voice_profile_layered():
    """Voice Profile 分层结构存在"""
    vp = (ROOT/'references/voice-profile.md').read_text(encoding='utf-8')
    assert '核心 8 维' in vp
    assert '可选 4 维' in vp
    assert 'confidence' in vp
    assert 'source_count' in vp
    assert 'scope' in vp
    assert 'conflict' in vp.lower() or '冲突' in vp
    yaml = (ROOT/'profiles/voice-profile.example.yaml').read_text(encoding='utf-8')
    assert 'dimensions' in yaml
    assert 'optional_dimensions' in yaml
    assert 'confidence' in yaml
    assert 'source_count' in yaml

def test_editorial_review_enhanced():
    """内容审稿增强检查项存在"""
    review = (ROOT/'references/editorial-review.md').read_text(encoding='utf-8')
    assert 'claim→mechanism' in review
    assert 'A vs B' in review or '结构化对比' in review
    assert '示例去重' in review
    assert 'So what' in review
    assert 'Perspective Audit' in review or '视角审计' in review

def test_edit_learning_config():
    """编辑学习配置和双向置信度存在"""
    el = (ROOT/'references/edit-learning.md').read_text(encoding='utf-8')
    assert 'analyze_automatically' in el
    assert 'persist_automatically' in el
    assert 'require_confirmation' in el
    assert '禁止静默写入' in el or '禁止静默修改' in el
    assert 'key 复用' in el or 'key复用' in el
    assert 'confidence' in el
    assert '双向调整' in el
    assert 'support_count' in el
    assert 'conflict_count' in el
    assert 'status' in el
    assert 'active' in el
    assert 'revoked' in el
    assert 'stale' in el
    assert '当前指令优先' in el
    assert 'Reviewer' in el
    assert 'relation' in el

def test_edit_rules_enhanced():
    """编辑规则增强字段存在（含双向置信度）"""
    rules = (ROOT/'profiles/edit-rules.example.yaml').read_text(encoding='utf-8')
    assert 'key' in rules
    assert 'support_count' in rules
    assert 'conflict_count' in rules
    assert 'confidence' in rules
    assert 'status' in rules
    assert 'last_supported_at' in rules
    assert 'last_conflicted_at' in rules
    assert 'active' in rules

def test_editor_report_json():
    """评分器 JSON 输出模板存在"""
    report = (ROOT/'templates/editor-report.md').read_text(encoding='utf-8')
    assert 'JSON' in report
    assert 'overall_score' in report
    assert 'delivery_status' in report
    assert 'strengths' in report
    assert 'improvements' in report
    assert 'checklist' in report

def test_failure_exit_mechanism():
    """失败退出机制存在（含 research_limited）"""
    workflow = (ROOT/'references/workflow.md').read_text(encoding='utf-8')
    assert '失败退出' in workflow
    assert 'core_broken' in workflow
    assert 'evidence_conflict' in workflow
    assert 'unsuitable_topic' in workflow
    assert 'review_blocked' in workflow
    assert 'research_limited' in workflow
    skill = (ROOT/'SKILL.md').read_text(encoding='utf-8')
    assert '失败退出' in skill
    assert 'core_broken' in skill
    assert 'research_limited' in skill

def test_acceptance_criteria():
    """验收标准存在"""
    skill = (ROOT/'SKILL.md').read_text(encoding='utf-8')
    assert 'Actionable endpoint' in skill
    assert 'Evidence density' in skill
    assert 'Research-dependent' in skill
    assert 'Tension' in skill

def test_calibration_architecture():
    """评分器校准架构存在"""
    calibrate = ROOT / 'scripts' / 'calibrate_scorer.py'
    assert calibrate.exists()
    test_cal = ROOT / 'tests' / 'test_calibration.py'
    assert test_cal.exists()
    labels = ROOT / 'tests' / 'fixtures' / 'labels.example.json'
    assert labels.exists()
    samples_dir = ROOT / 'tests' / 'fixtures' / 'samples'
    assert samples_dir.exists()
    blind_dir = ROOT / 'tests' / 'fixtures' / 'blind'
    assert blind_dir.exists()

def test_no_preset_persona():
    """确认不包含预设 persona"""
    vp = (ROOT/'references/voice-profile.md').read_text(encoding='utf-8')
    assert 'cold-analyst' not in vp
    assert 'humor-storyteller' not in vp
    assert 'midnight-friend' not in vp

def test_no_seo():
    """确认不包含 SEO 机制"""
    skill = (ROOT/'SKILL.md').read_text(encoding='utf-8')
    assert 'SEO' not in skill
    assert '关键词排名' not in skill

def test_no_ai_flavor_removal():
    """确认不包含去 AI 味硬阈值"""
    review = (ROOT/'references/editorial-review.md').read_text(encoding='utf-8')
    assert '禁用词' not in review
    assert 'burstiness' not in review.lower()

def test_analogy_crack_handling():
    """承重类比裂口四类判断存在"""
    structure = (ROOT/'references/structure-design.md').read_text(encoding='utf-8')
    assert '类比裂口' in structure
    assert '裂开' in structure
    assert '裂口揭示结论边界' in structure
    assert '裂口只是局部不完全映射' in structure
    assert '裂口破坏核心因果' in structure
    assert '裂口会误导读者' in structure
    assert '必须弃用类比' in structure
    assert '判断步骤' in structure

def test_handoff_enhanced():
    """下游交接增强存在"""
    handoff = (ROOT/'references/handoff.md').read_text(encoding='utf-8')
    assert 'humanizer' in handoff
    assert 'formatter' in handoff
    assert 'publisher' in handoff
    assert 'trigger' in handoff

def test_burstiness_non_blocking():
    """Burstiness 诊断为非阻塞"""
    score_script = (ROOT/'scripts/score_article.py').read_text(encoding='utf-8')
    assert 'compute_burstiness' in score_script
    assert 'blocking' in score_script
    assert 'handoff_to' in score_script
    assert 'humanizer' in score_script
    assert '30%' not in score_script

def test_burstiness_output_format():
    """Burstiness 输出格式正确"""
    test_article = "这是一个测试句子，长度差不多。这也是一个测试句子，长度差不多。还有一个测试句子，长度差不多。再来一个测试句子，长度差不多。最后是测试句子，长度差不多。\n\n这是第二段内容，长度也很接近。这也是第二段内容，长度也很接近。这是第三句内容，长度也很接近。\n\n这是第三段内容，长度也差不多。这也是第三段内容，长度也差不多。这是第三段最后一句。"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
        f.write(test_article)
        f.flush()
        temp_path = f.name
    try:
        p = subprocess.run(
            [sys.executable, str(ROOT/'scripts/score_article.py'), temp_path, '--json'],
            capture_output=True, text=True
        )
        assert p.returncode == 0, p.stderr
        result = json.loads(p.stdout)
        assert 'burstiness' in result
        burst = result['burstiness']
        assert 'risk' in burst
        assert burst['blocking'] == False
        assert burst['handoff_to'] == 'humanizer'
        assert 'evidence' in burst
        assert isinstance(burst['evidence'], list)
    finally:
        Path(temp_path).unlink()


# ── Edit learning behavioral tests ──

def test_edit_learning_diff_generation():
    """Python generates structured diffs from draft→final."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import extract_changes
    draft = "这是一个反问句？这是另一个反问句？这是陈述句。"
    final = "这是陈述句。这是新增的句子。"
    changes = extract_changes(draft, final)
    assert len(changes) > 0
    assert changes[0]["type"] in ("deletion", "replacement", "insertion")
    assert "removed" in changes[0]
    assert "added" in changes[0]


def test_edit_learning_reviewer_judgment_schema():
    """Reviewer judgments are validated for correct schema."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import validate_reviewer_judgments
    changes = [{"type": "replacement", "removed": "a", "added": "b", "removed_len": 1, "added_len": 1, "before_position": 0, "after_position": 0}]
    judgments = [{"change_index": 0, "relation": "new", "key": "test_key", "instruction": "test instruction", "scope": "global", "evidence": "test evidence", "confidence": 1, "observed_at": "2026-07-14", "source_id": "pair-test"}]
    validated = validate_reviewer_judgments(judgments, changes)
    assert len(validated) == 1
    assert validated[0]["relation"] == "new"


def test_edit_learning_invalid_relation_rejected():
    """Invalid relation values are rejected."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import validate_reviewer_judgments
    changes = [{"type": "replacement", "removed": "a", "added": "b", "removed_len": 1, "added_len": 1, "before_position": 0, "after_position": 0}]
    judgments = [{"change_index": 0, "relation": "maybe", "key": "test", "instruction": "test", "scope": "global", "evidence": "test", "confidence": 1}]
    try:
        validate_reviewer_judgments(judgments, changes)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_edit_learning_end_to_end_new_rule():
    """End-to-end: draft→final→reviewer judgments→new rule created."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import extract_changes, validate_reviewer_judgments, generate_updated_rules
    draft_path = ROOT / 'tests' / 'fixtures' / 'edit-pairs' / 'pair-01' / 'draft.md'
    final_path = ROOT / 'tests' / 'fixtures' / 'edit-pairs' / 'pair-01' / 'final.md'
    judgments_path = ROOT / 'tests' / 'fixtures' / 'edit-pairs' / 'pair-01' / 'judgments.json'
    assert draft_path.exists(), f"Draft missing: {draft_path}"
    assert final_path.exists(), f"Final missing: {final_path}"
    assert judgments_path.exists(), f"Judgments missing: {judgments_path}"

    draft = draft_path.read_text(encoding='utf-8')
    final = final_path.read_text(encoding='utf-8')
    raw_judgments = json.loads(judgments_path.read_text(encoding='utf-8'))

    changes = extract_changes(draft, final)
    judgments = validate_reviewer_judgments(raw_judgments, changes)
    result = generate_updated_rules(judgments, None)

    rules = result['rules']
    assert len(rules) >= 2  # At least reduce_questions and concrete_before_abstract
    keys = [r['key'] for r in rules]
    assert 'reduce_questions' in keys
    assert 'concrete_before_abstract' in keys
    # New rules should have support_count=1
    for r in rules:
        assert r['support_count'] == 1
        assert r['conflict_count'] == 0
        assert r['status'] == 'active'


def test_edit_learning_end_to_end_conflict():
    """End-to-end: second pair conflicts with rule from first pair."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import extract_changes, validate_reviewer_judgments, generate_updated_rules
    import tempfile, yaml

    # Step 1: Process pair-01 to create initial rules
    draft1 = (ROOT / 'tests' / 'fixtures' / 'edit-pairs' / 'pair-01' / 'draft.md').read_text(encoding='utf-8')
    final1 = (ROOT / 'tests' / 'fixtures' / 'edit-pairs' / 'pair-01' / 'final.md').read_text(encoding='utf-8')
    judgments1_raw = json.loads((ROOT / 'tests' / 'fixtures' / 'edit-pairs' / 'pair-01' / 'judgments.json').read_text(encoding='utf-8'))
    changes1 = extract_changes(draft1, final1)
    judgments1 = validate_reviewer_judgments(judgments1_raw, changes1)
    initial_rules = generate_updated_rules(judgments1, None)

    # Save initial rules to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        yaml.dump(initial_rules, f)
        f.flush()
        rules_path = f.name

    try:
        # Step 2: Process pair-02 which has a conflict with reduce_questions
        draft2 = (ROOT / 'tests' / 'fixtures' / 'edit-pairs' / 'pair-02' / 'draft.md').read_text(encoding='utf-8')
        final2 = (ROOT / 'tests' / 'fixtures' / 'edit-pairs' / 'pair-02' / 'final.md').read_text(encoding='utf-8')
        judgments2_raw = json.loads((ROOT / 'tests' / 'fixtures' / 'edit-pairs' / 'pair-02' / 'judgments.json').read_text(encoding='utf-8'))
        changes2 = extract_changes(draft2, final2)
        # pair-02 has a conflict with 'reduce_questions' from pair-01
        existing_keys = {'reduce_questions', 'concrete_before_abstract'}
        judgments2 = validate_reviewer_judgments(judgments2_raw, changes2, existing_keys)

        # Generate updated rules with conflict
        updated = generate_updated_rules(judgments2, rules_path)
        rules = updated['rules']

        # Find the reduce_questions rule - should have conflict_count=1
        rq_rule = next(r for r in rules if r.get('key') == 'reduce_questions')
        assert rq_rule['conflict_count'] == 1, f"Expected conflict_count=1, got {rq_rule['conflict_count']}"
        assert rq_rule['confidence'] == 0, f"Expected confidence=0 (was 1, -1 for conflict), got {rq_rule['confidence']}"
        assert rq_rule['_action'] == 'update'
    finally:
        Path(rules_path).unlink()


def test_edit_learning_no_relation_no_confidence_change():
    """Without reviewer judgments, confidence is never changed."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import generate_updated_rules
    import tempfile, yaml

    existing = {
        'version': 2,
        'rules': [{
            'key': 'reduce_questions',
            'instruction': '减少反问',
            'scope': 'global',
            'confidence': 3,
            'support_count': 3,
            'conflict_count': 0,
            'status': 'active',
            'sources': [],
            'exceptions': [],
            'last_supported_at': '',
            'last_conflicted_at': '',
            'confirmed': True,
        }]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        yaml.dump(existing, f)
        f.flush()
        rules_path = f.name

    try:
        # Empty judgments - no relation provided
        result = generate_updated_rules([], rules_path)
        rule = result['rules'][0]
        assert rule['confidence'] == 3  # Unchanged
        assert rule['support_count'] == 3  # Unchanged
        assert rule['conflict_count'] == 0  # Unchanged
        assert rule['_action'] == 'keep'
    finally:
        Path(rules_path).unlink()


def test_edit_learning_low_confidence_not_deleted():
    """Low confidence rules are marked stale/ignored, not deleted."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import generate_updated_rules
    import tempfile, yaml

    existing = {
        'version': 2,
        'rules': [{
            'key': 'old_rule',
            'instruction': '旧规则',
            'scope': 'global',
            'confidence': 0,
            'support_count': 1,
            'conflict_count': 2,
            'status': 'stale',
            'sources': ['d1'],
            'exceptions': [],
            'last_supported_at': '',
            'last_conflicted_at': '',
            'confirmed': True,
        }]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        yaml.dump(existing, f)
        f.flush()
        rules_path = f.name

    try:
        result = generate_updated_rules([], rules_path)
        # Rule should still exist, not deleted
        assert len(result['rules']) == 1
        rule = result['rules'][0]
        assert rule['status'] in ('stale', 'ignored')
        assert rule['_action'] == 'keep'
    finally:
        Path(rules_path).unlink()


def test_edit_learning_cli_diff_mode():
    """CLI without reviewer judgments generates diff report only."""
    draft_path = ROOT / 'tests' / 'fixtures' / 'edit-pairs' / 'pair-01' / 'draft.md'
    final_path = ROOT / 'tests' / 'fixtures' / 'edit-pairs' / 'pair-01' / 'final.md'
    output_path = ROOT / 'tests' / 'fixtures' / 'edit-test-output.json'
    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'learn_edits.py'),
         str(draft_path), str(final_path), '-o', str(output_path)],
        capture_output=True, text=True
    )
    assert p.returncode == 0, p.stderr
    result = json.loads(output_path.read_text(encoding='utf-8'))
    assert 'changes' in result
    assert len(result['changes']) > 0
    assert result['reviewer_judgments'] is None
    assert 'Reviewer' in result['instruction']
    output_path.unlink()


def test_edit_learning_cli_with_judgments():
    """CLI with reviewer judgments generates updated rules preview."""
    draft_path = ROOT / 'tests' / 'fixtures' / 'edit-pairs' / 'pair-01' / 'draft.md'
    final_path = ROOT / 'tests' / 'fixtures' / 'edit-pairs' / 'pair-01' / 'final.md'
    judgments_path = ROOT / 'tests' / 'fixtures' / 'edit-pairs' / 'pair-01' / 'judgments.json'
    output_path = ROOT / 'tests' / 'fixtures' / 'edit-test-output.json'
    p = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'learn_edits.py'),
         str(draft_path), str(final_path),
         '--reviewer-judgments', str(judgments_path),
         '--generate-update',
         '-o', str(output_path)],
        capture_output=True, text=True
    )
    assert p.returncode == 0, p.stderr
    result = json.loads(output_path.read_text(encoding='utf-8'))
    assert result['reviewer_judgments'] is not None
    assert len(result['reviewer_judgments']) == 3
    assert 'updated_rules_preview' in result
    assert len(result['updated_rules_preview']['rules']) >= 2
    output_path.unlink()


def test_skill_md_no_typo_bengchang():
    """SKILL.md should not contain 崩場 (should be 崩塌)."""
    skill = (ROOT/'SKILL.md').read_text(encoding='utf-8')
    assert '崩場' not in skill, "SKILL.md contains typo 崩場, should be 崩塌"
    assert '崩塌' in skill


def test_version_date_correct():
    """VERSION file should have 2026 date, not 2025."""
    version = (ROOT/'VERSION').read_text(encoding='utf-8')
    assert '2026-07-14' in version
    assert '2025' not in version


def test_manifest_posix_paths():
    """MANIFEST.sha256 should use POSIX paths (forward slashes)."""
    manifest_path = ROOT / 'MANIFEST.sha256'
    if not manifest_path.exists():
        return  # Manifest is generated at packaging time
    content = manifest_path.read_text(encoding='utf-8')
    # No backslashes in paths
    lines = [l for l in content.strip().split('\n') if l.strip()]
    for line in lines:
        parts = line.split('  ', 1)
        if len(parts) == 2:
            path = parts[1]
            assert '\\' not in path, f"Manifest contains backslash path: {path}"


# ── R3: Reviewer judgment strict validation ──

def test_r3_new_without_key_rejected():
    """R3: new relation without key must be rejected."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import validate_reviewer_judgments
    changes = [{"type": "replacement", "removed": "a", "added": "b", "removed_len": 1, "added_len": 1, "before_position": 0, "after_position": 0}]
    judgments = [{"change_index": 0, "relation": "new", "instruction": "test", "evidence": "test", "confidence": 1}]
    try:
        validate_reviewer_judgments(judgments, changes)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "key" in str(e).lower()


def test_r3_new_without_instruction_rejected():
    """R3: new relation without instruction must be rejected."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import validate_reviewer_judgments
    changes = [{"type": "replacement", "removed": "a", "added": "b", "removed_len": 1, "added_len": 1, "before_position": 0, "after_position": 0}]
    judgments = [{"change_index": 0, "relation": "new", "key": "test_key", "instruction": "", "evidence": "test", "confidence": 1}]
    try:
        validate_reviewer_judgments(judgments, changes)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "instruction" in str(e).lower()


def test_r3_new_without_evidence_rejected():
    """R3: new relation without evidence must be rejected."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import validate_reviewer_judgments
    changes = [{"type": "replacement", "removed": "a", "added": "b", "removed_len": 1, "added_len": 1, "before_position": 0, "after_position": 0}]
    judgments = [{"change_index": 0, "relation": "new", "key": "test_key", "instruction": "test", "evidence": "", "confidence": 1}]
    try:
        validate_reviewer_judgments(judgments, changes)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "evidence" in str(e).lower()


def test_r3_support_nonexistent_key_rejected():
    """R3: support/conflict with non-existent key must be rejected."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import validate_reviewer_judgments
    changes = [{"type": "replacement", "removed": "a", "added": "b", "removed_len": 1, "added_len": 1, "before_position": 0, "after_position": 0}]
    judgments = [{"change_index": 0, "relation": "support", "key": "nonexistent", "evidence": "test", "confidence": 1}]
    existing_keys = {"real_key"}
    try:
        validate_reviewer_judgments(judgments, changes, existing_keys)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "nonexistent" in str(e) or "non-existent" in str(e)


def test_r3_invalid_confidence_rejected():
    """R3: confidence outside [1,5] must be rejected."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import validate_reviewer_judgments
    changes = [{"type": "replacement", "removed": "a", "added": "b", "removed_len": 1, "added_len": 1, "before_position": 0, "after_position": 0}]
    judgments = [{"change_index": 0, "relation": "one_off", "evidence": "test", "confidence": 10}]
    try:
        validate_reviewer_judgments(judgments, changes)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "confidence" in str(e).lower()


def test_r3_duplicate_change_index_rejected():
    """R3: duplicate change_index must be rejected."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import validate_reviewer_judgments
    changes = [
        {"type": "replacement", "removed": "a", "added": "b", "removed_len": 1, "added_len": 1, "before_position": 0, "after_position": 0},
        {"type": "insertion", "removed": "", "added": "c", "removed_len": 0, "added_len": 1, "before_position": 0, "after_position": 0},
    ]
    judgments = [
        {"change_index": 0, "relation": "one_off", "evidence": "test1", "confidence": 1},
        {"change_index": 0, "relation": "one_off", "evidence": "test2", "confidence": 1},
    ]
    try:
        validate_reviewer_judgments(judgments, changes)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "duplicate" in str(e).lower()


# ── R4: Stable key generation ──

def test_r4_stable_key_deterministic():
    """R4: _generate_stable_key produces same key across calls."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import _generate_stable_key
    key1 = _generate_stable_key("减少反问句")
    key2 = _generate_stable_key("减少反问句")
    assert key1 == key2, f"Keys should be identical: {key1} vs {key2}"
    assert key1.startswith("auto_"), f"Key should start with auto_: {key1}"


def test_r4_stable_key_different_instructions():
    """R4: Different instructions produce different keys."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import _generate_stable_key
    key1 = _generate_stable_key("减少反问句")
    key2 = _generate_stable_key("增加具体案例")
    assert key1 != key2


# ── R5: Time/evidence field separation ──

def test_r5_time_field_writes_date_not_evidence():
    """R5: last_supported_at should contain observed_at date, not evidence text."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import generate_updated_rules
    import tempfile, yaml

    existing = {
        'version': 2,
        'rules': [{
            'key': 'test_rule',
            'instruction': '测试规则',
            'scope': 'global',
            'confidence': 2,
            'support_count': 2,
            'conflict_count': 0,
            'status': 'active',
            'sources': [],
            'exceptions': [],
            'last_supported_at': '',
            'last_conflicted_at': '',
            'confirmed': True,
        }]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        yaml.dump(existing, f)
        f.flush()
        rules_path = f.name

    try:
        judgments = [{
            'change_index': 0,
            'relation': 'support',
            'key': 'test_rule',
            'instruction': '',
            'scope': 'global',
            'evidence': 'This is a long evidence text, not a date',
            'confidence': 1,
            'observed_at': '2026-07-14',
            'source_id': 'pair-test',
        }]
        result = generate_updated_rules(judgments, rules_path)
        rule = result['rules'][0]
        assert rule['last_supported_at'] == '2026-07-14', \
            f"Expected date '2026-07-14', got '{rule['last_supported_at']}'"
        assert rule['_evidence'] == 'This is a long evidence text, not a date', \
            f"Evidence should be in _evidence field"
        assert 'pair-test' in rule.get('sources', []), \
            f"source_id should be in sources"
    finally:
        Path(rules_path).unlink()


def test_r5_conflict_time_field_writes_date():
    """R5: last_conflicted_at should contain observed_at date, not evidence text."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import generate_updated_rules
    import tempfile, yaml

    existing = {
        'version': 2,
        'rules': [{
            'key': 'test_rule',
            'instruction': '测试规则',
            'scope': 'global',
            'confidence': 2,
            'support_count': 2,
            'conflict_count': 0,
            'status': 'active',
            'sources': [],
            'exceptions': [],
            'last_supported_at': '2026-06-01',
            'last_conflicted_at': '',
            'confirmed': True,
        }]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        yaml.dump(existing, f)
        f.flush()
        rules_path = f.name

    try:
        judgments = [{
            'change_index': 0,
            'relation': 'conflict',
            'key': 'test_rule',
            'instruction': '',
            'scope': 'global',
            'evidence': 'User changed direction completely',
            'confidence': 1,
            'observed_at': '2026-07-14',
            'source_id': 'pair-conflict',
        }]
        result = generate_updated_rules(judgments, rules_path)
        rule = result['rules'][0]
        assert rule['last_conflicted_at'] == '2026-07-14', \
            f"Expected date '2026-07-14', got '{rule['last_conflicted_at']}'"
        assert rule['_evidence'] == 'User changed direction completely'
        assert 'pair-conflict' in rule.get('sources', [])
    finally:
        Path(rules_path).unlink()


# ── H1: support/conflict without existing rules must fail ──

def test_h1_support_empty_existing_keys_fails():
    """H1: support with empty existing_keys must fail."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import validate_reviewer_judgments
    changes = [{"type": "replacement", "removed": "a", "added": "b", "removed_len": 1, "added_len": 1, "before_position": 0, "after_position": 0}]
    judgments = [{"change_index": 0, "relation": "support", "key": "some_key", "evidence": "test", "confidence": 1, "observed_at": "2026-07-14", "source_id": "p1"}]
    try:
        validate_reviewer_judgments(judgments, changes, existing_keys=set())
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "existing" in str(e).lower() or "empty" in str(e).lower()


def test_h1_conflict_empty_existing_keys_fails():
    """H1: conflict with empty existing_keys must fail."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import validate_reviewer_judgments
    changes = [{"type": "replacement", "removed": "a", "added": "b", "removed_len": 1, "added_len": 1, "before_position": 0, "after_position": 0}]
    judgments = [{"change_index": 0, "relation": "conflict", "key": "some_key", "evidence": "test", "confidence": 1, "observed_at": "2026-07-14", "source_id": "p1"}]
    try:
        validate_reviewer_judgments(judgments, changes, existing_keys=set())
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "existing" in str(e).lower() or "empty" in str(e).lower()


def test_h1_support_defensive_check_in_merge():
    """H1: generate_updated_rules must also defensively reject support for non-existent key."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import generate_updated_rules
    import tempfile, yaml

    existing = {
        'version': 2,
        'rules': [{
            'key': 'real_key',
            'instruction': '真实规则',
            'scope': 'global',
            'confidence': 2,
            'support_count': 2,
            'conflict_count': 0,
            'status': 'active',
            'sources': [],
            'exceptions': [],
            'last_supported_at': '',
            'last_conflicted_at': '',
            'confirmed': True,
        }]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, encoding='utf-8') as f:
        yaml.dump(existing, f)
        f.flush()
        rules_path = f.name

    try:
        # Bypass validation to test defensive check in merge function
        judgments = [{
            'change_index': 0,
            'relation': 'support',
            'key': 'nonexistent_key',
            'instruction': '',
            'scope': 'global',
            'evidence': 'test',
            'confidence': 1,
            'observed_at': '2026-07-14',
            'source_id': 'p1',
        }]
        try:
            generate_updated_rules(judgments, rules_path)
            assert False, "Should have raised ValueError in merge"
        except ValueError as e:
            assert "nonexistent_key" in str(e) or "non-existent" in str(e)
    finally:
        Path(rules_path).unlink()


# ── H2: observed_at/source_id required + date format validation ──

def test_h2_new_without_observed_at_rejected():
    """H2: new relation without observed_at must be rejected."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import validate_reviewer_judgments
    changes = [{"type": "replacement", "removed": "a", "added": "b", "removed_len": 1, "added_len": 1, "before_position": 0, "after_position": 0}]
    judgments = [{"change_index": 0, "relation": "new", "key": "test_key", "instruction": "test", "evidence": "test", "confidence": 1, "source_id": "p1"}]
    try:
        validate_reviewer_judgments(judgments, changes)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "observed_at" in str(e)


def test_h2_new_without_source_id_rejected():
    """H2: new relation without source_id must be rejected."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import validate_reviewer_judgments
    changes = [{"type": "replacement", "removed": "a", "added": "b", "removed_len": 1, "added_len": 1, "before_position": 0, "after_position": 0}]
    judgments = [{"change_index": 0, "relation": "new", "key": "test_key", "instruction": "test", "evidence": "test", "confidence": 1, "observed_at": "2026-07-14"}]
    try:
        validate_reviewer_judgments(judgments, changes)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "source_id" in str(e)


def test_h2_support_without_observed_at_rejected():
    """H2: support relation without observed_at must be rejected."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import validate_reviewer_judgments
    changes = [{"type": "replacement", "removed": "a", "added": "b", "removed_len": 1, "added_len": 1, "before_position": 0, "after_position": 0}]
    judgments = [{"change_index": 0, "relation": "support", "key": "real_key", "evidence": "test", "confidence": 1, "source_id": "p1"}]
    try:
        validate_reviewer_judgments(judgments, changes, existing_keys={"real_key"})
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "observed_at" in str(e)


def test_dist_lite_exists_and_under_2000_hanzi():
    """Batch 3:dist/super-writer-lite.md 存在且汉字数 <=2000(人工蒸馏版)。"

    确定性计数口径(测试里写死):仅统计 CJK 统一表意文字 U+4E00–U+9FFF
    (re.findall [\u4e00-\u9fff]),不含标点、拉丁字符与数字;计数 <=2000。
    """
    import re
    p = ROOT / "dist" / "super-writer-lite.md"
    assert p.is_file(), "dist/super-writer-lite.md must exist"
    text = p.read_text(encoding="utf-8")
    hanzi = len(re.findall(r"[\u4e00-\u9fff]", text))
    assert hanzi <= 2000, f"dist lite 汉字数 {hanzi} > 2000"
    assert hanzi > 500, f"dist lite 汉字数 {hanzi} 过少,疑似空文件"


def test_h2_invalid_date_format_rejected():
    """H2: invalid observed_at date format must be rejected."""
    sys.path.insert(0, str(ROOT / 'scripts'))
    from learn_edits import validate_reviewer_judgments
    changes = [{"type": "replacement", "removed": "a", "added": "b", "removed_len": 1, "added_len": 1, "before_position": 0, "after_position": 0}]
    judgments = [{"change_index": 0, "relation": "new", "key": "test_key", "instruction": "test", "evidence": "test", "confidence": 1, "observed_at": "14/07/2026", "source_id": "p1"}]
    try:
        validate_reviewer_judgments(judgments, changes)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "observed_at" in str(e) or "format" in str(e).lower()
