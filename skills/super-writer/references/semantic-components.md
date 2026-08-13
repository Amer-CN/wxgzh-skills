# 统一语义词表

> 本文件定义 Super Writer 输出的稳定语义角色，不直接绑定某个主题。
> 写作 Skill 只声明语义角色和候选组件；Formatter 拥有最终组件选择权。
>
> 每个角色定义：语义含义、必需字段、可选字段、允许子角色、是否逐字保留、是否需要证据、候选组件、fallback、禁止滥用条件。

---

## 一、文章级角色

### article_cover

| 字段 | 值 |
|------|-----|
| role | article_cover |
| 语义含义 | 文章封面/引言卡，包含标题和开头引言 |
| required_fields | title, summary_or_intro |
| optional_fields | author_name, cover_image_url |
| allowed_children | 无（文章级容器） |
| preserve_exactly | title（标题逐字保留） |
| evidence_required | 否 |
| formatter_candidates | cover-breaking |
| fallback | 普通标题段落 |
| 禁止滥用条件 | 无标题文章不使用 |

### article_toc

| 字段 | 值 |
|------|-----|
| role | article_toc |
| 语义含义 | 目录导航，精选 2-3 个核心章节看点 |
| required_fields | toc_items（≤3 项） |
| optional_fields | 无 |
| allowed_children | 无 |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | toc-scroll |
| fallback | 不生成目录 |
| 禁止滥用条件 | 文章少于 3 个章节时不使用；目录是精选不是全量 |

### article_intro

| 字段 | 值 |
|------|-----|
| role | article_intro |
| 语义含义 | 文章开头引言段落 |
| required_fields | text |
| optional_fields | highlight_phrases |
| allowed_children | paragraph, key_statement |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | cover-breaking, paragraph |
| fallback | paragraph |
| 禁止滥用条件 | 无 |

### article_section

| 字段 | 值 |
|------|-----|
| role | article_section |
| 语义含义 | `##` 级别的章节标题 |
| required_fields | heading_text, section_index |
| optional_fields | english_label, is_conclusion |
| allowed_children | 所有正文级角色 |
| preserve_exactly | heading_text（标题逐字保留） |
| evidence_required | 否 |
| formatter_candidates | chapter-title |
| fallback | 普通加粗标题 |
| 禁止滥用条件 | 无章节的文章不使用 |

### article_conclusion

| 字段 | 值 |
|------|-----|
| role | article_conclusion |
| 语义含义 | 文章结语章节 |
| required_fields | heading_text |
| optional_fields | section_index |
| allowed_children | paragraph, key_statement, article_cta |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | chapter-title（结语编号变体） |
| fallback | article_section |
| 禁止滥用条件 | 无明确结语语义时不使用 |

### article_cta

| 字段 | 值 |
|------|-----|
| role | article_cta |
| 语义含义 | 文章行动终点，下一步操作建议 |
| required_fields | text, url（必须 HTTPS） |
| optional_fields | action, title |
| allowed_children | 无 |
| preserve_exactly | text（行动文本逐字保留） |
| evidence_required | 否 |
| formatter_candidates | cta |
| fallback | 使用原有签名，不生成 CTA |
| 禁止滥用条件 | 无明确行动建议时不使用；不得自动添加营销口号；URL 非 HTTPS 不使用 |

### article_signature

| 字段 | 值 |
|------|-----|
| role | article_signature |
| 语义含义 | 文章末尾固定署名 |
| required_fields | 无（固定文案由 formatter 生成） |
| optional_fields | 无 |
| allowed_children | 无 |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | footer-signature-brand |
| fallback | 无（固定组件，末尾唯一） |
| 禁止滥用条件 | 只在文章末尾出现一次；不得在中间出现 |

---

## 二、正文级角色

### paragraph

| 字段 | 值 |
|------|-----|
| role | paragraph |
| 语义含义 | 普通正文段落 |
| required_fields | text |
| optional_fields | highlight_phrases（每段 1-3 个关键词） |
| allowed_children | secondary_emphasis |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | paragraph |
| fallback | 无（最基础角色） |
| 禁止滥用条件 | 无 |

