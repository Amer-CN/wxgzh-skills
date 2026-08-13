#!/usr/bin/env python3
"""Edit-learning script: generates diffs, validates schema, merges keys, updates counts.

Responsibility split:
  - Python: stable sentence/paragraph-level diff, length/position changes, schema validation,
    key merging, count updates, preview generation.
  - Reviewer/LLM: semantic classification, rule abstraction, support/conflict/new/one_off judgment.

The script NEVER auto-classifies semantics or auto-increases confidence without a reviewer judgment.

Usage:
    # Step 1: Generate diff report (no reviewer needed)
    python learn_edits.py draft.md final.md -o report.json

    # Step 2: After Reviewer fills in judgments, merge into rules
    python learn_edits.py draft.md final.md \
        --reviewer-judgments judgments.json \
        --existing-rules profiles/edit-rules.yaml \
        --generate-update -o report.json
"""
from pathlib import Path
from datetime import datetime
import argparse, difflib, json, re, hashlib

# ── Key reuse mapping ──
KEY_SYNONYMS = {
    "reduce_questions": ["少用反问", "减少疑问句", "不喜欢连续提问", "少提问", "减少反问"],
    "tool_result_first": ["先写结果", "先写亲测", "结果在前", "结论先行"],
    "shorten_paragraphs": ["段落太长", "缩短段落", "减少长段", "拆分段落"],
    "concrete_before_abstract": ["具体在前", "先具体后抽象", "案例先行"],
}


def find_reuse_key(description: str) -> str:
    """Find if a description matches an existing key's synonyms."""
    for key, synonyms in KEY_SYNONYMS.items():
        for syn in synonyms:
            if syn in description:
                return key
    return ""


def extract_changes(before: str, after: str) -> list:
    """Extract sentence-level diffs between before and after text.

    Returns structured diff info. Does NOT classify semantics.
    Semantic classification is the Reviewer's job.
    """
    bs = [s.strip() for s in re.split(r'(?<=[。！？!?])', before) if s.strip()]
    as_ = [s.strip() for s in re.split(r'(?<=[。！？!?])', after) if s.strip()]

    matcher = difflib.SequenceMatcher(None, bs, as_)
    changes = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            continue
        removed = ''.join(bs[i1:i2])
        added = ''.join(as_[j1:j2])
        if not removed.strip() and not added.strip():
            continue

        # Detect basic change type for structural info only
        if not removed.strip() and added.strip():
            change_type = "insertion"
        elif removed.strip() and not added.strip():
            change_type = "deletion"
        else:
            change_type = "replacement"

        changes.append({
            "type": change_type,
            "removed": removed[:300],
            "added": added[:300],
            "removed_len": len(removed),
            "added_len": len(added),
            "before_position": i1,
            "after_position": j1,
        })
    return changes


def _generate_stable_key(instruction: str) -> str:
    """Generate a deterministic key from instruction using SHA-256.

    This is a fallback when Reviewer does not provide a key.
    The same instruction always produces the same key across processes.
    """
    normalized = instruction.strip().lower().replace(' ', '')
    return f"auto_{hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:12]}"


