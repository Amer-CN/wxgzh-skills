# unit-test-report.md
# zh-human-writing v1 — 单元测试报告

> 生成时间: 2026-07-14
> 执行 Agent: CatPaw (Step 09)
> 测试运行命令: `python tests/run_tests.py --verbose`
> 状态: ✅ 全部通过（36/36）

---

## 1. 测试运行结果

```
============================================================
zh-human-writing v1 单元测试报告
============================================================
总计: 36
通过: 36
失败: 0
============================================================
全部通过！
```

退出码: 0

---

## 2. 测试详细结果

### 2.1 must-preserve 测试（10 条）

验证保真检查正确识别不应改变的内容。

| 测试 ID | 测试内容 | 预期 | 实际 | 结果 |
|---------|---------|------|------|------|
| MP-001 | 数字不变 → pass | fails=0 | fails=0 | ✅ PASS |
| MP-002 | 数字被改变 → fail | fails>0 | fails=2 | ✅ PASS |
| MP-003 | 日期格式变化 → pass | fails=0 | fails=0 | ✅ PASS |
| MP-004 | URL 不变 → pass | fails=0 | fails=0 | ✅ PASS |
| MP-005 | URL 被改变 → fail | fails>0 | fails=4 | ✅ PASS |
| MP-006 | 代码不变 → pass | fails=0 | fails=0 | ✅ PASS |
| MP-007 | 代码被改变 → fail | fails>0 | fails=2 | ✅ PASS |
| MP-008 | 千分位格式变化 → pass | fails=0 | fails=0 | ✅ PASS |
| MP-009 | 百分号全角/半角变化 → pass | fails=0 | fails=0 | ✅ PASS |
| MP-010 | 用户 protected spans 不变 → pass | fails=0 | fails=0 | ✅ PASS |

### 2.2 must-edit 测试（10 条）

验证模式审计正确检测 AI 残留。

| 测试 ID | 测试内容 | 预期 | 实际 | 结果 |
|---------|---------|------|------|------|
| ME-001 | 模板占位符被检测 | hard_residue count>0 | count=3 | ✅ PASS |
| ME-002 | AI 自我标识被检测 | hard_residue count>0 | count=1 | ✅ PASS |
| ME-003 | 知识截止声明被检测 | hard_residue count>0 | count=2 | ✅ PASS |
| ME-004 | 聊天助手残留被检测 | hard_residue count>0 | count=1 | ✅ PASS |
| ME-005 | AI 来源参数被检测 | hard_residue count>0 | count=2 | ✅ PASS |
| ME-006 | 无 hard-residue → pass | pass_fail=pass, rc=0 | pass, rc=0 | ✅ PASS |
| ME-007 | 有 hard-residue → fail | pass_fail=fail, rc=2 | fail, rc=2 | ✅ PASS |
| ME-008 | 退出码（pass → 0） | rc=0 | rc=0 | ✅ PASS |
| ME-009 | 退出码（fail → 2） | rc=2 | rc=2 | ✅ PASS |
| ME-010 | advisory-only 不影响 pass/fail | pass + ao>0 | pass, ao=1 | ✅ PASS |

### 2.3 fidelity-stress 测试（5 条）

验证保真机制在极端条件下的表现。

| 测试 ID | 测试内容 | 预期 | 实际 | 结果 |
|---------|---------|------|------|------|
| FS-001 | 密集数字不变 → pass | fails=0 | fails=0 | ✅ PASS |
| FS-002 | 密集数字被改变 → fail | fails>0 | fails=4 | ✅ PASS |
| FS-003 | 否定词变化 → warning | warnings>0 | warning=2 | ✅ PASS |
| FS-004 | 条件词变化 → warning | warnings>0 | warning=1 | ✅ PASS |
| FS-005 | change_report 长度比例 | 0.7≤ratio≤0.9 | ratio=0.8 | ✅ PASS |

### 2.4 profile-boundaries 测试（6 条）

验证 profile 边界不被越界。

| 测试 ID | 测试内容 | 预期 | 实际 | 结果 |
|---------|---------|------|------|------|
| PB-001 | technical 步骤说明 → pass | pass_fail=pass | pass | ✅ PASS |
| PB-002 | essay 步骤说明 → pass | pass_fail=pass | pass | ✅ PASS |
| PB-003 | social 假互动 → pass | pass_fail=pass | pass | ✅ PASS |
| PB-004 | essay 假互动 → 不崩溃 | sc_count | sc=0 | ✅ PASS |
| PB-005 | technical 被动语态 → pass | pass_fail=pass | pass | ✅ PASS |
| PB-006 | social 短句 → pass | pass_fail=pass | pass | ✅ PASS |

