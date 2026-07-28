"""Per-stage execution model for dev2-hotfix1.

Classifies each stage as agent-driven (handshake) or executable (real
subprocess), declares the contract outputs, and resolves the entrypoint /
official-validator scripts by network mode. All entry CLIs are the REAL
sub-skill CLIs (dev2's invented --stage-dir/--article args are gone):

  media-enrichment  run_media_enrichment.py  --request/--output-dir[/--fixture-dir]
                    validate_media_manifest.py --manifest/--request/--bindings
  gzh-design        render_article.py --article/--bindings/--output-dir/--theme
                    validate_gzh_html.py <final.html>   (positional)
  wechat_draft      publish_wechat_draft.py --html/--title/--audit-dir/--dry-run

- fake_live -> shim scripts under fake_live/skills/** that mirror the EXACT real
  CLIs (real subprocess, no network, honestly marked simulated).
- live      -> the audited installed sub-skill under <skills_home>/<skill>/**.

Agent-driven stages also declare their OFFICIAL sub-skill validators, which the
orchestrator subprocess-executes for real (P0#5).
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FAKE_LIVE_HOME = REPO_ROOT / "fake_live" / "skills"

AGENT = "agent_handshake"
SUBPROC = "subprocess"
WECHAT = "wechat"

STAGE_EXEC = {
    "aihot": AGENT,
    "super_writer": AGENT,
    "zh_human_writing": AGENT,
    "media_enrichment": SUBPROC,
    "gzh_design": SUBPROC,
    "wechat_draft": WECHAT,
}

# Contract outputs each stage must produce into its stage dir (enforced).
EXPECTED_OUTPUTS = {
    "aihot": ["raw_items.json", "deduplicated_items.json", "fetch_log.json"],
    "super_writer": ["article.md", "outline.md", "canonical_claim_registry.json",
                     "full_mode_validator_report.json"],
    "zh_human_writing": ["final_article.md", "fidelity_report.json"],
    "media_enrichment": ["media_manifest.json", "article_image_bindings.json"],
    "gzh_design": ["final.html", "final_runtime.html",
                   "component_usage_report.json", "theme_identity_report.json"],
    "wechat_draft": ["draft_before.json", "draft_after.json", "draft_creation_result.json"],
}

# Real upstream inputs each stage consumes (relative to run_dir). Receipts bind
# these files + their hashes (P0#2); the contract enforces their presence (P0#7).
UPSTREAM_INPUTS = {
    "aihot": [],
    "super_writer": ["aihot/deduplicated_items.json", "aihot/raw_items.json",
                     "aihot/fetch_log.json"],
    "zh_human_writing": ["super_writer/article.md",
                         "super_writer/canonical_claim_registry.json",
                         "super_writer/full_mode_validator_report.json"],
    "media_enrichment": ["zh_human_writing/final_article.md",
                         "media_enrichment/media_request.json"],
    "gzh_design": ["zh_human_writing/final_article.md",
                   "media_enrichment/article_image_bindings.json",
                   "media_enrichment/media_manifest.json"],
    "wechat_draft": ["gzh_design/final.html", "gzh_design/final_runtime.html",
                     "media_enrichment/article_image_bindings.json",
                     "gzh_design/theme_identity_report.json"],
}

# Executable stage -> sub-skill entry + official validator, by mode.
LIVE_ENTRY = {
    "media_enrichment": {"skill": "media-enrichment",
                         "entry": "scripts/run_media_enrichment.py",
                         "validator": "scripts/validate_media_manifest.py"},
    "gzh_design": {"skill": "gzh-design",
                   "entry": "scripts/render_article.py",
                   "validator": "scripts/validate_gzh_html.py"},
    "wechat_draft": {"skill": "gzh-design",
                     "entry": "scripts/publish_wechat_draft.py", "validator": None},
}

FAKE_ENTRY = {
    "media_enrichment": {"entry": "media-enrichment/run_media_enrichment.py",
                         "validator": "media-enrichment/validate_media_manifest.py"},
    "gzh_design": {"entry": "gzh-design/render_article.py",
                   "validator": "gzh-design/validate_gzh_html.py"},
    "wechat_draft": {"entry": "gzh-design/publish_wechat_draft.py", "validator": None},
}

# Agent stage -> official sub-skill validators the orchestrator subprocess-runs
# (P0#5). Each: (skill, validator_relpath). The argv is built in producers.py.
AGENT_VALIDATORS = {
    "super_writer": [
        ("super-writer", "scripts/material_ingestion.py"),
        ("super-writer", "scripts/validate_article_length.py"),
        ("super-writer", "scripts/validate_semantic_map.py"),
    ],
    "zh_human_writing": [
        ("zh-human-writing", "scripts/fidelity_guard.py"),
        ("zh-human-writing", "scripts/pattern_audit.py"),
        ("zh-human-writing", "scripts/change_report.py"),
    ],
    "aihot": [],
}

# fake_live shim homes for agent validators (skill name -> shim dir name)
FAKE_SKILL_DIR = {"super-writer": "super-writer", "zh-human-writing": "zh-human-writing"}


def resolve_entry(stage: str, network_mode: str, skills_home: Path):
    """Return (entry_path, validator_path) for a subprocess/wechat stage."""
    if network_mode == "fake_live":
        fe = FAKE_ENTRY.get(stage, {})
        entry = (FAKE_LIVE_HOME / fe["entry"]) if fe.get("entry") else None
        val = (FAKE_LIVE_HOME / fe["validator"]) if fe.get("validator") else None
        return entry, val
    le = LIVE_ENTRY.get(stage)
    if not le:
        return None, None
    root = Path(skills_home) / le["skill"]
    entry = root / le["entry"]
    val = (root / le["validator"]) if le.get("validator") else None
    return entry, val


def resolve_agent_validator(skill: str, rel: str, network_mode: str, skills_home: Path) -> Path:
    """Resolve one official agent-stage validator script by mode."""
    if network_mode == "fake_live":
        return FAKE_LIVE_HOME / FAKE_SKILL_DIR.get(skill, skill) / Path(rel).name
    return Path(skills_home) / skill / rel