def validate_reviewer_judgments(judgments: list, changes: list, existing_keys: set = None) -> list:
    """Validate reviewer judgment schema with strict checks.

    Expected format per judgment:
    {
        "change_index": 0,
        "relation": "new|support|conflict|one_off",
        "key": "reduce_questions",
        "instruction": "减少连续反问句",
        "scope": "global",
        "evidence": "用户将两个反问句改为具体陈述",
        "confidence": 1,
        "observed_at": "2026-07-14",
        "source_id": "pair-001"
    }

    Strict validation:
    - new: must have non-empty key, instruction, evidence; valid scope
    - support/conflict: must have non-empty key that exists in existing_keys;
      if existing_keys is empty, support/conflict always fails
    - one_off: allow no key but must have evidence
    - new/support/conflict: must have observed_at (YYYY-MM-DD) and source_id
    - confidence must be 1-5
    - change_index must not be duplicated
    """
    valid_relations = {"new", "support", "conflict", "one_off"}
    valid_scopes = {"global", "article_type_specific"}
    if existing_keys is None:
        existing_keys = set()

    validated = []
    seen_change_indices = set()

    for j in judgments:
        idx = j.get("change_index")
        if idx is None or not isinstance(idx, int) or idx < 0 or idx >= len(changes):
            raise ValueError(f"Invalid change_index {idx} in reviewer judgment")
        if idx in seen_change_indices:
            raise ValueError(f"Duplicate change_index {idx} in reviewer judgments")
        seen_change_indices.add(idx)

        relation = j.get("relation", "")
        if relation not in valid_relations:
            raise ValueError(
                f"Invalid relation '{relation}'. Must be one of {valid_relations}."
            )

        key = j.get("key", "")
        instruction = j.get("instruction", "")
        evidence = j.get("evidence", "")
        scope = j.get("scope", "global")
        confidence = j.get("confidence", 1)
        observed_at = j.get("observed_at", "")
        source_id = j.get("source_id", "")

        # Validate confidence
        if not isinstance(confidence, (int, float)) or confidence < 1 or confidence > 5:
            raise ValueError(
                f"confidence must be a number in [1, 5], got {confidence}"
            )

        # Validate scope
        if scope not in valid_scopes:
            raise ValueError(
                f"Invalid scope '{scope}'. Must be one of {valid_scopes}."
            )

        # Relation-specific validation
        if relation == "new":
            if not key:
                raise ValueError("new relation requires non-empty key")
            if not instruction.strip():
                raise ValueError("new relation requires non-empty instruction")
            if not evidence.strip():
                raise ValueError("new relation requires non-empty evidence")
            if not observed_at:
                raise ValueError("new relation requires observed_at")
            if not source_id:
                raise ValueError("new relation requires source_id")

        elif relation in ("support", "conflict"):
            if not key:
                raise ValueError(f"{relation} relation requires non-empty key")
            # support/conflict must always reference a real existing key;
            # if existing_keys is empty, this always fails
            if key not in existing_keys:
                if not existing_keys:
                    raise ValueError(
                        f"{relation} relation requires existing rules, "
                        f"but no --existing-rules provided or rules file is empty"
                    )
                raise ValueError(
                    f"{relation} relation references non-existent key '{key}'. "
                    f"Available keys: {sorted(existing_keys)}"
                )
            if not evidence.strip():
                raise ValueError(f"{relation} relation requires non-empty evidence")
            if not observed_at:
                raise ValueError(f"{relation} relation requires observed_at")
            if not source_id:
                raise ValueError(f"{relation} relation requires source_id")

        elif relation == "one_off":
            if not evidence.strip():
                raise ValueError("one_off relation requires non-empty evidence")

        # Validate observed_at date format (if present)
        if observed_at:
            try:
                datetime.strptime(observed_at, "%Y-%m-%d")
            except ValueError:
                raise ValueError(
                    f"observed_at must be YYYY-MM-DD format, got '{observed_at}'"
                )

        validated.append({
            "change_index": idx,
            "relation": relation,
            "key": key,
            "instruction": instruction,
            "scope": scope,
            "evidence": evidence,
            "confidence": confidence,
            "observed_at": observed_at,
            "source_id": source_id,
        })
    return validated


def check_playbook_trigger(existing_rules_path: str = None) -> dict:
    """Check if playbook update should be triggered (every 5 lessons)."""
    if not existing_rules_path or not Path(existing_rules_path).exists():
        return {"trigger": False, "lesson_count": 0}

    import yaml
    existing = yaml.safe_load(Path(existing_rules_path).read_text(encoding='utf-8'))
    if not existing or not existing.get('rules'):
        return {"trigger": False, "lesson_count": 0}

    total_support = sum(r.get('support_count', r.get('occurrences', 1)) for r in existing['rules'])
    total_conflict = sum(r.get('conflict_count', 0) for r in existing['rules'])
    total = total_support + total_conflict
    trigger = total >= 5 and total % 5 == 0

    return {
        "trigger": trigger,
        "lesson_count": total,
        "support_count": total_support,
        "conflict_count": total_conflict,
        "message": f"已积累 {total} 次修改记录（支持 {total_support}，冲突 {total_conflict}），建议审核候选规则。" if trigger else ""
    }


