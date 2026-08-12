#!/usr/bin/env python3
"""FAKE-LIVE shim mirroring gzh-design `scripts/render_article.py`.

EXACT real CLI: --article / --bindings / --output-dir / --theme. Emits
final.html / final_runtime.html / component_usage_report.json /
theme_identity_report.json with the official hammer structural fingerprints and
chapters derived DYNAMICALLY from the article's `## ` headings. Also writes
gzh_exec_receipt.json marked simulated=true — a SIMULATED executor's output must
NEVER be presented as an official gzh-design call (theme identity can only be
OFFICIAL with a real gzh execution receipt). No network, no side effects.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HAMMER = "#B3593B"  # moyu-green #059669 must be ABSENT


def chapters_of(md: str) -> list[str]:
    return [ln[3:].strip() for ln in md.splitlines()
            if ln.startswith("## ") and not ln.startswith("### ")]


def build_html(title: str, titles: list[str], images: list[dict],
               intro_paras: list[str] | None = None) -> str:
    p = []
    # cover-breaking (fingerprint + safe strikethrough)
    p.append(
        f'<section style="margin:0 0 32px;background:#fff;border:1.5px solid rgba(179,89,59,0.15);'
        f'border-radius:20px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.06);">'
        f'<p style="font-size:15px;color:#737373;text-decoration:line-through;'
        f'text-decoration-color:#737373;text-decoration-thickness:1px;"><span leaf="">别急着划走</span></p>'
        f'<p style="font-size:24px;font-weight:900;color:{HAMMER};"><span leaf="">{title}</span></p>'
        f'</section>')
    # toc-scroll (fingerprint + PART 01..0N + ///)
    cards = "".join(
        f'<section style="display:inline-block;width:110px;"><p style="font-size:9px;font-weight:700;">'
        f'<span leaf="">PART {i:02d}</span></p><p style="font-size:13px;font-weight:800;">'
        f'<span leaf="">{t}</span></p></section>'
        for i, t in enumerate(titles, 1))
    p.append(
        f'<section style="margin:0 20px 32px;"><section style="overflow-x:scroll;'
        f'-webkit-overflow-scrolling:touch;white-space:nowrap;padding-bottom:8px;">{cards}'
        f'<section style="display:inline-block;width:110px;"><p style="font-size:9px;font-weight:700;">'
        f'<span leaf="">PART ///</span></p><p style="font-size:13px;font-weight:800;">'
        f'<span leaf="">写在最后</span></p></section></section></section>')
    # intro paragraphs BEFORE the first chapter (OBS-73, mirrors the real
    # renderer: first line also feeds cover subtitle/oneliner truncation)
    for para in intro_paras or []:
        p.append(
            f'<section style="margin:0 20px;"><p style="margin-bottom:16px;font-size:14px;'
            f'line-height:1.9;text-align:justify;color:#555555;"><span leaf="">{para}</span></p></section>')
    # chapters (fingerprint exactly once per chapter) + images
    img_q = list(images)
    for i, t in enumerate(titles, 1):
        p.append(
            f'<section style="margin-top:48px;padding:0 20px;">'
            f'<p style="margin:0;font-size:28px;font-weight:900;color:{HAMMER};line-height:1;">'
            f'<span leaf="">{i:02d}</span></p>'
            f'<p style="font-size:17px;font-weight:800;color:#555555;"><span leaf="">{t}</span></p>'
            f'<p style="font-size:14px;line-height:1.9;color:#555555;">'
            f'<span leaf="">本章围绕{t}展开说明。</span></p></section>')
        if img_q:
            img = img_q.pop(0)
            url = img.get("remote_url", "")
            if i == 1:
                # media+text card (fingerprint 0 4px 16px -4px rgba(179,89,59,0.10))
                p.append(
                    f'<section style="margin:0 0 8px;background:#F7F7F7;border-radius:12px;padding:6px;'
                    f'box-shadow:0 4px 16px -4px rgba(179,89,59,0.10);">'
                    f'<span leaf=""><img src="{url}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span>'
                    f'</section><p style="font-size:14px;color:#555555;"><span leaf="">图文说明。</span></p>')
            else:
                # standard 2a (fingerprint 0 4px 12px -2px rgba(0,0,0,0.08))
                p.append(
                    f'<section style="background:#FFF;border-radius:12px;padding:6px;'
                    f'box-shadow:0 4px 12px -2px rgba(0,0,0,0.08);margin-bottom:8px;">'
                    f'<span leaf=""><img src="{url}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span>'
                    f'</section>')
    for img in img_q:
        p.append(
            f'<section style="background:#FFF;border-radius:12px;padding:6px;'
            f'box-shadow:0 4px 12px -2px rgba(0,0,0,0.08);margin-bottom:8px;">'
            f'<span leaf=""><img src="{img.get("remote_url", "")}" style="max-width:100%;height:auto;display:block;margin:0 auto;"></span>'
            f'</section>')
    # fixed signature (authoritative 文案)
    p.append(
        f'<section style="padding:0 20px 24px;">'
        f'<p style="font-size:15px;color:#555555;"><span leaf="">好了，今天就先聊到这儿。</span></p>'
        f'<section style="border-left:3px solid {HAMMER};background:#EAD6CC;padding:10px 14px;">'
        f'<p style="font-size:14px;font-weight:600;color:#8A4530;"><span leaf="">热闹是 AI 的，淡定可以是我们的。</span></p>'
        f'<p style="font-size:14px;font-weight:600;color:#8A4530;"><span leaf="">不用马上跟上，知道一点，就不算掉队。</span></p></section>'
        f'<p style="font-size:12px;color:#737373;"><span leaf="">/ 作者 给自己造把锤子</span></p>'
        f'<p style="font-size:12px;color:#737373;"><span leaf="">/ 投稿或反馈，请联系邮箱：cd.hyxc.jz@foxmail.com</span></p></section>')
    # footer-cta (fingerprint radial-gradient(circle at center,)
    p.append(
        f'<section style="background:radial-gradient(circle at center,#FAF9F5 0%,#FFFFFF 100%);'
        f'border-radius:16px;padding:32px 20px;text-align:center;margin:0 20px 24px;">'
        f'<p style="font-size:13px;font-weight:bold;color:#555555;">'
        f'<span leaf="">既然看到这里了，随手点个赞、在看、转发三连吧。</span></p>'
        f'<p style="font-size:10px;color:#737373;"><span leaf="">THANKS FOR READING</span></p></section>')
    return ('<section style="max-width:677px;margin:0 auto;background:#ffffff;color:#555555;">'
            + "\n".join(p) + "</section>")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="render_article (fake-live shim)")
    ap.add_argument("--article", required=True)
    ap.add_argument("--bindings", default=None)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--theme", default="smartisan")
    ap.add_argument("--date", default=None)   # 档HF-6/72E-1:与真实 CLI 对齐
    ap.add_argument("--strike", default=None)
    ap.add_argument("--brand", default=None)
    ap.add_argument("--tags", default=None)
    ap.add_argument("--kicker", default=None)
    ap.add_argument("--title", default=None)   # 档76D/OBS-257:与真实 CLI 对齐
    ap.add_argument("--subtitle", default=None)
    a = ap.parse_args(argv)
    if a.theme.strip().lower() not in ("smartisan", "hammer"):
        print(f"ERROR: unsupported theme {a.theme}"); return 2

    md = Path(a.article).read_text(encoding="utf-8")
    title = next((ln[2:].strip() for ln in md.splitlines()
                  if ln.startswith("# ") and not ln.startswith("## ")), "未命名")
    if a.title:
        title = a.title
    titles = chapters_of(md) or [title]
    intro_paras = []
    title_seen = False
    for ln in md.splitlines():
        st = ln.strip()
        if not title_seen and st.startswith("# ") and not st.startswith("## "):
            title_seen = True
            continue
        if st.startswith("## ") and not st.startswith("### "):
            break
        if st.startswith("#") or not st:
            continue
        intro_paras.append(st)
    images = []
    if a.bindings and Path(a.bindings).is_file():
        images = json.loads(Path(a.bindings).read_text(encoding="utf-8")).get("body_images", [])

    html = build_html(title, titles, images, intro_paras)
    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "final.html").write_text(html, encoding="utf-8", newline="\n")
    (out / "final_runtime.html").write_text(
        "<!DOCTYPE html>\n<html lang=\"zh-CN\"><head><meta charset=\"UTF-8\"></head>"
        f"<body style=\"margin:0;background:#f5f5f5;\">{html}</body></html>",
        encoding="utf-8", newline="\n")

    usage = {"simulated": True, "theme": "hammer", "chapters": len(titles),
             "images": len(images),
             "components": {"cover_breaking": 1, "toc_scroll": 1,
                            "chapter_title": len(titles), "fixed_signature": 1,
                            "footer_cta": 1,
                            "image_media_text_card": 1 if images else 0,
                            "image_2a_standard": max(len(images) - 1, 0)}}
    (out / "component_usage_report.json").write_text(
        json.dumps(usage, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    identity = {"simulated": True, "theme": "hammer", "theme_alias": a.theme,
                "render_entry": "FAKE-LIVE shim render_article.py",
                "official_gzh_call": False,
                "note": "simulated executor — must NOT be reported as an official gzh-design call",
                "chapters": len(titles), "hammer_primary_present": HAMMER in html,
                "moyu_green_absent": "#059669" not in html, "theme_fallback_used": False}
    (out / "theme_identity_report.json").write_text(
        json.dumps(identity, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    # simulated execution receipt (theme identity can only be OFFICIAL with a REAL one)
    me = Path(__file__)
    (out / "gzh_exec_receipt.json").write_text(json.dumps({
        "simulated": True, "official": False,
        "render_entry_path": str(me), "render_entry_sha256": hashlib.sha256(me.read_bytes()).hexdigest(),
        "component_source_path": None, "component_source_sha256": None,
        "gzh_commit": None,
    }, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    print(f"[fake render_article] chapters={len(titles)} images={len(images)} simulated=True")
    return 0


if __name__ == "__main__":
    sys.exit(main())
