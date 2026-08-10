# Super Writer

一个面向中文长文/公众号文章的 AI 写作 Skill。它只负责：素材充分性检查、选题评分、研究、找核、攻核、结构、初稿和内容审稿。

明确不负责：去 AI 味、美化排版、配图和发布。最终稿通过 `handoff` 交给下游 Skill。

> **v0.3.6-rc1** — `release_candidate` | 242 tests passed | MIT License

## 目录结构

```
super-writer/
├── SKILL.md                  # Skill 主入口（方法论核心）
├── VERSION                   # 版本与状态
├── CHANGELOG.md              # 完整变更历史
├── README.md                 # 本文件
├── LICENSE                   # MIT
├── ATTRIBUTION.md            # 引用与归属
├── MANIFEST.sha256           # 文件完整性校验
├── references/               # 方法论文档（按需加载）
│   ├── workflow.md           #   工作流与运行契约
│   ├── research-evidence.md  #   研究协议与证据地图
│   ├── core-finding.md       #   找核与压力测试
│   ├── structure-design.md   #   结构设计
│   ├── drafting.md           #   初稿写作
│   ├── editorial-review.md   #   内容审稿
│   ├── edit-learning.md      #   编辑学习
│   ├── voice-profile.md      #   文风画像
│   ├── handoff.md            #   下游交接
│   ├── semantic-components.md    #   统一语义词表（v0.3 新增）
│   └── formatter-capability-map.md  # 排版组件能力映射（v0.3 新增）
├── templates/                # 输出模板
│   ├── writing-brief.md
│   ├── evidence-map.md
│   ├── core-card.md
│   ├── outline.md
│   ├── editor-report.md
│   └── semantic-map.yaml     #   语义映射模板（v0.3 新增）
├── profiles/                 # Profile 示例
│   ├── audience-profile.example.yaml
│   ├── voice-profile.example.yaml
│   ├── belief-profile.example.yaml
│   └── edit-rules.example.yaml
├── scripts/                  # 工具脚本
│   ├── score_article.py      #   预检评分
│   ├── calibrate_scorer.py   #   评分器校准
│   ├── learn_edits.py        #   编辑学习
│   ├── validate_skill.py     #   结构验证
│   ├── validate_semantic_map.py  # 语义映射校验
│   ├── validate_article_length.py  # 篇幅门禁校验（v0.3.1 新增）
│   ├── check_manifest.py     #   文件完整性校验
│   ├── package_zip.py        #   打包脚本
│   └── gen_source_bundle.py  #   源码合并文档生成
├── tests/                    # 测试套件（242 个）
│   ├── test_structure.py
│   ├── test_calibration.py
│   ├── test_semantic_handoff.py
│   ├── test_length_material.py  # 篇幅策略与素材路由测试（v0.3.1 新增）
│   └── fixtures/             #   测试样本
├── capability-matrix.md      # 能力对比矩阵
├── design-decisions.md       # 设计决策记录
└── conflict-resolution.md    # 冲突处置记录
```

## 设计原则

1. 事实真实性高于文风和戏剧性。
2. 先评估素材充分性，再决定能写到什么程度。
3. 先找到值得写的核心，再扩写。
4. 先构造证据地图，再写正文。
5. 作者经历只能来自用户输入或经历库。
6. Writer 与 Reviewer 分离；严重问题会阻塞交付。
7. 文风画像短小、可执行、可复用、分层加载。
8. 大规则按需加载，避免一个巨型 SKILL.md 占满上下文。
9. 允许失败退出，不强行产出有问题的文章。
10. 编辑学习自动分析但人工确认写入，禁止静默修改持久规则。

## v0.3 新增能力：语义化排版交接

### 核心目标

让写作 Skill 输出不含样式但具备丰富语义结构的 `semantic-map.yaml`，使下游排版引擎（如 `gzh-design`）无需猜测内容形态，同时保持写作内容与视觉排版的解耦。

### 关键能力

