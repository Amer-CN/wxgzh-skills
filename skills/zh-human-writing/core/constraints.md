# core/constraints.md
# zh-human-writing v1 — 核心约束（invariants 的别名文件）
# 内容与 core/invariants.md 一致，参见 core/invariants.md

参见 `core/invariants.md`。

核心约束包括：

1. **必须保护的内容**：事实性、技术性、语义性、作者性内容
2. **禁止的动作**：内容捏造、伪装、评分、检测、加载类禁止
3. **回滚规则**：硬约束失败 → 局部回滚
4. **不使用综合分**：每项独立判定
5. **执行流程约束**：固定 9 步
6. **advisory-only 约束**：不得单独触发自动修改

完整内容见 `core/invariants.md`。
