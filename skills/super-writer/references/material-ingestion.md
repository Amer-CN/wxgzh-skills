# 素材摄入与路由

## 概述

当用户输入大量素材（链接、笔记、PDF、访谈稿等）时，Super Writer 需要系统地摄入、去重、分类和路由这些素材，确保每条素材被合理使用，不遗漏关键信息，不重复报道同一事件。

## material-ledger（素材台账）

每条素材摄入后记录到 material-ledger 中。模板见 `templates/material-ledger.yaml`。

### 结构

```yaml
material_ledger:
  total_count: 177
  materials:
    - id: mat-001
      source_type: url           # url / pdf / note / interview / text
      source_url: "https://..."
      title: "素材标题或摘要"
      raw_text: "原始内容片段"
      ingested_at: "2026-07-20"
      event_id: evt-001          # 关联的事件 ID
      claim_ids: [cl-001, cl-003] # 关联的论点 ID
      status: used                # used / deduplicated / conflicting / excluded
      excluded_reason: null       # excluded 时填写排除原因
```

### 字段说明

| 字段 | 含义 |
|---|---|
| id | 素材唯一标识（mat-NNN） |
| source_type | 素材来源类型 |
| source_url | 原始 URL（如有） |
| title | 素材标题或一句话摘要 |
| raw_text | 原始内容片段（用于去重比对） |
| ingested_at | 摄入日期 |
| event_id | 关联的事件 ID（多条素材可关联同一事件） |
| claim_ids | 关联的论点 ID 列表 |
| status | 素材使用状态 |
| excluded_reason | 被排除时的原因说明 |

## 三层去重模型

### 第一层：URL 去重

同一 URL 的素材视为同一条。不同 URL 但内容完全相同的素材也视为同一条（基于内容哈希）。

```
url_hash = sha256(normalized_url)
content_hash = sha256(normalized_text[:500])
```

同一 url_hash 或 content_hash → 合并为一条，状态标记 `deduplicated`。

### 第二层：事件级去重

**唯一 URL 不等于唯一事件。** 多个不同 URL 可能报道同一事件。

事件（event）= 一个独立发生的事情或事实。多条素材报道同一事件时，合并为一条事件记录，保留不同来源。

```yaml
events:
  - id: evt-001
    title: "事件简述"
    materials: [mat-001, mat-005, mat-012]
    sources_count: 3
    has_conflict: false
    claims: [cl-001]
```

#### 事件合并规则

| 情况 | 处理 |
|---|---|
| 多条素材报道同一事件，信息一致 | 合并为一条事件，保留所有来源 |
| 多条素材报道同一事件，信息冲突 | 合并为一条事件，标记 has_conflict: true |
| 同一事件的新进展 | 保留为同事件的子项，不删除旧信息 |
| 不同事件但同一来源 | 分别建立事件记录 |

#### 冲突处理

当多条素材对同一事件有不同描述时：

1. 保留所有不同版本，不自动选择某一个。
2. 标记 `has_conflict: true`。
3. 在 material-ingestion-report 中列出冲突详情。
4. 写作时需要显式处理冲突（选择一方 + 说明 / 列出分歧 / 标注未决）。

### 第三层：论点映射

论点（claim）= 文章需要论证的一个具体观点。一个事件可以支持多个论点，一个论点可以由多个事件支撑。

```yaml
claims:
  - claim_id: cl-001             # 76G-R/OBS-264:字段名与 canonical_claim_registry 对齐(原 id/statement 已废弃)
    claim_text: "多阶段构建可以显著减小镜像体积"
    source_excerpt: "多阶段构建可以显著减小镜像体积"   # 必填:素材中支撑该 claim 的逐字摘录(缺省会在媒体阶段 FAIL_CLOSED,三次生产返工实证)
    supporting_events: [evt-001, evt-003]
    conflicting_events: []
    coverage: covered            # covered / partial / missing
```

## canonical_claim_registry（主张注册表）

`canonical_claim_registry.json` 是 super-writer 阶段必检产物（full-mode 12 件之一），
顶层必须是 **对象（dict）**，禁止数组（76Q/OBS-287：76F 首版工具误按数组实现，
与生产产物不符，三轮生产各踩一次返工）。

### 结构（唯一真源形状）

```json
{
  "claims": [
    {
      "claim_id": "C-01",
      "claim_text": "Grok 4.6 于 2026-08-12 发布",
      "material_id": "M-01",
      "source_url": "https://x.ai/news/grok-4-6",
      "aihot_permalink": "https://aihot.virxact.com/items/...",
      "source_excerpt": "逐字摘录", "numbers": [],
      "support_strength": "strong", "qualifier": "", "conflict_status": "none"
    }
  ],
  "materials": [
    {
      "material_id": "M-01",
      "dedup_id": "cmsqabu...",
      "source_url": "https://x.ai/news/grok-4-6",
      "aihot_permalink": "https://aihot.virxact.com/items/...",
      "provenance": "normal"
    }
  ]
}
```

### 必填字段

### claims 数字与图表字段（77B/OBS-310，唯一真源形状）