- **统一语义词表**：定义 41 种文章级和正文级语义角色（comparison、timeline、key_statement、steps、faq 等），每个角色附带必需字段、候选组件及降级规则。
- **语义规划前置**：在结构设计阶段为每节额外规划 `content_shape`、`semantic_blocks`、`formatter_opportunities`、`required_payload`、`fallback_shape`。
- **语义内容生成**：初稿阶段根据 outline 的 semantic_blocks 生成真实结构化内容，禁止在 article.md 内写 HTML/CSS/视觉指令。
- **semantic-map.yaml 交接**：声明每个语义块的 role、payload、source_anchor、formatter_candidates 和 fallback，由校验器保证 anchor 定位准确且载荷完整。
- **handoff v2.0 契约**：新增 `semantic_map_path` 和 `formatter` 配置块；强制要求 humanizer 修改正文后必须更新 anchor。
- **Formatter 最终决定权**：写作端只建议组件，排版端根据平台和主题做最终选择。
- **校验驱动**：`scripts/validate_semantic_map.py` 检查 block_id 唯一性、source_anchor 存在性、必需字段完整性、HTML/CSS 渗入禁止。

### 设计原则

- 内容与结构分离：`article.md` 保持纯净，结构化载荷存放在 `semantic-map.yaml`
- 写作 Skill 不关心视觉样式，只关心语义结构
- 排版 Skill 不关心写作逻辑，只关心如何把语义块渲染成视觉组件

## v0.2 新增能力

### P1（核心能力）

- **素材充分性检查**：分维度评估已有素材，决定输出上限和后续动作。
- **两层选题评分**：HKR 判断阅读价值 + UEPT 判断可写性。
- **研究协议增强**：排斥分析 + 痛点深度检查 + 研究停止条件。
- **证据地图增强**：完整字段（来源日期、原始来源、支持/反对、适用边界、核验状态等）+ Reader Tension Statement。
- **四铲深化**：反转 / 追问前提 / 追问情绪 / 翻转定义。
- **Voice Profile 分层重构**：核心 8 维 + 可选 4 维，每维带 confidence/source_count/sources/scope。
- **内容审稿增强**：claim→mechanism 检查、A vs B 结构化对比、示例去重、"So what" 测试、视角审计。
- **编辑学习基础架构**：自动分析 + 自动提议 + 人工确认写入 + key 复用 + confidence 分级。
- **评分器 JSON Schema**：结构化 JSON 输出支持校准。
- **失败退出机制**：core_broken / evidence_conflict / unsuitable_topic 等退出状态。
- **评分器校准架构**：样本集格式、盲测隔离、MAE/Spearman/classification 指标。

### P2（增强能力）

- **承重类比裂口处理**：类比"裂开"的地方是文章最值钱的段落。
- **下游交接增强**：humanizer / formatter / publisher 三种下游 Skill 及触发条件。
- **编辑学习 key 复用与置信度更新**：自动合并重复 key、occurrences 累加、confidence 自动提升。
- **评分器校准执行框架**：支持真实样本校准（需 24 篇校准集 + 12 篇盲测集）。

### P3（补充完善）

- **Burstiness 诊断**：非阻塞节奏诊断，不设通用中文硬阈值，交接给 humanizer。

## 当前状态

**v0.3.0-rc1** — `ready_for_personal_use`

- 242 个工程与行为测试：全部通过（含 50 项篇幅策略与素材路由测试）
- 4 场景冒烟测试：全部通过
- 3 篇语义 fixture 集成验收通过（简单观点文 / 结构化教程 / 深度分析）
- 正式 Phase 4 评测：跳过（个人使用）
- 迭代方式：真实使用持续验证（continuous dogfooding）

## 安装

### 从 GitHub 安装

```bash
git clone https://github.com/AIXM/super-writer.git ~/.claude/skills/super-writer
```

### 验证安装

```bash
cd ~/.claude/skills/super-writer
python -m pytest tests/ -v
```

应看到 `242 passed`。

## 使用方法

### 基本用法

在 Agent 对话中直接说：

```text
我想写一篇关于 XX 的公众号文章，素材在 materials 目录里。
帮我把这些散乱想法整理成一篇长文。
围绕"XX"找一个真正值得写的角度。
审一下 article.md，只检查内容和逻辑。
根据我改前和改后的文章，学习我的编辑偏好。
```

Skill 会自动按以下 7 个 Phase 执行（根据输入状态跳过不必要步骤）：

| Phase | 名称 | 做什么 |
|-------|------|--------|
| 1 | 写作简报 | 确认主题、读者、文章类型、约束 |
| 1.5 | 素材充分性检查 | 评估 6 个维度，决定输出级别 |
| 2 | 研究 | 证据地图、来源等级标注、研究停止条件 |
| 3 | 找核 | 核心卡 + 攻核六刀压力测试 |
| 4 | 结构设计 | 大纲、叙事弧、章节承重检查 |
| 5 | 初稿 | 按已确认核心扩写 |
| 6 | 审稿 | P0-P3 分级问题检查 |
| 7 | 修订 | 修复问题，生成交接信息 |

