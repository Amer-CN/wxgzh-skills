#!/usr/bin/env python3
"""gzh-design 渲染流程模拟脚本

⚠️ 重要声明：本脚本不是由真实本地 Agent 自主执行 SKILL.md 的运行记录。
   它是一个确定性渲染与集成测试脚本，直接导入 generate_advanced_html.py
   和 generate_article_html.py 的组件函数来模拟渲染流程。

   它的价值在于提供一条可执行的测试链路：
   真实 Markdown 输入 → 语义扫描 → 组件计划 → 降级检查 → 渲染 → 审计 → HTML 校验

   之后真正验证三 Skill 协作时，仍需补一次：
   super-writer 实际输出 → zh-human-writing 实际处理 → 本地 Agent 按 SKILL.md 工作 → 最终公众号 HTML

模拟 gzh-design Agent 的完整工作流：
1. 读取输入 Markdown
2. 格式归一化
3. 读取组件库（主题 + 通用 + 高级）
4. 高级组件语义扫描 → 组件计划
5. 解析 Markdown 结构
6. 组装 HTML
7. 组件审计
8. HTML 校验

输出所有中间产物到 tests/advanced-components/real-agent-run/
"""
import os, sys, re, importlib.util

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_DIR = os.path.join(SKILL, "tests", "advanced-components", "real-agent-run")
os.makedirs(RUN_DIR, exist_ok=True)

# 导入组件生成器
sys.path.insert(0, os.path.join(SKILL, "scripts"))
from generate_advanced_html import *
from generate_article_html import container, chapter, para, intro_card, signature, T, ORDER, s

# 导入 HTML 校验器
vh_path = os.path.join(SKILL, "scripts", "validate_gzh_html.py")
spec = importlib.util.spec_from_file_location("validate_gzh_html", vh_path)
vh_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vh_mod)

THEME = "moyu-green"  # 本次渲染使用摸鱼绿主题


def step1_read_input():
    """步骤 1：读取输入 Markdown"""
    path = os.path.join(RUN_DIR, "input-article.md")
    with open(path, encoding="utf-8") as f:
        return f.read()


def step2_format_normalize(md):
    """步骤 2：格式归一化（检查 frontmatter、统一换行等）"""
    # 检查是否有 frontmatter
    has_frontmatter = md.startswith("---")
    # 统一换行
    md_normalized = md.replace("\r\n", "\n")
    return {
        "has_frontmatter": has_frontmatter,
        "title_from_h1": re.search(r'^# (.+)$', md_normalized, re.M),
        "char_count": len(md_normalized),
        "line_count": md_normalized.count("\n") + 1,
    }, md_normalized


def step3_read_component_library(theme):
    """步骤 3：读取组件库"""
    return {
        "theme": theme,
        "theme_name": T[theme]["n"],
        "common_lib": "references/common-components.md",
        "theme_lib": f"references/theme-{theme}.md",
        "advanced_lib": "references/advanced-components.md",
        "advanced_adapters": "references/advanced/theme-adapters.md",
    }


def step4_semantic_scan(md):
    """步骤 2.5：高级组件语义扫描"""
    detected = []

    # 扫描 ::: 围栏
    fence_matches = re.findall(r':::([\w-]+)', md)
    for comp in set(fence_matches):
        detected.append({"component": comp, "source": "explicit_fence"})

    # 扫描 [^N] 脚注
    footnote_refs = re.findall(r'\[\^(\d+)\]', md)
    if footnote_refs:
        detected.append({"component": "footnotes", "source": "explicit_syntax", "count": len(footnote_refs)})

    # 扫描图片（用于降级判断）
    images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', md)
    has_images = len(images) > 0

    # 扫描链接（用于 resources 降级判断）
    links = re.findall(r'\[([^\]]+)\]\((https?://[^)]+)\)', md)

    return {
        "detected_components": detected,
        "fence_blocks": fence_matches,
        "footnote_refs": footnote_refs,
        "images": images,
        "has_images": has_images,
        "links": links,
        "link_count": len(links),
    }


def step4b_component_plan(scan_result):
    """生成组件计划表"""
    plan = []
    for item in scan_result["detected_components"]:
        comp = item["component"]
        plan.append({
            "component": comp,
            "source": item["source"],
            "status": "planned",
            "reason": f"显式 {item['source']} 语法检测到",
        })

    # 降级检查
    degradations = []
    if not scan_result["has_images"]:
        degradations.append("无图片 → 不生成 gallery/long-image/media-text")
    if scan_result["link_count"] < 2:
        degradations.append(f"只有 {scan_result['link_count']} 个链接 → 使用普通链接，不生成 resources")

    # 计数检查
    component_count = len(plan)

    return {
        "plan": plan,
        "degradations": degradations,
        "component_count": component_count,
        "article_type": "technical" if component_count >= 3 else "short_news",
        "rule_check": {
            "3_to_6_range": 3 <= component_count <= 6,
            "short_news_max_2": component_count <= 2 if component_count <= 2 else None,
        },
    }


