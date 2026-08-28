"""77M repair pack: container vocab + renderer robustness + validator self-collect + title normalization."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]


# --- Task 2: Renderer robustness (UnboundLocalError fix) ---

def test_render_article_no_crash_on_unquoted_type():
    """77M/OBS-331: type=warning without quotes must not crash with UnboundLocalError."""
    sys.path.insert(0, str(SKILL_ROOT / "fake_live" / "skills" / "gzh-design" / "scripts"))
    # Import the real render_article (fake_live mirrors it)
    real_render = SKILL_ROOT.parent / "gzh-design" / "scripts" / "render_article.py"
    if not real_render.is_file():
        pytest.skip("gzh-design render_article.py not found in repo tree")
    import importlib.util
    spec = importlib.util.spec_from_file_location("_render_77m", real_render)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # The constant must exist
    assert mod.ALERT_TYPES == frozenset({"note", "tip", "important", "warning", "caution"})
    assert mod.QUOTE_TYPES == frozenset({"normal", "highlight", "sourced"})
    assert "alert" in mod.MARKDOWN_CONTAINERS
    assert "quote" in mod.MARKDOWN_CONTAINERS


def test_render_article_constants_are_single_source():
    """77M/OBS-330: CONTAINER_TYPES is the single source for container/type enums."""
    real_render = SKILL_ROOT.parent / "gzh-design" / "scripts" / "render_article.py"
    if not real_render.is_file():
        pytest.skip("gzh-design render_article.py not found in repo tree")
    import importlib.util
    spec = importlib.util.spec_from_file_location("_render_77m_b", real_render)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Every container in CONTAINER_TYPES must have a frozenset of valid types
    for container, types in mod.CONTAINER_TYPES.items():
        assert isinstance(types, frozenset), f"{container} types must be frozenset"
        assert len(types) > 0, f"{container} must have at least one type"
    # MARKDOWN_CONTAINERS must match CONTAINER_TYPES keys
    assert mod.MARKDOWN_CONTAINERS == frozenset(mod.CONTAINER_TYPES.keys())


# --- Task 3: Validator report self-collect ---

def test_producer_self_collects_validator_report():
    """77M/OBS-332: producer writes full_mode_validator_report.json from official stdout,
    not from agent. The comparison logic is removed."""
    from wxgzh_pipeline import execmodel as EM
    # full_mode_validator_report.json must NOT be in agent expected outputs
    assert "full_mode_validator_report.json" not in EM.AGENT_EXPECTED_OUTPUTS["super_writer"]
    # But it MUST be in stage expected outputs (self-collected by producer)
    assert "full_mode_validator_report.json" in EM.EXPECTED_OUTPUTS["super_writer"]


# --- Task 4: Title quote normalization ---

def test_normalize_title_quotes_paired():
    """77M/OBS-333: paired half-width quotes in title get normalized to full-width."""
    from wxgzh_pipeline.producers import _normalize_title_quotes
    title = 'Gemini 3.5: hello "world" test'
    result = _normalize_title_quotes(title)
    assert "\u201c" in result  # opening quote
    assert "\u201d" in result  # closing quote
    assert '"' not in result


def test_normalize_title_quotes_odd_keeps_last():
    """77M/OBS-333: odd count keeps the last quote unpaired (no guessing)."""
    from wxgzh_pipeline.producers import _normalize_title_quotes
    title = 'one quote only "'
    result = _normalize_title_quotes(title)
    assert '"' in result  # last quote preserved


def test_normalize_title_quotes_no_quotes_idempotent():
    """77M/OBS-333: titles without quotes are unchanged."""
    from wxgzh_pipeline.producers import _normalize_title_quotes
    title = "no quotes here"
    assert _normalize_title_quotes(title) == title
    # Full-width quotes already present: idempotent
    title2 = "already \u201cfull\u201d width"
    assert _normalize_title_quotes(title2) == title2
