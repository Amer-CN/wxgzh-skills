---
name: zh-human-writing
version: "1.0"
description: 简体中文写作编辑 Skill — 在不改变事实、意图、立场和任务边界的前提下减少模板化机器表达
---

# zh-human-writing v1

## 产品定位

简体中文写作编辑 Skill。根据文本来源和发布场景选择编辑方式，减少模板化机器表达，提升准确性、自然度和可发布性。

**不是**：作者身份检测器、AI 检测规避工具、通用文字美化器、自动制造观点/经历/情绪的工具、把所有文章改成同一种"人味腔"的工具。

---

## 输入参数

| 参数 | 类型 | 允许值 | 默认值 |
|------|------|--------|--------|
| source | enum | author_written, ai_draft, mixed, unknown | unknown |
| strategy | enum | preserve, balance, rebuild | 由 source 推导 |
| profile | enum | essay, technical, social | essay |
| length_retention | enum | strict, balanced, free | balanced |
| output | enum | clean, diff, audit | clean |

不得自动判断文本是不是 AI 写的。没有 source 时使用 unknown。

详细定义见 `core/input-contract.md`。

---

## 默认路由

| source | 默认 strategy | 改动预算 | 审计范围 |
|--------|--------------|---------|---------|
| author_written | preserve | 低 | 改动区 |
| ai_draft | balance | 中 | 全文 |
| mixed | balance | 中 | 全文 + 改动区重点 |
| unknown | preserve | 低 | 改动区 |

- **author_written**：低改动预算，局部编辑优先，不静默重排段落，不删除承担信息/节奏/情绪作用的句子。
- **ai_draft**：允许删除纯空句，允许局部调整结构，rebuild 需要用户明确授权。
- **mixed**：先区分作者正文、AI 草稿、引用、代码和嵌入块。
- **unknown**：不得自行升级为 rebuild。

详细权限见 `core/routing.md`。

---

## 硬约束

### 必须保护

- 事实
- 数字、日期、百分比和单位
- 人名、机构名和产品名
- 责任主体和观点归属
- 引用
- URL
- 代码、命令、路径、参数和字段
- 日志、错误和状态码
- 否定
- 条件
- 因果
- 范围和不确定程度
- 用户明确指定不可改的片段

### 禁止

- 无依据增加具体细节
- 无依据增加第一人称
- 无依据增加观点、感受和经历
- 为了"人味"故意制造毛边
- 用综合分抵消硬约束失败

详细约束见 `core/invariants.md`。

---

## 执行流程（固定 9 步）

1. 读取输入合同
2. 提取 protected spans
3. 识别 source、strategy 和 profile 对应权限
4. 诊断真实表达问题
5. 执行最小必要编辑
6. 独立做双向保真审计
7. 硬约束失败则局部回滚
8. 最多做一次高置信残留检查
9. 按 clean/diff/audit 输出

不实现无限循环，不实现评分驱动迭代，不实现多轮改写（ouroboros）。

详细流程见 `core/execution-flow.md`。

---

## 模式分级

### hard-residue（单次出现即可触发）

- 模板占位符 `{{...}}`、`[INSERT...]`
- "作为AI"、"作为一个人工智能"
- "截至我的知识"、"截至我所知"
- 明显聊天助手残留
- 明显 AI 来源参数

**动作权限**：allow — 可自动删除或替换。

### strong-contextual（聚集出现才触发）

- 无信息开场
- 无信息导航
- 无信息总结
- 无来源权威铺垫
- 连续同构结构
- 明显假互动

**动作权限**：conditional — 聚集 ≥2 次时标记，需结合 profile 判断。

### advisory-only（仅建议，不单独触发自动修改）

- "不是…而是…"、"先…再…"、"从…到…"
- 破折号、三段式、反问、二人称
- 句长相近、段长相近、普通连接词、第一人称、对仗和重复

**动作权限**：deny auto-modify — 只在 diff/audit 输出中提示，不自动改写。

advisory-only 在所有 strategy 下都不得单独触发自动修改。

详细策略见 `references/patterns/` 下的模式包。

---

## Protected Spans

5 类保护项：

1. 事实性内容（数字、日期、百分比、单位、URL、人名、机构名、产品名）
2. 技术性内容（代码块、命令、路径、参数、字段名、日志、错误码、状态码）
3. 语义性内容（引用原文、否定、条件、因果、责任主体、不确定程度、用户显式 protected spans）
4. 作者性内容（作者明确不可改片段、个人观点和立场、语气和语域）
5. 用户显式 protected spans

详细定义见 `references/protected-spans.md`。

---

## 输出合同

| 模式 | 内容 | 禁止 |
|------|------|------|
| clean | 只输出终稿 | 不附评分，不附编辑表演 |
| diff | 终稿 + 关键改动 + 保真警告 + 待确认项 | 不附评分 |
| audit | 不改全文，最多 5 个问题，允许"建议保留原文" | 不改写 |

任何输出模式均不输出：AI 概率、人味分、综合质量分、评分维度、风格量化指标、作者身份判断。

详细规格见 `core/output-contract.md`。

---

## Fiction 拒绝机制

v1 不支持 fiction 编辑。

- 用户请求 fiction：明确拒绝，提示"v1 不支持 fiction 编辑"
- 用户坚持 fiction：重复拒绝，不降级为其他 profile 执行
- 不创建空有其名的 fiction 编辑规则

---

## 加载指引

### 始终加载

1. `SKILL.md`（本文件）
2. `core/invariants.md`
3. `core/input-contract.md`
4. `core/routing.md`
5. `core/execution-flow.md`
6. `references/protected-spans.md`
7. `references/false-positive-protection.md`
8. `references/domain-lexicon.yaml`

### 按 profile 加载（步骤 3）

- `profiles/essay.md`（profile=essay）
- `profiles/technical.md`（profile=technical）
- `profiles/social.md`（profile=social）

### 按问题加载（步骤 4）

- `references/patterns/hard-residue.md`（诊断发现 hard-residue 时）
- `references/patterns/strong-contextual.md`（诊断发现 strong-contextual 时）
- `references/patterns/advisory-only.md`（output=diff 或 audit 时）

### 按需加载

- `author-profile/schema.md`（用户提供作者样本时）

---

## v1 明确排除

- AI 概率、人味分、综合质量分
- stylometry、MATTR、burstiness
- ouroboros、真人停手门检
- 自由 voice injection
- 强制增加观点和第一人称
- 固定大型行业白名单
- 一次载入全部模式
- 自动补全模板占位值
- fiction 编辑

---

> 本工具的编辑规则基于合成测试用例验证，未在真实大规模中文语料上独立验证。
> 编辑结果应由作者人工审阅后再发布。
> 本工具不判断文本是否 AI 生成。
