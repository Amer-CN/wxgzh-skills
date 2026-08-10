# 下游交接契约

## v2.2 Schema（档76A 新增，向后兼容 v1.0/v2.0/v2.1）

写作 Skill 完成后输出：

```yaml
handoff:
  schema_version: "2.2"
  article_path: article.md
  semantic_map_path: semantic-map.yaml    # v2.0 新增
  content_score: 0
  p0_count: 0
  exit_status: ready_to_write

  prose_craft_applied: false              # Batch 2 新增：本文是否经过 prose-craft 层（R1–R9 自检）
  prose_craft_version: null               # Batch 2 新增：prose-craft.md 的版本号（如 "1.0"）

  handoff_stage: super_writer             # Batch 3 新增：产出本 handoff 的阶段标识
  author_intent: "写给谁/为什么写"       # Batch 3 新增：作者意图一句话（来自 Phase 1 简报）
  allow_rewrite_scope: "none"            # Batch 3 新增：作者授予下游的改写范围，枚举 none/expression_only，默认 none
  material_stats: {}                      # Batch 3 新增：材料/事件/claim 计数与三层覆盖率（材料门判定依据留痕）
  scope: ""                              # Batch 3 新增：文章范围声明；scope_reduction 发生时记录收窄结果与理由
  title_candidates: []                   # 档76A 新增：3–5 个候选标题（Phase 3 攻核后产出，不同角度；Phase 6 选定后保留备查）
  hook_line: ""                          # 档76A 新增：一句钩子（本文最反直觉/最值钱的点）；formatter.cover.strike 未单独指定时默认取此值
  selected_title: ""                    # 档76B 新增：Reviewer 按评分尺从 title_candidates 选定的最终 H1（article.md H1 与此一致）
  title_selection_reason: ""            # 档76B 新增：选定理由一行（评分尺依据）

  unresolved_facts: []
  editor_anchors: []
  author_confirmations: []
  preserve_exactly: []

  formatter:                               # v2.0 新增
    target_skill: gzh-design
    contract: semantic-component-handoff
    contract_version: "1.0"
    preferred_theme: null                  # null=不指定；用户指定时填主题英文标识
    component_policy:
      force_all_components: false
      formatter_has_final_choice: true
      allow_fallback: true
      prohibit_content_invention: true
    validation:
      anchors_resolved: true
      payloads_complete: true
      unsupported_roles: []
    cover:                                 # Batch 3 新增：封面文案（缺省则下游用渲染默认）
      kicker: null                         # 文章类型标签（如 "深度观察"）
      strike: null                         # 被本文推翻的旧认知疑问句
      tags: null                           # 2 个内容标签（如 ["深度", "观察"]）
                                           # 档76A 联动：strike 未单独指定时默认取 hook_line

  next:
    - skill: humanizer
      trigger: "P3 表达层问题存在或用户要求去 AI 味"
      priority: recommended
    - skill: gzh-design
      trigger: "需要公众号/多平台排版格式转换"
      priority: optional
    - skill: publisher
      trigger: "用户要求直接发布到平台"
      priority: optional
```

### v1.0 向后兼容

v1.0 字段（article_path、content_score、p0_count、exit_status、unresolved_facts、editor_anchors、author_confirmations、preserve_exactly、next）全部保留。v2.0/v2.1 新增字段：

| 新字段 | 含义 |
|--------|------|
| schema_version | 交接契约版本，v2.1 |
| semantic_map_path | 语义映射文件路径 |
| formatter | formatter 交接子契约 |
| prose_craft_applied | 本文是否经过 prose-craft 层（R1–R9 自检），true/false |
| prose_craft_version | prose-craft.md 的版本号（如 "1.0"） |
| formatter.target_skill | 目标排版 Skill（gzh-design） |
| formatter.contract | 交接契约类型（semantic-component-handoff） |
| formatter.contract_version | 契约版本（1.0） |
| formatter.preferred_theme | 首选主题（null=不指定） |
| formatter.component_policy | 组件策略 |
| formatter.validation | 校验状态 |
| handoff_stage | 产出本 handoff 的阶段标识（交接来源可追溯） |
| author_intent | 作者意图一句话（写给谁/为什么写，来自 Phase 1 简报） |
| allow_rewrite_scope | 作者授予下游的改写范围，枚举 none/expression_only，默认 none |
| material_stats | 材料/事件/claim 计数与三层覆盖率（材料门判定依据留痕） |
| scope | 文章范围声明；scope_reduction 发生时记录收窄结果与理由 |
| formatter.cover | 封面文案对象 {kicker, strike, tags}；缺省则下游用渲染默认 |
| title_candidates | 3–5 个候选标题（字符串数组，供用户草稿箱挑选，不自动替换 H1） |
| hook_line | 一句钩子（本文最反直觉/最值钱的点）；formatter.cover.strike 未单独指定时默认取此值 |
| selected_title | Reviewer 按评分尺从 title_candidates 选定的最终 H1（字符串；article.md H1 与此一致） |
| title_selection_reason | 选定理由一行（字符串，评分尺依据） |

