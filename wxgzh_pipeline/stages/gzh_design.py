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

# OBS-73 intro guard: renders can only show ONE intro line (first 40 chars), so any
# additional non-empty line before the first "## " would be SILENTLY dropped by
# gzh-design. This guard fails closed instead. The extraction below mirrors
# gzh-design/scripts/render_article.py parse_article() L79-104 line by line (the
# locked skill cannot be modified; gzh-design 升版修复后此守卫需同步复核).
_INTRO_MAX_LEN = 40  # oneliner truncation render_article.py L127-128 ([:40])


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
    # OBS-73: same frozen final_article.md the media_enrichment stage binds (the
    # zh_human_writing output). Unavailable = FAIL, never skip.
    fa = Path(ctx.run_dir) / "zh_human_writing" / "final_article.md"
    if not fa.is_file():
        return 1, {"reason": "frozen final_article.md missing — OBS-73 intro guard cannot run"}, vpath, vsha
    guard = _intro_guard_report(fa.read_text(encoding="utf-8"))
    if not guard["ok"]:
        return 1, {"reason": "INTRO_GUARD=FAIL (OBS-73)",
                   "intro_line_count": guard["intro_line_count"],
                   "intro_char_count": guard["intro_char_count"],
                   "intro_dropped_text": guard["dropped_text"],
                   "guidance": guard["guidance"], "INTRO_GUARD": "FAIL"}, vpath, vsha
    # DYNAMIC chapter/TOC gate: expected chapter count is derived from the FROZEN
    # article (## headings), not self-reported by super_writer.
    expected_chapters = _count_h2(fa)
    # P0#8: theme identity requires the gzh EXECUTION evidence + the locked
    # render-entry/component-source hashes — copied HTML without execution FAILs;
    # a simulated executor can only ever yield SIMULATED, never official PASS.
    evp = sd / "gzh_execution_evidence.json"
    exec_evidence = json.loads(evp.read_text(encoding="utf-8")) if evp.is_file() else None
    from ..skill_discovery import load_lock
    from . import SKILL_ROOT
    lock_entry = load_lock(SKILL_ROOT).get("skills", {}).get("gzh-design", {})
    mod = load_validator("validate_theme_identity")
    code, report = mod.validate(final_html, expected_chapters,
                                usage_out=sd / "component_usage_report.json",
                                exec_evidence=exec_evidence, lock_entry=lock_entry,
                                network_mode=ctx.network_mode)
    report["chapters_source"] = "frozen final_article.md (## headings)"
    report["INTRO_GUARD"] = "PASS"
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


def _intro_guard_report(md_text: str) -> dict:
    """Replicates gzh-design render_article.py parse_article() L79-104 intro handling.

    Line-by-line correspondence (render_article.py, locked skill):
      L81  md.replace("\r\n", "\n").split("\n")            -> same split
      L86  title H1 branch (L88: starts "# " not "## ")      -> title_seen
      L92  first "## " (not "### ") ends the intro region    -> break (chapters)
      L95  any other "#" line is skipped                      -> continue
      L97  blank lines are skipped                            -> continue
      L99-102  while cur is None: first non-empty line is intro, all later
              non-empty lines are DROPPED silently by the renderer            -> dropped[]
    gzh-design 升版修复后此守卫需同步复核(见 audit/quality/intro-guard-40.md).
    """
    lines = md_text.replace("\r\n", "\n").split("\n")
    title_seen = False
    intro = ""
    dropped: list[str] = []
    for ln in lines:
        st = ln.strip()
        if not title_seen and st.startswith("# ") and not st.startswith("## "):
            title_seen = True
            continue
        if st.startswith("## ") and not st.startswith("### "):
            break
        if st.startswith("#"):
            continue
        if not st:
            continue
        if not intro:
            intro = st
        else:
            dropped.append(st)
    if dropped:
        dropped_text = "\n".join(dropped)
    elif len(intro) > _INTRO_MAX_LEN:
        dropped_text = intro[_INTRO_MAX_LEN:]  # oneliner [:40] truncation tail
    else:
        dropped_text = ""
    ok = (not dropped) and len(intro) <= _INTRO_MAX_LEN
    return {
        "ok": ok,
        "intro_line_count": (1 + len(dropped)) if intro else len(dropped),
        "intro_char_count": len(intro),
        "dropped_text": dropped_text,
        "guidance": "首个 ## 之前只能有一行且不超过 40 字。请将导语内容并入第一个章节,或压缩为副标题。",
    }


def post(ctx, sd, state, exit_code, report):
    state.output_hashes.setdefault("gzh_design", {})["theme_identity"] = report.get("THEME_IDENTITY")


def run_live(ctx, state):
    from ..producers import produce
    return produce(ctx, STAGE, state)
