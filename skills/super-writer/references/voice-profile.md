# Voice Profile 规范

## 来源优先级

1. 用户明确认可的近期文章；
2. 用户亲自写的文章、笔记、邮件；
3. 用户人工修改后的最终稿；
4. 旧文章；
5. 用户仅表示"喜欢"的他人范文。

不得把他人风格直接声明为用户人格。

## 分层结构

Voice Profile 采用分层加载，不把 12 维作为每篇必须加载的刚性数量。

### 核心 8 维（默认加载）

| # | 维度 | 说明 |
|---|------|------|
| 1 | sentence_rhythm | 句长分布、长短交替模式 |
| 2 | paragraph_structure | 段落数、一句话段落使用 |
| 3 | claim_strength | 断言 vs 对冲频率 |
| 4 | uncertainty_style | hedging 方式（"可能""或许""取决于"等） |
| 5 | evidence_order | 证据呈现顺序（具体先于抽象？数据先于解释？） |
| 6 | reader_relationship | 人称策略、提问使用 |
| 7 | transition_style | 转折方式（显式连接词 vs 隐式跳跃 vs 回调） |
| 8 | never_do | 明确禁区列表 |

### 可选 4 维（按需加载）

| # | 维度 | 说明 |
|---|------|------|
| 9 | analogy_preference | 类比域、频率 |
| 10 | humor_style | 类型、频率、出现位置 |
| 11 | opening_closing | 开头动作、结尾模式 |
| 12 | punctuation_format | 标点个性、格式偏好 |

## 每维数据结构

```yaml
- dimension: sentence_rhythm
  value: "短长交替，一句话段落频繁用于强调"
  confidence: 0.0          # 累计置信度
  source_count: 0          # 支持该描述的范文数量
  sources: []              # 范文文件名列表
  scope: global            # global | article_type_specific
  last_confirmed: ""       # 最后一次用户确认的日期
```

## confidence 使用规则

- **≥ 5**：硬约束，写作时必须执行。
- **3-5**：软参考，倾向遵循但不强制。
- **< 3**：忽略，标记为 `stale`，提示用户复查。
- **≤ 0**：标记为 `ignored`，不执行，但**不自动删除**——保留来源和历史以备复查。

低置信维度标记为 `stale` 或 `ignored`，不自动删除来源和历史。这与编辑规则的保守学习原则一致。

## 冲突解决优先级

当 Voice Profile 与其他指令冲突时，按以下顺序裁决：

1. 用户当前明确要求
2. 当前文章类型要求
3. 已确认编辑规则（edit-rules）
4. 高置信 Voice Profile（confidence ≥ 5）
5. 低置信推断（confidence 3-5）
6. 默认文风

## Voice Profile 之外的内容

以下信息**不属于** Voice Profile，必须分开存储：

| 信息类型 | 存储位置 |
|----------|----------|
| 作者价值观 | `profiles/belief-profile.example.yaml` |
| 业务定位 | 写作简报 |
| 事实和经历 | 证据地图 |
| 目标读者 | `profiles/audience-profile.example.yaml` |
| 当前文章立场 | 写作简报 |

将非风格信息混入 Voice Profile 会导致它膨胀为人格总档案，失去可执行性。

## 操作标准

- 每条描述必须能指导写作或审稿。
- 避免"真诚、温暖、有力量"这类不可执行形容。
- 把稳定特征与当前文章要求分开。
- Profile 控制在可重复加载的长度内。
- 用户当前明确要求可以覆盖 Profile。
