#!/usr/bin/env python3
"""修复 HTML 属性中的中文引号 —— 将 style=「...」 等替换为 style="..."

根因：AI 模型生成 HTML 时将全角标点规则错误应用到 HTML 属性引号。
此脚本在生成后做确定性修复。

v2 改进：不再使用固定属性白名单（style/leaf/src/...），而是扫描所有 HTML
标签内的所有属性。否则遇到 cx/cy/r/stroke-linecap/stroke-linejoin/aria-*/
data-* 等会漏检。检测逻辑与 validate_gzh_html.py 共享同一套，确保修复与
校验完全一致。
"""
import os
import sys

# 与 validate_gzh_html.py 共享同一套检测逻辑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate_gzh_html import (
    TAG_RE,
    ANY_CN_QUOTED_ATTR,
    CN_QUOTE_PAIRS,
    find_cn_quoted_attrs,
)


def fix_html_attribute_quotes(html):
    """将 HTML 属性中的中文引号替换为 ASCII 双引号。

    扫描所有 <...> 标签内的所有属性（不限白名单），逐标签修复，避免跨标签
    误替换。返回 (修复后 HTML, 修复处数)。
    """
    fixes = 0
    result = []
    last_end = 0

    for tag_m in TAG_RE.finditer(html):
        # 先把标签前的正文原样保留
        result.append(html[last_end:tag_m.start()])
        tag_text = tag_m.group(0)

        # 在本标签内逐个修复中文引号属性
        fixed_tag_parts = []
        tag_pos = 0
        for attr_m in ANY_CN_QUOTED_ATTR.finditer(tag_text):
            attr_name = attr_m.group(1)
            open_quote = attr_m.group(2)
            close_quote = CN_QUOTE_PAIRS.get(open_quote, open_quote)

            value_start = attr_m.end()
            close_idx = tag_text.find(close_quote, value_start)
            if close_idx == -1:
                # 找不到配对闭引号，跳过（不修复这一处）
                continue

            fixed_tag_parts.append(tag_text[tag_pos:attr_m.start()])
            fixed_tag_parts.append(attr_name + '="')
            fixed_tag_parts.append(tag_text[value_start:close_idx])
            fixed_tag_parts.append('"')
            tag_pos = close_idx + 1
            fixes += 1

        fixed_tag_parts.append(tag_text[tag_pos:])
        result.append(''.join(fixed_tag_parts))
        last_end = tag_m.end()

    result.append(html[last_end:])
    return ''.join(result), fixes


def fix_rgba_green(html):
    """修复锤子主题 rgba(5,150,105,...) 绿色残留 → rgba(179,89,59,...)"""
    rgba_fixes = 0
    for old, new in [
        ('rgba(5,150,105,0.15)', 'rgba(179,89,59,0.15)'),
        ('rgba(5,150,105,0.12)', 'rgba(179,89,59,0.10)'),
        ('rgba(5,150,105,0.10)', 'rgba(179,89,59,0.10)'),
        ('rgba(5,150,105,0.08)', 'rgba(179,89,59,0.08)'),
        ('rgba(5,150,105,0.2)', 'rgba(179,89,59,0.18)'),
    ]:
        count = html.count(old)
        if count:
            html = html.replace(old, new)
            rgba_fixes += count
    return html, rgba_fixes


def main():
    if len(sys.argv) < 2:
        print("用法: fix_html_quotes.py <file.html>")
        sys.exit(1)

    filepath = sys.argv[1]
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    fixed_html, fixes = fix_html_attribute_quotes(html)
    fixed_html, rgba_fixes = fix_rgba_green(fixed_html)

    total = fixes + rgba_fixes
    if total > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_html)
        print(f"修复 {fixes} 处中文引号 -> ASCII 双引号")
        if rgba_fixes:
            print(f"修复 {rgba_fixes} 处 rgba(5,150,105) -> rgba(179,89,59)")
    else:
        print("未发现问题")

    # 验证：用共享逻辑重新扫描，确认 0 命中
    remaining = find_cn_quoted_attrs(fixed_html)
    if remaining:
        print(f"警告: 仍有 {len(remaining)} 处未修复: "
              + ", ".join(f"{n}={q}" for n, q in remaining[:5]))
    else:
        print("所有中文引号属性已修复 OK")

    if 'rgba(5,150,105' in fixed_html:
        print("警告: 仍有 rgba(5,150,105) 残留")
    else:
        print("无 rgba(5,150,105) 残留 OK")


if __name__ == "__main__":
    main()
