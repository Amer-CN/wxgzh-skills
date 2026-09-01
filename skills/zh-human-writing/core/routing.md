# core/routing.md
# zh-human-writing v1 — 路由与操作权限表

---

## 前置规则（Batch 2）

输入 handoff 携带 `prose_craft_applied=true` 时：
- strategy 一律 `preserve`（覆盖默认路由表任何来源行）；
- 检测照跑、只报告不改写（audit 语义：pattern_audit / fidelity_guard / change_report 全量执行，但不产改写动作）。
输入 handoff 携带 `prose_craft_applied=true` 时：
- strategy 一律 `preserve`（覆盖默认路由表任何来源行）；
- 检测照跑、只报告不改写（audit 语义：pattern_audit / fidelity_guard / change_report 全量执行，但不产改写动作）。
- `handoff.prose_craft` 是蒸馏产物与作者真实风格；它和通用去味规则冲突时以它为准。
- 该优先级不豁免 fidelity、hard-residue 或事实保护。

## 77R AI-tone 与证伪护栏

- `pattern_audit.ai_tone` 只做 review；禁按命中数自动循环改写。
- `balance` 下，确认翻案腔动作后可改为直陈句；正常分类/澄清/真实自我修正保留。
- 禁为“人味”调句长/段长节奏或做 CV 类统计检查；禁删设问、比喻、句内排比；禁补单字虚词。

## 默认路由表

| source | 默认 strategy | 改动预算 | 审计范围 | 规则 |
|--------|--------------|---------|---------|------|
| author_written | preserve | 低 | 改动区 | 局部编辑优先；不静默重排段落；不删除承担信息/节奏/情绪作用的句子 |
| ai_draft | balance | 中 | 全文 | 允许删除纯空句；允许局部调整结构；rebuild 需用户明确授权 |
| mixed | balance | 中 | 全文+改动区重点 | 先区分作者正文/AI草稿/引用/代码；对作者正文用 preserve，对 AI 草稿用 balance |
| unknown | preserve | 低 | 改动区 | 不得自行升级为 rebuild；以最保守方式处理 |

---

## 操作权限表

### preserve 策略

| 操作 | 权限 | 条件 |
|------|------|------|
| delete_prompt | allow | 仅限 hard-residue 和 strong-contextual 聚集 ≥2 时 |
| rewrite_sentence | conditional | 存在 hard-residue 或聚集，且改写不改变事实和语义 |
| delete_sentence | conditional | 纯空句且不承担节奏/转场作用 |
| merge_sentences | deny | preserve 不允许合并句子 |
| split_sentence | conditional | 原句过长导致语义不清，拆分不改变语义 |
| adjust_paragraph | deny | preserve 不允许调整段落结构 |
| rearrange_structure | deny | preserve 不允许重排结构 |
| rewrite_opening | conditional | 开头存在 hard-residue，只做最小替换 |
| rewrite_ending | conditional | 结尾存在 hard-residue或无信息总结，只做最小替换 |
| change_title | conditional | 标题存在 hard-residue |
| add_transition | deny | preserve 不允许添加内容 |
| add_example | deny | 硬约束 |
| add_fact | deny | 硬约束 |
| add_opinion | deny | 硬约束 |
| rewrite_quote | deny | 硬约束 |

### balance 策略

| 操作 | 权限 | 条件 |
|------|------|------|
| delete_prompt | allow | hard-residue 和 strong-contextual 均可 |
| rewrite_sentence | allow | 存在表达问题，改写不改变事实和语义 |
| delete_sentence | conditional | 纯空句或无信息总结，且 length_retention 允许 |
| merge_sentences | conditional | 相邻句子高度重复或碎片化，合并后语义不变 |
| split_sentence | conditional | 原句过长导致语义不清，拆分后语义不变 |
| adjust_paragraph | conditional | 段落内存在无信息导航句，删除后需微调 |
| rearrange_structure | conditional | 仅限删除无信息段落后的局部衔接调整 |
| rewrite_opening | allow | 开头存在 AI 模式，改写不改变核心信息 |
| rewrite_ending | allow | 结尾存在 AI 模式，改写不改变核心信息 |
| change_title | conditional | 标题存在 AI 模式或模板占位符 |
| add_transition | conditional | 删除无信息段落后衔接断裂，不引入新事实 |
| add_example | deny | 硬约束 |
| add_fact | deny | 硬约束 |
| add_opinion | deny | 硬约束 |
| rewrite_quote | deny | 硬约束 |

### rebuild 策略

| 操作 | 权限 | 条件 |
|------|------|------|
| delete_prompt | allow | 所有模式级别均可 |
| rewrite_sentence | allow | 改写不改变事实和语义 |
| delete_sentence | conditional | 空句/无信息句/重复句，且 length_retention 允许 |
| merge_sentences | allow | 合并后语义不变 |
| split_sentence | allow | 拆分后语义不变 |
| adjust_paragraph | conditional | 不破坏文章核心逻辑和事实链条 |
| rearrange_structure | conditional | 仅限删除无信息段落后的局部衔接调整 |
| rewrite_opening | allow | 改写不改变核心信息 |
| rewrite_ending | allow | 改写不改变核心信息 |
| change_title | conditional | 标题存在 AI 模式或用户要求 |
| add_transition | conditional | 不引入新事实，仅改善衔接 |
| add_example | deny | 硬约束——rebuild 也不例外 |
| add_fact | deny | 硬约束——rebuild 也不例外 |
| add_opinion | deny | 硬约束——rebuild 也不例外 |
| rewrite_quote | deny | 硬约束——rebuild 也不例外 |

---

## 全局禁止项（所有 strategy 均禁止）

- 无依据增加具体细节
- 无依据增加第一人称
- 无依据增加观点、感受和经历
- 为了"人味"故意制造毛边
- 用综合分抵消硬约束失败
- 改写引用原文
- 改变数字、日期、百分比和单位
- 改变人名、机构名和产品名
- 改变代码、命令、路径、参数和字段
- 改变 URL
- 改变日志、错误和状态码
- 静默改变否定、条件、因果
- 静默改变责任主体和观点归属
- 静默改变范围和不确定程度
- 删除用户明确指定不可改的片段
