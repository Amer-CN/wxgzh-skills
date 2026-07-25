# CHANGELOG

## v0.3.2-rc1 — Material-Heavy Editorial Mode (2026-07-24)

### 新增

- **INPUT_MODE 路由**：新增 `auto` / `direct` / `material_heavy` 三种输入模式。`auto` 按素材量、来源数、冲突等条件自动判断；`direct` 保持 v0.3.1 行为；`material_heavy` 执行中间编辑层。
- **Material-Heavy Editorial Mode**：在写作阶段之前增加 Phase 0–4.5 中间编辑层流程，包含 Input Census、Three-Layer Deduplication、Topic Clustering、Claim–Evidence Binding、Conflicts and Boundaries、Thesis and Article Blueprint、Section Evidence Packs、Super Writer Input Brief。
- **references/material-heavy-editorial.md**：新增参考文档，详述中间编辑层流程。
- **Validator 边界明确**：区分 `ARTICLE_LENGTH_VALIDATOR` 和 `FULL_MODE_VALIDATOR`，未执行 `--full-mode` 时必须记录 `NOT_RUN`。
- direct 模式与 material-heavy 模式已在独立候选包的 package-level 回归资产中完成验证；这些外层回归目录不属于 Git 仓库中的 Skill 发布文件；Git 仓库保留现有 230 项基线测试与内部 Fixture。

### 修改

- **SKILL.md**：新增输入模式路由、Material-Heavy Editorial Mode 流程、产物设计、Validator 边界等章节。原有 Phase 1–7、编辑学习流程、输出模式、失败退出等均保持不变。
- **VERSION**：更新为 0.3.2-rc1。

### 不变

- 所有脚本文件 SHA256 与 v0.3.1-rc1-hotfix5 一致（未修改任何脚本）。
- `direct` 模式行为与 v0.3.1 完全一致。
- 原有 article_mode、length_mode、输出模式、语义角色等全部保留。
- 禁止在通用 Skill 逻辑中硬编码特定主题、实体或数字。

### 来源

- 基于真实文章试运行 V1（real_article_pilot_v1）验证的 B 组编辑流程。
- 真实文章试运行已通过独立验收：AI HOT 原始素材 → 中间编辑层 → Super Writer 协议写作 → 来源追溯 → Article Length Validator → 可发布中长篇文章。

## v0.3.0-rc1 — 语义化排版交接 (2026-07-19)

### 状态变更

- `version`: `0.2.0-rc2.1-hotfix` → `0.3.0-rc1`
- `test_count`: 89 → 117（新增 28 项语义交接测试）
- `handoff_contract_version`: `v2.0`（新增字段）
- `semantic_roles_count`: `41`（新增字段）
- 写作核心方法论（找核、攻核、研究协议、证据地图、Voice Profile、编辑学习、校准）保持不变

### 核心目标

让写作 Skill 输出不含样式但具备丰富语义结构的 `semantic-map.yaml`，使下游排版引擎（如 `gzh-design`）无需猜测内容形态，同时保持写作内容与视觉排版的解耦。

### Phase 0：分支与基线保护

- 确认 v0.2.0-rc2.1-hotfix 的 89 项测试全部通过作为基线
- 所有 v0.3 变更在独立分支进行，不静默覆盖稳定版本

### Phase 1：建立排版组件能力映射

- 新增 `references/formatter-capability-map.md`
- 统一 Super Writer 与 gzh-design 两个 Skill 之间的认知
- 列出 gzh-design 已注册的全部组件名及其适用语义场景

### Phase 2：建立统一语义词表

- 新增 `references/semantic-components.md`
- 定义 41 种语义角色（article_wrapper、hero_quote、comparison、timeline、key_statement、steps、faq、quote、facts、decision、checklist、callout 等）
- 每个角色附带：必需 payload 字段、候选 formatter 组件、降级规则
- 区分文章级角色和正文级角色

### Phase 3：结构设计阶段前置语义规划

