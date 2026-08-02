#!/usr/bin/env python3
"""B 层确定性渲染记录生成器

⚠️ 重要声明：本脚本不是由真实本地 Agent 自主执行 SKILL.md 的运行记录。
   它是一个确定性渲染与集成测试脚本，直接导入 generate_b_html.py
   和 generate_article_html.py 的组件函数来模拟渲染流程。

模拟 gzh-design Agent 对 B 层组件的完整工作流：
1. 读取输入 Markdown
2. 语义扫描（B 层 ::: 围栏）
3. 组件计划
4. 渲染 HTML
5. 组件审计
6. HTML 校验
"""
import os, sys, re, importlib.util

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_DIR = os.path.join(SKILL, "tests", "advanced-components", "real-agent-run")

sys.path.insert(0, os.path.join(SKILL, "scripts"))
from generate_advanced_html import T, s
from generate_article_html import container, chapter, para, intro_card, signature
from generate_b_html import facts, decision, steps, faq, checklist

vh_path = os.path.join(SKILL, "scripts", "validate_gzh_html.py")
spec = importlib.util.spec_from_file_location("validate_gzh_html", vh_path)
vh_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vh_mod)

THEME = "moyu-green"


def main():
    print("=" * 60)
    print("gzh-design B 层确定性渲染记录")
    print(f"主题: {T[THEME]['n']} ({THEME})")
    print("=" * 60)

    # 步骤 1：读取输入
    md_path = os.path.join(RUN_DIR, "b-input.md")
    with open(md_path, encoding="utf-8") as f:
        md = f.read()
    print(f"\n[步骤 1] 读取输入: {len(md)} 字符")

    # 步骤 2：语义扫描
    fence = re.findall(r':::([\w-]+)', md)
    detected = list(set(fence))
    print(f"[步骤 2] 语义扫描: 检测到 {len(detected)} 个 B 层组件: {sorted(detected)}")

    # 步骤 3：组件计划
    comp_count = len(detected)
    print(f"[步骤 3] 组件计划: {comp_count} 个组件, 类型: technical")
    print(f"  规则检查: 3-6 范围 = {3 <= comp_count <= 6}")

    # 步骤 4：渲染 HTML
    p = []
    p.append(intro_card(THEME, "「三个月把一个 5 万行的单体 Node.js 服务拆成 12 个微服务。」", "甲木"))

    # 解析章节
    sections = re.split(r'^## (.+)$', md, flags=re.M)
    ch = 0
    for i in range(1, len(sections), 2):
        title = sections[i].strip()
        content = sections[i+1].strip() if i+1 < len(sections) else ""
        ch += 1
        p.append(chapter(THEME, f"{ch:02d}", title))

        blocks = re.split(r'(:::[\w-]+.*?:::)', content, flags=re.S)
        for block in blocks:
            block = block.strip()
            if not block: continue
            if block.startswith(":::facts"):
                items = re.findall(r'- (.+?): (.+)', block)
                p.append(facts(THEME, title="系统现状", items=items))
            elif block.startswith(":::decision"):
                rec_m = re.search(r'@recommended:\s*(.+)', block)
                opts = re.findall(r'@option:\s*(.+?)\s*\|\s*(.+)', block)
                p.append(decision(THEME, title="拆分策略",
                    recommended=rec_m.group(1).strip() if rec_m else "",
                    options=[(o[0].strip(), o[1].strip(), False) for o in opts]))
            elif block.startswith(":::steps"):
                steps_list = re.findall(r'\d+\.\s+(.+)', block)
                p.append(steps(THEME, title="拆分执行流程", items=steps_list))
            elif block.startswith(":::checklist"):
                cl_items = re.findall(r'- \[([ x])\]\s+(.+)', block)
                cl_data = [(m[1].strip(), m[0] == 'x') for m in cl_items]
                p.append(checklist(THEME, title="迁移前检查", items=cl_data))
            elif block.startswith(":::faq"):
                qa = re.findall(r'@q:\s*(.+?)\n@a:\s*(.+)', block)
                p.append(faq(THEME, title="拆分 FAQ", items=qa))
            else:
                for line in block.split("\n"):
                    line = line.strip()
                    if line and not line.startswith(":::") and not line.startswith("@"):
                        p.append(para(THEME, line))

    p.append(signature(THEME))
    html = container(THEME, "\n".join(p))
    print(f"[步骤 4] 渲染 HTML: {len(html)} 字符")

    # 步骤 5：组件审计
    issues = []
    for ph in ["编辑锚点", "TODO", "待补", "需要补充", "{{", "占位符"]:
        if ph in html: issues.append(f"CRITICAL: '{ph}' 残留")
    section_count = html.count("<section")
    para_count = html.count("<p style")
    if section_count > 10 and para_count < section_count:
        issues.append("WARNING: 容器过多")
    audit_pass = all(not i.startswith("CRITICAL") for i in issues)
    print(f"[步骤 5] 组件审计: {len(issues)} issues, {'PASS' if audit_pass else 'FAIL'}")

    # 步骤 6：HTML 校验
    errors, warnings, leaf_n = vh_mod.validate(html)
    val_pass = len(errors) == 0 and len(warnings) == 0
    print(f"[步骤 6] HTML 校验: ERROR={len(errors)}, WARNING={len(warnings)}, leaf={leaf_n}")
    print(f"  校验结果: {'PASS' if val_pass else 'FAIL'}")

    # 输出产物
    print("\n输出中间产物...")

    # 组件计划
    with open(os.path.join(RUN_DIR, "b-component-plan.md"), "w", encoding="utf-8") as f:
        f.write(f"# B 层组件计划 — {T[THEME]['n']}\n\n")
        f.write(f"**输入**: b-input.md\n**主题**: {THEME}\n**组件数**: {comp_count}\n\n")
        f.write("## 语义扫描结果\n\n")
        f.write(f"- 围栏语法: {sorted(detected)}\n")
        f.write(f"- 组件数: {comp_count}\n")
        f.write(f"- 3-6 范围: {'✅' if 3 <= comp_count <= 6 else '❌'}\n")
    print("  ✅ b-component-plan.md")

    # 组件审计
    with open(os.path.join(RUN_DIR, "b-component-audit.md"), "w", encoding="utf-8") as f:
        f.write(f"# B 层组件审计 — {T[THEME]['n']}\n\n")
        f.write(f"**审计结果**: {'✅ PASS' if audit_pass else '❌ FAIL'}\n\n")
        if issues:
            f.write("## 问题列表\n\n")
            for issue in issues: f.write(f"- {issue}\n")
        else:
            f.write("无问题。\n")
    print("  ✅ b-component-audit.md")

    # HTML
    with open(os.path.join(RUN_DIR, f"b-output-{THEME}.html"), "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✅ b-output-{THEME}.html ({len(html)} chars)")

    # 校验输出
    with open(os.path.join(RUN_DIR, "b-validation-output.txt"), "w", encoding="utf-8") as f:
        f.write(f"validate_gzh_html.py output for b-output-{THEME}.html\n")
        f.write(f"{'='*60}\nERROR: {len(errors)}\nWARNING: {len(warnings)}\n")
        f.write(f"span leaf count: {leaf_n}\nResult: {'ALL PASS' if val_pass else 'FAILED'}\n")
    print("  ✅ b-validation-output.txt")

    print(f"\n{'='*60}")
    print(f"最终结果: {'✅ ALL PASS' if val_pass and audit_pass else '❌ FAILED'}")
    print(f"{'='*60}")
    return 0 if val_pass and audit_pass else 1

if __name__ == "__main__":
    sys.exit(main())
