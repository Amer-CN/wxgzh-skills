# Writing Brief（已确认）

## 结构设计

### 文章原型
现象解读 + 趋势判断

### 叙事弧线
反直觉结论 → 证据 → 反方 → 边界

### 章节分配

| 章节 | 唯一任务 | 篇幅权重 | 素材来源 |
|------|---------|---------|---------|
| 引言：八天四款模型 | 建立冲突和悬念，吸引读者 | 5% | 素材②③ |
| K3 是什么 | 给出技术事实和数据 | 15% | 素材①② |
| 定价策略：不打价格战 | 解释最反直觉的决策 | 20% | 素材② |
| 开源权重：打破双头垄断 | 解释开源决定的战略意义 | 20% | 素材①⑤ |
| 不只是 K3：技术纵深 | 展示月之暗面的整体技术实力 | 15% | 素材④⑥ |
| 市场反应与政策博弈 | 展示事件的外部影响 | 15% | 素材⑤⑦⑧ |
| 边界和风险 | 反例和限制，保持可信度 | 5% | 攻核结果 |
| 总结 | 核心判断 + 开放问题 | 5% | — |

### 语义规划

| 章节 | semantic_blocks | formatter_opportunities |
|------|----------------|------------------------|
| 引言 | key_statement, statistic | oneliner-card |
| K3 是什么 | fact, statistic, comparison | facts, compare |
| 定价策略 | comparison, key_statement | compare, oneliner-card |
| 开源权重 | key_statement, quote | quote, oneliner-card |
| 技术纵深 | timeline, fact | timeline, facts |
| 市场反应 | resource_list, quote | resources, quote |
| 边界和风险 | checklist, warning | checklist, alert |
| 总结 | key_statement | oneliner-card |