- `references/structure-design.md`：新增"语义规划"小节
- `templates/outline.md`：新增 `content_shape`、`semantic_blocks`、`formatter_opportunities`、`required_payload`、`fallback_shape` 字段
- `SKILL.md` Phase 4：加载 `semantic-components.md` 和 `formatter-capability-map.md`，为每节规划语义形态
- 写作端根据内容选择语义形态，再由 formatter 选择具体组件

### Phase 4：初稿阶段生成可映射内容

- `references/drafting.md`：新增"语义内容生成"小节
- `SKILL.md` Phase 5：根据 outline 的 `semantic_blocks` 生成真实结构化内容
- comparison 必须写出双方和统一维度；steps 必须写出有顺序的动作；timeline 必须写出时间或阶段；facts 必须附证据 ID；decision 必须写出背景、选项、权衡和结论；faq 必须是真实问题与答案；checklist 必须是可执行检查项；quote 必须保留原话和来源
- 禁止在 article.md 内直接写组件 HTML、主题色、CSS 或视觉指令

### Phase 5：semantic-map.yaml 模板

- 新增 `templates/semantic-map.yaml`
- 结构：`article` 元数据 + `blocks` 列表 + `component_policy`
- 每个 block 包含：`block_id`、`role`、`source_anchor`（exact_text 或 section_heading）、`payload`、`formatter_candidates`、`fallback`
- `component_policy` 声明 preserve_exactly 清单和禁止 force 的组件

### Phase 6 + 7：handoff v2.0 契约 + Formatter 最终决定权

- `references/handoff.md` 升级至 v2.0
- 新增 `semantic_map_path` 字段指向 semantic-map.yaml
- 新增 `formatter` 配置块（候选主题、平台约束、preserve_exactly 清单）
- 明确 Formatter 最终决定权：写作端只建议组件，排版端根据平台和主题做最终选择
- 明确 humanizer 修改正文后必须更新 anchor 的链路顺序：writing → humanizer → 重新校验 anchor → formatter

### Phase 8：语义映射校验器

- 新增 `scripts/validate_semantic_map.py`
- 检查 `block_id` 唯一性
- 检查 `source_anchor` 在原文中的存在性（exact_text 精确匹配或 section_heading 标题匹配）
- 检查必需 payload 字段完整性（按角色定义）
- 检查禁止 HTML/CSS 渗入 article.md 和 semantic-map.yaml
- 检查 formatter_candidates 中的组件名在 gzh-design 注册表中存在
- 检查 force_all_components 标志（禁止强制使用全部组件）
- 支持 CLI 调用：`python validate_semantic_map.py <article_path> <semantic_map_path>`

### Phase 9：语义交接测试套件

- 新增 `tests/test_semantic_handoff.py`（28 项测试）
- 覆盖：基础结构校验、block_id 唯一性、anchor 定位、角色合法性、payload 必需字段、HTML/CSS 禁止、formatter 候选合法性、降级路径、preserve_exactly 不可改写、原 89 项测试仍通过、CLI 端到端、SKILL.md 引用语义文件、outline 字段、structure-design 语义规划、drafting 语义生成、handoff formatter 决定权
- 覆盖 3 篇 fixture 的集成验收（简单观点文、结构化教程、深度分析）

### Phase 10：集成验收

- 新增 `tests/fixtures/semantic/fixture-a-simple/`：简单观点文（5 个语义块，基础角色）
- 新增 `tests/fixtures/semantic/fixture-b-tutorial/`：结构化教程（10+ 语义块，含 steps、checklist、code）
- 新增 `tests/fixtures/semantic/fixture-c-analysis/`：深度分析（15+ 语义块，含 comparison、timeline、decision、quote）
- 三篇 fixture 全部通过 `validate_semantic_map.py` 校验

### 关键设计决策

1. **内容与结构分离**：article.md 保持纯净可读，语义信息放到独立的 semantic-map.yaml
2. **写作 Skill 不关心视觉样式**：只关心语义结构，不关心如何渲染
3. **排版 Skill 不关心写作逻辑**：只关心如何把语义块渲染成视觉组件
4. **Formatter 最终决定权**：写作端只建议组件，排版端做最终选择，避免双向耦合
5. **校验驱动**：通过 validate_semantic_map.py 保证 anchor 定位准确且载荷完整
6. **humanizer 链路保护**：修改正文后必须更新 anchor，不得使用已失效的旧 anchor

