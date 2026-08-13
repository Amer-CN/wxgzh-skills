# Example 03 — 技术文档

| 参数 | 值 |
|------|-----|
| source | unknown |
| strategy | preserve |
| profile | technical |

## 输入

一段技术部署文档，包含版本号、路径、命令、配置参数。

## 预期结果

- hard-residue: **0**
- strong-contextual: **0**
- advisory-only: **0**
- 总体: **pass**

说明：技术文档中的数字、路径、命令等是 Protected Spans，不应被检测为模式或误删。technical profile 调整系数 ×1.5，更宽松。