def generate_updated_rules(judgments: list, existing_rules_path: str = None) -> dict:
    """Generate updated rules YAML based on reviewer judgments.

    Requires explicit `relation` field from reviewer:
    - new: create new rule
    - support: increment support_count, confidence +1 (cap 5)
    - conflict: increment conflict_count, confidence -1 (floor 0)
    - one_off: record but don't create/update rule

    Without relation, confidence is NEVER auto-increased.
    """
    import yaml

    rules = []
    existing_rules = []
    if existing_rules_path and Path(existing_rules_path).exists():
        existing = yaml.safe_load(Path(existing_rules_path).read_text(encoding='utf-8'))
        if existing and existing.get('rules'):
            existing_rules = existing['rules']

    existing_by_key = {r.get('key', ''): r for r in existing_rules if r.get('key')}
    processed_keys = set()

    for j in judgments:
        relation = j.get("relation", "one_off")
        key = j.get("key", "")

        if relation == "one_off":
            # Record but don't create or update rules
            continue

        if not key:
            key = _generate_stable_key(j.get('instruction', ''))

        if relation == "new":
            if key in existing_by_key:
                # Key already exists - treat as support instead
                relation = "support"
            else:
                rules.append({
                    'key': key,
                    'instruction': j.get('instruction', ''),
                    'scope': j.get('scope', 'global'),
                    'confidence': min(j.get('confidence', 1), 5),
                    'support_count': 1,
                    'conflict_count': 0,
                    'status': 'active',
                    'sources': [j.get('source_id', '')] if j.get('source_id') else [],
                    'exceptions': [],
                    'last_supported_at': j.get('observed_at', ''),
                    'last_conflicted_at': '',
                    'confirmed': False,
                    '_action': 'new',
                    '_evidence': j.get('evidence', ''),
                })
                processed_keys.add(key)
                continue

        if relation == "support":
            # Defensive check: support must reference an existing rule
            if key not in existing_by_key:
                raise ValueError(
                    f"support relation references non-existent key '{key}' "
                    f"during rule merge. This should have been caught by validation."
                )
            existing_rule = existing_by_key[key]
            updated_rule = existing_rule.copy()
            updated_rule['support_count'] = existing_rule.get('support_count', 1) + 1
            updated_rule['confidence'] = min(updated_rule['support_count'], 5)
            updated_rule['last_supported_at'] = j.get('observed_at', '')
            if j.get('source_id') and j.get('source_id') not in updated_rule.get('sources', []):
                updated_rule.setdefault('sources', []).append(j.get('source_id'))
            updated_rule['_evidence'] = j.get('evidence', '')

            if updated_rule.get('conflict_count', 0) > updated_rule.get('support_count', 0):
                updated_rule['status'] = 'stale'
                updated_rule['_stale_reason'] = 'conflict_count > support_count'
            elif updated_rule.get('status') not in ('revoked',):
                updated_rule['status'] = 'active'

            updated_rule['_action'] = 'update'
            rules.append(updated_rule)
            processed_keys.add(key)

        elif relation == "conflict":
            # Defensive check: conflict must reference an existing rule
            if key not in existing_by_key:
                raise ValueError(
                    f"conflict relation references non-existent key '{key}' "
                    f"during rule merge. This should have been caught by validation."
                )
            existing_rule = existing_by_key[key]
            updated_rule = existing_rule.copy()
            updated_rule['conflict_count'] = existing_rule.get('conflict_count', 0) + 1
            updated_rule['confidence'] = max(existing_rule.get('confidence', 1) - 1, 0)
            updated_rule['last_conflicted_at'] = j.get('observed_at', '')
            if j.get('source_id') and j.get('source_id') not in updated_rule.get('sources', []):
                updated_rule.setdefault('sources', []).append(j.get('source_id'))
            updated_rule['_evidence'] = j.get('evidence', '')

            if updated_rule.get('conflict_count', 0) > updated_rule.get('support_count', 0):
                updated_rule['status'] = 'stale'
                updated_rule['_stale_reason'] = 'conflict_count > support_count'
            elif updated_rule.get('confidence', 0) <= 0:
                updated_rule['status'] = 'ignored'
                updated_rule['_ignored_reason'] = 'confidence reached 0'
            elif updated_rule.get('status') not in ('revoked',):
                updated_rule['status'] = 'active'

            updated_rule['_action'] = 'update'
            rules.append(updated_rule)
            processed_keys.add(key)

    # Add existing rules that weren't matched
    for r in existing_rules:
        if r.get('key', '') not in processed_keys:
            r_copy = r.copy()
            r_copy['_action'] = 'keep'
            if 'support_count' not in r_copy:
                r_copy['support_count'] = r_copy.get('occurrences', 1)
            if 'conflict_count' not in r_copy:
                r_copy['conflict_count'] = 0
            if 'status' not in r_copy:
                r_copy['status'] = 'active'
            if 'last_supported_at' not in r_copy:
                r_copy['last_supported_at'] = ''
            if 'last_conflicted_at' not in r_copy:
                r_copy['last_conflicted_at'] = ''
            rules.append(r_copy)

    return {
        'version': 2,
        'rules': rules,
        '_note': '此文件为基于 Reviewer 判断生成的候选更新。置信度双向调整：support +1，conflict -1。无 relation 字段时不调整置信度。'
    }


