#!/usr/bin/env python3
"""生成锤子升级双主题 430px 截图。

使用 Playwright 在 430x800 视口下对两份 HTML 进行全页截图。
"""
import os
import sys

SKILL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(SKILL, "tests", "hammer-upgrade")

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright not installed. Installing...")
    os.system(f"{sys.executable} -m pip install playwright")
    os.system(f"{sys.executable} -m playwright install chromium")
    from playwright.sync_api import sync_playwright


def screenshot(html_path, png_path, viewport_width=430, viewport_height=800):
    """在指定视口下对 HTML 进行全页截图"""
    file_url = f"file:///{os.path.abspath(html_path).replace(os.sep, '/')}"
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height},
            device_scale_factor=2,
        )
        page = context.new_page()
        page.goto(file_url, wait_until="networkidle")

        # 检查横向溢出
        overflow = page.evaluate(
            f"() => document.documentElement.scrollWidth > {viewport_width}"
        )

        # 获取实际内容宽度
        cw = page.evaluate("() => document.documentElement.clientWidth")
        sw = page.evaluate("() => document.documentElement.scrollWidth")

        page.screenshot(path=png_path, full_page=True)
        browser.close()

        print(f"  Screenshot: {png_path}")
        print(f"  clientWidth={cw}, scrollWidth={sw}, overflow={'YES' if overflow else 'NO'}")
        return not overflow


if __name__ == "__main__":
    results = {}
    for html, png in [
        ("reference-moyu-green.html", "reference-moyu-green-430.png"),
        ("target-hammer.html", "target-hammer-430.png"),
    ]:
        html_path = os.path.join(OUT, html)
        png_path = os.path.join(OUT, png)
        print(f"Processing: {html}")
        ok = screenshot(html_path, png_path)
        results[html] = ok

    print("\n=== Summary ===")
    for html, ok in results.items():
        status = "PASS" if ok else "FAIL"
        print(f"  {html}: {status} (no horizontal overflow: {ok})")
