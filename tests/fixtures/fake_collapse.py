#!/usr/bin/env python3
"""档71C-R3 反证测试假渲染器:多行塌陷(fake_collapse)。

模拟 render_article.py 的 CLI 接口(--article/--output-dir/--theme),把文章里
::: 组件块体的多行正文全部塌进单个 <p>(哨兵之间用字面 \\n,无 </p><p 载体、
无 <section 包裹),用于反证 struct_ok/multiline 名单能"响"。

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
    a = ap.parse_args(argv)

    md = Path(a.article).read_text(encoding="utf-8")
    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 提取所有哨兵(按出现顺序),塌进单个 <p>(字面 \n 分隔,无段落载体)。
    sentinels = re.findall(r"S_[A-Z0-9_]+|SENTINEL_[A-Z0-9]+", md)
    body = "\n".join(sentinels) if sentinels else "no sentinels"
    html = (f'<section style="max-width:677px;margin:0 auto;">'
            f'<p style="margin:0;font-size:14px;color:#555555;line-height:1.8;">'
            f'<span leaf="">{body}</span></p></section>')

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
