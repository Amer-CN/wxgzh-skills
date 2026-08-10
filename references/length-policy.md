# 篇幅策略

## 概述

篇幅策略决定一篇文章的目标可见字符数（target_visible_chars）、允许范围（acceptable_min / acceptable_max）和章节预算分配。篇幅由 article_mode 和 length_mode 共同决定。用户可以显式覆盖默认值。

## 可见字符定义

可见字符（visible_chars）= 文章正文中所有非空白字符的计数。包括中文、英文、数字、标点。排除空格、换行、制表符、Markdown 标记符号（#、*、-、>、| 等）。

代码内容（行内代码和代码块正文）计入可见字符，因为代码在最终文章中是可见正文。只删除 Markdown 围栏符和反引号，保留其中代码内容。

## article_mode（文章模式）

文章模式由写作简报阶段确定，描述文章的基本形态。

| article_mode | 说明 | 典型场景 |
|---|---|---|
| short | 短资讯/快评 | 单一事件、单一观点 |
| medium | 标准公众号文章 | 常规观点文、教程 |
| long | 深度长文 | 多维分析、案例复盘 |
| deep | 极深度分析 | 行业研究、系统性论证 |
| daily_digest | 日报/快讯合集 | 多事件简要汇总 |
| weekly_roundup | 周报/精选合集 | 一周精选、多主题综述 |
| material_synthesis | 素材合成 | 大批量素材整合成文 |

## length_mode 默认篇幅档位

每种 article_mode 对应一个 length_mode 预设，定义目标可见字符数和允许范围。

| article_mode | length_mode | target_visible_chars | acceptable_min | acceptable_max |
|---|---|---|---|---|
| short | short | 1,500 | 1,200 | 2,000 |
| medium | medium | 3,000 | 2,500 | 4,000 |
| long | long | 5,000 | 4,500 | 6,500 |
| deep | deep | 8,000 | 7,000 | 10,000 |
| daily_digest | daily_digest | 2,500 | 2,000 | 3,500 |
| weekly_roundup | weekly_roundup | 4,000 | 3,500 | 5,500 |
| material_synthesis | material_synthesis | 6,000 | 5,000 | 8,000 |

## 用户覆盖规则

用户可以在写作简报阶段显式指定 target_visible_chars 或 article_mode：

1. 用户指定 article_mode → 使用该模式的默认篇幅档位。
2. 用户指定 target_visible_chars → 覆盖默认值，acceptable_min/max 按比例调整（±15%）。
3. 用户同时指定 article_mode 和 target_visible_chars → 以 target_visible_chars 为准。
4. 用户不指定 → 根据素材量和文章类型推断 article_mode。

## needs_mode_selection（模式选择门禁）

当输入素材超过 100 条且用户未明确指定 article_mode 时，触发 `needs_mode_selection` 退出状态：

```yaml
exit_status: needs_mode_selection
reason: "素材量超过100条，需要用户明确指定文章模式"
material_count: 177
available_modes:
  - daily_digest
  - weekly_roundup
  - material_synthesis
  - long
  - deep
next_action: "请选择文章模式，或指定目标字数"
```

### 判定规则

| 素材量 | 用户指定模式 | 行为 |
|---|---|---|
| < 50 条 | 未指定 | 自动推断 article_mode |
| 50-100 条 | 未指定 | 自动推断，优先 medium 或 long |
| > 100 条 | 未指定 | `needs_mode_selection` |
| 任意 | 已指定 | 使用用户指定模式 |

## 章节预算分配

确定 target_visible_chars 后，按 outline 的章节权重分配字数预算。

### 分配公式

```
section_budget = target_visible_chars × section_weight
```

其中 section_weight 来自 outline 的权重（总计 100%）。

### 容差

每节实际可见字符数与预算的偏差不得超过 ±5%。

```
偏差率 = |实际字数 - 预算字数| / 预算字数
```

偏差率 > 5% → ERROR: 章节预算超限

### 示例

target_visible_chars = 3,000，三节权重 40% / 35% / 25%：

| 章节 | 预算 | 允许范围（±5%） |
|---|---|---|
| 第一节 | 1,200 | 1,140 - 1,260 |
| 第二节 | 1,050 | 998 - 1,103 |
| 第三节 | 750 | 713 - 788 |

## 重复正文检测

禁止通过重复正文凑长度。以下行为视为违规：

1. 同一段落出现两次（完全相同或仅标点差异）。
2. 同一论点用不同措辞重复出现超过 2 次。
3. 用填充性文字（无信息增量的过渡段）占用超过总篇幅 10%。

检测到重复正文 → ERROR: 重复正文凑长度

## 长度门禁

文章完成后必须通过长度门禁检查（`scripts/validate_article_length.py`）：

| 检查项 | 规则 | 失败状态 |
|---|---|---|
| 总长度下限 | visible_chars >= acceptable_min | ERROR: 低于最小篇幅 |
| 总长度上限 | visible_chars <= acceptable_max | WARNING: 超过最大篇幅，检查是否冗余 |
| 章节预算偏差 | 每节偏差 <= 5% | ERROR: 章节预算超限 |
| 重复正文 | 无重复段落 | ERROR: 重复正文凑长度 |

## full 模式完整性门禁

当 output_mode 为 `full` 时，以下 12 个产物必须全部存在、非空且包含必填字段，否则失败：

| # | 产物 | 必填字段 |
|---|---|---|
| 1 | generation-profile.yaml | mode, article_mode, length_mode, target_visible_chars, acceptable_min, acceptable_max, material_ledger_path, ingestion_report_path |
| 2 | writing-brief.md | article_mode, length_mode, target_visible_chars, acceptable_min, acceptable_max |
| 3 | material-readiness.yaml | topic, audience, core_opinion, evidence, personal_experience, voice_context, allowed_output, required_actions |
| 4 | material-ingestion-report.json | source_coverage, event_coverage, claim_coverage |
| 5 | material-ledger.yaml | material_ledger (通过 material_ingestion.py 校验) |
| 6 | evidence-map.md | 非空，含 Evidence ID |
| 7 | core-card.md | Core Statement, Reader Change, Core Tension, Value Carrier, Scope, Result |
| 8 | outline.md | target_visible_chars, weight_percent, planned_chars |
| 9 | article.md | 通过长度门禁 |
| 10 | semantic-map.yaml | 通过 validate_semantic_map.py 校验 |
| 11 | editor-report.md | P0, P1, P2 |
| 12 | handoff.yaml | schema_version, prose_craft_applied, prose_craft_version, formatter.cover（档76A/OBS-252 必检） |

执行顺序：
1. `python scripts/material_ingestion.py --ledger material-ledger.yaml --output material-ingestion-report.json`
2. `python scripts/validate_article_length.py --article article.md --full-mode --generation-profile ... --semantic-map ... --handoff handoff.yaml`
3. `python scripts/validate_semantic_map.py --article article.md --semantic-map semantic-map.yaml`

缺任意一项或字段不完整 → ERROR: full 模式产物不完整