### 兼容性

- v0.2 的全部 89 项测试仍然通过（test_22_original_tests_still_pass 显式验证）
- 旧版无 semantic-map.yaml 的交接仍可被 formatter 以"无语义信息"模式处理（降级路径）
- 写作核心方法论未改动，仅在外围增加语义规划与交接层

### 打包信息

- 测试：117 passed（89 原始 + 28 新增语义交接）
- 新增文件：6 个（formatter-capability-map.md、semantic-components.md、semantic-map.yaml、validate_semantic_map.py、test_semantic_handoff.py、3 篇 fixture）
- 修改文件：5 个（SKILL.md、structure-design.md、drafting.md、handoff.md、outline.md）
- 写作核心冻结日期：2026-07-14（未改动）
- v0.3.0-rc1 发布日期：2026-07-19

### 后续迭代规则

1. 继续采用真实使用持续验证（dogfooding）模式
2. 与 gzh-design 联调中发现的问题优先修复
3. semantic-components.md 的角色新增需经两方协商
4. 不得在写作端硬编码 formatter 的具体组件名作为唯一选择
5. preserve_exactly 清单中的内容不得被任何下游 Skill 改写

## v0.2.0-rc2.1-hotfix — 正式投入个人使用 (2026-07-14)

### 状态变更

- `status`: `frozen-for-evaluation` → `ready_for_personal_use`
- `formal_phase4`: `skipped_for_personal_use`（个人使用，不进行公开评测）
- `evaluation_method`: `continuous_dogfooding`（真实使用持续验证）
- `iteration_strategy`: `fix_repeated_real_world_issues`（重复出现的问题才纳入规则）

### 验收结论

- ZIP 和 Manifest 完整性通过
- SHA-256 校验通过
- 89 个工程与行为测试全部通过
- 4 个关键场景冒烟测试通过（S01 正常 / S02 缺经历 / S03 证据冲突 / S04 核心崩塌）
- 写作核心已冻结
- 无阻塞问题

### 后续迭代规则

1. 直接安装并投入日常写作
2. 保留当前 ZIP 作为稳定基线和回滚版本
3. 使用中记录真实问题、输入、输出和人工修改
4. 严重问题可以立即修复
5. 普通问题重复出现 2~3 次后再纳入规则
6. 每累计 5~10 篇文章集中复盘和升级一次
7. 不因单篇文章的问题立即修改通用写作规则
8. 后续升级不得静默覆盖当前稳定版本

## v0.2-rc2.1-hotfix (2026-07-14)

### rc2.1 审计修复（3 项工程边界 + 1 项文档）

基于 v0.2-rc2.1 最终复审报告，修复 3 个工程边界问题和 1 个文档问题。不修改写作方法论、Prompt、评分维度或权重。

#### H1: support/conflict 无已有规则时失败

- `scripts/learn_edits.py`：`validate_reviewer_judgments()` 中 support/conflict 不再跳过空 existing_keys 检查
- existing_keys 为空时，support/conflict 直接失败并报错"requires existing rules"
- `generate_updated_rules()` 新增第二层防御检查：support/conflict 引用不存在的 key 时抛出 ValueError
- 新增 3 个测试：`test_h1_support_empty_existing_keys_fails`、`test_h1_conflict_empty_existing_keys_fails`、`test_h1_support_defensive_check_in_merge`

#### H2: observed_at/source_id 强制必填 + 日期格式校验

- `scripts/learn_edits.py`：new/support/conflict 关系现在强制要求 `observed_at` 和 `source_id`
- `observed_at` 必须符合 `YYYY-MM-DD` 格式，使用 `datetime.strptime` 校验
- one_off 关系不强制要求这两个字段（保持灵活）
- 新增 4 个测试：`test_h2_new_without_observed_at_rejected`、`test_h2_new_without_source_id_rejected`、`test_h2_support_without_observed_at_rejected`、`test_h2_invalid_date_format_rejected`

