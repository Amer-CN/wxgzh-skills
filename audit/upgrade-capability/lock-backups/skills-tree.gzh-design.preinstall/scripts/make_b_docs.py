#!/usr/bin/env python3
"""批量创建 10 个 B 层组件文档 + 更新总目录"""
import os

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADV = os.path.join(SKILL, "references", "advanced")
EXPECTED = os.path.join(SKILL, "tests", "advanced-components", "expected")

def read_template(comp, theme="moyu-green"):
    p = os.path.join(EXPECTED, f"{comp}-{theme}.html")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read().strip()
    return ""

DOCS = {
    "facts.md": ("facts", "事实数据卡", "参数、版本、价格、状态等键值信息",
     ":::facts title=\"标题\"\\n- 键: 值\\n:::", "至少 2 条事实", "回退为普通列表"),
    "decision.md": ("decision", "决策说明卡", "方案选择、选型结论",
     ":::decision title=\"标题\"\\n@recommended: 推荐方案\\n@option: 方案A | 说明\\n@option: 方案B | 说明\\n:::", "至少 2 个候选方案", "回退为普通对比段落"),
    "steps.md": ("steps", "步骤流程", "操作教程、安装流程、部署流程",
     ":::steps title=\"标题\"\\n1. 步骤一\\n2. 步骤二\\n:::", "至少 2 步", "回退为普通有序列表"),
    "compare.md": ("compare", "结构化对比", "产品比较、版本差异、方案优缺点",
     ":::compare title=\"标题\"\\n| 维度 | A | B |\\n|---|---|---|\\n| 体积 | 大 | 小 |\\n:::", "至少 2 列方案 2 行对比", "回退为普通 Markdown 表格"),
    "annotated-image.md": ("annotated-image", "注释图片", "界面说明、架构图讲解、截图标注",
     ":::annotated-image image=\"url\" caption=\"说明\"\\n@note 1: 注释一\\n@note 2: 注释二\\n:::", "图片 URL + 至少 1 条注释", "回退为普通图片 + 列表"),
    "faq.md": ("faq", "问答组", "读者常见问题、产品 FAQ",
     ":::faq title=\"标题\"\\n@q: 问题\\n@a: 回答\\n:::", "至少 1 组问答", "回退为普通标题 + 段落"),
    "timeline.md": ("timeline", "时间线", "产品演进、项目里程碑、版本发布",
     ":::timeline title=\"标题\"\\n@item 2026-01: 事件\\n:::", "至少 2 个事件", "回退为普通列表"),
    "checklist.md": ("checklist", "清单", "发布前检查、迁移检查、安全检查",
     ":::checklist title=\"标题\"\\n- [x] 已完成项\\n- [ ] 未完成项\\n:::", "至少 2 项", "回退为普通列表"),
    "case.md": ("case", "案例复盘", "实践案例、项目复盘、问题-行动-结果",
     ":::case title=\"标题\"\\n@context: 背景\\n@challenge: 挑战\\n@action: 行动\\n@result: 结果\\n:::", "context/challenge/action/result 至少 3 项", "回退为普通小标题段落"),
    "cta.md": ("cta", "行动引导", "下一步操作、文章结尾行动建议",
     ":::cta title=\"标题\"\\ntext=\"引导文本\"\\naction=\"行动描述\"\\nurl=\"https://...\"\\n:::", "明确行动文本 + HTTPS URL", "使用原有签名，不生成 CTA"),
}

for doc_name, (comp_id, name, purpose, syntax, min_input, degradation) in DOCS.items():
    html = read_template(comp_id)
    content = f"""# 高级组件 —— {name}（{comp_id}）

> {purpose}

## 输入语法

```markdown
{syntax}
```

## 最小输入

{min_input}

## 选择条件

- 源稿有明确的{purpose}语义
- 显式 `:::{comp_id}` 语法优先

## 禁止自动识别条件

- 无明确{purpose}语义的普通段落不得自动升级
- 不得自动补造数据、结果或行动建议

## 降级方式

{degradation}

## 发布限制

- 正式 release HTML 禁止 `../assets/`、`file://`、本地磁盘路径
- 所有图片 `src` 必须是作者提供的可访问 HTTPS URL

## 六主题适配规则

见 [theme-adapters.md](theme-adapters.md)。组件语义跨主题一致，只有视觉语言不同。

## 生产 HTML 模板（moyu-green 主题示例）

> 其他主题使用相同结构，仅替换 `theme-adapters.md` 中的色值令牌。

```html
{html}
```

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/{comp_id}-*.html`（验收产物，非生产依赖）。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。
"""
    path = os.path.join(ADV, doc_name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"OK: {doc_name}")

print(f"\nAll 10 B-layer component docs created in {ADV}")
