# Material-Heavy Editorial Mode

## 概述

Material-Heavy Editorial Mode 是 Super Writer v0.3.2 新增的输入模式，用于处理大量素材、多来源事件和长篇文章场景。它在现有写作阶段之前增加一个中间编辑层，确保：

- 原始素材可追溯（Hash + material_id）；
- 同一事件不被多条转述误当独立证据；
- 每个 claim 绑定真实来源和逐字摘录；
- 冲突和不确定性被识别和保留；
- 文章结构由证据驱动，而非素材堆砌。

## 触发条件

当 `INPUT_MODE=material_heavy` 或 `auto` 模式判断满足以下任意条件时进入：

- 输入明确来自 AI HOT 完整抓取（含原始 JSON）；
- 原始素材条数 >= 20；
- 目标文章模式为 long/deep，且独立来源条数 >= 10；
- 多条素材明显描述同一事件；
- 素材中存在数字、主体、时间或事件定性冲突。

## 流程

### Phase 0: Input Census

**输入：** 原始素材（JSON / Markdown / 混合）

**操作：**
1. 统计素材数量；
2. 识别输入类型；
3. 计算原始素材的 SHA256 Hash；
4. 为每个素材分配稳定 ID（M-01, M-02, ...）；
5. 保存原始素材副本，禁止修改。

**输出：** `01_raw_material_inventory.md`

**关键规则：**
- 原始素材不得修改；
- Hash 必须在处理前计算；
- material_id 一旦分配，在后续所有阶段保持不变。

### Phase 1: Three-Layer Deduplication

**三层去重：**

1. **URL 去重**：检查原始来源 URL 是否相同。相同 URL 的素材合并。
2. **事件去重**：检查是否描述同一事件。多个来源描述同一事件时合并为一个 event_id（E-01, E-02, ...）。
3. **论点去重**：检查是否转述同一核心事实。同一论点的多条转述不作为独立证据叠加。

**输出：** `02_deduplicated_materials.md`

**关键规则：**
- 合并后的事件保留所有来源信息；
- 来源之间的差异和冲突必须保留；
- 不得因为来源数量多就把同一事件当成多项独立证据。

### Phase 1.5: Topic Clustering

**操作：** 将事件按文章论证需要聚类。

**聚类原则：**
- 不能只按关键词聚类；
- 聚类结果必须服务于文章结构；
- 每个事件只能有明确的主归属，必要时允许注明辅助归属。

**输出：** `03_topic_clusters.md`

### Phase 2: Claim–Evidence Binding

**操作：** 对准备写入文章的事实性 Claim 建立绑定。

每个 Claim 必须包含：

| 字段 | 说明 |
|---|---|
| claim_id | C-01, C-02, ... |
| claim_text | 原子化的事实陈述 |
| material_id | 支撑该 claim 的素材 ID |
| event_id | 所属事件 ID |
| source_url | 原始来源 URL |
| source_excerpt | **必填**——素材中支撑该 claim 的逐字摘录(缺省/None 会在媒体请求构造时 FAIL_CLOSED,76A/76C/76E 三次生产返工实证) |
| numbers | 数字、单位、主体、时间（如有） |
| support_strength | strong / moderate / weak |
| qualifiers | 必须保留的限定表述 |
| conflict_status | none / conflict / dual_characterization |

**输出：** `04_claim_evidence_map.md`

**禁止：**
- 只有 material_id，没有证据摘录；
- 只做关键词重合；
- 用一个素材支持素材中不存在的数字；
- 把分析判断伪装成来源事实。

### Phase 2.5: Conflicts and Boundaries

**必须识别的冲突类型：**
- 数字冲突（同一事实在不同来源中数字不同）；
- 主体冲突（同一事件涉及不同主体）；
- 时间冲突（同一事件在不同来源中时间不同）；
- 同一事件的不同定性；
- 二手来源与当事方来源差异；
- 推测、指控、测试结果和已确认事实的区别。

**表达边界级别：**

| 级别 | 含义 | 示例 |
|---|---|---|
| can_assert | 可以确定地写 | "AISI测试了5款模型" |
| must_attribute | 必须带归因 | "据Thomas Wolf透露" |
| must_qualify | 必须带限定词 | "有观点认为知识蒸馏可能是原因" |
| analysis_only | 只能作为分析 | "安全框架在追赶" |
| do_not_write | 不得写入正文 | 未经核实的具体数字 |

**输出：** `05_conflicts_and_uncertainties.md` + `09_expression_boundaries.md`

### Phase 3: Thesis and Article Blueprint

**生成：**
- 中心论点；
- 文章读者收益（认知变化）；
- 开场方式；
- 章节顺序；
- 每章独有信息目标；
- 每章使用的 event_id 和 claim_id；
- 章节间禁止重复的信息；
- 结尾应得出的结论及其证据边界。

**输出：** `06_article_thesis.md` + `07_article_outline.md`

### Phase 4: Section Evidence Packs

**每章生成独立证据包：**
- 本章作用；
- 本章核心 Claim；
- 证据摘录；
- 数字与主体；
- 可用限定词；
- 禁止扩大的结论；
- 与其他章节的去重约束。

**输出：** `08_section_evidence_packs.md`

### Phase 4.5: Super Writer Input Brief

**将前述结果转换为写作 Brief。**

Brief 必须包含：
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

**输出：** `10_super_writer_input_brief.md`

**之后进入 Super Writer 原有 Phase 5（初稿）和 Phase 6（审稿）。**

## 产物清单

| 文件 | 阶段 | 用途 |
|---|---|---|
| 01_raw_material_inventory.md | Phase 0 | 原始素材清单、Hash、来源URL |
| 02_deduplicated_materials.md | Phase 1 | 去重后事件清单 |
| 03_topic_clusters.md | Phase 1.5 | 事件聚类结果 |
| 04_claim_evidence_map.md | Phase 2 | Claim-Evidence 绑定 |
| 05_conflicts_and_uncertainties.md | Phase 2.5 | 冲突与不确定性 |
| 06_article_thesis.md | Phase 3 | 中心论点与文章蓝图 |
| 07_article_outline.md | Phase 3 | 文章大纲 |
| 08_section_evidence_packs.md | Phase 4 | 章节证据包 |
| 09_expression_boundaries.md | Phase 2.5 | 表达边界 |
| 10_super_writer_input_brief.md | Phase 4.5 | 写作输入 Brief |

## 与 direct 模式的兼容性

- `direct` 模式不执行 Phase 0–4.5，直接进入 Phase 1（写作简报）；
- `direct` 模式的行为与 v0.3.1 完全一致；
- 不指定 `INPUT_MODE` 时默认 `auto`，少量素材自动走 `direct`；
- 用户可随时显式指定 `INPUT_MODE=direct` 强制跳过中间编辑层。

## Validator 边界

| Validator 类型 | 说明 |
|---|---|
| ARTICLE_LENGTH_VALIDATOR | 普通文章长度和重复检测 |
| FULL_MODE_VALIDATOR | Full Mode 完整性检查（需 --full-mode） |

确定性 Validator 只负责：文件存在性、格式、ID 完整性、引用是否存在、长度、重复、Hash、Schema 一致性。

确定性 Validator 不得自行宣布：语义事实正确、来源一定支持 Claim、人工语义审核通过。
