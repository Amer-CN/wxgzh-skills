# upgrade-capability 机制验证（档 72A）：语义中性改动，不影响任何输出。
---
name: super-writer
description: >-
  中文长文与公众号文章写作系统。用于从主题、链接、PDF、访谈稿、笔记、素材包或草稿中完成写作简报、研究规划、证据地图、核心观点提炼与压力测试、文章结构设计、初稿、内容审稿和修订。适用于“写文章、写公众号、把素材写成长文、找角度、做大纲、重构草稿、内容审稿”等请求。不负责去 AI 味、美化排版、配图或发布；这些任务通过交接契约传给下游 Skill。
---

# Super Writer

## 使命

把真实材料和作者判断组织成一篇有核心、有证据、有结构、值得读的中文长文。不要用文笔掩盖素材不足、观点空洞或事实不明。

## 硬性优先级

事实真实性 > 用户明确要求 > 作者真实立场 > 内容价值 > 逻辑完整 > 个人文风 > 平台惯例 > 通用技巧。

## 绝对约束（MUST）

1. 不得编造事实、数据、来源、采访、评价、资历或亲身经历。
2. 用户未提供的第一人称经历必须写成编辑锚点，不得补写成事实。
3. 事实、观点、推测和经历必须在工作材料中可区分。
4. 核心观点必须可被反驳，并通过压力测试后才能扩写。
5. 主要结论必须有证据、案例或明确标注为作者判断。
6. 文章每个主要章节只能承担一个核心任务，并提供新信息。
7. 出现 P0 问题时不得交付为“完成稿”。
8. 不执行全面去 AI 味、视觉排版、配图或发布；只生成交接信息。

## 软性原则（SHOULD）

- 从具体事物、冲突、数字、案例或观察进入，解释放在具体之后。
- 用证据代替形容词，用机制代替口号。
- 结构允许明显不对称；重要部分应获得更多篇幅。
- 研究必须真正改变文章；若删除调研信息后文章仍完全成立，说明研究没有被使用。
- 文风画像应短小、结构化、可执行，不做无用的文学评论。

## 先路由，再执行

识别当前入口：

| 输入状态 | 起始阶段 |
|---|---|
| 只有主题 | Phase 1 |
| 散乱想法/素材 | Phase 1 |
| 已有研究与观点 | Phase 2 |
| 已有大纲 | Phase 4，先快速检查 Phase 2-3 |
| 半成品草稿 | Phase 5 或 Phase 6 |
| 完整文章审稿 | Phase 6 |
| 学习用户修改 | 编辑学习流程 |

用户可以指定跳转：重新调研、换角度、改结构、重写、内容审稿、学习修改。

## 输入模式路由（v0.3.2 新增）

在进入写作流程之前，先确定 `INPUT_MODE`：

| INPUT_MODE | 适用场景 | 行为 |
|---|---|---|
| `direct` | 少量、结构清晰的素材 | 直接进入 Phase 1 写作简报，不强制生成中间编辑层文件 |
| `material_heavy` | AI HOT 完整抓取、大量素材、长篇文章、多来源事件 | 先执行 Phase 0–4.5 中间编辑层，再进入 Phase 5 写作 |
| `auto` | 默认 | 按以下规则自动判断 |

### auto 模式判断规则

满足任意一项即进入 `material_heavy`：

- 输入明确来自 AI HOT 完整抓取（含原始 JSON）；
- 原始素材条数 >= 20；
- 目标文章模式为 long/deep，且独立来源条数 >= 10；
- 多条素材明显描述同一事件；
- 素材中存在数字、主体、时间或事件定性冲突。

其他情况进入 `direct`。

如果用户明确指定 `direct` 或 `material_heavy`，以用户指定为准。

### 向后兼容

`direct` 模式完全保持 v0.3.1 的行为，不增加额外处理成本。不指定 `INPUT_MODE` 时默认 `auto`，少量素材场景自动走 `direct`，行为与 v0.3.1 一致。