- `claims[].numbers`：数字点阵数组，元素只能是 **string**（如原始摘录）或
  **`{"value": <number>, "unit": "..."}`** 对象；`value` 仅接受 number（整数/浮点），
  禁止放日期、年份、时间字符串。
- 图表字段 **`chart_group` / `metric_name` / `series_label` / `time_value` 归属 claim 级**，
  与 `numbers` 数组并列，**禁止进 numbers 数组**（media schema additionalProperties=false，
  误放即被拒，i2z69i/Qwen/GLM 多轮付费实证）。
- `time_value`：真实时间（如 `2026-08-19` ISO 日期）；时间轴图表只在每个点都有
  time_value 时生成（media schema 语义）。

```json
{"claim_id": "C-01", "claim_text": "...", "numbers": [{"value": 150.8, "unit": "元/股"}],
 "chart_group": "ipo-pricing", "metric_name": "发行价", "series_label": "宇树 IPO", "time_value": "2026-08-19"}
```

- `claims[].claim_id / claim_text / material_id / source_url / source_excerpt` 必填（76G-R）；
- `materials[].material_id / dedup_id / source_url` 必填（76Q/OBS-287）。

### dedup-id ↔ material_id 映射（76Q/OBS-287）

`materials[].dedup_id` 必须与 aihot 阶段 `deduplicated_items.json` 对应条目的 `id`
逐字一致（dedup 池内 id 是唯一键，aihot_permalink 类字段名税绝版）；
`materials[].material_id` 是 registry 内部标识（M-NN）。claim 通过 `material_id` 挂到
material；任何 claim 的 `material_id` 必须在 materials 中存在，否则 registry 无效。

### claim / material source_url 逐字一致（76Q/OBS-287）

同一 material 在 `claims[].source_url` 与 `materials[].source_url` 必须**逐字完全相等**
——含锚点：一边带 `#anchor` 一边不带即不一致；大小写、协议、尾部斜杠均不得漂移。
该规则由 `validate_single_product.py --product registry` 机械层强制（76Q 起），
不再依赖 agent 自觉。

## 三层覆盖率

### source_coverage（素材覆盖率）

```
source_coverage = used_materials / total_materials
```

used_materials = status 为 `used` 的素材数量。

### event_coverage（事件覆盖率）

```
event_coverage = covered_events / total_events
```

covered_events = 至少有一条素材被 used 的事件数量。

未被覆盖的事件必须在 material-ingestion-report 中列出原因。

### claim_coverage（论点覆盖率）

```
claim_coverage = covered_claims / total_claims
```

covered_claims = supporting_events 中至少有一个事件被覆盖的论点。

未被覆盖的论点必须在 material-ingestion-report 中列出原因。

三层覆盖率独立计算，不互相替代。

## material-ingestion-report（素材摄入报告）

模板见 `templates/material-ingestion-report.json`。

### 结构

```json
{
  "total_materials": 177,
  "total_events": 45,
  "total_claims": 12,
  "source_coverage": 0.72,
  "event_coverage": 0.89,
  "claim_coverage": 0.92,
  "duplicates_removed": 23,
  "conflicts_detected": 3,
  "excluded_materials": [
    {"id": "mat-034", "reason": "与 mat-001 内容完全相同"}
  ],
  "uncovered_events": [
    {"event_id": "evt-017", "reason": "与文章核心论点无关"}
  ],
  "uncovered_claims": [
    {"claim_id": "cl-008", "reason": "支撑证据已被更重要的论点使用"}
  ],
  "conflicts": [
    {"event_id": "evt-005", "description": "两个来源对数字有不同报道", "sources": ["mat-007", "mat-022"]}
  ]
}
```

## 大批量素材路由（> 100 条）

当素材量超过 100 条时，按以下流程路由：

1. **URL 去重**：先按 url_hash 和 content_hash 去除完全重复。
2. **事件聚类**：将素材按事件聚类，同一事件的多条素材合并。
3. **冲突标记**：检测同一事件的不同描述，标记冲突。
4. **论点映射**：将事件映射到文章论点。
5. **覆盖率计算**：计算三层覆盖率。
6. **排除决策**：与文章核心论点无关的事件标记为 excluded，记录原因。
7. **模式建议**：根据素材量建议 article_mode（通常 daily_digest / weekly_roundup / material_synthesis）。

### 排除规则

素材被排除时必须记录原因。允许的排除原因：

| 原因 | 说明 |
|---|---|
| duplicate | 与其他素材内容完全相同 |
| irrelevant | 与文章核心论点无关 |
| outdated | 信息已过时 |
| superseded | 被新进展取代（保留旧信息但不作为主要来源） |
| conflicting_kept | 冲突双方均保留，但此条不作为主要论据 |

## 与写作流程的集成

### Phase 1（写作简报）

摄入素材后，根据素材量判断是否需要触发 `needs_mode_selection`。

### Phase 1.5（素材充分性检查）

material-ledger 的素材状态作为素材充分性检查的输入。source_coverage 低于 30% 时提示素材利用率不足。

### Phase 2（研究）

material-ingestion-report 中的 uncovered_events 和 conflicts 作为研究阶段的优先处理项。

### Phase 4（结构设计）

claim_coverage 决定大纲中哪些论点有充分支撑、哪些需要补充。