### key_statement

| 字段 | 值 |
|------|-----|
| role | key_statement |
| 语义含义 | 核心观点或关键金句，全文最强锚点 |
| required_fields | text |
| optional_fields | 无 |
| allowed_children | 无 |
| preserve_exactly | 是（金句逐字保留） |
| evidence_required | 否 |
| formatter_candidates | quote（highlight）, quote-oneliner |
| fallback | paragraph + strong |
| 禁止滥用条件 | max_recommended_per_article: 5；到处使用等于没有重点 |

### secondary_emphasis

| 字段 | 值 |
|------|-----|
| role | secondary_emphasis |
| 语义含义 | 行内强调（加粗/高亮/下划线/荧光笔） |
| required_fields | text, style_type（bold/highlight/underline/marker） |
| optional_fields | 无 |
| allowed_children | 无 |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | inline-styles |
| fallback | 普通文本 |
| 禁止滥用条件 | 每段 1-3 个短语，不整段划线 |

### subtitle

| 字段 | 值 |
|------|-----|
| role | subtitle |
| 语义含义 | 段落级小标题 |
| required_fields | heading_text |
| optional_fields | variant（left-bar/pill/numbered）, number |
| allowed_children | 无 |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | label-heading |
| fallback | 普通加粗段落 |
| 禁止滥用条件 | 不用虚线框包标题 |

### quote

| 字段 | 值 |
|------|-----|
| role | quote |
| 语义含义 | 引用内容，可带来源 |
| required_fields | text |
| optional_fields | source, quote_type（normal/highlight/sourced） |
| allowed_children | 无 |
| preserve_exactly | 是（引文逐字保留） |
| evidence_required | sourced 类型时需要 source |
| formatter_candidates | quote, quote-oneliner |
| fallback | paragraph |
| 禁止滥用条件 | 无引号或非金句的普通段落不使用；必须保留原话和来源 |

### fact

| 字段 | 值 |
|------|-----|
| role | fact |
| 语义含义 | 参数、版本、价格、状态等键值事实 |
| required_fields | items（≥2 项，每项含 key + value） |
| optional_fields | title |
| allowed_children | 无 |
| preserve_exactly | 是（事实数据逐字保留） |
| evidence_required | 是（每项事实需要 evidence_ids） |
| formatter_candidates | facts |
| fallback | 普通列表 |
| 禁止滥用条件 | 无明确键值信息语义时不使用；不得编造数据 |

### statistic

| 字段 | 值 |
|------|-----|
| role | statistic |
| 语义含义 | 统计数据，是 fact 的特化 |
| required_fields | value, label |
| optional_fields | source, date |
| allowed_children | 无 |
| preserve_exactly | 是（数字逐字保留） |
| evidence_required | 是 |
| formatter_candidates | facts |
| fallback | paragraph + strong |
| 禁止滥用条件 | 必须附证据 ID；不得编造数字 |

### example

| 字段 | 值 |
|------|-----|
| role | example |
| 语义含义 | 示例说明 |
| required_fields | text |
| optional_fields | 无 |
| allowed_children | paragraph, code |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | paragraph, label-heading |
| fallback | paragraph |
| 禁止滥用条件 | 无 |

### case

| 字段 | 值 |
|------|-----|
| role | case |
| 语义含义 | 实践案例、项目复盘、问题-行动-结果 |
| required_fields | context, challenge, action, result（至少 3 项） |
| optional_fields | title |
| allowed_children | paragraph, fact, statistic |
| preserve_exactly | 否 |
| evidence_required | 是（结果需要证据） |
| formatter_candidates | case |
| fallback | 普通小标题段落 |
| 禁止滥用条件 | 无明确案例复盘语义时不使用；案例必须真实 |

### step_sequence

| 字段 | 值 |
|------|-----|
| role | step_sequence |
| 语义含义 | 有序操作步骤、部署流程 |
| required_fields | steps（≥2 项，有序） |
| optional_fields | title |
| allowed_children | code, command, warning |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | steps |
| fallback | ordered_list |
| 禁止滥用条件 | 必须写出有顺序的动作；无明确操作流程语义时不使用 |

