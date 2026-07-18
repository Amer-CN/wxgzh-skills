#!/usr/bin/env python3
"""将生产 HTML 模板写入高级组件文档 —— 不再依赖 tests/expected 作为模板来源"""
import os

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADV = os.path.join(SKILL, "references", "advanced")
EXPECTED = os.path.join(SKILL, "tests", "advanced-components", "expected")

def read_template(component, theme="moyu-green"):
    """从已生成的验收 HTML 中读取一个代表性模板"""
    path = os.path.join(EXPECTED, f"{component}-{theme}.html")
    with open(path, encoding="utf-8") as f:
        return f.read().strip()

def append_template(doc_path, component, theme="moyu-green"):
    """在组件文档末尾追加生产 HTML 模板段"""
    html = read_template(component, theme)
    template_section = f"""

---

## 生产 HTML 模板（{theme} 主题示例）

> 其他主题使用相同结构，仅替换 `theme-adapters.md` 中的色值令牌。

```html
{html}
```

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/{component}-*.html`（验收产物，非生产依赖）。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。
"""
    with open(doc_path, "r", encoding="utf-8") as f:
        content = f.read()
    # 去掉旧的模板段（如果有）
    marker = "\n\n---\n\n## 生产 HTML 模板"
    if marker in content:
        content = content[:content.index(marker)]
    content += template_section
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(content)

DOCS = {
    "alerts.md": "alert",
    "quotes.md": "quote",
    "code-compare.md": "code-compare",
    "media.md": "media-text",  # 用 media-text 作为代表
    "links-resources.md": "resources",
    "footnotes.md": "footnotes",
    "dialogue.md": "dialogue",
}

for doc_name, comp_id in DOCS.items():
    doc_path = os.path.join(ADV, doc_name)
    if os.path.exists(doc_path):
        append_template(doc_path, comp_id)
        print(f"OK: {doc_name} <- {comp_id} template")

# media.md 需要额外追加 gallery 和 long-image 的模板
media_path = os.path.join(ADV, "media.md")
if os.path.exists(media_path):
    for comp in ["gallery", "long-image"]:
        html = read_template(comp)
        with open(media_path, "a", encoding="utf-8") as f:
            f.write(f"\n\n### {comp} 模板（moyu-green）\n\n```html\n{html}\n```\n")
        print(f"OK: media.md <- {comp} template")

print("\nAll component docs updated with production HTML templates.")
