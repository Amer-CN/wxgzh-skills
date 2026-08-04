#!/usr/bin/env python3
"""Official article-level renderer for the hammer (smartisan) theme — dev2-hotfix1.

Unlike generate_advanced_html.py / generate_hammer_upgrade_samples.py (which emit
FIXED acceptance samples), this is a real article renderer: it parses an arbitrary
Markdown article + an article_image_bindings.json (real WeChat-host image URLs)
and typesets them with the OFFICIAL hammer components imported from
generate_hammer_upgrade_samples.py. It hand-writes NO hammer HTML of its own — the
whole point is that wxgzh-pipeline can only ever call this official entry.

Usage:
    python scripts/render_article.py \
        --article final_article.md \
        --bindings article_image_bindings.json \
        --output-dir <dir> \
        --theme smartisan

Outputs (into --output-dir):
    final.html                    clean <section> fragment (paste into WeChat)
    final_runtime.html            browser-preview wrapper (wrap_html)
    component_usage_report.json   program-counted component usage
    theme_identity_report.json    program-derived theme identity facts

No network, no WeChat side effects — pure HTML generation.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

# OFFICIAL components (single reusable source of truth).
import generate_hammer_upgrade_samples as H
from validate_gzh_html import validate as validate_html

# smartisan is the pipeline alias for the registered gzh theme id "hammer".
THEME_ALIAS = {"smartisan": "hammer", "hammer": "hammer", "锤子风格": "hammer"}

# Chinese section-semantics -> English chapter label (else derived/PART).
EN_LABEL_MAP = [
    (("缘起", "起源", "背景", "开始"), "ORIGIN"),
    (("选型", "选择", "对比", "抉择"), "CHOICE"),
    (("装机", "安装", "部署", "配置", "搭建"), "SETUP"),
    (("驱动", "环境", "调试"), "ENVIRONMENT"),
    (("出图", "结果", "效果", "成果", "实测", "测试"), "RESULTS"),
    (("复盘", "总结", "结语", "反思", "思考", "写在最后"), "REVIEW"),
    (("原理", "机制", "架构", "设计"), "HOW"),
    (("问题", "风险", "坑", "陷阱"), "PITFALLS"),
]


def en_label_for(title: str, idx: int) -> str:
    for keys, lab in EN_LABEL_MAP:
        if any(k in title for k in keys):
            return lab
    return f"PART {idx:02d}"


def split_title(title: str) -> tuple[str, str]:
    """Split an H1 into two visual cover lines at a natural boundary."""
    for sep in ("：", ":", "，", ",", "——", "—", " "):
        if sep in title:
            a, b = title.split(sep, 1)
            a, b = a.strip(), b.strip()
            if a and b:
                return a, b
    if len(title) > 6:
        mid = len(title) // 2
        return title[:mid], title[mid:]
    return title, "深度拆解"


def parse_article(md: str) -> dict:
    """Parse H1 title, intro paragraph(s), and H2 chapters with paragraphs.

    OBS-73 (根治): every non-empty line before the first "## " (INCLUDING the
    first intro line, OBS-83) is kept in intro_paras and rendered as body
    paragraphs before the first chapter title. `intro` is unchanged and still
    feeds the cover subtitle (the oneliner card was removed in hammer.3 — its
    only content was intro[:40], now redundant with the full first paragraph).
    问题 B: ``` fenced blocks are parsed as code items ({"kind": "code"}) and
    are never merged into paragraph text. Paragraph items are
    {"kind": "para", "text": ...}; code items preserve whitespace verbatim.
    """
    lines = md.replace("\r\n", "\n").split("\n")
    title = ""
    intro = ""
    intro_paras: list[dict] = []
    chapters: list[dict] = []
    cur: dict | None = None
    in_code = False
    code_buf: list[str] = []
    for ln in lines:
        st = ln.strip()
        if in_code:
            if st.startswith("```"):
                if cur is None:
                    intro_paras.append({"kind": "code", "text": "\n".join(code_buf)})
                else:
                    cur["paras"].append({"kind": "code", "text": "\n".join(code_buf)})
                code_buf = []
                in_code = False
            else:
                code_buf.append(ln)
            continue
        if st.startswith("```"):
            in_code = True
            code_buf = []
            continue
        if not title and st.startswith("# ") and not st.startswith("## "):
            title = st[2:].strip()
            continue
        if st.startswith("## ") and not st.startswith("### "):
            cur = {"title": st[3:].strip(), "paras": []}
            chapters.append(cur)
            continue
        if st.startswith("#"):
            continue
        if not st:
            continue
        if cur is None:
            if not intro:
                intro = st
            # OBS-83: the FIRST intro line must ALSO render in the body (not only
            # the cover subtitle/oneliner). Same path as every later line.
            intro_paras.append({"kind": "para", "text": st})
            continue
        cur["paras"].append({"kind": "para", "text": st})
    if in_code:  # unclosed fence: keep collected lines as a code item (lenient)
        if cur is None:
            intro_paras.append({"kind": "code", "text": "\n".join(code_buf)})
        else:
            cur["paras"].append({"kind": "code", "text": "\n".join(code_buf)})
    return {"title": title or "未命名", "intro": intro, "intro_paras": intro_paras,
            "chapters": chapters}