### ordered_list

| 字段 | 值 |
|------|-----|
| role | ordered_list |
| 语义含义 | 有序列表 |
| required_fields | items（≥2 项） |
| optional_fields | 无 |
| allowed_children | paragraph |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | table-list-flow |
| fallback | paragraph（缩进） |
| 禁止滥用条件 | 无 |

### pill_list

| 字段 | 值 |
|------|-----|
| role | pill_list |
| 语义含义 | 药丸标签列表，用于并列要点 |
| required_fields | items（≥2 项） |
| optional_fields | 无 |
| allowed_children | 无 |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | table-list-flow, label-heading |
| fallback | ordered_list |
| 禁止滥用条件 | 无 |

### process_flow

| 字段 | 值 |
|------|-----|
| role | process_flow |
| 语义含义 | 流程图/过程描述 |
| required_fields | steps（≥2 项，含顺序关系） |
| optional_fields | title |
| allowed_children | paragraph |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | table-list-flow, steps |
| fallback | ordered_list |
| 禁止滥用条件 | 无明确流程语义时不使用 |

### comparison

| 字段 | 值 |
|------|-----|
| role | comparison |
| 语义含义 | 结构化对比，双方或多方在统一维度上的比较 |
| required_fields | subject_a, subject_b, dimensions, rows |
| optional_fields | title, subject_c（三方对比时） |
| allowed_children | 无 |
| preserve_exactly | 是（对比数据逐字保留） |
| evidence_required | 否 |
| formatter_candidates | compare, table-list-flow |
| fallback | paragraphs + ordered_list |
| 禁止滥用条件 | 只有单方描述不使用；比较维度不一致不使用；不得编造对比数据 |

### decision

| 字段 | 值 |
|------|-----|
| role | decision |
| 语义含义 | 方案选择、选型结论 |
| required_fields | recommended, options（≥2 项，每项含 name + description） |
| optional_fields | title, reasoning |
| allowed_children | 无 |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | decision |
| fallback | 普通对比段落 |
| 禁止滥用条件 | 必须写出背景、选项、权衡和结论；少于 2 个候选方案不使用 |

### timeline

| 字段 | 值 |
|------|-----|
| role | timeline |
| 语义含义 | 时间线/里程碑/版本演进 |
| required_fields | events（≥2 项，每项含 time + description） |
| optional_fields | title, event_title |
| allowed_children | 无 |
| preserve_exactly | 是（时间和事件逐字保留） |
| evidence_required | 否 |
| formatter_candidates | timeline |
| fallback | ordered_list |
| 禁止滥用条件 | 事件没有时间或阶段顺序不使用；无演进语义不使用 |

### checklist

| 字段 | 值 |
|------|-----|
| role | checklist |
| 语义含义 | 可执行检查项清单 |
| required_fields | items（≥2 项，每项含 text + checked） |
| optional_fields | title |
| allowed_children | 无 |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | checklist |
| fallback | 普通列表 |
| 禁止滥用条件 | 必须是可执行检查项；无明确检查清单语义时不使用 |

### faq

| 字段 | 值 |
|------|-----|
| role | faq |
| 语义含义 | 问答集合 |
| required_fields | items（≥1 项，每项含 question + answer） |
| optional_fields | title |
| allowed_children | 无 |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | faq |
| fallback | subtitle + paragraph |
| 禁止滥用条件 | 原文没有真实问题与回答结构不使用；只是为了增加视觉变化不使用 |

### dialogue

| 字段 | 值 |
|------|-----|
| role | dialogue |
| 语义含义 | 对话/访谈/排障问答 |
| required_fields | messages（≥1 组，每项含 role + content） |
| optional_fields | title, speaker_names |
| allowed_children | 无 |
| preserve_exactly | 是（对话内容逐字保留） |
| evidence_required | 否 |
| formatter_candidates | dialogue |
| fallback | 普通引用段落 |
| 禁止滥用条件 | 只能来自真实访谈或明确标注的模拟场景；无对话语义不使用 |

### warning