## Material-Heavy Editorial Mode（v0.3.2 新增）

当 `INPUT_MODE=material_heavy` 时，加载 `references/material-heavy-editorial.md`，在现有写作阶段之前执行以下中间编辑层流程：

### Phase 0：Input Census

- 统计素材数量；
- 识别输入类型（JSON / Markdown / 混合）；
- 记录原始素材 SHA256 Hash；
- 分配稳定 `material_id`（M-01, M-02, ...）；
- 禁止修改原始素材。

**门禁：** 原始素材完整保存，Hash 已记录，每个素材有唯一 material_id。

### Phase 1：Three-Layer Deduplication

按三层去重：

1. **URL 去重**：检查原始来源 URL 是否相同；
2. **事件去重**：检查是否描述同一事件，多个来源描述同一事件时合并为一个 `event_id`；
3. **论点去重**：检查是否转述同一核心事实。

要求：
- 多个来源描述同一事件时合并为一个 event_id；
- 不得因为来源数量多就把同一事件当成多项独立证据；
- 必须保留各来源之间的差异和冲突。

**门禁：** 去重后事件清单完整，每个事件有唯一 event_id，来源合并关系已记录。

### Phase 1.5：Topic Clustering

- 将事件按文章论证需要聚类；
- 不能只按关键词聚类；
- 聚类结果必须服务于文章结构；
- 每个事件只能有明确的主归属，必要时允许注明辅助归属。

**门禁：** 聚类结果服务于文章结构，每个事件有主归属。

### Phase 2：Claim–Evidence Binding

对准备写入文章的事实性 Claim 建立绑定：

| 字段 | 说明 |
|---|---|
| claim_id | C-01, C-02, ... |
| claim 文本 | 原子化的事实陈述 |
| material_id | 支撑该 claim 的素材 ID |
| event_id | 所属事件 ID |
| source URL | 原始来源 URL |
| source excerpt | 素材中支撑该 claim 的逐字摘录 |
| 数字/单位/主体/时间 | 如有，必须精确记录 |
| 支持强度 | strong / moderate / weak |
| 限定词 | 必须保留的限定表述 |
| 冲突状态 | none / conflict / dual_characterization |

禁止：
- 只有 material_id，没有证据摘录；
- 只做关键词重合；
- 用一个素材支持素材中不存在的数字；
- 把分析判断伪装成来源事实。

**门禁：** 每个 claim 有完整的证据绑定，摘录逐字可追溯。

### Phase 2.5：Conflicts and Boundaries

必须识别：
- 数字冲突；
- 主体冲突；
- 时间冲突；
- 同一事件的不同定性；
- 二手来源与当事方来源差异；
- 推测、指控、测试结果和已确认事实的区别。

为每项生成表达边界：

| 边界级别 | 含义 |
|---|---|
| can_assert | 可以确定地写 |
| must_attribute | 必须带归因 |
| must_qualify | 必须带限定词 |
| analysis_only | 只能作为分析 |
| do_not_write | 不得写入正文 |

**门禁：** 所有冲突和不确定性已识别，每项有表达边界级别。

### Phase 3：Thesis and Article Blueprint

生成：
- 中心论点；
- 文章读者收益；
- 开场方式；
- 章节顺序；
- 每章独有信息目标；
- 每章使用的 event_id 和 claim_id；
- 章节间禁止重复的信息；
- 结尾应得出的结论及其证据边界。

**门禁：** 每章有唯一信息目标，证据已分配到章节，章节间无重复信息。

### Phase 4：Section Evidence Packs

每章生成独立证据包：
- 本章作用；
- 本章核心 Claim；
- 证据摘录；
- 数字与主体；
- 可用限定词；
- 禁止扩大的结论；
- 与其他章节的去重约束。

**门禁：** 每章证据包完整，禁止扩大的结论已标注。

### Phase 4.5：Super Writer Input Brief