def render(theme_key: str, parsed: dict, body_images: list[dict]) -> tuple[str, dict]:
    title = parsed["title"]
    chapters = parsed["chapters"] or [{"title": title, "paras": [parsed.get("intro", "")]}]
    chapter_titles = [c["title"] for c in chapters]
    usage = {"cover_breaking": 0, "toc_scroll": 0, "chapter_title": 0,
             "fixed_signature": 0, "footer_cta": 0,
             "image_2a_standard": 0, "image_media_text_card": 0, "paragraph": 0}

    parts: list[str] = []

    l1, l2 = split_title(title)
    kicker = "深度观察 · " + en_label_for(chapter_titles[0] if chapter_titles else title, 1)
    subtitle = (parsed.get("intro") or "结构化拆解与要点梳理")[:48]
    parts.append(H.hammer_cover(theme_key, kicker=kicker, strike="别急着划走",
                                title_line1=l1, title_line2=l2, subtitle=subtitle))
    usage["cover_breaking"] += 1

    parts.append(H.hammer_toc(theme_key, chapter_titles))
    usage["toc_scroll"] += 1

    # OBS-73 (根治): intro paragraphs render BEFORE the first chapter title.
    # Order: cover -> intro paras -> chapter 1 title -> chapter body.
    for item in parsed.get("intro_paras") or []:
        parts.append(_render_item(theme_key, item))
        usage["paragraph"] += 1

    # distribute images across chapters: first image as media+text, rest as 2a.
    img_queue = list(body_images)
    per_chapter = _distribute(len(img_queue), len(chapters))

    for i, ch in enumerate(chapters, 1):
        parts.append(H.hammer_chapter(theme_key, f"{i:02d}", ch["title"],
                                      en_label_for(ch["title"], i)))
        usage["chapter_title"] += 1
        for item in ch["paras"]:
            parts.append(_render_item(theme_key, item))
            usage["paragraph"] += 1
        for _ in range(per_chapter[i - 1]):
            if not img_queue:
                break
            img = img_queue.pop(0)
            url = img.get("remote_url", "")
            cap = img.get("caption") or img.get("alt_text") or ""
            if usage["image_media_text_card"] == 0 and (ch["paras"] or img.get("alt_text")):
                parts.append(H.hammer_media_text(theme_key, url, cap,
                             img.get("alt_text") or cap or "图示说明"))
                usage["image_media_text_card"] += 1
            else:
                parts.append(H.hammer_image_2a(theme_key, url, cap))
                usage["image_2a_standard"] += 1

    # any leftover images -> standard 2a at the end
    for img in img_queue:
        parts.append(H.hammer_image_2a(theme_key, img.get("remote_url", ""),
                                       img.get("caption") or img.get("alt_text") or ""))
        usage["image_2a_standard"] += 1

    parts.append(H.hammer_fixed_signature(theme_key))
    usage["fixed_signature"] += 1
    parts.append(H.hammer_footer_cta(theme_key))
    usage["footer_cta"] += 1

    html = H.hammer_container(theme_key, "\n".join(parts))
    usage["chapters"] = len(chapters)
    usage["images"] = len(body_images)
    return html, usage