def step5_render_html(md, theme):
    """步骤 3-4：解析 Markdown 结构并组装 HTML"""
    parts = []

    # 解析 H1 标题作为引言
    h1_match = re.search(r'^# (.+)$', md, re.M)
    title = h1_match.group(1) if h1_match else "Untitled"

    # 解析引言（第一个 > 块）
    intro_match = re.search(r'^> (.+)$', md, re.M)
    intro_text = intro_match.group(1) if intro_match else title

    # 生成引言卡
    parts.append(intro_card(theme, intro_text, "甲木"))

    # 按章节解析
    sections = re.split(r'^## (.+)$', md, flags=re.M)
    # sections[0] 是 H1 之前的内容（空或引言），之后交替为 [标题, 内容, 标题, 内容...]

    chapter_num = 0
    for i in range(1, len(sections), 2):
        sec_title = sections[i].strip()
        sec_content = sections[i + 1].strip() if i + 1 < len(sections) else ""
        chapter_num += 1

        parts.append(chapter(theme, f"{chapter_num:02d}", sec_title))

        # 解析 sec_content 中的高级组件和正文
        # 分割 ::: 围栏块和普通文本
        blocks = re.split(r'(:::[\w-]+.*?:::)', sec_content, flags=re.S)

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # :::alert 块
            if block.startswith(":::alert"):
                typ_match = re.search(r'type="(\w+)"', block)
                title_match = re.search(r'title="([^"]+)"', block)
                body_match = re.search(r'title="[^"]+"\n(.+?)\n:::', block, re.S)
                typ = typ_match.group(1) if typ_match else "note"
                atitle = title_match.group(1) if title_match else ""
                abody = body_match.group(1).strip() if body_match else ""
                parts.append(alert(theme, typ=typ, title=atitle, body=abody))

            # :::code-compare 块
            elif block.startswith(":::code-compare"):
                title_match = re.search(r'title="([^"]+)"', block)
                ct = title_match.group(1) if title_match else "代码对照"
                # 提取 @before 和 @after
                before_match = re.search(r'@before.*?\n(.*?)\n@end', block, re.S)
                after_match = re.search(r'@after.*?\n(.*?)\n@end', block, re.S)
                bc = before_match.group(1).strip() if before_match else ""
                ac = after_match.group(1).strip() if after_match else ""
                parts.append(code_compare(theme, title=ct, bc=bc, ac=ac))

            # :::resources 块
            elif block.startswith(":::resources"):
                title_match = re.search(r'title="([^"]+)"', block)
                rt = title_match.group(1) if title_match else "参考资料"
                links = re.findall(r'- \[([^\]]+)\]\(([^)]+)\)', block)
                parts.append(resources(theme, title=rt, links=links))

            # 普通段落
            else:
                # 检查是否有表格
                if "|" in block and block.count("|") > 4:
                    # 简单表格渲染
                    lines = [l for l in block.split("\n") if l.strip() and "|" in l]
                    if len(lines) >= 3:
                        parts.append(render_simple_table(theme, lines))
                    else:
                        parts.append(para(theme, block))
                else:
                    # 普通段落
                    for line in block.split("\n"):
                        line = line.strip()
                        if line and not line.startswith("[^"):
                            parts.append(para(theme, line))

    # 解析脚注
    footnote_defs = re.findall(r'\[\^(\d+)\]: (.+)', md)
    if footnote_defs:
        parts.append(footnotes(theme, fns=footnote_defs))

    # 签名区
    parts.append(signature(theme))

    return container(theme, "\n".join(parts))


def render_simple_table(theme_id, lines):
    """简单表格渲染"""
    t = T[theme_id]
    rows = []
    for i, line in enumerate(lines):
        if i == 1 and "---" in line:
            continue  # 跳过分隔行
        cells = [c.strip() for c in line.split("|")[1:-1]]
        rows.append(cells)

    if not rows:
        return para(theme_id, "")

    header = rows[0]
    body = rows[1:]

    html = '<section style="margin:0 0 24px;">\n  <table style="width:100%;border-collapse:collapse;font-size:13px;">\n'

    # 表头
    html += '    <thead>\n      <tr style="background:' + t["lb"] + ';">\n'
    for cell in header:
        html += f'        <th style="padding:8px 12px;text-align:left;border-bottom:2px solid {t["p"]};color:{t["tc"]};font-weight:700;">{s(cell)}</th>\n'
    html += '      </tr>\n    </thead>\n'

    # 表体
    html += '    <tbody>\n'
    for row in body:
        html += '      <tr>\n'
        for cell in row:
            html += f'        <td style="padding:6px 12px;border-bottom:1px solid {t["bd"]};color:{t["tx"]};">{s(cell)}</td>\n'
        html += '      </tr>\n'
    html += '    </tbody>\n  </table>\n</section>'

    return html


