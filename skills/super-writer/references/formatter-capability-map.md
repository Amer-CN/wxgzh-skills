# Formatter 能力映射表

> 本文件是 Super Writer 对 gzh-design 排版 Skill 组件契约的语义化摘要。
> **不包含任何 HTML/CSS/主题色**——写作 Skill 只保存语义能力和载荷要求。
>
> 来源：`f:/AIXM/wxgzh/gzh-design-skill/` 的 SKILL.md、theme-index.md、common-components.md、advanced-components.md 及 references/advanced/*.md。
>
> 版本对应：gzh-design 已注册 7 套主题（moyu-green / red-white / graphite-minimal / zen-whitespace / moyu-ticket / olive-journal / hammer），13 个核心组件 + 19 个高级组件。

---

## 一、13 个主题核心组件

### 1. 全局容器（global-container）

| 字段 | 值 |
|------|-----|
| component_id | global-container |
| semantic_role | formatter_generated |
| 适用内容 | 文章最外层容器，包裹所有正文片段 |
| 必需载荷字段 | 无（由 formatter 自动生成） |
| 可选载荷字段 | 无 |
| 不适用条件 | 非公众号平台 |
| fallback | 无（容器始终存在） |
| 允许 formatter 自动选择 | 是 |
| 需要作者提供素材 | 否 |

### 2. 封面/引言卡（cover-breaking）

| 字段 | 值 |
|------|-----|
| component_id | cover-breaking |
| semantic_role | article_cover |
| 适用内容 | 文章标题 + 开头引言/摘要 |
| 必需载荷字段 | title, summary_or_intro |
| 可选载荷字段 | author_name, cover_image_url |
| 不适用条件 | 无标题文章 |
| fallback | 普通标题段落 |
| 允许 formatter 自动选择 | 是 |
| 需要作者提供素材 | 封面图（可选） |

### 3. 目录导航（toc-scroll）

| 字段 | 值 |
|------|-----|
| component_id | toc-scroll |
| semantic_role | article_toc |
| 适用内容 | 精选 2-3 个核心章节看点 |
| 必需载荷字段 | toc_items（≤3 项） |
| 可选载荷字段 | 无 |
| 不适用条件 | 文章少于 3 个章节 |
| fallback | 不生成目录 |
| 允许 formatter 自动选择 | 是 |
| 需要作者提供素材 | 否 |

### 4. 章节标题（chapter-title）

| 字段 | 值 |
|------|-----|
| component_id | chapter-title |
| semantic_role | article_section |
| 适用内容 | `##` 级别的章节标题 |
| 必需载荷字段 | heading_text, section_index |
| 可选载荷字段 | english_label, is_conclusion |
| 不适用条件 | 无章节的文章 |
| fallback | 普通加粗标题 |
| 允许 formatter 自动选择 | 是 |
| 需要作者提供素材 | 否 |

### 5. 正文段落（paragraph）

| 字段 | 值 |
|------|-----|
| component_id | paragraph |
| semantic_role | paragraph |
| 适用内容 | 普通正文段落 |
| 必需载荷字段 | text |
| 可选载荷字段 | highlight_phrases（关键词下划线标记，每段 1-3 个） |
| 不适用条件 | 无 |
| fallback | 无（最基础组件） |
| 允许 formatter 自动选择 | 是 |
| 需要作者提供素材 | 否 |

### 6. 行内样式（inline-styles）

| 字段 | 值 |
|------|-----|
| component_id | inline-styles |
| semantic_role | secondary_emphasis |
| 适用内容 | 加粗/高亮/下划线/荧光笔等行内强调 |
| 必需载荷字段 | text, style_type（bold/highlight/underline/marker） |
| 可选载荷字段 | 无 |
| 不适用条件 | 无 |
| fallback | 普通文本 |
| 允许 formatter 自动选择 | 是 |
| 需要作者提供素材 | 否 |

### 7. 小标签标题（label-heading）

| 字段 | 值 |
|------|-----|
| component_id | label-heading |
| semantic_role | subtitle |
| 适用内容 | 段落级小标题、强调标题 |
| 必需载荷字段 | heading_text |
| 可选载荷字段 | variant（left-bar/pill/numbered）, number |
| 不适用条件 | 无 |
| fallback | 普通加粗段落 |
| 允许 formatter 自动选择 | 是 |
| 需要作者提供素材 | 否 |

### 8. 代码块（code-block）

| 字段 | 值 |
|------|-----|
| component_id | code-block |
| semantic_role | code / command / prompt |
| 适用内容 | 代码、命令、Prompt 提示词 |
| 必需载荷字段 | code_text |
| 可选载荷字段 | language, variant（dark/light）, title |
| 不适用条件 | 无 |
| fallback | 普通等宽文本 |
| 允许 formatter 自动选择 | 是 |
| 需要作者提供素材 | 否 |

### 9. 引用/金句（quote-oneliner）

| 字段 | 值 |
|------|-----|
| component_id | quote-oneliner |
| semantic_role | quote / key_statement |
| 适用内容 | 普通引用、重点金句、带来源引用 |
| 必需载荷字段 | text |
| 可选载荷字段 | quote_type（normal/highlight/sourced）, source |
| 不适用条件 | 无引号或非金句的普通段落 |
| fallback | 普通段落 |
| 允许 formatter 自动选择 | 是（需有金句语义） |
| 需要作者提供素材 | 来源信息（sourced 类型时） |

### 10. 提示框（alert-box）

| 字段 | 值 |
|------|-----|
| component_id | alert-box |
| semantic_role | warning / tip / information |
| 适用内容 | 风险提示、小技巧、重点强调、补充说明 |
| 必需载荷字段 | alert_type（note/tip/important/warning/caution）, text |
| 可选载荷字段 | title |
| 不适用条件 | 无明确警示语义的普通段落 |
| fallback | 普通引用块 `>` |
| 允许 formatter 自动选择 | 是（需有警示语义） |
| 需要作者提供素材 | 否 |

### 11. 表格/列表/流程（table-list-flow）

| 字段 | 值 |
|------|-----|
| component_id | table-list-flow |
| semantic_role | ordered_list / pill_list / process_flow |
| 适用内容 | Markdown 表格、有序列表、药丸标签列表 |
| 必需载荷字段 | items 或 rows |
| 可选载荷字段 | headers, variant |
| 不适用条件 | 无 |
| fallback | 普通缩进段落 |
| 允许 formatter 自动选择 | 是 |
| 需要作者提供素材 | 否 |

### 12. 图片/视频（image-video）

| 字段 | 值 |
|------|-----|
| component_id | image-video |
| semantic_role | image / video |
| 适用内容 | 图片、GIF 动图、截图 |
| 必需载荷字段 | image_url |
| 可选载荷字段 | caption, is_gif, is_video |
| 不适用条件 | 无图片 URL |
| fallback | 待补素材占位（2c） |
| 允许 formatter 自动选择 | 是 |
| 需要作者提供素材 | **是**——图片 URL 必须由作者提供 |

### 13. 页脚/签名/品牌（footer-signature-brand）

| 字段 | 值 |
|------|-----|
| component_id | footer-signature-brand |
| semantic_role | article_signature |
| 适用内容 | 文章末尾固定署名 |
| 必需载荷字段 | 无（固定文案，由 formatter 生成） |
| 可选载荷字段 | 无 |
| 不适用条件 | 无 |
| fallback | 无（固定组件，末尾唯一） |
| 允许 formatter 自动选择 | 是（固定生成） |
| 需要作者提供素材 | 否（文案固定） |

---

## 二、19 个高级组件

### 1. alert

| 字段 | 值 |
|------|-----|
| component_id | alert |
| semantic_role | warning / tip / information |
| 适用内容 | GFM 风格 NOTE/TIP/IMPORTANT/WARNING/CAUTION |
| 必需载荷字段 | type（note/tip/important/warning/caution）, body |
| 可选载荷字段 | title |
| 不适用条件 | 无明确警示语义；缺少 type；缺少正文 |
| fallback | 普通引用块 `>` |
| 允许 formatter 自动选择 | 是（需有警示语义） |
| 需要作者提供素材 | 否 |

### 2. quote

| 字段 | 值 |
|------|-----|
| component_id | quote |
| semantic_role | quote / key_statement |
| 适用内容 | 普通引用、重点金句、带来源引用 |
| 必需载荷字段 | text |
| 可选载荷字段 | type（normal/highlight/sourced）, source |
| 不适用条件 | 无引号或非金句的普通段落 |
| fallback | 普通段落 |
| 允许 formatter 自动选择 | 是（需有金句语义） |
| 需要作者提供素材 | source（sourced 类型时必需） |

### 3. code-compare

| 字段 | 值 |
|------|-----|
| component_id | code-compare |
| semantic_role | code_comparison |
| 适用内容 | 改前/改后或 A/B 代码对照 |
| 必需载荷字段 | before_code, after_code |
| 可选载荷字段 | title, before_lang, after_lang |
| 不适用条件 | 单一代码块；无明确对照语义 |
| fallback | 通用库 1a/1b 代码块 |
| 允许 formatter 自动选择 | 是（需有对照语义） |
| 需要作者提供素材 | 否 |

### 4. media-text

| 字段 | 值 |
|------|-----|
| component_id | media-text |
| semantic_role | media_text |
| 适用内容 | 图片 + 绑定解释段落 |
| 必需载荷字段 | image_url, explanation_text |
| 可选载荷字段 | image_caption |
| 不适用条件 | 无图片；图片无绑定解释 |
| fallback | 通用库 2a 标准图片 |
| 允许 formatter 自动选择 | 是（需有图文绑定语义） |
| 需要作者提供素材 | **是**——图片 URL |

### 5. gallery

| 字段 | 值 |
|------|-----|
| component_id | gallery |
| semantic_role | gallery |
| 适用内容 | 2-4 张相关图片组图 |
| 必需载荷字段 | images（≥2 项，每项含 url + caption） |
| 可选载荷字段 | title |
| 不适用条件 | 只 1 张图；图片无关联 |
| fallback | 多张独立 2a 图片 |
| 允许 formatter 自动选择 | 是（需有组图语义） |
| 需要作者提供素材 | **是**——所有图片 URL |

### 6. long-image

| 字段 | 值 |
|------|-----|
| component_id | long-image |
| semantic_role | long_image |
| 适用内容 | 长截图、流程图、信息图 |
| 必需载荷字段 | image_url, caption |
| 可选载荷字段 | 无 |
| 不适用条件 | 普通截图无长图语义 |
| fallback | 通用库 2a 标准图片 |
| 允许 formatter 自动选择 | 是（需有长图语义） |
| 需要作者提供素材 | **是**——图片 URL |

### 7. resources

| 字段 | 值 |
|------|-----|
| component_id | resources |
| semantic_role | resource_list |
| 适用内容 | 2 个及以上参考资料链接集合 |
| 必需载荷字段 | links（≥2 项，每项含 name + url） |
| 可选载荷字段 | title |
| 不适用条件 | 只 1 个链接；非参考资料语义 |
| fallback | 普通链接文本 |
| 允许 formatter 自动选择 | 是（需有参考资料语义） |
| 需要作者提供素材 | **是**——链接 URL |

### 8. footnotes

| 字段 | 值 |
|------|-----|
| component_id | footnotes |
| semantic_role | footnote |
| 适用内容 | 正文引用标记 + 文末注释区 |
| 必需载荷字段 | notes（≥1 项，每项含 id + content） |
| 可选载荷字段 | source_url |
| 不适用条件 | 无 `[^N]` 脚注语法 |
| fallback | 不生成脚注区；重要内容融入正文 |
| 允许 formatter 自动选择 | 是（需有脚注语法） |
| 需要作者提供素材 | 否 |

### 9. dialogue

| 字段 | 值 |
|------|-----|
| component_id | dialogue |
| semantic_role | dialogue |
| 适用内容 | 用户/助手对话、访谈、排障问答 |
| 必需载荷字段 | messages（≥1 组，每项含 role + content） |
| 可选载荷字段 | title, speaker_names |
| 不适用条件 | 无对话语义的普通段落 |
| fallback | 普通引用段落 |
| 允许 formatter 自动选择 | 是（需有对话语义） |
| 需要作者提供素材 | 否（但对话内容必须真实） |

### 10. facts

| 字段 | 值 |
|------|-----|
| component_id | facts |
| semantic_role | fact / statistic |
| 适用内容 | 参数、版本、价格、状态等键值信息 |
| 必需载荷字段 | items（≥2 项，每项含 key + value） |
| 可选载荷字段 | title |
| 不适用条件 | 无明确键值信息语义 |
| fallback | 普通列表 |
| 允许 formatter 自动选择 | 是（需有键值信息语义） |
| 需要作者提供素材 | 否（但数据必须真实） |

### 11. decision

| 字段 | 值 |
|------|-----|
| component_id | decision |
| semantic_role | decision |
| 适用内容 | 方案选择、选型结论 |
| 必需载荷字段 | recommended, options（≥2 项，每项含 name + description） |
| 可选载荷字段 | title, reasoning |
| 不适用条件 | 无明确方案选择语义；少于 2 个候选方案 |
| fallback | 普通对比段落 |
| 允许 formatter 自动选择 | 是（需有选型语义） |
| 需要作者提供素材 | 否 |

### 12. steps

| 字段 | 值 |
|------|-----|
| component_id | steps |
| semantic_role | step_sequence |
| 适用内容 | 操作教程、安装流程、部署流程 |
| 必需载荷字段 | steps（≥2 项，有序） |
| 可选载荷字段 | title |
| 不适用条件 | 无明确操作流程语义 |
| fallback | 普通有序列表 |
| 允许 formatter 自动选择 | 是（需有流程语义） |
| 需要作者提供素材 | 否 |

### 13. compare

| 字段 | 值 |
|------|-----|
| component_id | compare |
| semantic_role | comparison |
| 适用内容 | 产品比较、版本差异、方案优缺点 |
| 必需载荷字段 | subject_a, subject_b, dimensions, rows |
| 可选载荷字段 | title |
| 不适用条件 | 只有单方描述；比较维度不一致；无明确比较语义 |
| fallback | 普通段落 / 有序列表 |
| 允许 formatter 自动选择 | 是（需有比较语义） |
| 需要作者提供素材 | 否 |

### 14. annotated-image

| 字段 | 值 |
|------|-----|
| component_id | annotated-image |
| semantic_role | image_annotation |
| 适用内容 | 界面说明、架构图讲解、截图标注 |
| 必需载荷字段 | image_url, notes（≥1 项，每项含 number + description） |
| 可选载荷字段 | caption |
| 不适用条件 | 无图片；无注释点 |
| fallback | 普通图片 + 列表 |
| 允许 formatter 自动选择 | 是（需有标注语义） |
| 需要作者提供素材 | **是**——图片 URL + 真实标注点 |

### 15. faq

| 字段 | 值 |
|------|-----|
| component_id | faq |
| semantic_role | faq |
| 适用内容 | 读者常见问题、产品 FAQ |
| 必需载荷字段 | items（≥1 项，每项含 question + answer） |
| 可选载荷字段 | title |
| 不适用条件 | 原文没有真实问题与回答结构；仅为增加视觉变化 |
| fallback | 普通标题 + 段落 |
| 允许 formatter 自动选择 | 是（需有问答语义） |
| 需要作者提供素材 | 否 |

### 16. timeline

| 字段 | 值 |
|------|-----|
| component_id | timeline |
| semantic_role | timeline |
| 适用内容 | 产品演进、项目里程碑、版本发布 |
| 必需载荷字段 | events（≥2 项，每项含 time + description） |
| 可选载荷字段 | title, event_title |
| 不适用条件 | 事件没有时间或阶段顺序；无演进语义 |
| fallback | 普通有序列表 |
| 允许 formatter 自动选择 | 是（需有时间线语义） |
| 需要作者提供素材 | 否 |

### 17. checklist

| 字段 | 值 |
|------|-----|
| component_id | checklist |
| semantic_role | checklist |
| 适用内容 | 发布前检查、迁移检查、安全检查 |
| 必需载荷字段 | items（≥2 项，每项含 text + checked） |
| 可选载荷字段 | title |
| 不适用条件 | 无明确检查清单语义 |
| fallback | 普通列表 |
| 允许 formatter 自动选择 | 是（需有检查清单语义） |
| 需要作者提供素材 | 否 |

### 18. case

| 字段 | 值 |
|------|-----|
| component_id | case |
| semantic_role | case |
| 适用内容 | 实践案例、项目复盘、问题-行动-结果 |
| 必需载荷字段 | context, challenge, action, result（至少 3 项） |
| 可选载荷字段 | title |
| 不适用条件 | 无明确案例复盘语义 |
| fallback | 普通小标题段落 |
| 允许 formatter 自动选择 | 是（需有案例语义） |
| 需要作者提供素材 | 否（但案例必须真实） |

### 19. cta

| 字段 | 值 |
|------|-----|
| component_id | cta |
| semantic_role | article_cta |
| 适用内容 | 下一步操作、文章结尾行动建议 |
| 必需载荷字段 | text, url（必须 HTTPS） |
| 可选载荷字段 | action, title |
| 不适用条件 | 无明确行动建议语义；URL 非 HTTPS |
| fallback | 使用原有签名，不生成 CTA |
| 允许 formatter 自动选择 | 是（需有行动终点语义） |
| 需要作者提供素材 | **是**——行动 URL |

---

## 三、组件覆盖矩阵

### 13 核心组件 → 语义角色映射

| # | 核心组件 | 对应语义角色 | 文章级/正文级 |
|---|---------|-------------|-------------|
| 1 | 全局容器 | formatter_generated | 文章级（Formatter 自动生成） |
| 2 | 封面/引言卡 | article_cover | 文章级 |
| 3 | 目录导航 | article_toc | 文章级 |
| 4 | 章节标题 | article_section | 文章级 |
| 5 | 正文段落 | paragraph | 正文级 |
| 6 | 行内样式 | secondary_emphasis | 正文级 |
| 7 | 小标签标题 | subtitle | 正文级 |
| 8 | 代码块 | code / command / prompt | 正文级 |
| 9 | 引用/金句 | quote / key_statement | 正文级 |
| 10 | 提示框 | warning / tip / information | 正文级 |
| 11 | 表格/列表/流程 | ordered_list / pill_list / process_flow | 正文级 |
| 12 | 图片/视频 | image / video | 正文级 |
| 13 | 页脚/签名/品牌 | article_signature | 文章级 |

### 19 高级组件 → 语义角色映射

| # | 高级组件 | 对应语义角色 | formatter 自动选择 |
|---|---------|-------------|-------------------|
| 1 | alert | warning / tip / information | 是（需警示语义） |
| 2 | quote | quote / key_statement | 是（需金句语义） |
| 3 | code-compare | code_comparison | 是（需对照语义） |
| 4 | media-text | media_text | 是（需图文绑定） |
| 5 | gallery | gallery | 是（需组图语义） |
| 6 | long-image | long_image | 是（需长图语义） |
| 7 | resources | resource_list | 是（需参考资料语义） |
| 8 | footnotes | footnote | 是（需脚注语法） |
| 9 | dialogue | dialogue | 是（需对话语义） |
| 10 | facts | fact / statistic | 是（需键值信息） |
| 11 | decision | decision | 是（需选型语义） |
| 12 | steps | step_sequence | 是（需流程语义） |
| 13 | compare | comparison | 是（需比较语义） |
| 14 | annotated-image | image_annotation | 是（需标注语义） |
| 15 | faq | faq | 是（需问答语义） |
| 16 | timeline | timeline | 是（需时间线语义） |
| 17 | checklist | checklist | 是（需检查清单语义） |
| 18 | case | case | 是（需案例语义） |
| 19 | cta | article_cta | 是（需行动终点语义） |

---

## 四、降级规则总表

| 条件 | 降级方式 |
|------|---------|
| 无图片 | 不得生成 gallery/long-image/media-text/annotated-image |
| 只有 1 个普通链接 | 使用原版链接，不生成 resources |
| 单一代码块 | 使用通用库 1a/1b，不生成 code-compare |
| 无 `[^N]` 脚注 | 不生成脚注区 |
| 缺少高级组件必需字段 | 回退到 fallback 或正文，**绝不保留占位符** |
| 无 `:::` 语法且无语义匹配 | 正常按原版流程排版，不生成高级组件 |
| URL 非 HTTPS | 不生成 CTA，使用原有签名 |
| 对话内容非真实访谈 | 不生成 dialogue，回退为引用段落 |

---

## 五、Formatter 自动选择权限

1. Formatter 可以根据目标平台、用户主题、内容长度、组件兼容性、视觉密度最终选择组件。
2. Formatter 可以选择 fallback。
3. Formatter **不得**编造缺失字段。
4. Formatter **不得**把普通段落强改成 FAQ/timeline/checklist 等。
5. Formatter **不得**为凑组件重复正文。
6. Formatter **不得**改写核心观点、事实、数字或引用。
7. "支持所有组件"不等于"一篇文章使用所有组件"。
8. 一篇文章主要高级组件建议 3-6 个；短资讯 0-2 个。
9. `force_all_components` 必须为 `false`。
