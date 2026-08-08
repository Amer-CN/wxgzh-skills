# references/patterns/hard-residue.md
# zh-human-writing v1 — hard-residue 模式包
# 单次出现即可高度确定是 AI 残留，不需要密度判断。

---

## HR-001: 模板占位符

- **ID**: HR-001
- **问题**: 文本中包含未替换的模板占位符
- **触发线索**: `{{...}}`、`[INSERT...]`、`<...>`、`[待填]`
- **状态**: 代码实现 `{{...}}` / `[INSERT...]` / `[待填]`;`<...>` 变体**未实现**（72C-1 M-2a,留 Batch 3）
- **适用 profile**: essay, technical, social
- **处理权限**: allow 删除/替换
- **language_origin**: language_general
- **false positives**: 讨论模板语法的文章中可能出现，需结合上下文
- **protected cases**: 文本本身就是在讨论模板语法时
- **来源说明**: 重新实现，通用模式

---

## HR-002: AI 自我标识

- **ID**: HR-002
- **问题**: AI 自我标识残留
- **触发线索**: "作为AI"、"作为一个人工智能"、"我是一个AI"、"作为语言模型"、"作为一款AI"（代码变体集,72C-2 以代码为准补齐）
- **适用 profile**: essay, technical, social
- **处理权限**: allow 删除/替换
- **language_origin**: language_general
- **false positives**: 讨论 AI 的文章中引用 AI 回复可能被误判，需结合上下文
- **protected cases**: 文章本身在讨论 AI 回复或引用 AI 对话
- **来源说明**: 重新实现，通用模式

---

## HR-003: 知识截止声明

- **ID**: HR-003
- **问题**: AI 知识截止声明残留
- **触发线索**: "截至我的知识"、"截至我所知"、"我的知识截止"（代码实现,匹配"我的知识截止到"前缀）、"根据我的训练数据"（代码变体集,72C-2 以代码为准补齐）
- **适用 profile**: essay, technical, social
- **处理权限**: allow 删除/替换
- **language_origin**: language_general
- **false positives**: 无
- **protected cases**: 无
- **来源说明**: 重新实现，通用模式

---

## HR-004: 聊天助手残留

- **ID**: HR-004
- **问题**: 聊天助手的提示语残留
- **触发线索**: 代码变体集（72C-2 以代码为准补齐）:"请问还有什么可以帮助"、"还有什么我可以帮助"、"如果您有其他问题"、"还有什么我可以为您"、"希望这对你有帮助"、"如果还有其他问题"、"请随时告诉我"
- **适用 profile**: essay, technical, social
- **处理权限**: allow 删除/替换
- **language_origin**: language_general
- **false positives**: 讨论 AI 客服的文章可能引用这些句子，需结合上下文
- **protected cases**: 文章本身在讨论 AI 客服对话
- **来源说明**: 重新实现，通用模式

---

## HR-005: AI 来源参数泄露

- **ID**: HR-005
- **问题**: AI 模型参数泄露
- **触发线索**: `model=gpt`（匹配 `model=gpt-...` 前缀）、`temperature=`、`top_p=`、`max_tokens=`（代码变体集,72C-2 以代码为准补齐）
- **适用 profile**: essay, technical, social
- **处理权限**: allow 删除/替换
- **language_origin**: language_general
- **false positives**: 讨论 AI 参数的技术文章中可能出现，需结合上下文
- **protected cases**: 技术文章中讨论模型参数配置时
- **来源说明**: 重新实现，通用模式

---

## HR-006: 用户指定删除的模板

- **ID**: HR-006
- **问题**: 用户在输入中明确要求删除的模板残留
- **触发线索**: 用户指定
- **状态**: **未实现，Batch 3**（72C-1 M-2a:代码 HR 只有 001–005）
- **适用 profile**: essay, technical, social
- **处理权限**: allow 删除/替换
- **language_origin**: N/A
- **false positives**: 无（用户指定）
- **protected cases**: 无
- **来源说明**: 用户驱动

---

## HR-007: 元话语路标

- **ID**: HR-007
- **问题**: 元话语路标残留（"先说结论"、"说白了"、"说穿了"）
- **触发线索**: "先说结论"、"说白了"、"说穿了"
- **适用 profile**: essay, technical, social
- **处理权限**: allow 删除/替换
- **language_origin**: chinese_specific
- **false positives**: 讨论写作技巧的文章中引用这些词时可能出现,需结合上下文
- **protected cases**: 文章本身在讨论/引用这些路标词
- **来源说明**: 档72C-2 §3(任务书 §3.1)由 strong-contextual 移入 hard-residue,命中即 exit 2
- **状态**: 已实现（pattern_audit.py HR-007,含 PB-016 正例 / HR-007-NEG 反例）

---

## 动作权限汇总

| 级别 | preserve | balance | rebuild |
|------|---------|---------|---------|
| hard-residue | allow 删除/替换 | allow 删除/替换 | allow 删除/替换 |

hard-residue 可以进入确定性检测。单次出现即可标记为 finding。
