# references/patterns/advisory-only.md
# zh-human-writing v1 — advisory-only 模式包
# 这些模式在真人写作中也常见，不能单独触发自动修改。
# 只在 diff/audit 输出中作为建议列出。

---

## AO-001: "不是…而是…"

- **ID**: AO-001
- **问题**: 可能是二元对立结构壳
- **触发线索**: "不是…而是…"、"并非…而是…"(档72C-2 补)
- **合法情况**: 精确对比（"不是 A 而是 B"有实质对比内容）
- **升级机制**(档72C-2 §5): 同一段落内命中 ≥2 → 升级为 strong-contextual SC-007b(confidence=low,见 strong-contextual.md);单发只留 advisory
- **处理权限**: deny auto-modify
- **language_origin**: language_general
- **来源说明**: 重新实现，通用模式

---

## AO-002: "先…再…"

- **ID**: AO-002
- **问题**: 可能是阶段递进结构壳
- **触发线索**: "先…再…"
- **合法情况**: 步骤说明（技术文档中的步骤说明是合法的）
- **处理权限**: deny auto-modify
- **language_origin**: language_general
- **来源说明**: 重新实现，通用模式

---

## AO-003: "从…到…"

- **ID**: AO-003
- **问题**: 可能是范围描述结构壳
- **触发线索**: "从…到…"
- **合法情况**: 范围描述、历史演变
- **处理权限**: deny auto-modify
- **language_origin**: language_general
- **来源说明**: 重新实现，通用模式

---

## AO-004: 破折号

- **ID**: AO-004
- **问题**: 可能过度使用破折号
- **触发线索**: "——"
- **合法情况**: 中文破折号有合法用途（补充说明、转折）
- **处理权限**: deny auto-modify
- **language_origin**: chinese_specific
- **来源说明**: 重新实现

---

## AO-005:

- **状态**: **未实现，Batch 3**: 总分总结构检测在代码中无落点(72C-1 M-2a)。 三段式

- **ID**: AO-005
- **问题**: 可能是总分总结构
- **触发线索**: 总分总结构
- **合法情况**: 常见文章结构
- **处理权限**: deny auto-modify
- **language_origin**: language_general
- **来源说明**: 重新实现，通用模式

---

## AO-006: 反问

- **ID**: AO-006
- **问题**: 可能是公式化挑战结构
- **触发线索**: "难道不是吗？"、"不是吗？"
- **状态**: 代码已实现"难道…[吗呢？?]"分支;"不是吗？"独立变体**未实现**（72C-1 M-2a,留 Batch 3）
- **合法情况**: 修辞手段
- **处理权限**: deny auto-modify
- **language_origin**: language_general
- **来源说明**: 重新实现，通用模式

---

## AO-007: 二人称

- **ID**: AO-007
- **问题**: 可能是假互动
- **触发线索**: "你"
- **合法情况**: 社媒中常态
- **处理权限**: deny auto-modify
- **language_origin**: language_general
- **来源说明**: 重新实现，通用模式

---

## AO-008:

- **状态**: **作废，由统计层取代（Batch 1 §4）**: 句长相近改由统计层指标负责(72C-1 M-2a)。 句长相近

- **ID**: AO-008
- **问题**: 连续句长差异小
- **触发线索**: 连续句子长度相近
- **合法情况**: 可能是风格设计
- **处理权限**: deny auto-modify
- **language_origin**: language_general
- **来源说明**: 重新实现

---

## AO-009:

- **状态**: **作废，由统计层取代（Batch 1 §4）**: 段长相近改由统计层指标负责(72C-1 M-2a)。 段长相近

- **ID**: AO-009
- **问题**: 连续段长差异小
- **触发线索**: 连续段落长度相近
- **合法情况**: 可能是结构设计
- **处理权限**: deny auto-modify
- **language_origin**: language_general
- **来源说明**: 重新实现

---

## AO-010:

- **状态**: **作废，由统计层取代（Batch 1 §4）**: 普通连接词（因此/所以/然而/但是）是正常语法成分,不列入检测(72C-1 M-2a)。 普通连接词

- **ID**: AO-010
- **问题**: 使用普通连接词
- **触发线索**: "因此"、"所以"、"然而"、"但是"
- **合法情况**: 正常语法成分
- **处理权限**: deny auto-modify
- **language_origin**: language_general
- **来源说明**: 重新实现

---

## AO-011: 第一人称

- **ID**: AO-011
- **问题**: 使用第一人称
- **触发线索**: "我"、"我们"
- **合法情况**: 作者声音
- **处理权限**: deny auto-modify
- **language_origin**: language_general
- **来源说明**: 重新实现

---

## AO-012:

- **状态**: **未实现，Batch 3**: 对仗和重复检测在代码中无落点(72C-1 M-2a)。 对仗和重复

- **ID**: AO-012
- **问题**: 工整对仗
- **触发线索**: 对仗结构
- **合法情况**: 修辞手段
- **处理权限**: deny auto-modify
- **language_origin**: language_general
- **来源说明**: 重新实现

---

## 动作权限汇总

| 级别 | preserve | balance | rebuild |
|------|---------|---------|---------|
| advisory-only | deny auto-modify | deny auto-modify | deny auto-modify |

advisory-only 不影响 pass/fail，不得自动改写。
只在 diff/audit 输出中作为建议列出。