---

## 下游 Skill 说明

| Skill | 职责 | 触发条件 | 传递内容 |
|-------|------|----------|----------|
| humanizer | 去 AI 味、节奏调整、表达优化 | P3 问题存在或用户要求 | 核心观点、不可删证据、必须保留原话、编辑锚点、内容已确认边界、semantic-map（需更新 anchor） |
| gzh-design | 排版、格式转换、组件装配 | 需要平台格式转换 | article.md + semantic-map.yaml + handoff |
| publisher | 多平台发布 | 用户要求直接发布 | 完成稿 + 格式标记 |

## 给去 AI 味 Skill（humanizer）

传递：核心观点、不可删证据、必须保留的作者原话、编辑锚点、内容已确认边界、semantic-map.yaml。

去 AI 味过程中不得改变事实、立场和论证关系。

### humanizer 后 anchor 失效处理

如果调用 humanizer 修改了正文：

1. humanizer 修改 article.md
2. **必须更新 semantic-map.yaml 中失效的 `source_anchor.exact_text`**
3. 重新运行 `scripts/validate_semantic_map.py` 确认所有 anchor 可定位
4. 然后才交给 gzh-design

**不得让 humanizer 修改正文后继续使用已失效的旧 anchor。**

链路顺序：

```
article.md → humanizer → 更新 semantic-map anchor → gzh-design → publisher
```

## 给排版 Skill（gzh-design）

传递：article.md + semantic-map.yaml + handoff 契约。

排版 Skill 根据 semantic-map 中的语义角色和候选组件选择具体组件，不需要重新猜测文章内容形态。

### Formatter 最终决定权（Phase 7）

1. **Writer 只声明语义角色和候选组件。** Writer 不指定具体组件、主题色或视觉样式。

2. **Formatter 根据以下因素最终选择组件：**
   - 目标平台
   - 用户主题
   - 内容长度
   - 组件兼容性
   - 视觉密度

3. **Formatter 可以选择 fallback。** 当候选组件不适合当前场景时，formatter 可以使用 fallback 角色。

4. **Formatter 不得：**
   - 编造缺失字段
   - 把普通段落强改成 FAQ
   - 把无时间顺序内容改成 timeline
   - 为凑组件重复正文
   - 改写核心观点、事实、数字或引用

5. **"支持所有组件"不等于"一篇文章使用所有组件"。** 一篇文章主要高级组件建议 3-6 个，短资讯 0-2 个。

6. **`force_all_components` 必须为 `false`。** 不允许强制使用所有组件。

7. **`formatter_has_final_choice` 必须为 `true`。** Formatter 拥有最终组件选择权。

8. **`prohibit_content_invention` 必须为 `true`。** 禁止编造内容。

9. **`prohibit_duplicate_full_content` 必须为 `true`。** 禁止同一信息完整复制到多个组件。

### semantic-map 规则

1. `article.md` 保持干净可读。
2. 语义信息放到独立的 `semantic-map.yaml`。
3. `source_anchor.exact_text` 必须能在 article.md 中定位。
4. `block_id` 必须唯一。
5. 未找到 anchor 时 formatter 必须降级，不得猜测。
6. semantic map 不得包含 HTML/CSS。
7. `preferred_theme` 可以为空；用户指定 Hammer 时才写 hammer。
8. 写作 Skill 不替用户自动固定主题。

## 未决项

未决事实、作者未确认立场和缺失经历必须显式保留，不得因进入下一环节而消失。

## 交接校验

交付前运行：

```bash
python scripts/validate_semantic_map.py \
  --article article.md \
  --semantic-map semantic-map.yaml \
  --formatter-root f:/AIXM/wxgzh/gzh-design-skill/
```

校验通过（0 ERROR）才可交付给 gzh-design。
