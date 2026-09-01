# references/patterns/ai-tone.md

# 77R/OBS-342 — 语料验证 AI-tone 六族（只读审计层）

> 来源：[larashero3-dotcom/lieflat-less-ai-tone](https://github.com/larashero3-dotcom/lieflat-less-ai-tone)
> Pin：`27d29232f10124db904ca9c0536d0b67cb3b2833`
> License：MIT（Copyright (c) 2026 shiujan）
> 接入方式：上游规则与算子口径定点移植到 `pattern_audit.py`，不整体复制仓库，不引入上游语料。
> 输出位置：`pattern_audit --check-level full --output json` 的顶层 `ai_tone` 段。
> 红线：`ai_tone` 只做 review-only 信号；`fidelity_guard` 与既有 hard/strong/advisory 优先级不变。

## 六族算子

| ID | 家族 | 触发口径 | 最小改法 |
|---|---|---|---|
| LT-001 | 段首零回指评论 | 非首段以评论语开头，且缺少“这/那/其/此”等回指 | 补回指词或点明对象；不动段落顺序 |
| LT-002 | 拟人化喻体 | 像/相当于 + 理想化职业人格 + 褒义修饰 | 改成实际机制；不删普通比喻 |
| LT-003 | 起首语 | 说白了 / 说穿了 / 先说结论 | 删除提示语，直接给判断 |
| LT-004 | 序数词通篇编号小标题 | 连续 3 个以上编号小标题 | 只删编号；标题文字/顺序/层级不动 |
| LT-005 | 相邻句同构 + 顿号过密 | 相邻两句结构指纹一致；或单分句顿号串 >=3 项 | 打散其中一句句法或压缩罗列；Markdown 列表豁免 |
| LT-006 | 译文句式 | 过长前置定语 / “的”连用 / 当…时 / 话题壳 / 句首连接词 / “这意味着”复述 | 按五式最小改写；未列出的“翻译腔”不改 |

## 翻案腔政策

- `SC-007a` / `AO-001` 仍是上下文判断，不是字面一刀切。
- `balance` 策略下，确认是“先虚立误解再推翻”的姿势时，可改写为直陈句。
- 判定看动作，不限“不是……而是……”字面；正常分类、澄清和真实自我修正保留。

## DO-NOT 硬条款

禁止为了“人味”做以下动作：

1. 调句长或段长节奏；禁做 CV 类统计检查（上游 R=0.87 无区分力，KKKKhazix 也反向证实）。
2. 删设问、删比喻、删句内同构排比。
3. 补单字虚词。
4. 无证据地扩大六族触发范围。
5. 用 `ai_tone` 命中数替代 fidelity / hard-residue / strong gate。

## prose_craft 优先级

`handoff.prose_craft` 是蒸馏产物与作者真实风格，不是 AI 痕迹。它与通用去味规则冲突时，以 `prose_craft` 为准；fidelity、hard-residue 和事实保护仍不可越过。

## 误伤回捞位

新增反例先记录到本文：豁免段落、命中样本、保留理由、证据链接。只有 ≥20 条抽样支持后才考虑调整阈值；禁止凭单篇语感扩案。
