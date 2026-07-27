"""Stage 5 — gzh-design smartisan (hammer). Must be REAL official components:
cover-breaking=1, toc-scroll=1, chapter-title==chapters, signature=1, footer-cta=1,
official image component types 2-4, no fallback, safe strikethrough. THEME_IDENTITY=PASS.
"""
from __future__ import annotations

from pathlib import Path

from . import subskill_validator_sha, load_validator

STAGE = "gzh_design"
STAGE_CONFIG = {"GZH_THEME": "smartisan", "THEME_NAME": "锤子风格", "THEME_FALLBACK_ALLOWED": False}


def stage_inputs(ctx, state):
    return {"final_article": "../zh_human_writing/final_article.md",
            "media_bindings": "../media_enrichment/article_image_bindings.json"}


def invoked_entrypoint(ctx):
    return ("gzh-design scripts/generate_hammer_upgrade_samples.py + generate_advanced_html.py "
            "(official hammer components) validated by scripts/validate_gzh_html.py + theme identity")


def side_effects(ctx, state):
    return []


def content_validate(ctx, sd: Path, state):
    vpath, vsha = subskill_validator_sha(ctx, "gzh-design", "scripts/validate_gzh_html.py")
    final_html = sd / "final.html"
    if not final_html.is_file():
        return 1, {"reason": "final.html missing"}, vpath, vsha
    expected_chapters = (state.output_hashes.get("super_writer") or {}).get("chapters")
    mod = load_validator("validate_theme_identity")
    code, report = mod.validate(final_html, expected_chapters, usage_out=sd / "component_usage_report.json")
    return code, report, vpath, vsha


def post(ctx, sd, state, exit_code, report):
    state.output_hashes.setdefault("gzh_design", {})["theme_identity"] = report.get("THEME_IDENTITY")


def run_live(ctx, state):
    raise NotImplementedError("live gzh-design invokes the official hammer generator; not run in dev/tests")
