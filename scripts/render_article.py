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
import generate_advanced_html as ADV  # OBS-108:import 零写盘(OUT 已移入 main)
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
    code_lang = ""
    in_component = False
    component_buf: list[str] = []
    component_name = ""
    component_head = ""
    scattered_fns: list[str] = []  # 1g(OBS-128):正文散落 [^N]: 定义行
    for ln in lines:
        st = ln.strip()
        if in_component:
            if st.startswith(":::"):
                item = {"kind": "component", "name": component_name,
                        "head": component_head,
                        "body": "\n".join(component_buf)}
                if cur is None:
                    intro_paras.append(item)
                else:
                    cur["paras"].append(item)
                component_buf = []
                in_component = False
            else:
                component_buf.append(ln)
            continue
        if st.startswith(":::"):
            # 高级组件块:仅识别 A 组 9 类;未知名记录为 component(渲染时进 unknown)
            in_component = True
            component_buf = []
            head = st[3:].strip()
            component_name = head.split()[0] if head.split() else ""
            component_head = head
            continue
        if in_code:
            if st.startswith("```"):
                if cur is None:
                    intro_paras.append({"kind": "code", "text": "\n".join(code_buf),
                                        "language": code_lang})
                else:
                    cur["paras"].append({"kind": "code", "text": "\n".join(code_buf),
                                         "language": code_lang})
                code_buf = []
                in_code = False
            else:
                code_buf.append(ln)
            continue
        if st.startswith("```"):
            in_code = True
            code_buf = []
            code_lang = ln.strip()[3:].strip()
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
        # 1g(OBS-128):散落 [^N]: 定义行 → 收集,不当作正文段落渲染。
        if re.match(r"^\[\^\d+\]\s*:", st):
            scattered_fns.append(st)
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
    # 1g(OBS-128):正文散落 [^N]: 定义 → 若无 :::footnotes 块,自动追加 footnotes 组件
    # (与显式块产出 HTML 一致)。已显式用块的不重复追加。
    has_footnotes_block = any(
        (p2.get("kind") == "component" and p2.get("name") == "footnotes")
        for ch in chapters for p2 in ch.get("paras", [])) or any(
        p2.get("kind") == "component" and p2.get("name") == "footnotes"
        for p2 in intro_paras)
    if scattered_fns and not has_footnotes_block:
        fn_item = {"kind": "component", "name": "footnotes",
                   "head": ":::footnotes", "body": "\n".join(scattered_fns)}
        if cur is not None:
            cur["paras"].append(fn_item)
        else:
            intro_paras.append(fn_item)
    return {"title": title or "未命名", "intro": intro, "intro_paras": intro_paras,
            "chapters": chapters}
def render(theme_key: str, parsed: dict, body_images: list[dict]) -> tuple[str, dict]:
    title = parsed["title"]
    chapters = parsed["chapters"] or [{"title": title, "paras": [parsed.get("intro", "")]}]
    chapter_titles = [c["title"] for c in chapters]
    usage = {"cover_breaking": 0, "toc_scroll": 0, "chapter_title": 0,
             "fixed_signature": 0, "footer_cta": 0,
             "image_2a_standard": 0, "image_media_text_card": 0, "paragraph": 0,
             "code_block": 0, "components": {}, "unknown": [], "unknown_count": 0}

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
        parts.append(_render_item(theme_key, item, usage))
        if isinstance(item, dict) and item.get("kind") in ("code", "component"):
            continue
        usage["paragraph"] += 1

    # distribute images across chapters: first image as media+text, rest as 2a.
    img_queue = list(body_images)
    per_chapter = _distribute(len(img_queue), len(chapters))

    for i, ch in enumerate(chapters, 1):
        parts.append(H.hammer_chapter(theme_key, f"{i:02d}", ch["title"],
                                      en_label_for(ch["title"], i)))
        usage["chapter_title"] += 1
        for item in ch["paras"]:
            parts.append(_render_item(theme_key, item, usage))
            if isinstance(item, dict) and item.get("kind") in ("code", "component"):
                continue
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

# OBS-106(档71C-1):A 组 9 类组件 -> generate_advanced_html.py 官方 builder。
# R11:零手写 HTML;未知名组件不静默降级,由 render() 计入 unknown。
_COMPONENT_BUILDERS = {
    "alert": ADV.alert, "quote": ADV.quote, "code-compare": ADV.code_compare,
    "media-text": ADV.media_text, "gallery": ADV.gallery,
    "long-image": ADV.long_image, "resources": ADV.resources,
    "footnotes": ADV.footnotes, "dialogue": ADV.dialogue,
}


def _render_item(theme_key: str, item, usage: dict) -> str:
    """Render one body item (paragraph / fenced code block / ::: component)."""
    if isinstance(item, str):
        return H.hammer_para(theme_key, item)
    kind = item.get("kind")
    if kind == "code":
        usage["code_block"] += 1
        return _hammer_code_block(theme_key, item["text"], item.get("language", ""))
    if kind == "component":
        name = item.get("name", "")
        builder = _COMPONENT_BUILDERS.get(name)
        if builder is None:
            usage["unknown"].append({"name": name,
                                     "head": item.get("head", "")[:120]})
            usage["unknown_count"] += 1
            return ""
        usage["components"][name] = usage["components"].get(name, 0) + 1
        return _render_component(builder, item)
    return H.hammer_para(theme_key, item.get("text", ""))