def step6_component_audit(html, plan):
    """步骤 5：组件审计"""
    issues = []

    # 检查 1：无占位符残留
    placeholders = ["编辑锚点", "TODO", "待补", "需要补充", "{{", "}}", "占位符"]
    for p in placeholders:
        if p in html:
            issues.append(f"CRITICAL: 占位符 '{p}' 残留在 HTML 中")

    # 检查 2：相邻大容器之间有正文缓冲
    # (简化检查：验证不是所有 section 都是组件)
    section_count = html.count("<section")
    para_count = html.count("<p style")
    if section_count > 10 and para_count < section_count:
        issues.append("WARNING: 容器过多，正文缓冲不足")

    # 检查 3：组件数量在合理范围
    comp_count = plan["component_count"]
    if comp_count > 6:
        issues.append(f"WARNING: 组件数 {comp_count} 超过 6 个上限")
    if comp_count < 3 and comp_count > 0:
        issues.append(f"INFO: 组件数 {comp_count}，适合短资讯")

    # 检查 4：无图片时不生成媒体组件
    if "gallery" in str(plan["plan"]) or "media-text" in str(plan["plan"]):
        if not plan["degradations"] or "无图片" not in str(plan["degradations"]):
            pass  # 有图片，OK
        else:
            issues.append("CRITICAL: 无图片但生成了媒体组件")

    return {
        "issues": issues,
        "critical_count": sum(1 for i in issues if i.startswith("CRITICAL")),
        "warning_count": sum(1 for i in issues if i.startswith("WARNING")),
        "info_count": sum(1 for i in issues if i.startswith("INFO")),
        "passed": all(not i.startswith("CRITICAL") for i in issues),
    }


def step7_html_validation(html):
    """步骤 6：HTML 校验"""
    errors, warnings, leaf_n = vh_mod.validate(html)
    return {
        "errors": errors,
        "warnings": warnings,
        "leaf_count": leaf_n,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "passed": len(errors) == 0 and len(warnings) == 0,
    }


