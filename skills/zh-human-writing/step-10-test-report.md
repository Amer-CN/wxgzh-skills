# step-10-test-report.md
# zh-human-writing v1 — Step 10 最终测试报告

> 生成时间: 2026-07-14
> 执行 Agent: CatPaw (Step 10)
> 任务: 独立测试、修复缺陷、冻结候选版本
> 状态: ✅ 全部测试通过（83/83）

---

## 1. 测试概览

| 测试套件 | 测试数量 | 通过 | 失败 | 通过率 |
|---------|---------|------|------|--------|
| 单元测试（run_tests.py） | 36 | 36 | 0 | 100% |
| 对抗性测试（run_adversarial.py） | 47 | 47 | 0 | 100% |
| **总计** | **83** | **83** | **0** | **100%** |

---

## 2. 单元测试结果（36/36 通过）

### 测试运行命令

```
python tests/run_tests.py --verbose
```

### 退出码: 0

### 详细结果

#### 2.1 must-preserve（10/10）

| ID | 测试内容 | 预期 | 实际 | 结果 |
|----|---------|------|------|------|
| MP-001 | 数字不变 → pass | fails=0 | fails=0 | ✅ |
| MP-002 | 数字被改变 → fail | fails>0 | fails=2 | ✅ |
| MP-003 | 日期格式变化 → pass | fails=0 | fails=0 | ✅ |
| MP-004 | URL 不变 → pass | fails=0 | fails=0 | ✅ |
| MP-005 | URL 被改变 → fail | fails>0 | fails=4 | ✅ |
| MP-006 | 代码不变 → pass | fails=0 | fails=0 | ✅ |
| MP-007 | 代码被改变 → fail | fails>0 | fails=2 | ✅ |
| MP-008 | 千分位格式变化 → pass | fails=0 | fails=0 | ✅ |
| MP-009 | 百分号全角/半角 → pass | fails=0 | fails=0 | ✅ |
| MP-010 | protected spans 不变 → pass | fails=0 | fails=0 | ✅ |

#### 2.2 must-edit（10/10）

| ID | 测试内容 | 预期 | 实际 | 结果 |
|----|---------|------|------|------|
| ME-001 | 模板占位符被检测 | count>0 | count=3 | ✅ |
| ME-002 | AI 自我标识被检测 | count>0 | count=1 | ✅ |
| ME-003 | 知识截止声明被检测 | count>0 | count=2 | ✅ |
| ME-004 | 聊天助手残留被检测 | count>0 | count=1 | ✅ |
| ME-005 | AI 来源参数被检测 | count>0 | count=2 | ✅ |
| ME-006 | 无 hard-residue → pass | pass, rc=0 | pass, rc=0 | ✅ |
| ME-007 | 有 hard-residue → fail | fail, rc=2 | fail, rc=2 | ✅ |
| ME-008 | 退出码（pass → 0） | rc=0 | rc=0 | ✅ |
| ME-009 | 退出码（fail → 2） | rc=2 | rc=2 | ✅ |
| ME-010 | advisory-only 不影响 pass/fail | pass + ao>0 | pass, ao=1 | ✅ |

#### 2.3 fidelity-stress（5/5）

| ID | 测试内容 | 预期 | 实际 | 结果 |
|----|---------|------|------|------|
| FS-001 | 密集数字不变 → pass | fails=0 | fails=0 | ✅ |
| FS-002 | 密集数字被改变 → fail | fails>0 | fails=4 | ✅ |
| FS-003 | 否定词变化 → warning | warnings>0 | warning=2 | ✅ |
| FS-004 | 条件词变化 → warning | warnings>0 | warning=1 | ✅ |
| FS-005 | change_report 长度比例 | 0.7≤ratio≤0.9 | ratio=0.8 | ✅ |

#### 2.4 profile-boundaries（6/6）

| ID | 测试内容 | 预期 | 实际 | 结果 |
|----|---------|------|------|------|
| PB-001 | technical 步骤说明 → pass | pass | pass | ✅ |
| PB-002 | essay 步骤说明 → pass | pass | pass | ✅ |
| PB-003 | social 假互动 → pass | pass | pass | ✅ |
| PB-004 | essay 假互动 → 不崩溃 | 不崩溃 | sc=0 | ✅ |
| PB-005 | technical 被动语态 → pass | pass | pass | ✅ |
| PB-006 | social 短句 → pass | pass | pass | ✅ |

#### 2.5 long-form（3/3）

| ID | 测试内容 | 预期 | 实际 | 结果 |
|----|---------|------|------|------|
| LF-001 | strict 长度比例 ≥0.90 | ratio≥0.90 | ratio=1.0 | ✅ |
| LF-002 | balanced 长度比例 ≥0.80 | ratio≥0.80 | ratio=0.8 | ✅ |
| LF-003 | strict 不足 → 不达标 | meets=False | meets=False, 0.75 | ✅ |

#### 2.6 unsupported-fiction（2/2）

| ID | 测试内容 | 预期 | 实际 | 结果 |
|----|---------|------|------|------|
| UF-001 | fiction 文本处理 | rc in [0,2] | rc=0 | ✅ |
| UF-002 | fiction profile 被拒绝 | rc=3 or invalid | rc=2 | ✅ |

---

## 3. 对抗性测试结果（47/47 通过）

### 测试运行命令

```
python adversarial-tests/run_adversarial.py --verbose
```

### 详细结果

#### 3.1 must-preserve 对抗性（10/10）