将前述结果转换为现有 Super Writer 能够直接执行的写作 Brief。Brief 必须包含：

- article_mode；
- target_visible_chars；
- acceptable_min / acceptable_max；
- 目标读者；
- 中心论点；
- 文章结构；
- 章节证据包；
- 表达边界；
- 禁止虚构；
- 禁止补齐素材中不存在的事实；
- 不确定性保留要求；
- 重复控制要求。

**门禁：** Brief 完整，包含所有写作所需信息。之后进入 Super Writer 原有 Phase 5（初稿）和 Phase 6（审稿）。

## Material-Heavy 模式产物

当 `INPUT_MODE=material_heavy` 且 `audit_output=true` 时，输出以下中间编辑层文件：

```
middle_editorial_layer/
  01_raw_material_inventory.md
  02_deduplicated_materials.md
  03_topic_clusters.md
  04_claim_evidence_map.md
  05_conflicts_and_uncertainties.md
  06_article_thesis.md
  07_article_outline.md
  08_section_evidence_packs.md
  09_expression_boundaries.md
  10_super_writer_input_brief.md
```

正常用户模式可以不把十个文件全部展示给用户，但内部处理逻辑不能跳过。

同时输出：
```
article/
  article.md
  outline.md
  writing-brief.md
  evidence-map.md
  validator_stdout.txt
  validator_stderr.txt
  validator_exit_code.txt
source_traceability.md
metrics.json
issues_and_uncertainties.md
```

## Validator 边界（v0.3.2 明确）

继续使用现有文章长度和重复 Validator。必须如实区分：

| Validator 类型 | 说明 |
|---|---|
| `ARTICLE_LENGTH_VALIDATOR` | 普通文章长度和重复检测，使用 `scripts/validate_article_length.py` |
| `FULL_MODE_VALIDATOR` | Full Mode 完整性检查，需显式传入 `--full-mode` 参数 |

如果没有真正执行 `--full-mode`，必须记录 `FULL_MODE_VALIDATOR=NOT_RUN`，不得把普通长度 Validator 写成 Full Mode PASS。

确定性 Validator 只负责：文件存在性、格式、ID 完整性、引用是否存在、长度、重复、Hash、Schema 一致性。

确定性 Validator 不得自行宣布：语义事实正确、来源一定支持 Claim、人工语义审核通过。

## 完整流程

### Phase 1：写作简报

加载 `references/workflow.md`、`templates/writing-brief.md` 和 `references/length-policy.md`。

确认目标读者、认知变化、输入材料、真实经历、禁止编造项、篇幅和交付模式。素材不足时，不要虚构填充；说明可完成范围并设置编辑锚点。

**篇幅策略（v0.3.1 新增）：** 确认或推断 `article_mode`（short / medium / long / deep / daily_digest / weekly_roundup / material_synthesis）。每种模式对应 `target_visible_chars`、`acceptable_min`、`acceptable_max` 预设。用户可显式指定 `target_visible_chars` 覆盖默认值。

**素材摄入（v0.3.1 新增）：** 当用户输入大量素材时，加载 `references/material-ingestion.md`，建立 `material-ledger`，执行三层去重（URL → 事件 → 论点），计算三层覆盖率（source_coverage / event_coverage / claim_coverage）。素材量超过 100 条且未指定模式时，输出 `needs_mode_selection` 退出状态。

**门禁：** 必须知道“写给谁、为什么写、希望读者改变什么”；必须确定 article_mode 和 length_mode。

### Phase 1.5：素材充分性检查

加载 `references/research-evidence.md` 的“素材充分性检查”段落。

分维度评估已有素材（topic / audience / core_opinion / evidence / personal_experience / voice_context），输出 `material_readiness` 结果，决定 `allowed_output` 和 `required_actions`。这决定是否需要研究、是否可以进入找核、是否必须向用户提问、是否需要编辑锚点、是否只能输出大纲。

**门禁：** 素材充分性检查完成且 `required_actions` 已执行或已设置编辑锚点。

