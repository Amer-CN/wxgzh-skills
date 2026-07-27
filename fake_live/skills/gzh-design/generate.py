#!/usr/bin/env python3
"""FAKE-LIVE shim for gzh-design's official hammer (smartisan) render entry.

Stands in for the installed generate_advanced_html.py. Emits final.html carrying
the EXACT official hammer structural fingerprints the theme-identity validator
reverse-parses, with the chapter-title count and TOC entries derived DYNAMICALLY
from the article's H2 (`## `) headings (dynamic chapter/TOC gate). Pure HTML
generation — no network, no WeChat, no side effects.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

HAMMER = "#B3593B"  # hammer primary; moyu green #059669 must be ABSENT


def count_chapters(md: str) -> list[str]:
    titles = []
    for ln in md.splitlines():
        if ln.startswith("## ") and not ln.startswith("### "):
            titles.append(ln[3:].strip())
    return titles


def build_html(titles, image_urls) -> str:
    n = len(titles)
    toc_items = "".join(f'<span style="margin-right:16px">PART {i:02d} · {t}</span>'
                        for i, t in enumerate(titles, 1))
    # cover-breaking (exactly one)
    cover = (f'<section class="cover-breaking" style="border-radius:20px;overflow:hidden;'
             f'box-shadow:0 4px 20px rgba(0,0,0,0.06)"><img src="{image_urls[0]}" alt="cover"></section>')
    # toc-scroll (exactly one) containing PART 01..0N
    toc = (f'<nav class="toc-scroll" style="overflow-x:scroll;-webkit-overflow-scrolling:touch;'
           f'white-space:nowrap">{toc_items}</nav>')
    # chapter-title x N (fingerprint used ONLY here)
    chapters = "".join(
        f'<h2 class="chapter-title" style="font-size:28px;font-weight:900;color:{HAMMER}">'
        f'{t}</h2><p>正文段落 {i}。</p>' for i, t in enumerate(titles, 1))
    # two official image component types
    img_a = (f'<figure class="image-2a" style="box-shadow:0 4px 12px -2px rgba(0,0,0,0.08)">'
             f'<img src="{image_urls[1 % len(image_urls)]}"></figure>')
    img_b = (f'<figure class="image-media-text" style="box-shadow:0 4px 16px -4px '
             f'rgba(179,89,59,0.10)"><img src="{image_urls[2 % len(image_urls)]}">'
             f'<figcaption>说明</figcaption></figure>')
    signature = '<section class="signature"><p>热闹是 AI 的，淡定可以是我们的。</p></section>'
    footer = ('<section class="footer-cta" style="background:radial-gradient(circle at center,'
              f'{HAMMER}22,transparent)"><p>关注我们</p></section>')
    return (f'<!doctype html><html lang="zh"><head><meta charset="utf-8">'
            f'<title>hammer</title></head><body data-theme="smartisan-hammer">'
            f'{cover}{toc}{chapters}{img_a}{img_b}{signature}{footer}</body></html>')


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage-dir", required=True)
    ap.add_argument("--article", required=True)
    ap.add_argument("--bindings", default=None)
    a = ap.parse_args(argv)
    sd = Path(a.stage_dir)
    sd.mkdir(parents=True, exist_ok=True)
    titles = count_chapters(Path(a.article).read_text(encoding="utf-8"))
    urls = ["http://mmbiz.qpic.cn/mmbiz_jpg/FAKE01/640"]
    if a.bindings and Path(a.bindings).is_file():
        b = json.loads(Path(a.bindings).read_text(encoding="utf-8"))
        urls = [x.get("wechat_remote_url") for x in b.get("body_images", []) if x.get("wechat_remote_url")] or urls
    html = build_html(titles, urls)
    (sd / "final.html").write_text(html, encoding="utf-8", newline="\n")
    print(json.dumps({"GZH_DESIGN_FAKE_LIVE": "ok", "theme": "smartisan-hammer",
                      "chapters": len(titles)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