#### H3: Machine scores 防御检查

- `scripts/calibrate_scorer.py`：`load_machine_scores()` 新增 4 项防御检查：
  - 重复 article_id 检测
  - overall_score 范围校验（0-100）
  - 各维度分数范围校验（0-该维度 max）
  - 维度总和与 overall_score 一致性校验（±1 容差）
- 新增 5 个测试：`test_h3_duplicate_article_id_fails`、`test_h3_overall_score_above_100_fails`、`test_h3_overall_score_negative_fails`、`test_h3_dimension_out_of_range_fails`、`test_h3_dimension_sum_mismatch_fails`

#### H4: 交付报告修正

- 重新生成 `super-writer-v0.2-rc2.1-hotfix-delivery.md`，修正版本号为 rc2.1-hotfix
- 修正修改文件数量描述为"3 类核心修复"
- 更新测试数量为 89

### 打包信息

- ZIP：`super-writer-v0.2-rc2.1-hotfix.zip`
- 测试：89 passed（新增 12 个回归测试）

## v0.2-rc2.1 (2026-07-14)

### rc2 审计修复（5 项工程补丁）

基于 v0.2-rc2 文件级复审报告，修复全部 5 个剩余工程问题。不修改写作方法论、Prompt、评分维度或权重。

#### R1: Spearman ties 使用秩向量 Pearson

- `scripts/calibrate_scorer.py`：新增 `_pearson()` 函数
- `spearman_rank_correlation()` 改为对两个平均秩向量计算 Pearson 相关系数
- 处理零方差情况（返回 0.0）
- 新增 4 个测试：`test_spearman_asymmetric_ties_exact`、`test_spearman_zero_variance`、`test_spearman_both_zero_variance`、`test_pearson_basic`

#### R2: load_samples 缺失文章时失败

- `load_samples()` 不再打印 Warning 后跳过，改为收集全部缺失 ID 后抛出 ValueError
- 新增重复 article_id 检查
- 新增空文件检查（<50 字符）
- 新增 4 个测试：`test_load_samples_missing_article_fails`、`test_load_samples_duplicate_id_fails`、`test_load_samples_empty_article_fails`、`test_load_samples_short_article_fails`

#### R3: Reviewer judgment 严格 Schema 校验

- `validate_reviewer_judgments()` 新增 `existing_keys` 参数
- `new`：必须提供非空 key、instruction、evidence
- `support/conflict`：必须提供非空 key，且 key 必须存在于 existing_keys
- `one_off`：允许无 key，但必须有 evidence
- confidence 必须是 1-5 范围内的数字
- change_index 不得重复
- 无效输入直接失败，不静默跳过
- 新增 6 个测试

#### R4: 稳定 key 生成

- 移除 `hash(instruction) % 10000`（Python hash 带随机种子，跨进程不稳定）
- 新增 `_generate_stable_key()` 使用 `sha256(normalized_instruction)[:12]`
- 同一 instruction 在不同进程中始终生成相同 key
- 新增 2 个测试：`test_r4_stable_key_deterministic`、`test_r4_stable_key_different_instructions`

#### R5: 时间字段和 evidence 字段分离

- Reviewer judgment 新增 `observed_at` 和 `source_id` 字段
- `last_supported_at` / `last_conflicted_at` 写入 `observed_at`（日期）
- evidence 保存到独立 `_evidence` 字段
- `source_id` 追加到 `sources` 列表
- 更新 fixture judgments 文件以包含新字段
- 新增 2 个测试：`test_r5_time_field_writes_date_not_evidence`、`test_r5_conflict_time_field_writes_date`

### 打包信息

- ZIP：`super-writer-v0.2-rc2.1.zip`
- 测试：77 passed

## v0.2-rc2 (2026-07-14)

### 审计修复（4 个 Blocking + 9 个 Important）

基于 v0.2-rc1 文件级审计报告，修复全部 4 个 Blocking 问题和 9 个 Important 问题。

