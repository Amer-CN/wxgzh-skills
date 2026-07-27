"""Stage 5 — gzh-design smartisan (hammer). Must be REAL official components:
cover-breaking=1, toc-scroll=1, chapter-title==chapters, signature=1, footer-cta=1,
official image component types 2-4, no fallback, safe strikethrough. THEME_IDENTITY=PASS.
"""
from __future__ import annotations

import json
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
    # DYNAMIC chapter/TOC gate: expected chapter count is derived from the FROZEN
    # article (## headings), not self-reported by super_writer.
    fa = Path(ctx.run_dir) / "zh_human_writing" / "final_article.md"
    expected_chapters = _count_h2(fa) if fa.is_file() else None
    mod = load_validator("validate_theme_identity")
    code, report = mod.validate(final_html, expected_chapters,
                                usage_out=sd / "component_usage_report.json")
    report["chapters_source"] = "frozen final_article.md (## headings)"
    # program-generated theme identity report (never hand-declared)
    (sd / "theme_identity_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return code, report, vpath, vsha


def _count_h2(md_path: Path) -> int:
    n = 0
    for ln in Path(md_path).read_text(encoding="utf-8").splitlines():
        if ln.startswith("## ") and not ln.startswith("### "):
            n += 1
    return n


def post(ctx, sd, state, exit_code, report):
    state.output_hashes.setdefault("gzh_design", {})["theme_identity"] = report.get("THEME_IDENTITY")


def run_live(ctx, state):
    from ..producers import produce
    return produce(ctx, STAGE, state)