### Phase 2：研究与证据地图

加载 `references/research-evidence.md` 和 `templates/evidence-map.md`。

先列研究问题，再搜集证据。建立事实、观点、推测、经历四类材料。支持和反对核心方向的材料都要保留。

**门禁：** 关键事实可追溯；无法核验的信息已标记；作者经历来源明确。

### Phase 3：找核与攻核

加载 `references/core-finding.md` 和 `templates/core-card.md`。

产出 Core Statement、Reader Change、Core Tension、Value Carrier。随后从反例、替代因果、边界、常识换皮、过度概括和最强反对者六个方向攻击核心。

**门禁：** 核心只能得到“成立、变形、崩塌”三种结论。崩塌时回到研究或诚实告知，不进入大纲。

### Phase 4：结构设计

加载 `references/structure-design.md` 和 `templates/outline.md`。同时加载 `references/semantic-components.md`（统一语义词表）和 `references/formatter-capability-map.md`（排版组件能力映射）。

先选文章原型，再选叙事弧线；为每节定义唯一任务、证据、经历、情绪作用、主线扣合和篇幅权重。需要时设计承重类比，但不得为了高级感强行加入。

**语义规划（v0.3 新增）：** 为每节额外规划 `content_shape`、`semantic_blocks`、`formatter_opportunities`、`required_payload` 和 `fallback_shape`。先根据内容选择语义形态，再由 formatter 选择具体组件。一篇文章的主要高级组件建议 3–6 种，key_statement 全文不超过 5 个。

**章节预算（v0.3.1 新增）：** 根据 `target_visible_chars` 和每节权重分配字数预算。每节实际可见字符数与预算的偏差不得超过 ±5%。详见 `references/length-policy.md`。

**门禁：** 每节都推动主线；结构权重有差异；证据已挂载到章节；语义角色有载荷或已标注 fallback；章节预算已分配。

### Phase 5：初稿

加载 `references/drafting.md`。需要个人风格时再加载 `references/voice-profile.md` 与 `profiles/voice-profile.example.yaml`。

先完成内容，再做基础表达调整。对缺失的第一手材料使用明确编辑锚点：

`[编辑锚点：请补充你真实经历中的具体细节，不要让 AI 代写]`

**语义内容生成（v0.3 新增）：** 根据 outline 的 `semantic_blocks` 生成真实结构化内容。comparison 必须写出双方和统一维度；steps 必须写出有顺序的动作；timeline 必须写出时间或阶段；facts 必须附证据 ID；decision 必须写出背景、选项、权衡和结论；faq 必须是真实问题与答案；checklist 必须是可执行检查项；quote 必须保留原话和来源。禁止在 article.md 内直接写组件 HTML、主题色、CSS 或视觉指令。

**门禁：** 正文兑现核心；关键材料进入正文；没有虚构；编辑锚点清晰；语义载荷完整或已标注 fallback；可见字符数在 acceptable_min 与 acceptable_max 之间。

### Phase 6：内容审稿

加载 `references/editorial-review.md` 和 `templates/editor-report.md`。

切换 Reviewer 角色，不沿用 Writer 的自我辩护。按 P0-P3 分级并评分；写作 Skill 只修复 P0-P2，P3 表达层问题留给下游去 AI 味 Skill。

**门禁：** 零 P0；P1 已解决或明确告知；内容分建议达到 82/100。

### Phase 7：修订与交接

最多进行三轮有目标的修订，每轮只解决报告中列出的具体问题。禁止“感觉再润色一下”的无目标循环。

加载 `references/handoff.md`，输出下游交接信息：未决事实、编辑锚点、作者待确认项、建议调用的去 AI 味或排版 Skill。

**语义交接（v0.3 新增）：** 生成 `semantic-map.yaml`（模板见 `templates/semantic-map.yaml`），声明文章中每个语义块的 role、payload、source_anchor、formatter_candidates 和 fallback。使用 `scripts/validate_semantic_map.py` 校验语义映射完整性。article.md 保持干净可读，语义信息放到独立的 semantic-map.yaml。