def _render_component(builder, item) -> str:
    """按 references/advanced-components.md 输入语法取参调用 builder。

    解析 :::name key="val" 头部参数 + 块内行;参数缺失用 builder 默认值。
    tid 固定为 "hammer"(smartisan 别名映射的主题 id)。
    """
    import re as _re
    head = item.get("head", "")
    body = item.get("body", "")
    args = {"tid": "hammer"}
    for m in _re.finditer(r'([\w-]+)="([^"]*)"', head):
        args[m.group(1)] = m.group(2)
    name = item.get("name", "")
    if name == "alert":
        # 1f(OBS-127):文档 type= 优先,兼容 typ=。
        typ = args.get("type") or args.get("typ") or "warning"
        args.setdefault("title", "风险提示")
        args.setdefault("body", body.strip() or "提示内容")
        return builder(args["tid"], typ=typ, title=args["title"], body=args["body"])
    if name == "quote":
        # 1f(OBS-127):文档 type= 优先,兼容 qt=。
        qt = args.get("type") or args.get("qt") or "highlight"
        args.setdefault("text", body.strip() or "金句")
        return builder(args["tid"], qt=qt, text=args["text"])
    if name == "code-compare":
        # 1d(OBS-124):@before/@after 支持续行直到 @end;同行 lang="..." 解析为语言标签,
        # 不串入代码正文。@before lang="python" → 语言标签作 title 后缀(不污染代码)。
        before = after = ""
        before_lang = after_lang = ""
        cur = None
        for l in body.splitlines():
            st = l.strip()
            if st.startswith("@before"):
                cur = "before"
                m = _re.search(r"lang=\"([^\"]*)\"", st)
                if m:
                    before_lang = m.group(1)
                cont = st[len("@before"):]
                cont = _re.sub(r"lang=\"[^\"]*\"", "", cont).strip()
                if cont:
                    before = cont
                continue
            if st.startswith("@after"):
                cur = "after"
                m = _re.search(r"lang=\"([^\"]*)\"", st)
                if m:
                    after_lang = m.group(1)
                cont = st[len("@after"):]
                cont = _re.sub(r"lang=\"[^\"]*\"", "", cont).strip()
                if cont:
                    after = cont
                continue
            if st.startswith("@end"):
                cur = None
                continue
            if cur == "before":
                before = (before + "\n" if before else "") + l
            elif cur == "after":
                after = (after + "\n" if after else "") + l
        args.setdefault("title", "改前与改后")
        if before_lang:
            args["title"] += f"（{before_lang}）"
        return builder(args["tid"], title=args["title"], bc=before, ac=after)
    if name == "media-text":
        # 1c(OBS-126):块体 ![说明](url) 解析为图 URL + 说明;剩余行作解释段(多行逐行)。
        m_img = _re.search(r"!\[([^\]]*)\]\(([^)]+)\)", body)
        url = args.get("url") or args.get("image") or ""
        cap = args.get("cap")
        exp_lines = []
        for l in body.splitlines():
            if _re.match(r"^!\[[^\]]*\]\([^)]+\)", l.strip()):
                continue
            if l.strip():
                exp_lines.append(l)
        if m_img:
            cap = cap or m_img.group(1)
            url = url or m_img.group(2)
        args.setdefault("cap", cap or "图示说明")
        args["exp"] = "\n".join(exp_lines).strip()
        return builder(args["tid"], url=url, cap=args["cap"], exp=args["exp"] or " ")
    if name == "gallery":
        urls = _re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", body)
        imgs = [(u, c) for c, u in urls] if urls else None
        args.setdefault("title", "图集")
        return builder(args["tid"], title=args["title"], imgs=imgs)
    if name == "long-image":
        # 1e(OBS-125):文档 image=/caption= 优先,兼容 url=/cap=;缺 caption 不出说明行。
        url = args.get("image") or args.get("url") or ""
        cap = args.get("caption") or args.get("cap")
        return builder(args["tid"], url=url, cap=cap or "")
    if name == "resources":
        links = _re.findall(r"- \[([^\]]*)\]\(([^)]+)\)", body)
        args.setdefault("title", "参考资料")
        return builder(args["tid"], title=args["title"],
                       links=[(c, u) for c, u in links] if links else None)
    if name == "footnotes":
        # 1g(OBS-128):块体 [^N]: 定义 + 正文散落 [^N](由 parse_article 收集) 两种写法。
        fns = [(m.group(1), m.group(2))
               for m in _re.finditer(r"\[\^(\d+)\]\s*:\s*(.+)", body)]
        return builder(args["tid"], fns=fns if fns else None)
    if name == "dialogue":
        turns = []
        for l in body.splitlines():
            if l.startswith("@user:"):
                turns.append(("user", l[len("@user:"):].strip()))
            elif l.startswith("@assistant:"):
                turns.append(("assistant", l[len("@assistant:"):].strip()))
        args.setdefault("title", "排障问答")
        return builder(args["tid"], title=args["title"],
                       turns=turns if turns else None)
    # 不可达:name 已在 _COMPONENT_BUILDERS 校验
    return ""


def _hammer_code_block(theme_key: str, text: str, language: str = "") -> str:
    """OBS-91/档67D:委托官方 hammer_code_block 组件(common-components 1a)。

    本文件不手写任何 hammer HTML(文件头声明为真);结构/色值/缩进规则全部
    来自 generate_hammer_upgrade_samples.hammer_code_block。
    """
    return H.hammer_code_block(language, text)

if __name__ == "__main__":
    sys.exit(main())