| 字段 | 值 |
|------|-----|
| role | warning |
| 语义含义 | 风险提示/严重警告 |
| required_fields | text |
| optional_fields | title |
| allowed_children | 无 |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | alert（warning/caution）, alert-box |
| fallback | 普通引用块 `>` |
| 禁止滥用条件 | 无明确警示语义不使用 |

### tip

| 字段 | 值 |
|------|-----|
| role | tip |
| 语义含义 | 小技巧/建议 |
| required_fields | text |
| optional_fields | title |
| allowed_children | 无 |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | alert（tip）, alert-box |
| fallback | 普通引用块 `>` |
| 禁止滥用条件 | 无明确建议语义不使用 |

### information

| 字段 | 值 |
|------|-----|
| role | information |
| 语义含义 | 补充说明/重点强调 |
| required_fields | text |
| optional_fields | title |
| allowed_children | 无 |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | alert（note/important）, alert-box |
| fallback | 普通引用块 `>` |
| 禁止滥用条件 | 无明确补充说明语义不使用 |

### code

| 字段 | 值 |
|------|-----|
| role | code |
| 语义含义 | 代码块 |
| required_fields | code_text |
| optional_fields | language, title |
| allowed_children | 无 |
| preserve_exactly | 是（代码逐字保留） |
| evidence_required | 否 |
| formatter_candidates | code-block（1a 深色/1b 浅色） |
| fallback | 普通等宽文本 |
| 禁止滥用条件 | 代码块内的英文、半角符号、缩进原样保留 |

### command

| 字段 | 值 |
|------|-----|
| role | command |
| 语义含义 | 命令行指令 |
| required_fields | code_text |
| optional_fields | title |
| allowed_children | 无 |
| preserve_exactly | 是（命令逐字保留） |
| evidence_required | 否 |
| formatter_candidates | code-block（1b 浅色） |
| fallback | code |
| 禁止滥用条件 | 无 |

### prompt

| 字段 | 值 |
|------|-----|
| role | prompt |
| 语义含义 | Prompt 提示词 |
| required_fields | code_text |
| optional_fields | title |
| allowed_children | 无 |
| preserve_exactly | 是（Prompt 逐字保留） |
| evidence_required | 否 |
| formatter_candidates | code-block（1a 深色） |
| fallback | code |
| 禁止滥用条件 | 无 |

### code_comparison

| 字段 | 值 |
|------|-----|
| role | code_comparison |
| 语义含义 | 改前/改后或 A/B 代码对照 |
| required_fields | before_code, after_code |
| optional_fields | title, before_lang, after_lang |
| allowed_children | 无 |
| preserve_exactly | 是（代码逐字保留） |
| evidence_required | 否 |
| formatter_candidates | code-compare |
| fallback | 通用库 1a/1b 代码块 |
| 禁止滥用条件 | 必须同时存在前后或 A/B 代码；单一代码块不使用 |

### resource_list

| 字段 | 值 |
|------|-----|
| role | resource_list |
| 语义含义 | 参考资料链接集合 |
| required_fields | links（≥2 项，每项含 name + url） |
| optional_fields | title |
| allowed_children | 无 |
| preserve_exactly | 是（URL 逐字保留） |
| evidence_required | 否 |
| formatter_candidates | resources |
| fallback | 普通链接文本 |
| 禁止滥用条件 | 必须有名称、用途和链接；只 1 个链接不使用 |

### footnote

| 字段 | 值 |
|------|-----|
| role | footnote |
| 语义含义 | 脚注/引用注释 |
| required_fields | notes（≥1 项，每项含 id + content） |
| optional_fields | source_url |
| allowed_children | 无 |
| preserve_exactly | 是（注释内容逐字保留） |
| evidence_required | 否 |
| formatter_candidates | footnotes |
| fallback | 不生成脚注区；重要内容融入正文 |
| 禁止滥用条件 | 无 `[^N]` 脚注语法不使用 |

### media_text

| 字段 | 值 |
|------|-----|
| role | media_text |
| 语义含义 | 图文绑定，图片 + 解释段落 |
| required_fields | image_url, explanation_text |
| optional_fields | image_caption |
| allowed_children | 无 |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | media-text |
| fallback | image + paragraph |
| 禁止滥用条件 | 无图片不使用；图片无绑定解释不使用 |

