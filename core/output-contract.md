# core/output-contract.md
# zh-human-writing v1 — 输出合同

---

## 1. clean 模式

只输出终稿。不附评分，不附编辑表演，不附保真警告。

- 回滚处恢复为原文
- clean 输出中不标注回滚

---

## 2. diff 模式

输出终稿 + 关键改动 + 保真警告 + 待确认项 + 改动统计。不附评分。

### 结构

```
## 终稿
{终稿全文}

## 关键改动
### 改动 1
- 位置：第 N 段，第 M 句
- 类型：{删除/改写/替换}
- 原文：{片段}
- 编辑后：{片段}
- 原因：{理由}

## 保真警告
### 警告 1
- 位置：第 N 段，第 M 句
- 类型：{否定变化/条件变化/...}
- 原文：{片段}
- 编辑后：{片段}
- 说明：{警告说明}

## 待确认项
### 待确认 1
- 位置：第 N 段，第 M 句
- 类型：{回滚/warning}
- 原文：{片段}
- 编辑后：{片段 或 "已回滚至原文"}
- 建议：{处理建议}

## 改动统计
- 字符数变化：{原文} → {终稿}（{比例}%）
- 句数变化：{原文} → {终稿}
- 段落数变化：{原文} → {终稿}
- 删除整句数：{N}
- 回滚数：{N}
- 待确认数：{N}
```

---

## 3. audit 模式

不改全文。允许"建议保留原文"。每条 finding 统一为十字段(任务书 §6,
档72C-3 落地):

### 结构(每条 finding)

```
- rule_id：{HR-001…HR-007 / SC-001…SC-007b / AO-001…}
- group：{hard_residue | strong_contextual | advisory_only}
- severity：{audit | strong | advisory}
- confidence：{high | medium | low}
- profile：{essay | technical | social}
- action：{mark | suggest | review_only}(命中保护区一律 review_only)
- location：第 N 段，第 M 句
- span_text：{原文片段,100 字截断,截断加 …}
- reason：{为什么判它,一句话}
- suggestion：{处置建议,一句话}
```

保留的额外字段:language_origin、cluster_count、cluster_threshold、context_note。

顶层结构:{hard_residue|strong_contextual|advisory_only}{count,items} +
overall{pass_fail,description} 不变。count 为条目数(不设 5 条上限,
档72C-3 起以全量输出为准;截断由消费侧处理)。

### "建议保留原文"的条件

1. 未发现 hard-residue
2. strong-contextual 聚集未超过阈值
3. advisory-only 模式不超过 3 个
4. 文本没有明显的表达问题

### "建议保留原文"的条件

1. 未发现 hard-residue
2. strong-contextual 聚集未超过阈值
3. advisory-only 模式不超过 3 个
4. 文本没有明显的表达问题

---

## 4. 输出与 strategy 的交互

| output | strategy | 行为 |
|--------|---------|------|
| clean | preserve | 输出终稿（改动少） |
| clean | balance | 输出终稿（改动适中） |
| clean | rebuild | 输出终稿（改动较大） |
| diff | preserve | 终稿 + 少量改动说明 |
| diff | balance | 终稿 + 改动说明 |
| diff | rebuild | 终稿 + 改动说明 + 多条保真警告 |
| audit | preserve | 诊断（问题少） |
| audit | balance | 诊断 |
| audit | rebuild | 报错：audit 不执行改写 |

---

## 5. 输出禁止项

- AI 概率
- 人味分
- 综合质量分
- 评分维度
- 风格量化指标（MATTR、burstiness 等）
- 作者身份判断
- 编辑表演
- 未授权的改写

---

## 6. Benchmark 限制声明

所有输出末尾附带：

> 本工具的编辑规则基于合成测试用例验证，未在真实大规模中文语料上独立验证。
> 编辑结果应由作者人工审阅后再发布。
> 本工具不判断文本是否 AI 生成。
