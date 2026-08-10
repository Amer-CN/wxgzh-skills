# core/execution-flow.md
# zh-human-writing v1 — 执行流程

---

## 固定 9 步

### 步骤 1：读取输入合同

- 加载 SKILL.md 和 core/ 文件
- 解析 source、strategy、profile、length_retention、output
- 处理参数冲突（CR-1 到 CR-7）

### 步骤 2：提取 protected spans

- 加载 references/protected-spans.md、false-positive-protection.md、domain-lexicon.yaml
- 从原文中提取所有保护项
- 标记用户显式 protected spans

### 步骤 3：识别权限

- 加载 config/default.yaml 的 pattern_thresholds(profile 阈值真源;profiles/*.md 已删除,OBS-232)
- 根据 source 确认 strategy（如用户未指定）
- 根据 strategy 确认操作权限表

### 步骤 4：诊断真实表达问题

- 按诊断结果按需加载 pattern pack
- 识别 hard-residue（单次出现即标记）
- 识别 strong-contextual（聚集 ≥2 才标记）
- 识别 advisory-only（只在 diff/audit 时列出）

### 步骤 5：执行最小必要编辑

- 按操作权限表执行编辑
- 每处改动必须能说出"原文这里真正打绊了"
- 不执行全局禁止项

### 步骤 6：独立做双向保真审计

- 正向审计（原文 → 编辑后）：检查 protected spans 是否保留
- 反向审计（编辑后 → 原文）：检查是否引入原文没有的内容
- 审计独立于改写，不改写文本

### 步骤 7：硬约束失败则局部回滚

- 确定性检查 fail → 局部回滚
- warning → 加入待确认项
- 不自动重试

### 步骤 8：最多做一次高置信残留检查

- 只检查 hard-residue 是否残留
- 不检查 advisory-only
- 不改写
- 不进入循环

### 步骤 9：按 clean/diff/audit 输出

- clean：只输出终稿
- diff：终稿 + 关键改动 + 保真警告 + 待确认项 + 改动统计
- audit：诊断报告，最多 5 个问题

---

## 禁止的流程变体

- 不实现无限循环
- 不实现评分驱动迭代
- 不实现多轮改写（ouroboros）
- 不实现第二轮自由改写
- 不实现"改写→评分→低分→再改写"循环
- 残留检查最多一次，且只检查高置信模式