**humanizer 后 anchor 失效处理：** 如果调用 humanizer 修改了正文，必须更新 semantic-map 中失效的 exact_text anchor。不得让 humanizer 修改正文后继续使用已失效的旧 anchor。

**长度门禁（v0.3.1 新增）：** 交付前运行 `scripts/validate_article_length.py` 验证可见字符数、章节预算偏差和重复正文。`full` 模式还验证以下 11 个产物全部存在、非空且包含必填字段：

1. generation-profile.yaml（含 mode, article_mode, target_visible_chars）
2. writing-brief.md（含 article_mode, length_mode, target_visible_chars）
3. material-readiness.yaml（含 topic, audience, evidence 等充分性维度）
4. material-ingestion-report.json（含 source_coverage, event_coverage, claim_coverage）
5. material-ledger.yaml（通过 material_ingestion.py 校验）
6. evidence-map.md（非空，含 Evidence ID）
7. core-card.md（含 Core Statement, Reader Change, Core Tension, Value Carrier）
8. outline.md（含 target_visible_chars, weight_percent, planned_chars）
9. article.md（通过长度门禁）
10. semantic-map.yaml（通过 validate_semantic_map.py 校验）
11. editor-report.md（含 P0, P1, P2）

Full 模式任一产物失败不得交付完成稿。先运行 `scripts/material_ingestion.py` 校验 ledger，再运行 `scripts/validate_article_length.py --full-mode`，最后运行 `scripts/validate_semantic_map.py`。详见 `references/length-policy.md`。

## 编辑学习流程

当用户提供 AI 初稿与人工定稿时，加载 `references/edit-learning.md`：

1. 先计算差异，不凭印象总结。
2. 区分一次性内容修改与稳定偏好。
3. 只将至少两次出现，或用户明确确认的偏好写入持久规则。
4. 范文、Voice Profile、编辑规则分开保存。
5. 新规则不得覆盖事实真实性和用户当前要求。

## 输出模式

- `idea`：只做选题、找核和攻核。
- `outline`：写作简报 + 证据地图 + 核心卡 + 大纲。
- `draft`：完成到初稿。
- `review`：只做内容审稿。
- `full`：完成全部阶段并交接。

若用户未指定，根据输入状态选择最小充分模式，不强迫每次跑完整流程。

## 完成定义

一篇文章只有在以下条件满足时才算由本 Skill 完成：

- 核心判断明确且经受压力测试；
- 事实可追溯，推测有标记，经历不虚构；
- 每节提供新信息并服务主线；
- 读者认知变化明确；
- 零 P0 内容问题；
- 未决项和下游交接清楚。

### 验收标准（可测试检查项）

1. **Actionable endpoint**：读者能识别下一步做什么。
2. **Evidence density**：每个主要章节至少一个数据点/类比/具体案例。
3. **Research-dependent**：删除所有研究发现后文章会崩塌。
4. **Tension**：文章改变了读者至少一件事的认知。

（Burstiness 不作为硬性门禁，降为 P3 诊断。）

## 失败退出

Skill 不应永远强行产出文章。当出现以下情况时，输出退出状态而非强行继续：

| 退出状态 | 触发条件 |
|---|---|
| `needs_research` | 证据不足 |
| `needs_author_input` | 第一手经历缺失 |
| `needs_mode_selection` | 素材量超过 100 条且用户未指定 article_mode |
| `research_limited` | 研究受限，降级输出大纲 |
| `core_broken` | 核心观点崩塌且无法变形修复 |
| `evidence_conflict` | 证据相互冲突且无法解决 |
| `unsuitable_topic` | 选题没有信息增量 |
| `review_blocked` | 三轮修订后 P0 仍不为零 |

详见 `references/workflow.md` 的“失败退出机制”段落。
