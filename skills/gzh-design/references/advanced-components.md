# 高级组件总目录

> **本文件是高级组件的单一来源**。列出了三层能力，每项标明输入语法、最小输入、自动识别条件、禁止自动识别条件、降级方式和全主题适配状态。
>
> **平台限制不变**：禁 class/id/div/style/script/grid/float/@media/CSS 变量；只用内联 style + `<span leaf="">` 包裹。
>
> **兼容性铁律**：新增 `:::` 围栏语法是标准 Markdown 的严格超集。不含 `:::` 的文章行为与升级前完全一致。`preserve_exactly`、`editor_anchors`、`[[protected]]`、`<!--keep-->` 内容逐字保留。

---

## A. 本阶段已实现（有真实 HTML 模板）

| 组件 | 输入语法 | 最小输入 | 自动识别条件 | 禁止自动识别 | 降级方式 | 6 主题适配 |
|------|---------|---------|-------------|-------------|---------|-----------|
| alert | `:::alert type="warning" title="标题"\n正文\n:::` | type + 正文 | 源稿有明确风险提示/注意事项语义段 | 无明确警示语义 | 回退为普通引用块 `>` | ✅ 全部 |
| quote | `> 金句` 或 `:::quote type="highlight"\n金句\n:::` | 金句文本 | 源稿有引号包裹的判断句 | 无引号或非金句 | 回退为普通段落 | ✅ 全部 |
| code-compare | `:::code-compare title="标题"\n@before lang="python"\n旧代码\n@end\n@after lang="python"\n新代码\n@end\n:::` | before + after 各一段代码 | 源稿有明确"改前/改后"或"A/B"对照 | 单一代码块或无对照语义 | 回退为通用库 1a/1b 代码块 | ✅ 全部 |
| media-text | `:::media-text\n![说明](url)\n解释段落\n:::` | 图片 URL + 解释文字 | 图片后紧跟解释段落且语义绑定 | 图片无绑定解释 | 回退为通用库 2a 标准图片 | ✅ 全部 |
| gallery | `:::gallery title="标题"\n![一](url1)\n![二](url2)\n:::` | ≥ 2 张图片 | 源稿有 2-4 张相关图片且语义为组图 | 只 1 张图或图片无关联 | 回退为多张独立 2a 图片 | ✅ 全部 |
| long-image | `:::long-image image="url" caption="说明"\n:::` | 图片 URL + 说明 | 源稿有明确的长截图/流程图/信息图 | 普通截图无长图语义 | 回退为通用库 2a 标准图片 | ✅ 全部 |
| resources | `:::resources title="标题"\n- [名称](url)\n- [名称](url)\n:::` | ≥ 2 个 HTTPS 链接 | 源稿有 2 个及以上作者提供的 HTTPS 链接且语义为参考资料 | 只 1 个链接或非参考资料 | 回退为普通链接文本 | ✅ 全部 |
| footnotes | `正文[^1]` + `[^1]: 注释内容` | ≥ 1 个脚注引用 + 定义 | 源稿有 `[^N]` 脚注语法 | 无脚注语法 | 不生成脚注区 | ✅ 全部 |
| dialogue | `:::dialogue title="标题"\n@user: 问题\n@assistant: 回答\n:::` | ≥ 1 组对话 | 源稿有问答/访谈/排障语义块 | 无对话语义 | 回退为普通引用段落 | ✅ 全部 |

---

## B. 已实现（Stage B，有真实 HTML 模板）

| 组件 | 输入语法 | 职责 | 状态 |
|------|---------|------|------|
| facts | `:::facts title="标题"\n- 键: 值\n:::` | 参数、版本、价格等键值信息 | ✅ 已实现 |
| decision | `:::decision\n@recommended: 方案\n@option: 方案 \| 说明\n:::` | 方案选择、选型结论 | ✅ 已实现 |
| steps | `:::steps title="标题"\n1. 步骤\n:::` | 可执行步骤、部署流程 | ✅ 已实现 |
| compare | `:::compare\n\| 维度 \| A \| B \|\n:::` | 结构化对比表（移动端纵向卡） | ✅ 已实现 |
| annotated-image | `:::annotated-image image="url"\n@note 1: 说明\n:::` | 图片局部编号注释（不用覆盖层） | ✅ 已实现 |
| faq | `:::faq\n@q: 问题\n@a: 回答\n:::` | 问答集合 | ✅ 已实现 |
| timeline | `:::timeline\n@item date: 事件\n:::` | 版本/事件/里程碑 | ✅ 已实现 |
| checklist | `:::checklist\n- [x] 项\n- [ ] 项\n:::` | 发布前检查（视觉状态呈现） | ✅ 已实现 |
| case | `:::case\n@context:\n@challenge:\n@action:\n@result:\n:::` | 案例复盘 | ✅ 已实现 |
| cta | `:::cta\ntext="引导"\naction="描述"\nurl="https://..."\n:::` | 行动引导（必须 HTTPS） | ✅ 已实现 |

---

## C. 永远保留的基础能力

现有 6 套主题的以下能力**全部保留，不修改**：

- 主题封面（杂志快讯/引言卡/票据封面/头图卡）
- 目录导航
- 章节自动编号
- 普通正文 + 关键词下划线标记
- 普通引用块 `>`
- 普通链接 `[文字](url)`
- 普通图片 `![说明](url)` / GIF
- 普通代码块围栏 / 行内代码
- 普通表格
- 作者签名区
- 预览页（wrap_preview.py）
- HTML 合规校验（validate_gzh_html.py）

---

## 组件选择与降级规则

### 选择规则（在 SKILL.md 第 2 步"读组件库"之后、第 3 步"解析 Markdown"之前执行）

1. **高级组件语义扫描**：扫描源稿中是否有 `:::` 围栏语法或 `[^N]` 脚注
2. **内部组件计划表**：列出本文将使用的高级组件，默认 3-6 个；短资讯 0-2 个
3. **按主题取高级组件 HTML**：读 `references/advanced/` 下对应组件文档，按当前主题取 HTML 模板
4. **组件审计**：检查是否有缺字段、占位符残留、降级需求
5. **原有 HTML 校验**：跑 `validate_gzh_html.py` 确保 ERROR × 0

### 降级规则

| 条件 | 降级方式 |
|------|---------|
| 无图片 | 不得生成 gallery/long-image/media-text/annotated-image |
| 只有 1 个普通链接 | 使用原版链接，不生成 resources 模块 |
| 单一代码块 | 使用通用库 1a/1b，不生成 code-compare |
| 无 `[^N]` 脚注 | 不生成脚注区 |
| 缺少高级模块字段 | 回退到原版组件或正文，**绝不保留占位符** |
| 无 `:::` 语法且无语义匹配 | 正常按原版流程排版，不生成高级组件 |

### 兼容性铁律

- `:::` 语法是标准 Markdown 的**严格超集**：不含 `:::` 的文章行为不变
- `preserve_exactly` / `editor_anchors` / `[[protected]]` / `<!--keep-->` 内容逐字保留
- 代码块/行内代码/URL/数字/日期 逐字保留
- zh-human-writing 不得改写/拆散/全角化任何高级模块块
