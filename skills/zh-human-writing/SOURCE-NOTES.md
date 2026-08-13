# SOURCE-NOTES.md
# zh-human-writing v1 — 来源声明

---

## 1. 各机制来源

| 机制 | 来源项目 | 借鉴方式 | 复制内容 |
|------|---------|---------|---------|
| Protected Spans | renwei | 吸收思想，重新实现 | 无 |
| 模式分级（hard/strong/advisory） | renwei, qu-ai-wei | 吸收思想，重新实现 | 无 |
| 双向保真审计 | renwei | 吸收思想，重新实现 | 无 |
| 误杀防护 | renwei, qu-ai-wei | 吸收思想，重新实现 | 无 |
| profile 路由 | renwei | 吸收思想，重新实现 | 无 |
| 作者 Profile Schema | renwei, writer-booster | 吸收思想，重新设计 schema | 无 |
| 聚集判断机制 | renwei | 吸收思想，重新实现 | 无 |
| 语言来源标记 | patina | 吸收思想，重新实现 | 无 |
| 不使用综合分 | stop-slop, slopbuster | 吸收思想 | 无 |
| 硬约束回滚 | renwei | 吸收思想，重新实现 | 无 |
| change_report 统计 | 通用 | 重新实现 | 无 |
| domain-lexicon | 通用 | 重新实现 | 无 |

---

## 2. 重新实现的机制

以下机制受外部项目启发但完全重新实现，未复制任何规则文本：

- **Protected Spans**：从 renwei 吸收"保护项逐字比对"的思想，实现方式为 Python 正则提取 + 逐字比对。
- **模式分级**：从 renwei 和 qu-ai-wei 吸收"分级检测"的思想，分级标准重新定义为"检测置信度和动作权限"而非"词频倍数"。
- **双向保真审计**：从 renwei 吸收"双向审计"的思想，实现方式为独立步骤执行，不要求跨模型。
- **误杀防护**：从 renwei 吸收"误杀防护"的思想，实现方式为横切层约束，不单独加载。
- **profile 路由**：从 renwei 吸收"按文体路由"的思想，profile 定义为 essay/technical/social 而非 README/release-note/forum/issue。
- **作者 Profile Schema**：从 renwei 和 writer-booster 吸收"作者样本约束"的思想，schema 重新设计为 9 字段 + 生成规则。

---

## 3. 只吸收思想的机制

以下机制只吸收了思想，未复制任何实现：

- **不使用综合分**：从 stop-slop 和 slopbuster 吸收"不评分"的思想，实现方式为独立检查项 pass/fail/warning。
- **语言来源标记**：从 patina 吸收"标记语言来源"的思想，实现方式为每条模式标记 language_origin。
- **硬约束回滚**：从 renwei 吸收"失败回滚"的思想，实现方式为局部回滚而非全局回滚。

---

## 4. 未复制的内容

- **未复制** qu-ai-wei 的 51 条规则
- **未复制** qu-ai-wei 的完整白名单
- **未复制** renwei 的六组检查清单
- **未复制** 任何外部项目的完整模式库
- **未复制** 任何外部项目的作者样本
- **未复制** 任何外部项目的大段文字

---

## 5. 许可证状态

| 项目 | 许可证状态 | 处理方式 |
|------|-----------|---------|
| renwei | custom-dual-license | 不复制规则文本，用不同表述重新实现。法律确认仍需进行。 |
| qu-ai-wei | 无 LICENSE 文件 | 仅作研究参考，不直接复制。 |
| writer-booster | 无 LICENSE 文件 | 仅作研究参考，不直接复制。 |
| ai-flavor-remover-light | 无 LICENSE 文件 | 仅作研究参考。 |
| humanizer-upstream | 无 LICENSE 文件 | 仅作研究参考。 |
| humanizer-zh | 无 LICENSE 文件 | 仅作研究参考。 |
| patina | 未确认 | 仅吸收思想，不复制内容。 |
| stop-slop | 可能含 Wikipedia CC BY-SA 内容 | 不直接复制，只借鉴机制。 |
| slopbuster | 未确认 | 仅吸收思想。 |
| shuorenhua | 未确认 | 仅作研究参考。 |

---

## 6. Blocked 能力为何没有实现

| 能力 | 排除原因 |
|------|---------|
| AI 概率 | v1 排除。不输出文本是 AI 生成的概率。 |
| 人味分 | v1 排除。不输出"人味"评分。 |
| 综合质量分 | v1 排除。不汇总为综合分。 |
| stylometry | v1 排除。不使用文体计量学。 |
| MATTR | v1 排除。不使用移动平均类型-令牌比。 |
| burstiness | v1 排除。不使用突发性指标。 |
| ouroboros | v1 排除。不使用多轮循环改写。 |
| 真人停手门检 | v1 排除。不自动判断文本是否真人写作。 |
| 自由 voice injection | v1 排除。不注入个性。 |
| fiction 编辑 | v1 排除。明确拒绝。 |
| 固定大型行业白名单 | v1 排除。只保留小型核心词典。 |
| 自动补全模板占位值 | v1 排除。不猜测模板占位符的"正确值"。 |
| MPS/语义锚点 | v1 排除。改为逐项检查。 |
| Floor + rollback | v1 排除。改为硬约束触发回滚。 |
| 5 层仲裁树 | v1 排除。改为模式分级。 |
| Personality 门控 | v1 排除。改为 profile 路由。 |
| Scene Packs | v1 排除。改为 essay/technical/social。 |
| SF/SNF 框架 | v1 排除。改为 6 类测试合同。 |
| Tier 词频分级 | v1 排除。改为置信度分级。 |
| 三档 Scope | v1 排除。改为 strategy + 权限表。 |
