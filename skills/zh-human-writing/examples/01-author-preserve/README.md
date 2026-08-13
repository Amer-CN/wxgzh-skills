# Example 01 — 作者原创 + preserve

| 参数 | 值 |
|------|-----|
| source | author_written |
| strategy | preserve |
| profile | essay |

## 输入

一段作者原创短文，语言自然，无模板化表达。

## 预期结果

- hard-residue: **0**
- strong-contextual: **0**
- advisory-only: 1-2（第一人称"我"，正常）
- 总体: **pass**

说明：作者风格文本不应被误杀。advisory-only 的"我"是预期行为，不影响 pass/fail。
