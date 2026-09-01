"""Tests for 77S/OBS-345: explicit runtime policy dispatch (AST7 fix).

Covers _apply_runtime_policy_defaults after the loop/setattr dispatch was
replaced with literal-attribute dispatch:
1. Profile defaults fill unset (None) fields.
2. Explicitly passed values are not overridden by the profile.
"""
import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from validate_article_length import _apply_runtime_policy_defaults


def _write_profile(tmp_path):
    path = tmp_path / 'gp.yaml'
    path.write_text(yaml.dump({
        'mode': 'full', 'article_mode': 'long',
        'target_visible_chars': 5000, 'acceptable_min': 4500, 'acceptable_max': 6500,
    }, allow_unicode=True), encoding='utf-8')
    return str(path)


def test_profile_defaults_fill_unset_fields(tmp_path):
    profile = _write_profile(tmp_path)
    args = argparse.Namespace(
        full_mode=True, generation_profile=profile,
        target_visible_chars=None, acceptable_min=None,
        acceptable_max=None, article_mode=None,
    )
    policy = _apply_runtime_policy_defaults(args)
    assert policy == {
        'article_mode': 'long', 'target_visible_chars': 5000,
        'acceptable_min': 4500, 'acceptable_max': 6500,
    }
    assert args.target_visible_chars == 5000
    assert args.acceptable_min == 4500
    assert args.acceptable_max == 6500
    assert args.article_mode == 'long'


def test_explicit_values_not_overridden(tmp_path):
    profile = _write_profile(tmp_path)
    args = argparse.Namespace(
        full_mode=True, generation_profile=profile,
        target_visible_chars=3000, acceptable_min=2500,
        acceptable_max=4000, article_mode='medium',
    )
    policy = _apply_runtime_policy_defaults(args)
    assert policy is not None
    assert args.target_visible_chars == 3000
    assert args.acceptable_min == 2500
    assert args.acceptable_max == 4000
    assert args.article_mode == 'medium'