### image

| 字段 | 值 |
|------|-----|
| role | image |
| 语义含义 | 普通图片/截图 |
| required_fields | image_url |
| optional_fields | caption, is_gif |
| allowed_children | 无 |
| preserve_exactly | 是（URL 逐字保留） |
| evidence_required | 否 |
| formatter_candidates | image-video（2a/2b） |
| fallback | 待补素材占位（2c） |
| 禁止滥用条件 | 无图片 URL 不使用；不得凭空编造图床链接 |

### image_annotation

| 字段 | 值 |
|------|-----|
| role | image_annotation |
| 语义含义 | 图片局部编号注释 |
| required_fields | image_url, notes（≥1 项，每项含 number + description） |
| optional_fields | caption |
| allowed_children | 无 |
| preserve_exactly | 否 |
| evidence_required | 否 |
| formatter_candidates | annotated-image |
| fallback | image + ordered_list |
| 禁止滥用条件 | 必须有图片和真实标注点；无图片不使用 |

### gallery

| 字段 | 值 |
|------|-----|
| role | gallery |
| 语义含义 | 图片组图（2-4 张相关图片） |
| required_fields | images（≥2 项，每项含 url + caption） |
| optional_fields | title |
| allowed_children | 无 |
| preserve_exactly | 是（URL 逐字保留） |
| evidence_required | 否 |
| formatter_candidates | gallery |
| fallback | 多张独立 image |
| 禁止滥用条件 | 只 1 张图不使用；图片无关联不使用 |

### long_image

| 字段 | 值 |
|------|-----|
| role | long_image |
| 语义含义 | 长截图/流程图/信息图 |
| required_fields | image_url, caption |
| optional_fields | 无 |
| allowed_children | 无 |
| preserve_exactly | 是（URL 逐字保留） |
| evidence_required | 否 |
| formatter_candidates | long-image |
| fallback | image |
| 禁止滥用条件 | 普通截图无长图语义不使用 |

### video

| 字段 | 值 |
|------|-----|
| role | video |
| 语义含义 | 视频/录屏（以 GIF 或图片占位呈现） |
| required_fields | video_url 或 image_url |
| optional_fields | caption |
| allowed_children | 无 |
| preserve_exactly | 是（URL 逐字保留） |
| evidence_required | 否 |
| formatter_candidates | image-video（2b/2c） |
| fallback | 待补素材占位（2c） |
| 禁止滥用条件 | 无视频/图片 URL 不使用 |

---

## 三、使用规则

1. **先根据内容选择语义形态，再由 formatter 选择具体组件。**
2. **不得为了使用组件改变文章论证。**
3. **同一个信息不得同时完整复制到多个组件。**
4. **一篇文章的主要高级组件建议控制在 3–6 种。**
5. **key_statement 建议全文不超过 5 个。**
6. **表格、对比、时间线、FAQ 必须有完整结构化载荷。**
7. **缺少载荷时必须使用 fallback，不允许 formatter 编造。**
8. **所有角色都有可触发的语义角色；内容需要时能稳定触发；内容不需要时不强行使用。**

---

## 四、角色总数统计

| 类别 | 数量 | 角色列表 |
|------|------|---------|
| 文章级 | 7 | article_cover, article_toc, article_intro, article_section, article_conclusion, article_cta, article_signature |
| 正文级-基础 | 5 | paragraph, key_statement, secondary_emphasis, subtitle, quote |
| 正文级-数据 | 3 | fact, statistic, example |
| 正文级-结构 | 9 | case, step_sequence, ordered_list, pill_list, process_flow, comparison, decision, timeline, checklist |
| 正文级-交互 | 2 | faq, dialogue |
| 正文级-提示 | 3 | warning, tip, information |
| 正文级-代码 | 4 | code, command, prompt, code_comparison |
| 正文级-引用 | 2 | resource_list, footnote |
| 正文级-媒体 | 6 | media_text, image, image_annotation, gallery, long_image, video |
| **合计** | **41** | |
