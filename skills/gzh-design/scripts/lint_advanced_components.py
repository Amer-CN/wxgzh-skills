#!/usr/bin/env python3
"""高级组件源头检查器 —— 专门扫描 references/advanced/ 下的组件文档。

与 component_lint.py 互补：
  component_lint.py          → 扫描 references/*.md（平级文件）
  lint_advanced_components.py → 扫描 references/advanced/**/*.md（嵌套文件）

沿用同一套公众号禁用规则（white-space:pre / div / class / id /
style / script / position / grid / CSS 变量 / @media），确保新增的
高级组件文档也经过确定性源头检查。

用法：
    python3 scripts/lint_advanced_components.py [skill-dir]
退出码：1 = 有 ERROR，0 = 通过。
"""

import glob
import os
import re
import sys

# (正则, 级别, 说明) —— 与 component_lint.py 完全一致的禁用规则
CHECKS = [
    (re.compile(r"white-space\s*:\s*pre", re.I), "ERROR",
     "用了 white-space:pre —— 会把 HTML 源码缩进/换行渲染成大左缩进+空行；"
     "代码块改成每行一个 <p style=\"margin:0\">，缩进用全角空格"),
    (re.compile(r"</?div[\s>]", re.I), "ERROR", "出现 <div>，应用 <section>"),
    (re.compile(r"\sclass\s*=", re.I), "ERROR", "出现 class 属性（会被公众号剥离）"),
    (re.compile(r"\sid\s*=", re.I), "ERROR", "出现 id 属性"),
    (re.compile(r"<style[\s>]", re.I), "ERROR", "出现 <style> 标签"),
    (re.compile(r"<script[\s>]", re.I), "ERROR", "出现 <script> 标签"),
    (re.compile(r"position\s*:\s*(fixed|absolute|sticky)", re.I), "ERROR",
     "position fixed/absolute/sticky 不被支持"),
    (re.compile(r"display\s*:\s*grid", re.I), "ERROR", "display:grid 不被支持"),
    (re.compile(r"var\s*\(\s*--", re.I), "ERROR", "用了 CSS 变量 var(--x)"),
    (re.compile(r"@(media|keyframes|import)", re.I), "ERROR", "@media/@keyframes/@import 不被支持"),
]

# 四周虚线框：border: ... dashed（不含方向）
FOURSIDE_DASHED = re.compile(r"border\s*:\s*[^;{}]*dashed", re.I)
CENTERED = re.compile(r"text-align\s*:\s*center", re.I)


def lint_file(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    name = os.path.relpath(path, os.path.dirname(os.path.dirname(path)))
    found = []
    seen = set()

    def add(level, msg):
        if msg not in seen:
            seen.add(msg)
            found.append((level, msg))

    for m in re.finditer(r"```html\s*\n(.*?)```", text, re.S):
        html = m.group(1)
        for rx, level, msg in CHECKS:
            if rx.search(html):
                add(level, msg)
        # 四周虚线框检查
        if FOURSIDE_DASHED.search(html) and not CENTERED.search(html):
            add("WARN", "四周虚线框 border:…dashed（正文强调请用左竖条；"
                        "仅居中的素材占位块可用 dashed）")
    return name, found


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    adv_dir = os.path.join(root, "references", "advanced")
    files = sorted(glob.glob(os.path.join(adv_dir, "**", "*.md"), recursive=True))

    if not files:
        print(f"未找到 {adv_dir}/**/*.md")
        sys.exit(1)

    total_err = total_warn = clean = 0
    print(f"📐 高级组件源头检查：{len(files)} 个文件\n")
    for path in files:
        name, found = lint_file(path)
        if not found:
            clean += 1
            continue
        errs = [m for lv, m in found if lv == "ERROR"]
        warns = [m for lv, m in found if lv == "WARN"]
        total_err += len(errs)
        total_warn += len(warns)
        print(f"── {name} ──")
        for m in errs:
            print(f"   ❌ {m}")
        for m in warns:
            print(f"   ⚠️  {m}")

    print(f"\n汇总：{clean}/{len(files)} 个文件干净，ERROR×{total_err}，WARN×{total_warn}")
    if total_err == 0 and total_warn == 0:
        print("✅ 全部高级组件文档源头无反模式")
    sys.exit(1 if total_err else 0)


if __name__ == "__main__":
    main()
