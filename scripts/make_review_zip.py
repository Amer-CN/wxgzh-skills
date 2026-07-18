#!/usr/bin/env python3
"""打包 Stage B 完整审查包为 zip —— v5

包含原版 gzh-design 的核心文件 + Stage 1 + Stage B 全部增量。
"""
import zipfile, os, re

skill = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(skill)

files = [
    # 核心文档
    'SKILL.md',
    # 原版组件库
    'references/common-components.md',
    'references/theme-index.md',
    # 原版主题库
]
# 添加全部 theme-*.md
for f in sorted(os.listdir('references')):
    if f.startswith('theme-') and f.endswith('.md'):
        files.append(f'references/{f}')

files += [
    # 高级组件总目录
    'references/advanced-components.md',
    # Stage 1 组件文档
    'references/advanced/alerts.md',
    'references/advanced/quotes.md',
    'references/advanced/code-compare.md',
    'references/advanced/media.md',
    'references/advanced/links-resources.md',
    'references/advanced/footnotes.md',
    'references/advanced/dialogue.md',
    'references/advanced/theme-adapters.md',
    # Stage B 组件文档
    'references/advanced/facts.md',
    'references/advanced/decision.md',
    'references/advanced/steps.md',
    'references/advanced/compare.md',
    'references/advanced/annotated-image.md',
    'references/advanced/faq.md',
    'references/advanced/timeline.md',
    'references/advanced/checklist.md',
    'references/advanced/case.md',
    'references/advanced/cta.md',
    # 原版脚本
    'scripts/validate_gzh_html.py',
    'scripts/component_lint.py',
    'scripts/wrap_preview.py',
    # Stage 1 脚本
    'scripts/lint_advanced_components.py',
    'scripts/generate_advanced_html.py',
    'scripts/generate_article_html.py',
    'scripts/make_test_assets.py',
    'scripts/update_component_docs.py',
    'scripts/make_review_zip.py',
    'scripts/run_real_agent.py',
    # Stage B 脚本
    'scripts/generate_b_html.py',
    'scripts/generate_b_articles.py',
    'scripts/make_b_docs.py',
    'scripts/make_b_assets.py',
    'scripts/run_b_agent.py',
    # 测试
    'tests/test_advanced_components.py',
    'tests/advanced-components/e2e-compatibility-fixture.md',
    # 报告
    'reports/preflight-integration-contract.md',
    'reports/baseline-sha256-stage1.md',
    'reports/stage1-delivery-report.md',
]

# 测试图片素材
for f in sorted(os.listdir('tests/advanced-components/assets')):
    if f.endswith('.png'):
        files.append(f'tests/advanced-components/assets/{f}')

# 真实 Agent 渲染记录
ra_dir = 'tests/advanced-components/real-agent-run'
for f in sorted(os.listdir(ra_dir)):
    files.append(f'{ra_dir}/{f}')

# 验收 HTML
expected_dir = 'tests/advanced-components/expected'
for f in sorted(os.listdir(expected_dir)):
    if f.endswith('.html'):
        files.append(f'{expected_dir}/{f}')

# ---- 自检 ----
print("自检：验证 HTML 中的图片 src...")
missing = []
for f in files:
    if f.endswith('.html') and 'expected' in f:
        with open(f, encoding="utf-8") as fh:
            html = fh.read()
        for m in re.finditer(r'src="([^"]+)"', html):
            src = m.group(1)
            if src.startswith('http') or src.startswith('data:'):
                continue
            src_norm = src[2:] if src.startswith('./') else src
            resolved = os.path.normpath(os.path.join(os.path.dirname(f), src_norm))
            resolved_norm = resolved.replace('\\', '/')
            if resolved_norm not in files and not os.path.exists(resolved):
                missing.append((f, src, resolved))

if missing:
    print(f"❌ 自检失败：{len(missing)} 个图片 src 无对应文件")
    for f, src, resolved in missing[:5]:
        print(f"  {f}: src='{src}' -> {resolved}")
    exit(1)
print("✅ 自检通过：所有 HTML 图片 src 均有对应文件")

# ---- 打包 ----
z = 'gzh-design-stage-b-review.zip'  # 输出到当前工作目录
actual = []
with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in files:
        if os.path.exists(f):
            zf.write(f, 'gzh-design/' + f)
            actual.append(f)
        else:
            print(f'MISSING: {f}')

print(f'OK: {os.path.getsize(z) // 1024}KB, {len(actual)} files')