#### B1: 校准脚本 machine scores 输入链路修复

- `scripts/calibrate_scorer.py`：完全重写
  - 新增 `--machine-scores` 参数，人工标签和机器评分使用独立输入文件
  - 新增 `--mode architecture|calibrated` 显式模式选择
  - calibrated 模式缺少 `--machine-scores` 时失败退出，不再静默补 0
  - 新增 `check_id_overlap()`，校准集和盲测集 article_id 重叠时失败
  - `load_samples()` 不再加载 machine_score，由 `load_machine_scores()` 独立加载
  - `calibration_status` 由显式 mode 决定，不再通过"是否全为0"猜测

#### B2: 编辑学习职责重划分

- `scripts/learn_edits.py`：完全重写
  - Python 只负责生成 diff、验证 Schema、合并 key、更新计数
  - 语义分类和规则抽象交给 Reviewer/LLM 输出 JSON judgments
  - 新增 `validate_reviewer_judgments()` 验证 relation 字段
  - `generate_updated_rules()` 需要 `relation` 字段才能调整 confidence
  - 未提供 relation 时，不调整置信度
  - 新增 `ignored` status（confidence 降为 0 时标记，不删除）
- `references/edit-learning.md`：更新流程文档，新增职责划分和 Reviewer 判断格式

#### B3: 真实 fixtures 和行为测试

- `tests/fixtures/samples/`：新增 3 篇真实最小文章
- `tests/fixtures/machine-scores.json`：新增独立机器评分文件
- `tests/fixtures/blind/blind-001.md` + `blind-labels.json` + `blind-machine-scores.json`：新增盲测 fixtures
- `tests/fixtures/edit-pairs/pair-01/`：draft/final/judgments（new 规则）
- `tests/fixtures/edit-pairs/pair-02/`：draft/final/judgments（conflict 规则）
- `tests/test_calibration.py`：重写为 23 个行为测试（含 Spearman ties、ID 重叠、CLI 端到端）
- `tests/test_structure.py`：重写，修复空测试，新增 12 个编辑学习行为测试
- 测试从 42 个增加到 59 个：结构测试 26 + 脚本单元测试 12 + 行为测试 21

#### B4: 缺失设计文档纳入包内

- 新增 `capability-matrix.md`：能力对比矩阵
- 新增 `design-decisions.md`：16 项设计决策
- 新增 `conflict-resolution.md`：14 项冲突处置
- `phase4-materials-structure.md` 已在包内

#### I1: MANIFEST.sha256 跨平台修复

- `scripts/package_zip.py`：Manifest 路径统一使用 POSIX 正斜杠

#### I2: 冻结日期修正

- `VERSION`：freeze_date 从 2025-07-14 改为 2026-07-14
- `phase4-evaluation-plan.md`：日期从 2025 改为 2026

#### I3: SKILL.md 错字修正

- 两处"崩場"修正为"崩塌"

#### I4: README 测试数量修正

- 从"38 个测试"改为"59 个测试"，区分结构测试、脚本单元测试、行为测试

#### I5: Phase 4 输出数量修正

- 稳定性检查从"88 个额外输出"修正为"64 个额外输出"
- 完整总数从隐含的 184 修正为 160（96 + 64）

#### I6: Spearman 并列分数处理

- `_rank()` 替换为 `_rank_with_ties()`，使用平均秩处理 ties
- 新增 `test_spearman_with_ties` 和 `test_rank_with_ties` 测试

#### I7: Voice Profile 移除自动删除

- `references/voice-profile.md`：confidence < 2 从"淘汰，自动删除"改为"标记 stale/ignored，不自动删除"

#### I8: 训练数据表述安全化

- `references/research-evidence.md`：从"使用训练数据中的已知信息，标注为推测"改为"先验知识作为线索，时间敏感信息必须核验，无法核验标记 unverified_background"

#### I9: 发布门槛 Hard Fail 说明修正

- `phase4-evaluation-plan.md`：hard_fail_rate 从"<= 3%"改为"0 次即不通过"，明确 24 个任务中任何 1 次都不通过

