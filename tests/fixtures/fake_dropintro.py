#!/usr/bin/env python3
"""档71C-R5 陷阱反证假渲染器:丢弃首个 "## " 之前的所有非组件正文行(fake_dropintro)。

模拟渲染器吞导语:首个 ## 之前的普通正文行(非 ::: 块)全部丢弃;
::: 组件块内的文本与 head title="X" 照常渲染进锚集内 style 的 <p>。
用于 R37 反证:导语段被吞 + 组件同名文本在正文区 -> guard 假绿是否可构造。

仅测试用,不进入生产路径。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_P_STYLE = 'margin:0;font-size:14px;color:#555555;line-height:1.8;'


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--article", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--theme", default="smartisan")
    ap.add_argument("--strike", default="")
    ap.add_argument("--brand", default="")
    ap.add_argument("--tags", default="")
    ap.add_argument("--kicker", default="")

    a = ap.parse_args(argv)

    md = Path(a.article).read_text(encoding="utf-8")
    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    lines = md.splitlines()
    body_parts: list[str] = []
    seen_h2 = False
    in_component = False

    def emit(text: str):
        body_parts.append(
            f'<p style="{_P_STYLE}"><span leaf="">{text}</span></p>')

    for ln in lines:
        st = ln.strip()
        if in_component:
            if st.startswith(":::"):
                in_component = False
                continue
            m = re.search(r'title="([^"]*)"', st)
            if m and m.group(1):
                emit(m.group(1))
                continue
            if st.startswith(("@", "[^", "![", "- [")) or not st:
                continue
            emit(st)
            continue
        if st.startswith(":::"):
            # 开标签行:提取 title="X" 渲染(模拟真渲染器 title 渲染)
            m = re.search(r'title="([^"]*)"', st)
            if m and m.group(1):
                emit(m.group(1))
            in_component = True
            continue
        if st.startswith("## "):
            seen_h2 = True
            continue
        if not seen_h2:
            continue  # 首个 ## 之前的非组件正文行被丢弃(模拟吞导语)
        if not st or st.startswith("#"):
            continue
        emit(st)

    html = ('<section style="max-width:677px;margin:0 auto;">'
            + "".join(body_parts) + "</section>")
    (out / "final.html").write_text(html, encoding="utf-8", newline="\n")
    usage = {"theme": "hammer", "components": {
        "cover_breaking": 0, "toc_scroll": 0, "chapter_title": 0,
        "fixed_signature": 0, "footer_cta": 0,
        "image_2a_standard": 0, "image_media_text_card": 0,
        "paragraph": 0, "code_block": 0, "components": {},
        "unknown": [], "unknown_count": 0, "unknown_component_args": []},
        "leaf_count": 1, "validator_error_count": 0,
        "validator_warning_count": 0}
    (out / "component_usage_report.json").write_text(
        json.dumps(usage, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