def main():
    p = argparse.ArgumentParser(description="Analyze edits and generate diff report or merge reviewer judgments.")
    p.add_argument('draft', help='Path to AI draft')
    p.add_argument('final', help='Path to user final version')
    p.add_argument('-o', '--output', default='edit-learning-report.json')
    p.add_argument('--reviewer-judgments', default=None,
                   help='Path to reviewer judgments JSON (enables rule merging)')
    p.add_argument('--existing-rules', default=None, help='Path to existing edit-rules YAML')
    p.add_argument('--generate-update', action='store_true',
                   help='Generate updated rules preview (requires --reviewer-judgments)')
    a = p.parse_args()

    before = Path(a.draft).read_text(encoding='utf-8')
    after = Path(a.final).read_text(encoding='utf-8')

    ratio = difflib.SequenceMatcher(None, before, after).ratio()
    changes = extract_changes(before, after)

    # Load reviewer judgments if provided
    reviewer_judgments = None
    if a.reviewer_judgments:
        if not Path(a.reviewer_judgments).exists():
            raise FileNotFoundError(f"Reviewer judgments file not found: {a.reviewer_judgments}")
        raw_judgments = json.loads(Path(a.reviewer_judgments).read_text(encoding='utf-8'))

        # Load existing keys for support/conflict validation
        existing_keys = set()
        if a.existing_rules and Path(a.existing_rules).exists():
            import yaml
            existing = yaml.safe_load(Path(a.existing_rules).read_text(encoding='utf-8'))
            if existing and existing.get('rules'):
                existing_keys = {r.get('key', '') for r in existing['rules'] if r.get('key')}

        reviewer_judgments = validate_reviewer_judgments(raw_judgments, changes, existing_keys)
    else:
        # Without reviewer judgments, generate suggestions for the reviewer
        for i, c in enumerate(changes):
            c["suggested_for_reviewer"] = True
            c["reviewer_prompt"] = (
                f"Change {i}: {c['type']} at position {c['before_position']}. "
                f"Removed: {c['removed'][:80]}... Added: {c['added'][:80]}... "
                f"Please provide: relation (new/support/conflict/one_off), key, instruction, scope, evidence."
            )

    # Check playbook trigger
    playbook_check = check_playbook_trigger(a.existing_rules)

    report = {
        "similarity": round(ratio, 4),
        "before_chars": len(before),
        "after_chars": len(after),
        "before_sentences": len([s for s in re.split(r'(?<=[。！？!?])', before) if s.strip()]),
        "after_sentences": len([s for s in re.split(r'(?<=[。！？!?])', after) if s.strip()]),
        "length_change_ratio": round((len(after) - len(before)) / max(len(before), 1), 4),
        "changes": changes,
        "reviewer_judgments": reviewer_judgments,
        "playbook_trigger": playbook_check,
        "config": {
            "analyze_automatically": True,
            "propose_rules_automatically": False,  # Only with reviewer judgments
            "persist_automatically": False,
            "merge_duplicate_keys": True,
            "require_confirmation": True,
        },
        "instruction": "Python 已生成结构化 diff。语义分类和规则判断需由 Reviewer 完成。"
    }

    if reviewer_judgments is None:
        report["instruction"] += (
            " 请将 changes 交给 Reviewer 填写 judgments，然后重新运行 --reviewer-judgments。"
        )
    else:
        report["instruction"] += " Reviewer 判断已加载。"

    # Generate updated rules if requested
    if a.generate_update and reviewer_judgments:
        updated = generate_updated_rules(reviewer_judgments, a.existing_rules)
        report['updated_rules_preview'] = updated
        report['instruction'] += ' 已生成更新预览（updated_rules_preview），请审核后手动写入。'
    elif a.generate_update and not reviewer_judgments:
        report['instruction'] += ' --generate-update 需要 --reviewer-judgments。'

    Path(a.output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(a.output)
    if playbook_check.get('trigger'):
        print(f"\n⚠️ {playbook_check['message']}")


if __name__ == '__main__':
    main()
