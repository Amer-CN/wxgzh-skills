#!/usr/bin/env python3
"""扫描 SKILL.md 中所有本地引用，验证目标文件存在。

检查模式：
  [text](references/...)
  [text](scripts/...)
  [text](assets/...)
  <SKILL_ROOT>/scripts/...
"""
import os
import re
import sys

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_MD = os.path.join(SKILL_ROOT, "SKILL.md")

# Markdown 链接模式: [text](path)
LINK_RE = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')
# <SKILL_ROOT>/scripts/... 模式
SKILL_ROOT_RE = re.compile(r'<SKILL_ROOT>/([^\s<]+)')

dangling = []

with open(SKILL_MD, encoding="utf-8") as f:
    content = f.read()

# 检查 Markdown 链接
for m in LINK_RE.finditer(content):
    text = m.group(1)
    path = m.group(2)
    # 跳过外部 URL 和占位符
    if path.startswith("http"):
        continue
    # 跳过文档示例中的占位符 (URL, url, xxx.gif 等)
    if path in ("URL", "url", "xxx.gif", "..."):
        continue
    # 去掉锚点
    path_clean = path.split("#")[0]
    if not path_clean:
        continue
    full = os.path.join(SKILL_ROOT, path_clean)
    if not os.path.exists(full):
        dangling.append(f"[{text}]({path})")

# 检查 <SKILL_ROOT>/ 模式
for m in SKILL_ROOT_RE.finditer(content):
    path = m.group(1)
    full = os.path.join(SKILL_ROOT, path)
    if not os.path.exists(full):
        dangling.append(f"<SKILL_ROOT>/{path}")

if dangling:
    print(f"发现 {len(dangling)} 个悬空引用:")
    for d in dangling:
        print(f"  - {d}")
    sys.exit(1)
else:
    print("dangling references = 0")
    sys.exit(0)
