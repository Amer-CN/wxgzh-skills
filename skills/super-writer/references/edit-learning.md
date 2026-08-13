# 编辑学习协议

## 配置

```yaml
edit_learning:
  analyze_automatically: true       # Python 自动生成结构化 diff
  propose_rules_automatically: false # 不自动提议规则（需 Reviewer 语义判断）
  persist_automatically: false      # 禁止静默写入持久规则
  merge_duplicate_keys: true        # 合并重复 key
  require_confirmation: true        # 必须人工确认才能写入
```

## 职责划分

| 角色 | 职责 |
|------|------|
| Python 脚本 | 生成句子/段落级 diff、长度变化、位置变化；验证 Schema；合并 key；更新计数；生成预览 |
| Reviewer/LLM | 语义分类、规则抽象、support/conflict/new/one_off 判断 |
| 用户 | 确认写入 |

Python 脚本**不做**语义分类和规则抽象。语义判断必须由 Reviewer 输出。

## 流程

```
Python 生成 diff → Reviewer 输出 judgments (relation/key/instruction) → Python 验证 Schema 并合并 key → 更新计数和 confidence → 用户确认 → 写入
```

**无 Reviewer 判断时，不调整置信度。**

## 输入

- AI 初稿；
- 用户人工定稿；
- 可选：用户对修改原因的说明。

## Reviewer 判断格式

Reviewer 对每个 diff 输出 JSON 判断：

```json
{
  "change_index": 0,
  "relation": "new|support|conflict|one_off",
  "key": "reduce_questions",
  "instruction": "减少连续反问句",
  "scope": "global",
  "evidence": "用户将两个反问句改为具体陈述",
  "confidence": 1
}
```

### relation 取值

| relation | 含义 | 对规则的影响 |
|----------|------|-------------|
| `new` | 新偏好 | 创建新规则，support_count = 1 |
| `support` | 支持已有规则 | support_count +1，confidence +1（上限 5）|
| `conflict` | 与已有规则冲突 | conflict_count +1，confidence -1（下限 0）|
| `one_off` | 一次性修改 | 记录但不创建或更新规则 |

**未提供 relation 时，不调整置信度。** Python 脚本不会自动推测 relation。

## 三层记忆

- `examples/`：完整范文和改前改后对。
- `profiles/voice-profile.*`：稳定表达特征。
- `profiles/edit-rules.*`：明确、可执行的编辑偏好。

## 写入条件

满足**任一**条件才可写入持久规则：

- 用户明确说"以后都这样"；
- 同一倾向在至少两组修改中出现；
- 用户确认候选规则；
- 已有规则再次被修改样本支持。

## confidence 双向调整机制

置信度不是只升不降的。每条规则的 confidence 根据**新样本**双向调整：

| 事件 | confidence 变化 | 说明 |
|------|-----------------|------|
| 新样本支持同一倾向 | +1 | support_count +1，confidence 上限 5 |
| 新样本与规则冲突 | -1 | conflict_count +1，记录冲突详情 |
| 用户撤销规则 | 停用 | status 改为 `revoked`，不删除 |
| 长期未出现（>10 篇文章） | 不自动删除 | 标记 `stale`，提示用户复查 |
| 只适用于某类文章 | 缩小 scope | scope 从 `global` 改为具体文章类型 |
| 当前指令与历史规则冲突 | 当前指令优先 | 历史规则不阻塞用户当前要求 |

## 规则数据结构

每条规则保留以下完整字段：

```yaml
- id: ER001
  key: reduce_questions          # 复用 key，同种偏好累加
  instruction: "减少反问句和连续提问"
  scope: global                  # global | article_type_specific
  confidence: 3                  # 0-5，双向调整
  support_count: 3              # 被新样本支持的次数
  conflict_count: 0             # 被新样本冲突的次数
  status: active                 # active | revoked | stale
  sources: ["draft-001", "draft-007", "draft-012"]
  exceptions: []
  last_supported_at: "2025-07-01"
  last_conflicted_at: ""
  confirmed: true
  confirmed_at: "2025-06-15"
```

### status 取值

| status | 含义 | 写作时行为 |
|--------|------|------------|
| `active` | 活跃，正常使用 | 按 confidence 级别执行 |
| `revoked` | 用户撤销 | 不执行，保留记录以备复查 |
| `stale` | 长期未出现或冲突过多 | 不执行，提示用户复查 |
| `ignored` | confidence 降为 0 | 不执行，保留记录 |

### confidence 使用规则

- **≥ 5**：硬约束，写作时必须执行。
- **3-5**：软参考，倾向遵循但不强制。
- **< 3**：忽略，可能已过时。
- **≤ 0**（conflict_count > support_count 或 confidence 降为 0）：自动标记 `stale` 或 `ignored`，提示用户复查。不自动删除。

## key 复用机制

同种偏好使用相同 key，support_count 累加，confidence 自动调整。

避免出现以下重复规则（应合并为同一条）：

```
ER-001 少用反问
ER-018 减少疑问句
ER-031 不喜欢连续提问
```

正确做法：合并为一条规则，key = `reduce_questions`，support_count = 3。

## 冲突解决优先级

当编辑规则与其他指令冲突时：

1. 用户当前明确要求
2. 当前文章类型要求
3. 已确认编辑规则（edit-rules，confidence ≥ 5，status = active）
4. 高置信 Voice Profile（confidence ≥ 5）
5. 低置信推断（confidence 3-5）
6. 默认文风

**当前指令与历史规则冲突时，当前指令优先。** 历史规则不阻塞用户当前要求，但冲突事件会记录到规则的 conflict_count 中。

## 验证测试

学习新规则后，写一段验证段落让用户确认"这听起来像我吗"。不匹配则迭代调整。

## 触发提示

每积累 5 次 lessons，提示用户触发审核（不自动写入）。提示格式：

```
已积累 5 次修改记录，建议审核候选规则：
1. [候选规则1] — 支持 3 次，冲突 0 次
2. [候选规则2] — 支持 2 次，冲突 1 次
是否写入持久规则？
```