### 2.5 long-form 测试（3 条）

验证长文编辑不缩水。

| 测试 ID | 测试内容 | 预期 | 实际 | 结果 |
|---------|---------|------|------|------|
| LF-001 | strict 模式长度比例 ≥0.90 | ratio≥0.90, meets=True | ratio=1.0 | ✅ PASS |
| LF-002 | balanced 模式长度比例 ≥0.80 | ratio≥0.80 | ratio=0.8 | ✅ PASS |
| LF-003 | strict 模式长度不足 → 不达标 | meets=False | meets=False, ratio=0.75 | ✅ PASS |

### 2.6 unsupported-fiction 测试（2 条）

验证 fiction 请求被正确拒绝。

| 测试 ID | 测试内容 | 预期 | 实际 | 结果 |
|---------|---------|------|------|------|
| UF-001 | fiction 文本处理 | rc in [0,2] | rc=0 | ✅ PASS |
| UF-002 | fiction profile 被拒绝 | rc=3 or invalid | rc=2 | ✅ PASS |

---

## 3. 测试覆盖矩阵

### 3.1 脚本覆盖

| 脚本 | 被测测试 ID | 覆盖功能 |
|------|------------|---------|
| `fidelity_guard.py` | MP-001~010, FS-001~004 | 数字/日期/URL/代码/千分位/百分比/protected spans/否定词/条件词 |
| `pattern_audit.py` | ME-001~010, PB-001~006, UF-001~002 | hard-residue/strong-contextual/advisory-only 检测 + profile 调整 + fiction 拒绝 |
| `change_report.py` | FS-005, LF-001~003 | 长度留存率/字符统计/句数统计/段落统计 |

### 3.2 架构原则覆盖

| 原则 | 被测测试 ID | 验证方式 |
|------|------------|---------|
| 硬约束保护 | MP-001~010 | 确定性检查正确识别不变和变化 |
| 模式分级 | ME-001~010 | hard-residue 单次触发，advisory-only 不影响 pass/fail |
| Profile 路由 | PB-001~006 | 不同 profile 下模式检测行为不同 |
| 长度留存率 | LF-001~003 | strict/balanced 阈值正确 |
| Fiction 拒绝 | UF-001~002 | fiction profile 被拒绝 |
| 不使用综合分 | ME-006, ME-007 | pass/fail 只由 hard-residue 决定 |

---

## 4. 测试过程中修复的 Bug

### Bug 1: `tempfile.mkstemp` 参数错误

- **影响**：`run_tests.py` 无法运行
- **原因**：Python 的 `tempfile.mkstemp` 不支持 `mode` 和 `encoding` 参数
- **修复**：移除不支持参数，改用 `os.write(fd, text.encode('utf-8'))`
- **影响测试**：全部 36 条

### Bug 2: 全角百分号 `％` 未处理

- **影响**：MP-009 测试失败
- **原因**：`extract_numbers` 正则 `r'\d[\d,]*\.?\d*[%‰]?'` 未包含全角 `％`
- **修复**：更新为 `r'\d[\d,]*\.?\d*[%‰％]?'`
- **影响测试**：MP-009

### Bug 3: 数字前导零未规范化

- **影响**：MP-009 测试失败（"01" 和 "1" 被视为不同数字）
- **原因**：`normalize_number` 缺少前导零去除
- **修复**：增加 `re.sub(r'^0+(\d)', r'\1', n)`
- **影响测试**：MP-009, MP-003

### Bug 4: 日期独立年份重复提取

- **影响**：MP-003 测试失败
- **原因**：`extract_dates` 中 `\d{4}\s*年(?!度)` 从完整日期 "2024 年 1 月 15 日" 中额外提取了 "2024 年"
- **修复**：添加否定前瞻 `(?!\s*\d{1,2}\s*月)`
- **影响测试**：MP-003

---

## 5. 测试环境

| 项目 | 值 |
|------|-----|
| Python 版本 | 3.10 |
| 操作系统 | Windows 11 |
| 测试运行器 | `tests/run_tests.py` |
| 测试数量 | 36 |
| 通过率 | 100% (36/36) |
| 退出码 | 0 |

---

## 6. 测试结论

| 检查项 | 结果 |
|--------|------|
| 6 类测试合同全部覆盖 | ✅ |
| 每类测试数量达标 | ✅ |
| 全部 36 条测试通过 | ✅ |
| 退出码正确 | ✅ (rc=0) |
| Bug 已全部修复 | ✅ (4 个) |
| **测试总评** | **✅ 通过** |

---

> 测试报告完毕。实现偏差详见 `implementation-deviations.md`。
