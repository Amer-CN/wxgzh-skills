# core/input-contract.md
# zh-human-writing v1 — 输入合同

---

## 参数定义

| 参数 | 类型 | 允许值 | 默认值 |
|------|------|--------|--------|
| source | enum | author_written, ai_draft, mixed, unknown | unknown |
| strategy | enum | preserve, balance, rebuild | 由 source 推导 |
| profile | enum | essay, technical, social | essay |
| length_retention | enum | strict, balanced, free | balanced |
| output | enum | clean, diff, audit | clean |

---

## source — 文本来源

由用户显式提供。不得由 Skill 自动推断文本是否 AI 生成。

- **author_written**：用户声明这是自己写的文章
- **ai_draft**：用户声明这是 AI 生成的草稿
- **mixed**：用户声明文本中混合了作者正文和 AI 草稿
- **unknown**：用户未提供来源或不确定

用户未提供时使用 unknown，默认 preserve 策略。
无效值时报错并列出允许值，使用 unknown 作为 fallback。

---

## strategy — 编辑策略

- **preserve**：最低改动，只修明确问题
- **balance**：适度改动，可删空句、调结构
- **rebuild**：较大改动，需用户明确授权

默认由 source 推导：

| source | 默认 strategy |
|--------|--------------|
| author_written | preserve |
| ai_draft | balance |
| mixed | balance |
| unknown | preserve |

rebuild 必须由用户明确指定，不得自动升级。

---

## profile — 文体场景

- **essay**：公众号文章、个人随笔、评论
- **technical**：技术文章、产品说明、技术复盘
- **social**：社媒短文、短文案

用户未提供时使用 essay。
无效值时报错并列出允许值，使用 essay 作为 fallback。

---

## length_retention — 长度保持

- **strict**：字数留存率目标 ≥ 0.90，不允许删整句
- **balanced**：字数留存率目标 ≥ 0.80，可删空句
- **free**：无字数留存率硬下限，允许较大改动

---

## output — 输出模式

- **clean**：只输出终稿
- **diff**：终稿 + 关键改动 + 保真警告 + 待确认项
- **audit**：不改全文，最多 5 个问题，允许"建议保留原文"

---

## 参数冲突处理

### CR-1: source 与 strategy 不匹配

| 条件 | 动作 | 级别 |
|------|------|------|
| source=author_written AND strategy=rebuild | 报错：不建议 rebuild。降级为 balance。 | warning |
| source=unknown AND strategy=rebuild | 报错：不允许 rebuild。降级为 preserve。 | error |
| source=ai_draft AND strategy=preserve | 允许但提示可能不足。 | info |
| source=mixed AND strategy=rebuild | 允许但提示注意。 | info |

### CR-2: technical + rebuild

| 条件 | 动作 | 级别 |
|------|------|------|
| profile=technical AND strategy=rebuild | 报错：风险高。降级为 balance。 | warning |
| profile=technical AND rebuild AND user_confirmed | 允许，protected spans 检查加严。 | allowed |

### CR-3: unknown + rebuild

| 条件 | 动作 | 级别 |
|------|------|------|
| source=unknown AND strategy=rebuild | 报错：不允许。强制降级为 preserve。 | error |
| source=unknown AND strategy=balance | 允许但提示。 | info |

### CR-4: strict + 结构性修改

| 条件 | 动作 | 级别 |
|------|------|------|
| strict AND rebuild | 报错：冲突。降级为 balance。 | warning |
| strict AND balance | 允许但限制：不删整句，≥ 0.90。 | allowed |
| strict AND preserve | 正常执行。 | allowed |

### CR-5: audit + 改写

| 条件 | 动作 | 级别 |
|------|------|------|
| output=audit | 不改全文，最多 5 个问题。 | enforced |
| output=audit AND strategy=rebuild | 报错：audit 不执行改写。 | warning |

### CR-6: fiction 请求

明确拒绝：v1 不支持 fiction 编辑。不降级为其他 profile 执行。

### CR-7: 不支持的文体

- 公文：提示不支持，可尝试 essay
- 学术论文：提示不支持，可尝试 technical
- 法律/医疗高风险：明确拒绝
