#!/usr/bin/env python3
"""档71C-R4 反证假渲染器:只渲染每类一半哨兵(fake_partial)。

每类组件只输出其样本哨兵的前一半 -> 另一半 render_ok=False ->
QUARANTINED 非空且不等于全 9 类(证明名单有区分度,不是全 0 或全 1)。

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

    sentinels = re.findall(r"S_[A-Z0-9_]+", md)
    # 9 类组件字母序前 4 个完整渲染,其余 5 个丢弃 -> QUARANTINED = 后 5 个
    # (非空、非全 9,有区分度)。硬编码组件名(测试夹具,与被测结构固定对应)。
    _FULL_COMPS = {"ALERT", "CODE", "DIALOGUE", "FOOTNOTES"}
    keep = [s for s in sentinels
            if (s.split("_")[1] if len(s.split("_")) > 1 else "?") in _FULL_COMPS]
    parts = [
        f'<p style="margin:0;font-size:14px;color:#555555;line-height:1.8;">'
        f'<span leaf="">{s}</span></p>' for s in keep]
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
