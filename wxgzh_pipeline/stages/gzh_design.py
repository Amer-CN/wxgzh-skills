"""Stage 5 — gzh-design smartisan (hammer). Must be REAL official components:
cover-breaking=1, toc-scroll=1, chapter-title==chapters, signature=1, footer-cta=1,
official image component types 2-4, no fallback, safe strikethrough. THEME_IDENTITY=PASS.
"""
from __future__ import annotations

import html as _html
import json
import re as _re
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
    # 档71B OBS-102:未支持语法门禁(probe 判据)——冻结文章含渲染器不支持的
    # 语法即 FAIL_CLOSED;判据来自安装侧渲染器实测,不含跨仓硬编码期望值,
    # 71C 接线后 probe 自动放行 :::(免悖论声明见 validators/validate_syntax_gate.py)。
    from ..validators_syntax import run_syntax_gate
    gate = run_syntax_gate(ctx, sd, state)
    if gate is not None and gate["exit_code"] != 0:
        return 1, {"reason": "OBS102_SYNTAX_GATE=FAIL",
                   "syntax_gate": gate["report"]}, vpath, vsha
    # OBS-73: same frozen final_article.md the media_enrichment stage binds (the
    # zh_human_writing output). Unavailable = FAIL, never skip.
    fa = Path(ctx.run_dir) / "zh_human_writing" / "final_article.md"
    if not fa.is_file():
        return 1, {"reason": "frozen final_article.md missing — OBS-73 intro guard cannot run"}, vpath, vsha
    guard = _intro_content_fidelity(fa.read_text(encoding="utf-8"),
                                    final_html.read_text(encoding="utf-8"))
    if not guard["ok"]:
        return 1, {"reason": "INTRO_GUARD=FAIL (OBS-73)",
                   "intro_line_count": guard["intro_line_count"],
                   "intro_char_count": guard["intro_char_count"],
                   "intro_missing_text": guard["missing_text"],
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


def _intro_paras(md_text: str) -> list[str]:
    """Intro-region paragraphs: non-empty non-heading lines between the H1 and
    the first "## " (same region parse_article renders; see _INTRO_MAX_LEN note
    above — the renderer now emits every line, so nothing is dropped)."""
    lines = md_text.replace("\r\n", "\n").split("\n")
    title_seen = False
    paras: list[str] = []
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
        paras.append(st)
    return paras


_WS_RE = _re.compile(r"\s+")


def _normalize_text(text: str) -> str:
    """单一归一函数(3C-a):去标签 -> HTML 实体解码 -> 删除全部空白。

    与 _body_plain_text 旧三步逐字一致(去标签 re.sub(r"<[^>]+>","",s) ->
    html.unescape -> _WS_RE.sub("", ...));正文区与查找串共用,禁止另写一套。"""
    stripped = _re.sub(r"<[^>]+>", "", text)
    return _WS_RE.sub("", _html.unescape(stripped))
# OBS-83 (hammer.3): body paragraphs rendered by hammer_para (and code blocks).
# The guard must inspect the BODY region only — cover subtitle / TOC / signature
# / footer text must NOT count as "present" (档50 showed subtitle can carry the
# first line coincidentally, which the old whole-HTML check could not tell).
_PARA_RE = _re.compile(
    r'<p style="margin-bottom:16px;font-size:14px;line-height:1.9;'
    r'text-align:justify;[^"]*">(.*?)</p>', _re.S)
# OBS-111(档71B'):67D 代码块 = 每行一个 <p style="margin:0;font-family:'SF Mono',
# Consolas,...;font-size:13px;line-height:1.6;color:#E2E8F0;">,无 <pre>。
# _CODE_ROW_RE 以 1b 抄录的真实开标签为锚(color:#E2E8F0 + SF Mono 双特征):
#   - 锚点一 color:#E2E8F0 已实测全仓 18 处且全在代码行(1c),但为确保不误匹配
#     未来新增的顶栏/语言标签,追加同一标签内的第二个稳定特征 font-family SF Mono;
#   - 只匹配代码行,不匹配封面/目录/署名/页脚(那些用其它颜色与字体)。
_PRE_RE = _re.compile(r"<pre[^>]*>(.*?)</pre>", _re.S)  # 兼容 67D 之前历史产物,当前命中 0


# OBS-111(档71B'):代码行锚点(1b 抄录的真实开标签)。保留 _PRE_RE 兼容历史产物。
_CODE_ROW_RE = _re.compile(
    "<p style=\"margin:0;font-family:'SF Mono',Consolas[^\"]*?color:#E2E8F0;\">"
    "(.*?)</p>", _re.S)


def _body_plain_text(html_text: str) -> str:
    """Plain text of BODY content only: hammer_para paragraphs + 1a 代码行 +
    <pre> 历史代码块(whitespace-normalized, HTML entities decoded)。
    Cover/TOC/signature/footer regions are excluded on purpose (OBS-83)。"""
    parts = (_PARA_RE.findall(html_text) + _CODE_ROW_RE.findall(html_text)
             + _PRE_RE.findall(html_text))
    return _normalize_text("".join(parts))


def _intro_content_fidelity(md_text: str, html_text: str) -> dict:
    """OBS-73/OBS-83 content fidelity guard.

    The renderer emits every intro paragraph (INCLUDING the first line, hammer.3)
    as body paragraphs before the first chapter title. What must hold:
      - EVERY intro paragraph's text must appear IN FULL in the BODY region
        (hammer_para paragraphs / <pre> code blocks), whitespace-normalized;
      - the FIRST line uses the SAME full-presence standard — a cover-subtitle or
        oneliner occurrence does NOT count (OBS-83: the 档50 HTML carried the
        first line only inside the cover and the old guard still passed).
    Frozen article missing => handled by the caller (FAIL, never skip).
    No skip switch / env / exemption parameter exists for this guard.
    """
    body = _body_plain_text(html_text)
    paras = _intro_paras(md_text)
    missing: list[str] = []
    for para in paras:
        norm = _normalize_text(para)
        if not norm:
            continue
        if norm not in body:
            missing.append(para)
    ok = not missing
    return {
        "ok": ok,
        "intro_line_count": len(paras),
        "intro_char_count": sum(len(p) for p in paras),
        "missing_text": "\n".join(missing),
        "guidance": ("渲染产物正文区域缺失首个 ## 之前的导语内容:每个段落(含首段)"
                     "必须完整存在于正文段落中;仅出现在封面/oneliner 不算数。"
                     "请核对渲染器输出与冻结文章,不要改写正文。"),
    }




def post(ctx, sd, state, exit_code, report):
    state.output_hashes.setdefault("gzh_design", {})["theme_identity"] = report.get("THEME_IDENTITY")


def run_live(ctx, state):
    from ..producers import produce
    return produce(ctx, STAGE, state)
