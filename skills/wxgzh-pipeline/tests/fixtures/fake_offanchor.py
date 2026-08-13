#!/usr/bin/env python3
"""档71C-R4 反证假渲染器:哨兵渲染进「不在锚集里」的 <p style>(fake_offanchor)。

把每个哨兵放进一个改过 margin 值(第一位 0->9)的 <p style=...>,该 style 不在
component_anchors.json 锚集内 -> 哨兵在 HTML 与 _body_plain_text 之间缺失
(anchor_ok=False) -> ANCHOR_GAP 非空、APPROVED 不足 9 类。

仅测试用,不进入生产路径。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


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

    # 每个哨兵一个独立 <p>,style 的 margin 第一位 0->9(不在锚集)。
    sentinels = re.findall(r"S_[A-Z0-9_]+", md)
    parts = []
    for s in sentinels:
        parts.append(
            f'<p style="margin:9px 0 0;font-size:14px;color:#555555;line-height:1.8;">'
            f'<span leaf="">{s}</span></p>')
    html = ('<section style="max-width:677px;margin:0 auto;">'
            + "".join(parts) + "</section>")
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