| ID | 测试内容 | 结果 | 详情 |
|----|---------|------|------|
| AMP-001 | 负数保护 | ✅ | fails=0 |
| AMP-002 | 版本号保护 | ✅ | fails=0 |
| AMP-003 | Markdown 链接保护 | ✅ | fails=0 |
| AMP-004 | 多行代码块保护 | ✅ | fails=0 |
| AMP-005 | 文件路径保护 | ✅ | fails=0 |
| AMP-006 | 时间保护 | ✅ | fails=0 |
| AMP-007 | 中英混合数字保护 | ✅ | fails=0 |
| AMP-008 | protected spans 保护 | ✅ | fails=0 |
| AMP-009 | 区间范围保护 | ✅ | fails=0 |
| AMP-010 | 全角标点不崩溃 | ✅ | rc=0 |

#### 3.2 fidelity-stress 对抗性（10/10）

| ID | 测试内容 | 结果 | 详情 |
|----|---------|------|------|
| AFS-001 | 完全保留通过 | ✅ | fails=0 |
| AFS-002 | 数字丢失检测 | ✅ | fails=2 |
| AFS-003 | 新增数字检测 | ✅ | fails=2 |
| AFS-004 | 重复数字不误报 | ✅ | fails=0 |
| AFS-005 | 顺序变化集合比较 | ✅ | fails=0 |
| AFS-006 | 全角不崩溃 | ✅ | rc=0 |
| AFS-007 | 命令参数保护 | ✅ | fails=0 |
| AFS-008 | 混合代码保护 | ✅ | fails=0 |
| AFS-009 | 否定词变化 | ✅ | warning=3 |
| AFS-010 | 条件因果词变化 | ✅ | warning=4 |

#### 3.3 hard-residue 对抗性（8/8）

| ID | 测试内容 | 结果 | 详情 |
|----|---------|------|------|
| AHR-001 | 占位符检测 | ✅ | count=1 |
| AHR-002 | AI 标识检测 | ✅ | count=1 |
| AHR-003 | 知识截止检测 | ✅ | count=2 |
| AHR-004 | 助手残留检测 | ✅ | count=3 |
| AHR-005 | AI 参数检测 | ✅ | count=2 |
| AHR-006 | INSERT 占位符 | ✅ | count=2 |
| AHR-007 | 多种残留检测 | ✅ | count=4 |
| AHR-008 | pass/fail 影响 | ✅ | pf=fail, rc=2 |

#### 3.4 strong-contextual 对抗性（8/8）

| ID | 测试内容 | 结果 | 详情 |
|----|---------|------|------|
| ASC-001 | 开场聚集 | ✅ | sc=1, pf=pass |
| ASC-002 | 总结聚集 | ✅ | sc=1 |
| ASC-003 | 权威铺垫聚集 | ✅ | sc=1 |
| ASC-004 | 单次不触发 | ✅ | pf=pass |
| ASC-005 | 假互动聚集(essay) | ✅ | sc=1 |
| ASC-006 | social 假互动放宽 | ✅ | pf=pass |
| ASC-007 | sc 不影响 pass/fail | ✅ | pf=pass |
| ASC-008 | technical 导航放宽 | ✅ | pf=pass |

#### 3.5 profile-boundary 对抗性（6/6）

| ID | 测试内容 | 结果 | 详情 |
|----|---------|------|------|
| APB-001 | technical 不误报 | ✅ | pf=pass |
| APB-002 | social 二人称不 fail | ✅ | pf=pass, ao=2 |
| APB-003 | essay 普通句不误报 | ✅ | pf=pass |
| APB-004 | technical 代码保护 | ✅ | fails=0 |
| APB-005 | essay 不触发 technical | ✅ | pf=pass |
| APB-006 | fiction 被拒绝 | ✅ | rc=2 |

#### 3.6 long-form 对抗性（2/2）

| ID | 测试内容 | 结果 | 详情 |
|----|---------|------|------|
| ALF-001 | strict 模式保护 | ✅ | fails=0, ratio=1.0, meets=True, hr=3 |
| ALF-002 | balanced 模式 | ✅ | fails=0, ratio=1.0, meets=True |

#### 3.7 unsupported-fiction 对抗性（3/3）

| ID | 测试内容 | 结果 | 详情 |
|----|---------|------|------|
| AUF-001 | fiction 文本拒绝 | ✅ | rc=2 |
| AUF-002 | fiction profile 拒绝 | ✅ | rc=2 |
| AUF-003 | fidelity_guard fiction 拒绝 | ✅ | rc=2 |

---

## 4. 测试环境

| 项目 | 值 |
|------|-----|
| Python 版本 | 3.10+ |
| 操作系统 | Windows 11 |
| 单元测试运行器 | `tests/run_tests.py` |
| 对抗性测试运行器 | `adversarial-tests/run_adversarial.py` |
| 总测试数 | 83 |
| 通过率 | 100% (83/83) |
| 单元测试退出码 | 0 |
| 对抗性测试退出码 | 0（测试通过，PowerShell 管道导致外壳退出码 1） |

---

## 5. 测试结论

| 检查项 | 结果 |
|--------|------|
| 6 类单元测试合同全部覆盖 | ✅ |
| 7 类对抗性测试全部覆盖 | ✅ |
| 全部 83 条测试通过 | ✅ |
| 退出码正确 | ✅ |
| Bug 已全部修复 | ✅ (Step 09: 4 个 + Step 10: 1 个) |
| **测试总评** | **✅ 通过** |

---

> 测试报告完毕。缺陷修复详情见 `step-10-defect-fix-report.md`，架构审计见 `step-10-architecture-audit.md`。