### 打包信息

- ZIP：`super-writer-v0.2-rc2.zip`
- 测试：59 passed

## v0.2-rc1 (2025-07-14)

### 冻结前复核修订（3 项）

基于用户上线第四阶段前的三个复核点，对 v0.2 进行最终修订后冻结为 rc1：

#### 复核点1：类比裂口四类判断

- `references/structure-design.md`：类比裂口从"一律用叙事推过去"改为四类判断框架
  - 裂口揭示结论边界 → 写出来作为洞察
  - 裂口只是局部不完全映射 → 说明边界后继续使用
  - 裂口破坏核心因果 → **必须弃用类比**
  - 裂口会误导读者 → **不得靠叙事掩盖**
  - 增加判断步骤和反例

#### 复核点2：编辑规则置信度双向调整

- `references/edit-learning.md`：confidence 从只升不降改为双向调整
  - 新样本支持：+1（cap 5）
  - 新样本冲突：-1（floor 0）
  - 用户撤销：status = revoked
  - 长期未出现：标记 stale，不自动删除
  - 只适用某类文章：缩小 scope
  - 当前指令与历史规则冲突：当前指令优先
- `profiles/edit-rules.example.yaml`：规则数据结构升级
  - 新增字段：support_count, conflict_count, status, last_supported_at, last_conflicted_at
  - status 取值：active | revoked | stale
- `scripts/learn_edits.py`：generate_updated_rules 支持双向 confidence
  - 新增 conflicts_with_existing 参数
  - conflict_count > support_count 时自动标记 stale
  - check_playbook_trigger 统计包含 conflict_count

#### 复核点3：研究停止条件三层结构

- `references/research-evidence.md`：停止条件从"六项全部满足"改为三层
  - 必须满足：关键事实可追溯、主要论断有证据、未解决项有标记
  - 尽量满足：找到反方、主要章节有价值载体、连续研究无增量、来源时效
  - 无法满足时退出：research_limited / needs_author_input / evidence_conflict / core_broken
  - 个人经历型文章可用作者基于真实经历进行自我质疑代替外部反方
- `references/workflow.md`：退出状态表增加 research_limited
- `SKILL.md`：退出状态表增加 research_limited

### 测试

- 42 个测试全部通过（新增 4 个双向置信度行为测试）
- 新增测试覆盖：支持时 confidence 上升、冲突时下降、conflict > support 时自动 stale、playbook trigger 包含 conflict_count

### 冻结声明

- 当前版本标记为 **v0.2-rc1**
- 评测期间不再修改规则、不调整评分权重、不修测试样本
- 所有发现登记为 issue，完成第一轮后统一形成 rc2

### 打包前术语修正（1 项）

- `references/research-evidence.md`：将"人格自我质疑"修正为"作者基于真实经历进行自我质疑"，避免与已拒绝引入的预设 Persona 概念混淆（术语校正，非机制修改）

### 打包信息

- ZIP：`super-writer-v0.2-rc1.zip`
- SHA-256：`4d5208645871f9a1ee786f73b4bc4d1ffe60be6b6dcd10d4265a9b409698dd72`
- 文件数：34（含 VERSION + MANIFEST.sha256）
- 排除：`__pycache__/`、`*.pyc`、`.git/`、临时脚本（`prepackage_check.py`、`package_zip.py`）
- 测试结果：42 passed in 0.32s

## v0.2.0 (2025-07-14)

### 评审修订

基于用户摘要级评审意见，对 v0.2 方案进行了 13 项修改：

1. 素材充分性检查从 P2 提升到 P1
2. 证据地图增强从 P3 提升到 P1
3. 评分器校准拆为 P1（架构）和 P2（用真实样本完成第一次校准）
4. Burstiness 从 P2 降为 P3，只允许非阻塞诊断
5. 选题评分采用两层结构（HKR + UEPT）
6. Voice Profile 采用核心 8 维 + 可选 4 维
7. Voice Profile 每维保存 confidence/source_count/sources/scope
8. 编辑学习采用"自动分析和提议、人工确认写入"
9. 校准集 24 篇 + 盲测集 12 篇
10. 增加研究停止条件
11. 增加失败退出状态
12. Burstiness 不设通用中文硬阈值
13. 保持现有边界

