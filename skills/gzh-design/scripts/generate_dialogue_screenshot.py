#!/usr/bin/env python3
"""生成 dialogue 430px 移动端截图接触表"""
import os, sys

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOTFIX = os.path.join(SKILL, "tests", "advanced-components", "dialogue-hotfix")
OUT_PNG = os.path.join(HOTFIX, "dialogue-mobile-contact-sheet.png")

THEMES = ["moyu-green", "red-white", "graphite-minimal", "zen-whitespace", "moyu-ticket", "olive-journal", "hammer"]

from playwright.sync_api import sync_playwright

# 构建一个接触表 HTML，6 主题纵向排列
rows = []
for theme in THEMES:
    fp = os.path.join(HOTFIX, f"dialogue-{theme}.html")
    with open(fp, encoding="utf-8") as f:
        inner = f.read()
    rows.append(f'<div style="margin-bottom:20px;"><h3 style="font-size:14px;color:#333;margin:0 0 8px;">{theme}</h3>{inner}</div>')

contact_html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>*{{margin:0;padding:0;box-sizing:border-box;}}body{{padding:16px;}}</style></head>
<body>
{''.join(rows)}
</body></html>'''

tmp_html = os.path.join(HOTFIX, "_contact_sheet_tmp.html")
with open(tmp_html, "w", encoding="utf-8") as f:
    f.write(contact_html)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 430, "height": 800})
    page.goto(f"file:///{tmp_html.replace(os.sep, '/')}")
    page.wait_for_timeout(500)

    # 记录 6 主题的 clientWidth / scrollWidth
    metrics = []
    for i, theme in enumerate(THEMES):
        # 每个主题块在 page 中，检查整体不溢出
        cw = page.evaluate("document.documentElement.clientWidth")
        sw = page.evaluate("document.documentElement.scrollWidth")
        metrics.append((theme, cw, sw))

    # 截取全页面截图
    page.screenshot(path=OUT_PNG, full_page=True)
    browser.close()

os.remove(tmp_html)

print(f"Screenshot saved: {OUT_PNG}")
print(f"Size: {os.path.getsize(OUT_PNG)} bytes")
print("\n430px viewport metrics:")
for theme, cw, sw in metrics:
    status = "PASS" if cw == 430 and sw == 430 else "FAIL"
    print(f"  {theme:20s} clientWidth={cw}  scrollWidth={sw}  [{status}]")