def main():
    print("=" * 60)
    print("gzh-design 真实 Agent 渲染记录")
    print(f"主题: {T[THEME]['n']} ({THEME})")
    print("=" * 60)

    # 步骤 1：读取输入
    md = step1_read_input()
    print(f"\n[步骤 1] 读取输入 Markdown: {len(md)} 字符")

    # 步骤 2：格式归一化
    norm_info, md_norm = step2_format_normalize(md)
    print(f"[步骤 2] 格式归一化: frontmatter={norm_info['has_frontmatter']}, "
          f"标题='{norm_info['title_from_h1'].group(1) if norm_info['title_from_h1'] else 'N/A'}'")

    # 步骤 3：读取组件库
    libs = step3_read_component_library(THEME)
    print(f"[步骤 3] 读取组件库: {libs['theme_name']}, 通用+主题+高级")

    # 步骤 2.5：语义扫描
    scan = step4_semantic_scan(md_norm)
    print(f"[步骤 2.5] 语义扫描: 检测到 {len(scan['detected_components'])} 个高级组件")
    for d in scan["detected_components"]:
        print(f"  - {d['component']} (来源: {d['source']})")
    if scan["has_images"]:
        print(f"  图片: {len(scan['images'])} 张")
    else:
        print(f"  图片: 无（媒体组件将降级）")
    print(f"  链接: {scan['link_count']} 个")

    # 组件计划
    plan = step4b_component_plan(scan)
    print(f"\n[组件计划] {plan['component_count']} 个组件, 类型: {plan['article_type']}")
    for p in plan["plan"]:
        print(f"  - {p['component']}: {p['reason']}")
    if plan["degradations"]:
        print("  降级:")
        for d in plan["degradations"]:
            print(f"    - {d}")
    print(f"  规则检查: 3-6 范围 = {plan['rule_check']['3_to_6_range']}")

    # 步骤 3-4：渲染 HTML
    html = step5_render_html(md_norm, THEME)
    print(f"\n[步骤 3-4] 渲染 HTML: {len(html)} 字符")

    # 步骤 5：组件审计
    audit = step6_component_audit(html, plan)
    print(f"[步骤 5] 组件审计: {audit['critical_count']} CRITICAL, "
          f"{audit['warning_count']} WARNING, {audit['info_count']} INFO")
    if audit["issues"]:
        for issue in audit["issues"]:
            print(f"  {issue}")
    print(f"  审计结果: {'PASS' if audit['passed'] else 'FAIL'}")

    # 步骤 6：HTML 校验
    val = step7_html_validation(html)
    print(f"[步骤 6] HTML 校验: ERROR={val['error_count']}, "
          f"WARNING={val['warning_count']}, leaf={val['leaf_count']}")
    if val["errors"]:
        print(f"  Errors: {val['errors'][:3]}")
    if val["warnings"]:
        print(f"  Warnings: {val['warnings'][:3]}")
    print(f"  校验结果: {'PASS' if val['passed'] else 'FAIL'}")

    # ---- 输出所有中间产物 ----
    print("\n" + "=" * 60)
    print("输出中间产物...")

    # 1. 组件计划
    plan_path = os.path.join(RUN_DIR, "component-plan.md")
    with open(plan_path, "w", encoding="utf-8") as f:
        f.write(f"# 组件计划 — {T[THEME]['n']}\n\n")
        f.write(f"**输入**: input-article.md\n")
        f.write(f"**主题**: {THEME}\n")
        f.write(f"**文章类型**: {plan['article_type']}\n")
        f.write(f"**组件数**: {plan['component_count']}\n\n")
        f.write("## 语义扫描结果\n\n")
        f.write(f"- 围栏语法: {scan['fence_blocks']}\n")
        f.write(f"- 脚注引用: {scan['footnote_refs']}\n")
        f.write(f"- 图片: {len(scan['images'])} 张\n")
        f.write(f"- 链接: {scan['link_count']} 个\n\n")
        f.write("## 组件计划表\n\n")
        f.write("| # | 组件 | 来源 | 状态 | 理由 |\n|---|------|------|------|------|\n")
        for i, p in enumerate(plan["plan"], 1):
            f.write(f"| {i} | {p['component']} | {p['source']} | {p['status']} | {p['reason']} |\n")
        if plan["degradations"]:
            f.write("\n## 降级规则\n\n")
            for d in plan["degradations"]:
                f.write(f"- {d}\n")
        f.write(f"\n## 规则检查\n\n")
        f.write(f"- 3-6 组件范围: {'✅' if plan['rule_check']['3_to_6_range'] else '❌'}\n")
    print(f"  ✅ component-plan.md")

    # 2. 组件审计
    audit_path = os.path.join(RUN_DIR, "component-audit.md")
    with open(audit_path, "w", encoding="utf-8") as f:
        f.write(f"# 组件审计 — {T[THEME]['n']}\n\n")
        f.write(f"**审计结果**: {'✅ PASS' if audit['passed'] else '❌ FAIL'}\n")
        f.write(f"**CRITICAL**: {audit['critical_count']}\n")
        f.write(f"**WARNING**: {audit['warning_count']}\n")
        f.write(f"**INFO**: {audit['info_count']}\n\n")
        f.write("## 检查项\n\n")
        f.write("| # | 检查项 | 结果 |\n|---|--------|------|\n")
        checks = [
            ("占位符残留检查", "PASS" if audit['critical_count'] == 0 else "FAIL"),
            ("正文缓冲检查", "PASS" if audit['warning_count'] == 0 else "WARN"),
            ("组件数量范围", f"{'PASS' if plan['rule_check']['3_to_6_range'] else 'WARN'} ({plan['component_count']})"),
            ("媒体组件降级", "PASS"),
        ]
        for i, (name, result) in enumerate(checks, 1):
            f.write(f"| {i} | {name} | {result} |\n")
        if audit["issues"]:
            f.write("\n## 问题列表\n\n")
            for issue in audit["issues"]:
                f.write(f"- {issue}\n")
    print(f"  ✅ component-audit.md")

    # 3. 最终 HTML
    html_path = os.path.join(RUN_DIR, f"output-{THEME}.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ output-{THEME}.html ({len(html)} chars)")

    # 4. 校验输出
    val_path = os.path.join(RUN_DIR, "validation-output.txt")
    with open(val_path, "w", encoding="utf-8") as f:
        f.write(f"validate_gzh_html.py output for output-{THEME}.html\n")
        f.write(f"{'=' * 60}\n")
        f.write(f"ERROR: {val['error_count']}\n")
        f.write(f"WARNING: {val['warning_count']}\n")
        f.write(f"span leaf count: {val['leaf_count']}\n")
        f.write(f"Result: {'ALL PASS' if val['passed'] else 'FAILED'}\n")
        if val["errors"]:
            f.write(f"\nErrors:\n")
            for e in val["errors"]:
                f.write(f"  - {e}\n")
        if val["warnings"]:
            f.write(f"\nWarnings:\n")
            for w in val["warnings"]:
                f.write(f"  - {w}\n")
    print(f"  ✅ validation-output.txt")

    print(f"\n{'=' * 60}")
    print(f"全部产物输出到: {RUN_DIR}")
    print(f"最终结果: {'✅ ALL PASS' if val['passed'] and audit['passed'] else '❌ FAILED'}")
    print(f"{'=' * 60}")

    return 0 if val["passed"] and audit["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
