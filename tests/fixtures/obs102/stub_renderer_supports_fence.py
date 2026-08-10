#!/usr/bin/env python3
"""档71B'-C 第 4 步:免悖论验证用最小渲染器(stub)。

CLI 与生产渲染器一致(--article / --bindings / --output-dir / --theme)。
行为 = 解析 :::alert 块并把块内每行输出成与 _PARA_RE 同形态的正文段落,
写出 final.html —— 模拟 71C 接线后渲染器支持 ::: 的情形。

★只用于测试(免悖论用例);禁止放进 scripts/、禁止被任何生产代码 import。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="stub renderer supporting :::alert")
    ap.add_argument("--article", required=True)
    ap.add_argument("--bindings", default=None)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--theme", default="smartisan")
    ap.add_argument("--strike", default="")
    ap.add_argument("--brand", default="")
    ap.add_argument("--tags", default="")
    ap.add_argument("--kicker", default="")

    a = ap.parse_args(argv)

    md = Path(a.article).read_text(encoding="utf-8")
    lines = md.splitlines()
    paras = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith(":::"):
            # 收集 alert 块内每行(不含围栏行),渲染成 hammer_para 同形态段落
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(":::"):
                body = lines[i].strip()
                if body:
                    paras.append(
                        f'<p style="margin-bottom:16px;font-size:14px;line-height:1.9;'
                        f'text-align:justify;"><span leaf="">{body}</span></p>')
                i += 1
        elif ln.strip().startswith("#"):
            pass  # 标题行跳过
        elif ln.strip():
            body = ln.strip()
            paras.append(
                f'<p style="margin-bottom:16px;font-size:14px;line-height:1.9;'
                f'text-align:justify;"><span leaf="">{body}</span></p>')
        i += 1

    html = "".join(paras)
    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "final.html").write_text(html, encoding="utf-8", newline="\n")
    print(f"[stub render_article] paragraphs={len(paras)} simulated=True")
    return 0


if __name__ == "__main__":
    sys.exit(main())
