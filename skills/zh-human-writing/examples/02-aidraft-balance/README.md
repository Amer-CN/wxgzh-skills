# Example 02 — AI 草稿 + balance

| 参数 | 值 |
|------|-----|
| source | ai_draft |
| strategy | balance |
| profile | essay |

## 输入

一段典型的 AI 生成文本，包含多种 hard-residue 模式。

## 预期结果

- hard-residue: **4-5**
  - HR-002 AI自我标识（"作为AI"）
  - HR-001 模板占位符（`{{产品名称}}`）
  - HR-004 聊天助手残留（"希望这对你有帮助"、"如果还有其他问题"、"请随时告诉我"）
- strong-contextual: 0
- advisory-only: 3+
- 总体: **fail**

说明：AI 草稿中的 hard-residue 应被正确检出，编辑时应删除或替换。
