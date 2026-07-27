"""Per-stage execution model for dev2.

Classifies each stage as agent-driven (handshake) or executable (real
subprocess), declares the contract outputs each stage must produce, and resolves
the entrypoint / official-validator script for a given network mode:

- fake_live -> shipped fake-live shim scripts under fake_live/skills/** (real
  scripts, real subprocess, no network, no WeChat).
- live      -> the audited installed sub-skill under <skills_home>/<skill>/**.
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
    "gzh_design": ["final.html", "component_usage_report.json", "theme_identity_report.json"],
    "wechat_draft": ["draft_before.json", "draft_after.json", "draft_creation_result.json"],
}

# Executable stage -> installed sub-skill entry + official validator (live mode).
LIVE_ENTRY = {
    "media_enrichment": {"skill": "media-enrichment",
                         "entry": "scripts/run_media_enrichment.py",
                         "validator": "scripts/validate_media_manifest.py"},
    "gzh_design": {"skill": "gzh-design",
                   "entry": "scripts/generate_advanced_html.py",
                   "validator": "scripts/validate_gzh_html.py"},
    "wechat_draft": {"skill": "gzh-design",
                     "entry": "scripts/publish_wechat_draft.py", "validator": None},
}

# Executable stage -> fake-live shim entry + validator (fake_live mode).
FAKE_ENTRY = {
    "media_enrichment": {"entry": "media-enrichment/run_media_enrichment.py",
                         "validator": "media-enrichment/validate_media_manifest.py"},
    "gzh_design": {"entry": "gzh-design/generate.py",
                   "validator": "gzh-design/validate_gzh_html.py"},
    "wechat_draft": {"entry": "wechat/fake_wechat_client.py", "validator": None},
}


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
