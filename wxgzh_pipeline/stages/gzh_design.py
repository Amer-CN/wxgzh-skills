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
    # 冻结文章路径(2h'/OBS-73 共用,提前定义)
    fa = Path(ctx.run_dir) / "zh_human_writing" / "final_article.md"
    # OBS-119(档71C-2,2h'):隔离组件 fail-closed —— 冻结文章出现 QUARANTINED
    # 组件(code-compare/long-image,渲染器缺陷 OBS-124/125)即拦截。
    from . import load_validator as _lv2
    vis_gate = _lv2("validate_component_visibility")
    q_hits = vis_gate.quarantine_gate(fa.read_text(encoding="utf-8")) if fa.is_file() else []
    if q_hits:
        names = ",".join(f"{h['name']}@L{h['line']}" for h in q_hits)
        return 1, {"reason": f"COMPONENT_QUARANTINED:{names}",
                   "quarantined": q_hits}, vpath, vsha
    # OBS-129/132(档71C-2 收尾,2.6c):多行不支持组件门禁 —— alert/quote 块体
    # 有效文本 >=2 行即拦截(单 <p> 塌陷,微信端失行分隔)。
    ml_hits = vis_gate.multiline_gate(fa.read_text(encoding="utf-8")) if fa.is_file() else []
    if ml_hits:
        names = ",".join(f"{h['name']}@L{h['start_line']}-L{h['end_line']}({h['line_count']}行)"
                         for h in ml_hits)
        return 1, {"reason": f"COMPONENT_MULTILINE_UNSUPPORTED:{names}",
                   "multiline": ml_hits}, vpath, vsha
    # OBS-120(档71C-2,1d):未知组件 FAIL_CLOSED —— 读取渲染产出的
    # component_usage_report.json;unknown_count != 0 即拦截(R12:键存在才校验,
    # 文件不存在则行为不变)。
    usage_rep = sd / "component_usage_report.json"
    if usage_rep.is_file():
        try:
            usage_data = json.loads(usage_rep.read_text(encoding="utf-8"))
            comps = usage_data.get("components", {}) if isinstance(usage_data, dict) else {}
            unknown = comps.get("unknown", []) if isinstance(comps, dict) else []
            if isinstance(comps, dict) and comps.get("unknown_count", 0):
                return 1, {"reason": "COMPONENT_UNKNOWN=FAIL",
                           "unknown_components": unknown}, vpath, vsha
        except (OSError, ValueError):
            pass  # 解析失败不阻断(文件损坏另由 receipt 校验兜底)
    # OBS-110(档71C-1):final.html <img src> 白名单——只允许 https://;命中
    # ../ 、file:// 、盘符、data: -> FAIL_CLOSED。挂载于此因 final.html 在
    # gzh_design content_validate 路径上(validate_delivery 不在该路径)。
    # 5c 悖论检查:现 RUN 实测命中 0 后启用 enforce(见 validator docstring)。
    from . import load_validator as _lv
    img_gate = _lv("validate_img_src_whitelist")
    img_code, img_report = img_gate.validate(final_html, enforce=True)
    if img_code != 0:
        return 1, {"reason": "OBS110_IMG_SRC=FAIL", "img_src": img_report}, vpath, vsha
    # OBS-73: same frozen final_article.md the media_enrichment stage binds (the
    # zh_human_writing output). Unavailable = FAIL, never skip.
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
    above — the renderer now emits every line, so nothing is dropped).

    OBS-120(档71C-2):::: 组件块(从开标签 ::: 行到配对收尾 ::: 行,含两端)
    整块排除,不进入导语段落清单。块边界规则与安装侧
    render_article.parse_article 逐字一致(见其 L107-128:in_component 状态机,
    开行 st.startswith(":::") 置位,收行 st.startswith(":::") 复位)。"""
    lines = md_text.replace("\r\n", "\n").split("\n")
    title_seen = False
    paras: list[str] = []
    in_component = False
    for ln in lines:
        st = ln.strip()
        if in_component:
            if st.startswith(":::"):
                in_component = False
            continue
        if st.startswith(":::"):
            in_component = True
            continue
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
# OBS-106(档71C-1,7b 备选②)+OBS-119(档71C-2 C路线):组件正文段落锚,逐类
# 从 generate_advanced_html.py builder 真实产物抄录(每类各自形态,禁止通配):
#   alert      -> margin:0;font-size:14px;color:#555555;line-height:1.8;(alert() hammer)
#   dialogue   -> margin:0;font-size:14px;color:#555555;line-height:1.8;(dialogue() hammer)
#   footnotes  -> margin:0 0 6px;font-size:12px;color:#737373;line-height:1.7;(footnotes() hammer)
#   quote      -> margin:0;font-size:16px;font-weight:800;color:#8A4530;line-height:1.7;(quote() hammer)
#   media-text -> margin:0 0 24px;font-size:14px;color:#555555;line-height:1.8;(media_text() hammer)
#   gallery    -> margin:0 0 16px;font-size:12px;color:#737373;text-align:center;(gallery() hammer)
#   resources  -> margin:0;font-size:14px;color:#555555;font-weight:600;line-height:1.6;(resources() hammer)
# code-compare / long-image 归 QUARANTINED(2d' 类B:哨兵未进 final.html,渲染器缺陷
# OBS-124/OBS-125,见 validators/validate_component_visibility.py)。
# 负对照:现 RUN 无组件 final.html 中这些锚 0 命中(封面/目录/署名/页脚均不匹配)。
_COMPONENT_PARA_RES = [
    _re.compile("<p style=\"margin:0;font-size:14px;color:#555555;line-height:1.8;\">(.*?)</p>", _re.S),   # alert/dialogue
    _re.compile("<p style=\"margin:0 0 6px;font-size:12px;color:#737373;line-height:1.7;\">(.*?)</p>", _re.S),  # footnotes
    _re.compile("<p style=\"margin:0;font-size:16px;font-weight:800;color:#8A4530;line-height:1.7;\">(.*?)</p>", _re.S),  # quote
    _re.compile("<p style=\"margin:0 0 24px;font-size:14px;color:#555555;line-height:1.8;\">(.*?)</p>", _re.S),  # media-text
    _re.compile("<p style=\"margin:0 0 16px;font-size:12px;color:#737373;text-align:center;\">(.*?)</p>", _re.S),  # gallery
    _re.compile("<p style=\"margin:0;font-size:14px;color:#555555;font-weight:600;line-height:1.6;\">(.*?)</p>", _re.S),  # resources
]


def _body_plain_text(html_text: str) -> str:
    """Plain text of BODY content only: hammer_para paragraphs + 1a 代码行 +
    <pre> 历史代码块(whitespace-normalized, HTML entities decoded)。
    Cover/TOC/signature/footer regions are excluded on purpose (OBS-83)。"""
    parts = (_PARA_RE.findall(html_text) + _CODE_ROW_RE.findall(html_text)
             + [m for rx in _COMPONENT_PARA_RES for m in rx.findall(html_text)]
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