### P1 变更（11 项）

- `references/research-evidence.md`：增加素材充分性检查、排斥分析、痛点深度检查、研究停止条件
- `references/core-finding.md`：增加两层选题评分（HKR + UEPT）、四铲深化
- `templates/evidence-map.md`：重构为完整字段（来源日期、原始来源、支持/反对、适用边界、核验状态、使用状态）+ Reader Tension Statement
- `references/voice-profile.md`：重构为分层结构（核心 8 维 + 可选 4 维）+ confidence 使用规则 + 冲突解决优先级
- `profiles/voice-profile.example.yaml`：重构为分层 YAML 结构，每维带 confidence/source_count/sources/scope
- `references/editorial-review.md`：增加补充检查项（claim→mechanism、A vs B 对比、示例去重、So what 测试、视角审计）
- `references/edit-learning.md`：增加配置（自动分析+提议、禁止静默写入）、confidence 使用规则、key 复用机制、验证测试、触发提示
- `profiles/edit-rules.example.yaml`：增加 key/occurrences/confirmed/last_seen 字段
- `templates/editor-report.md`：增加 JSON 输出模板、补充检查项清单
- `references/workflow.md`：增加素材充分性门禁、失败退出机制
- `SKILL.md`：增加 Phase 1.5 素材充分性检查、验收标准、失败退出路径
- `scripts/learn_edits.py`：增加 pattern 分类、key 复用、候选规则生成
- `scripts/calibrate_scorer.py`：新建校准脚本（MAE/Spearman/classification 指标、盲测隔离）
- `tests/test_calibration.py`：新建校准测试
- `tests/fixtures/`：新建样本集和盲测集目录结构

### P2 变更（4 项）

- `references/structure-design.md`：增加类比裂口处理段落
- `references/handoff.md`：增强下游 Skill 列表（humanizer/formatter/publisher + 触发条件）
- `scripts/learn_edits.py`：增加 check_playbook_trigger、generate_updated_rules、置信度自动更新
- `scripts/calibrate_scorer.py`：支持真实样本校准执行

### P3 变更（1 项）

- `scripts/score_article.py`：增加 Burstiness 非阻塞诊断（6 项软诊断检查、风险等级输出、交接给 humanizer）

### 测试

- 38 个测试全部通过
- 覆盖：结构完整性、边界检查、素材充分性门禁、两层选题评分、研究停止条件、排斥分析、痛点深度、四铲深化、证据地图增强、Voice Profile 分层、内容审稿增强、编辑学习配置、编辑规则增强、评分器 JSON、失败退出机制、验收标准、校准架构、校准脚本运行、编辑学习增强、类比裂口处理、下游交接增强、Burstiness 非阻塞、Burstiness 输出格式、无预设 Persona、无 SEO、无去 AI 味硬阈值

### 设计文档更新

- `capability-matrix.md`：5 个设计问题标记为已解决，优先级标注更新
- `design-decisions.md`：从 13 项变更扩展到 16 项，优先级重新分配，增加评审决策记录
- `conflict-resolution.md`：从 10 项冲突扩展到 14 项，采用结构化格式，增加重开机制

## v0.1.0 (初始版本)

- 7 Phase 写作流程（简报 → 研究 → 找核 → 结构 → 初稿 → 审稿 → 修订）
- P0-P3 问题分级 + 100 分内容量表
- 证据地图（F/O/I/E 分类 + 来源等级 A-D）
- 找核七问 + 攻核六刀
- 9 种文章原型 + 6 条叙事弧线
- 承重类比四条件
- 编辑锚点机制
- Voice Profile 基础结构
- 编辑学习基础流程
- 下游交接契约
- 预检脚本（score_article.py）
- 编辑学习脚本（learn_edits.py）
- 结构测试（test_structure.py）