def _distribute(n_imgs: int, n_chapters: int) -> list[int]:
    out = [0] * max(n_chapters, 1)
    for k in range(n_imgs):
        out[k % len(out)] += 1
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Render an article to official hammer HTML")
    ap.add_argument("--article", required=True)
    ap.add_argument("--bindings", default=None,
                    help="article_image_bindings.json (real WeChat-host image URLs)")
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--theme", default="smartisan")
    a = ap.parse_args(argv)

    theme_key = THEME_ALIAS.get(a.theme.strip().lower(), None)
    if theme_key is None:
        print(f"ERROR: unsupported theme '{a.theme}' (this entry only renders hammer/smartisan)")
        return 2
    if theme_key not in H.PALETTES:
        print(f"ERROR: theme '{theme_key}' not in official PALETTES")
        return 2

    md = Path(a.article).read_text(encoding="utf-8")
    parsed = parse_article(md)

    body_images: list[dict] = []
    if a.bindings and Path(a.bindings).is_file():
        try:
            body_images = json.loads(Path(a.bindings).read_text(encoding="utf-8")).get("body_images", [])
        except (ValueError, OSError):
            body_images = []

    html, usage = render(theme_key, parsed, body_images)

    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "final.html").write_text(html, encoding="utf-8", newline="\n")
    (out / "final_runtime.html").write_text(
        H.wrap_html(html, parsed["title"]), encoding="utf-8", newline="\n")

    errors, warnings, leaf_count = validate_html(html, "final.html")
    usage_report = {"theme": theme_key, "theme_alias": a.theme,
                    "components": usage, "leaf_count": leaf_count,
                    "validator_error_count": len(errors),
                    "validator_warning_count": len(warnings)}
    (out / "component_usage_report.json").write_text(
        json.dumps(usage_report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8", newline="\n")

    moyu_green_absent = "#059669" not in html
    identity = {
        "theme": theme_key, "theme_alias": a.theme,
        "render_entry": "scripts/render_article.py",
        "component_source": "scripts/generate_hammer_upgrade_samples.py",
        "hammer_primary": H.PALETTES[theme_key]["primary"],
        "hammer_primary_present": H.PALETTES[theme_key]["primary"] in html,
        "moyu_green_absent": moyu_green_absent,
        "theme_fallback_used": not (H.PALETTES[theme_key]["primary"] in html and moyu_green_absent),
        "chapters": usage["chapters"],
        "fingerprints": {k: usage[k] for k in ("cover_breaking", "toc_scroll",
                         "chapter_title", "fixed_signature", "footer_cta",
                         "image_2a_standard", "image_media_text_card")},
    }
    (out / "theme_identity_report.json").write_text(
        json.dumps(identity, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8", newline="\n")

    print(f"[render_article] theme={theme_key} chapters={usage['chapters']} "
          f"images={usage['images']} leaf={leaf_count} "
          f"validator_errors={len(errors)}")
    return 0 if not errors else 1

def _render_item(theme_key: str, item) -> str:
    """Render one body item (paragraph or fenced code block)."""
    if isinstance(item, str) or item.get("kind") != "code":
        text = item if isinstance(item, str) else item["text"]
        return H.hammer_para(theme_key, text)
    return _hammer_code_block(theme_key, item["text"])


def _hammer_code_block(theme_key: str, text: str) -> str:
    """WeChat-friendly single-column fenced code block (OBS-91/档67C).

    每行一个 <p style="margin:0">(与 generate_advanced_html.code_compare 同构),
    不用 <pre>、不用 white-space:pre(自家 lint 判 ERROR 的特征)。可复制性与
    对齐同时成立:
    - 仅行首前导空白(空格/制表符)转 &nbsp;,保留缩进对齐;
    - 行内空格保持普通空格(可复制性:复制出来是普通空格);
    - 行内连续空格若确有折叠风险,只把该连续段中「第二个及之后」的空格转
      &nbsp;,首个保持普通空格;
    - 内容保持真实可选中文本,不截图、不伪装元素;⛔/⚠️ 前缀逐字保留。
    """
    body = H.PALETTES[theme_key]["body_color"]
    code_bg = H.PALETTES[theme_key].get("code_bg", "#F5F3F0")
    code_border = H.PALETTES[theme_key].get("code_border", "#E8E2DA")
    lines = (text or "").splitlines()
    rows = []
    for line in lines:
        # 最小 HTML 转义,再按 OBS-91 规则处理空白:
        # 1) 行首前导空白整段转 &nbsp;;
        # 2) 行内连续空白段:首个保持普通空格,第二个起转 &nbsp;。
        escaped = (line.replace("&", "&amp;").replace("<", "&lt;")
                   .replace(">", "&gt;"))
        stripped = escaped.lstrip(" \t")
        leading = escaped[: len(escaped) - len(stripped)].replace(" ", "&nbsp;").replace("\t", "&nbsp;")
        out = []
        run = 0
        for ch in stripped:
            if ch in (" ", "\t"):
                run += 1
                out.append(" " if run == 1 else "&nbsp;")
            else:
                run = 0
                out.append(ch)
        safe = leading + "".join(out)
        esc = '<span leaf="">' + safe + '</span>'
        rows.append(
            '<p style="margin:0;font-family:\'SF Mono\',Consolas,Monaco,monospace;'
            'font-size:13px;line-height:1.7;color:' + body + ';">'
            + esc + '</p>')
    return (f'<section style="margin:0 20px 16px;padding:14px 16px;'
            f'background:{code_bg};border:1px solid {code_border};'
            f'border-radius:8px;overflow-x:auto;">'
            + "".join(rows) + '</section>')

if __name__ == "__main__":
    sys.exit(main())