### 素材准备

每次写作时，建议准备以下素材（不必全部具备）：

- **主题与核心想法**：你想写什么，你想说什么
- **个人经历**：你亲历的事情（只有你能提供）
- **公开资料**：文章、报告、数据（附来源链接）
- **已有草稿**：如果已经写了初稿
- **约束条件**：字数、读者、平台、风格偏好

### 素材充分性门禁

Skill 会检查 6 个维度：`topic` / `audience` / `core_opinion` / `evidence` / `personal_experience` / `voice_context`。

- 全部 sufficient → 正常产出完整文章
- 部分缺失 → 标注编辑锚点，降级输出
- 关键缺失 → 返回 `needs_author_input` 或 `research_limited`

### 失败退出

以下情况 Skill 会停止并说明原因，而不是强行产出有问题的文章：

| 退出状态 | 含义 |
|----------|------|
| `ready_to_write` | 可以进入写作 |
| `needs_research` | 需要更多研究 |
| `needs_author_input` | 需要作者补充经历或确认 |
| `research_limited` | 研究受限，降级为大纲 |
| `core_broken` | 核心观点在压力测试中崩塌 |
| `evidence_conflict` | 证据互相矛盾，无法调和 |
| `unsuitable_topic` | 选题没有信息增量 |
| `review_blocked` | 审稿发现不可修复的 P0 |

### 产物

完整流程可产出：

- `writing-brief.md`
- `material-readiness.yaml`
- `evidence-map.md`
- `core-card.md`
- `outline.md`
- `article.md`
- `semantic-map.yaml`（v0.3 新增，语义化排版交接）
- `editor-report.md`（Markdown + JSON）
- `generation-profile.yaml`
- `handoff.yaml`（v2.0 契约，含 `semantic_map_path` 与 `formatter` 配置块）

### 下游交接

Super Writer 完成后输出 `handoff.yaml`（v2.0 契约），可交给下游 Skill：

- **humanizer**：去 AI 味、节奏调整（推荐）。若修改了正文，必须同步更新 `semantic-map.yaml` 中失效的 exact_text anchor。
- **formatter**：公众号排版、格式转换（推荐）。读取 `semantic-map.yaml`，根据平台和主题选择具体组件，拥有最终决定权。
- **publisher**：直接发布（可选）

v0.3 起，`handoff.yaml` 新增 `semantic_map_path` 字段指向同目录下的 `semantic-map.yaml`，以及 `formatter` 配置块（候选主题、平台约束、preserve_exactly 清单）。写作端只建议组件，排版端做最终选择。

## 测试

```bash
cd super-writer
python -m pytest tests/ -v
```

229 个测试分为四类：

- **结构测试**（26 个）：检查文件中存在必要字段和配置
- **脚本单元测试**（16 个）：测试 MAE、Spearman（含 ties）、分类准确率等指标计算
- **行为测试**（47 个）：端到端 CLI 测试、真实 fixture 加载、编辑学习冲突流程、校准器机器分输入、严格 Schema 校验、输入防御检查等
- **语义交接测试**（91 个）：覆盖 anchor 定位、角色校验、payload 必需字段、formatter 候选、降级路径、HTML/CSS 禁止、humanizer 失效链路、内容来源校验、anchor 唯一性、URL 来源校验、fixture 集成验收等
- **篇幅策略与素材路由测试**（49 个）：覆盖长度档位、文章模式、needs_mode_selection、事件级去重、章节预算、长度门禁、三层覆盖率、full 模式 11 产物深度校验、K3 177 条素材路由、material_ingestion CLI、code 字符统计、双向事件校验、重复状态强制、跨产物一致性校验等

## 设计文档

- `capability-matrix.md`：跨 10 个项目、20 个维度的能力对比矩阵
- `design-decisions.md`：16 项变更的详细设计方案（含评审修订）
- `conflict-resolution.md`：14 项规则冲突的处置决策（结构化格式，支持重开）

## 迭代规则

本版本采用真实使用持续验证（dogfooding）模式：

1. 直接投入日常写作，记录真实问题
2. 严重问题立即修复
3. 普通问题重复出现 2~3 次后再纳入规则
4. 每累计 5~10 篇文章集中复盘和升级一次
5. 不因单篇文章的问题立即修改通用写作规则
6. 后续升级不得静默覆盖当前稳定版本

## License

[MIT](LICENSE)
