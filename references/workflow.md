# 工作流与运行契约

## 最小充分原则

不要机械执行所有阶段。根据输入状态选择最少但足够的步骤：

- 只有主题：先简报、素材充分性检查、研究、找核。
- 已有完整材料：快速简报后直接做证据地图和找核。
- 已有大纲：检查核心与证据后进入结构修订。
- 已有文章：先诊断，禁止无理由推倒重写。

## 人机边界

### AI 可以做

- 梳理材料、寻找缺口；
- 检索和比较证据；
- 提供多个观点候选；
- 压力测试观点；
- 设计结构和篇幅权重；
- 按已确认观点扩写；
- 做内容审稿和修订。

### 只能由作者提供或确认

- 第一手经历；
- 私人感受的具体细节；
- 最终价值判断；
- 对人物动机的断言；
- 无公开证据的内部信息；
- 文章愿意承担的立场与风险。

## 素材充分性门禁

在 Phase 1（写作简报）之后、Phase 2（研究）之前，执行素材充分性检查。详见 `references/research-evidence.md` 的"素材充分性检查"段落。

门禁输出决定后续动作：是否需要研究、是否可以进入找核、是否必须向用户提问、是否需要编辑锚点、是否只能输出大纲。

## 失败退出机制

Skill 不应永远强行产出文章。以下情况允许停止并输出退出状态：

| 退出状态 | 含义 | 触发条件 |
|----------|------|----------|
| `ready_to_write` | 可以进入写作 | 所有门禁通过 |
| `needs_research` | 需要更多研究 | 证据不足，E < 2 |
| `needs_author_input` | 需要作者补充 | 第一手经历缺失，P < 2 |
| `research_limited` | 研究受限，降级输出 | 已尽力研究但证据仍不足，降级为大纲输出 |
| `core_broken` | 核心观点崩塌 | 攻核六刀后结论为 breaks，且无法变形修复 |
| `evidence_conflict` | 证据相互冲突 | 支持和反对证据无法调和，无法确定核心立场 |
| `unsuitable_topic` | 选题没有信息增量 | HKR 三项均低于 3 分 |
| `review_blocked` | 审稿发现不可修复的 P0 | 三轮修订后 P0 仍不为零 |
| `scope_reduction` | 材料门未过且可收窄 | 材料门分档未满足且选题范围可收窄(降档 long→medium 等或收窄范围),收窄结果与理由记入 handoff.scope;能收窄则收窄并继续,不能收窄才以 `needs_research` 等既有状态退出 |

### 退出输出格式

```yaml
exit_status: core_broken
reason: "核心观点'AI工具提升效率'在攻核时被反例击穿：多数用户使用AI工具后总产出并未增加，效率提升仅限于特定任务类型"
next_action: "建议回到研究阶段寻找新角度，或放弃此选题"
```

### 不可退出的情况

以下情况不允许退出，必须继续工作或请求用户输入：

- 只是"觉得难写"但核心未崩塌；
- 研究不充分但素材充分性检查显示可以研究；
- 审稿发现 P1/P2 问题（可以修订）。

## 状态对象

每次完整写作维护以下状态：

```yaml
mode: full
phase: 1
article_type: null
article_mode: null             # v0.3.1: short/medium/long/deep/daily_digest/weekly_roundup/material_synthesis
length_mode: null              # v0.3.1: 与 article_mode 对应的篇幅预设
target_visible_chars: null    # v0.3.1: 目标可见字符数
acceptable_min: null          # v0.3.1: 最小可见字符数
acceptable_max: null          # v0.3.1: 最大可见字符数
material_ledger_path: null    # v0.3.1: 素材台账路径
ingestion_report_path: null   # v0.3.1: 摄入报告路径
reader: null
core_status: pending
material_readiness: null      # 素材充分性检查结果
exit_status: null             # 失败退出状态
facts_verified: false
p0_count: 0
revision_round: 0
outputs: []
```

跨会话时保存为 `generation-profile.yaml`。不要依赖聊天记忆猜测上一次状态。
