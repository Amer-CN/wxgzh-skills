# implementation-report.md
# zh-human-writing v1 — 实现报告

> 生成时间: 2026-07-14
> 执行 Agent: CatPaw (Step 09)
> 任务: 按照 Step 08 冻结架构，实现 zh-human-writing v1 候选版
> 状态: ✅ 实现完成

---

## 1. 实现概述

本次实现严格按照 Step 08 冻结的架构规格，在 `./work/step-09/zh-human-writing/` 目录下创建了完整的 Skill 结构。所有核心约束、路由、Profiles、模式包、工具脚本及测试资产均已实现。

---

## 2. 交付物清单

### 核心文件

| # | 文件 | 说明 | 状态 |
|---|------|------|------|
| 1 | `SKILL.md` | 核心入口，定义流程、参数及加载指引 | ✅ |
| 2 | `README.md` | 用户文档 | ✅ |
| 3 | `SOURCE-NOTES.md` | 来源声明（12 个来源项目，全部重新实现） | ✅ |
| 4 | `config/default.yaml` | 默认配置（参数、阈值、调整系数） | ✅ |

### core/ 目录（8 个文件）

| # | 文件 | 说明 | 状态 |
|---|------|------|------|
| 5 | `core/invariants.md` | 不可变硬约束（保护项 + 禁止项 + 回滚规则） | ✅ |
| 6 | `core/input-contract.md` | 输入合同（5 参数 + 7 组冲突处理） | ✅ |
| 7 | `core/routing.md` | 路由与操作权限表（3 strategy × 15 操作） | ✅ |
| 8 | `core/execution-flow.md` | 固定 9 步执行流程 | ✅ |
| 9 | `core/output-contract.md` | 输出合同（clean/diff/audit） | ✅ |
| 10 | `core/fidelity.md` | 保真机制规格（确定性检查 + warning） | ✅ |
| 11 | `core/workflow.md` | 工作流（execution-flow 别名） | ✅ |
| 12 | `core/constraints.md` | 核心约束（invariants 别名） | ✅ |

### profiles/ 目录（3 个文件）

| # | 文件 | 说明 | 状态 |
|---|------|------|------|
| 13 | `profiles/essay.md` | essay profile 边界 | ✅ |
| 14 | `profiles/technical.md` | technical profile 边界 | ✅ |
| 15 | `profiles/social.md` | social profile 边界 | ✅ |

### references/ 目录（7 个文件）

| # | 文件 | 说明 | 状态 |
|---|------|------|------|
| 16 | `references/patterns/hard-residue.md` | hard-residue 模式包（6 条模式） | ✅ |
| 17 | `references/patterns/strong-contextual.md` | strong-contextual 模式包（6 条模式） | ✅ |
| 18 | `references/patterns/advisory-only.md` | advisory-only 模式包（12 条模式） | ✅ |
| 19 | `references/protected-spans.md` | Protected Spans 定义（5 类保护项） | ✅ |
| 20 | `references/false-positive-protection.md` | 误杀防护规则（11 条） | ✅ |
| 21 | `references/domain-lexicon.yaml` | 核心术语词典（30+ 术语 + 命令） | ✅ |

### author/ 和 author-profile/ 目录（3 个文件）

| # | 文件 | 说明 | 状态 |
|---|------|------|------|
| 22 | `author/author-profile.template.md` | 作者 Profile 模板 | ✅ |
| 23 | `author/sample-manifest.template.yaml` | 样本清单模板 | ✅ |
| 24 | `author-profile/schema.md` | 作者 Profile Schema（9 字段） | ✅ |

### scripts/ 目录（3 个脚本）

| # | 文件 | 说明 | 状态 |
|---|------|------|------|
| 25 | `scripts/fidelity_guard.py` | 保真检查脚本（8 类确定性检查 + 4 类 warning） | ✅ |
| 26 | `scripts/change_report.py` | 变化统计脚本（字符/句/段统计 + 长度留存率） | ✅ |
| 27 | `scripts/pattern_audit.py` | 模式审计脚本（3 级检测 + profile 调整） | ✅ |

### tests/ 目录（7 个文件 + 6 个 fixtures）

| # | 文件 | 说明 | 状态 |
|---|------|------|------|
| 28 | `tests/run_tests.py` | 自动化测试运行器（36 条测试） | ✅ |
| 29 | `tests/must-preserve/fixtures.yaml` | must-preserve 测试 fixtures | ✅ |
| 30 | `tests/must-edit/fixtures.yaml` | must-edit 测试 fixtures | ✅ |
| 31 | `tests/fidelity-stress/fixtures.yaml` | fidelity-stress 测试 fixtures | ✅ |
| 32 | `tests/profile-boundaries/fixtures.yaml` | profile-boundaries 测试 fixtures | ✅ |
| 33 | `tests/long-form/fixtures.yaml` | long-form 测试 fixtures | ✅ |
| 34 | `tests/unsupported-fiction/fixtures.yaml` | unsupported-fiction 测试 fixtures | ✅ |

---

## 3. 实现原则遵守情况

| 原则 | 要求 | 实际状态 |
|------|------|---------|
| 严格遵循 Step 08 冻结架构 | 不偏离、不增量、不遗漏 | ✅ 所有架构规格文件已实现 |
| 逐项保真检查 | 不使用综合分 | ✅ fidelity_guard.py 每项独立判定 |
| 分层加载 | 核心始终加载，参考按需加载 | ✅ SKILL.md 加载指引已定义 |
| 不猜测来源 | source 由用户提供 | ✅ input-contract.md 明确规定 |
| 不制造人味 | 删除模板化表达，不虚构内容 | ✅ invariants.md 禁止项已定义 |
| profile 约束 | 编辑行为受 profile 边界约束 | ✅ 3 个 profile 文件 + pattern_audit.py 实现 profile 调整系数 |
| Fiction 拒绝 | 明确拒绝，不降级 | ✅ input-contract.md CR-6 + 测试 UF-001/UF-002 |
| 不复制外部内容 | 全部重新实现 | ✅ SOURCE-NOTES.md 已声明 |
| 阶段一先交付骨架 | 核心约束+保真审计+测试合同先于模式库 | ✅ 按实现顺序完成 |
| 禁止并行编辑 | 最终交付不超过候选版 | ✅ 标记为 v1 候选版 |

---

## 4. 脚本实现详情

### 4.1 fidelity_guard.py

- **提取器**：8 类（数字、日期、URL、代码块、行内代码、命令、路径、引用、用户 protected spans）
- **规范化**：数字（去千分位、统一百分号、去前导零）、日期（YYYY年M月D日 ↔ YYYY-MM-DD）、URL（去末尾斜杠、统一协议）
- **确定性比较器**：8 个（数字、日期、URL、代码、命令、路径、引用、用户 protected spans）
- **Warning 检查**：4 类（否定词、条件词、因果词、不确定程度词）
- **退出码**：0=pass, 1=warning, 2=fail, 3=error

### 4.2 change_report.py

- **统计**：字符数（含/不含空白）、句数、段落数
- **长度留存率**：strict(≥0.90), balanced(≥0.80), free(无下限)
- **删除句检测**：找出原文有但终稿没有的句子
- **Protected spans 变化检查**：数字、URL、代码、用户标记
- **退出码**：0=success, 3=error

### 4.3 pattern_audit.py

- **hard-residue 检测**：5 个模式组（模板占位符、AI自我标识、知识截止声明、聊天助手残留、AI来源参数）
- **strong-contextual 检测**：6 个模式组（无信息开场、导航、总结、无来源权威铺垫、连续同构结构、假互动）
- **advisory-only 检测**：7 个模式（不是…而是、先…再、从…到、破折号、反问、二人称、第一人称）
- **Profile 调整系数**：essay(×1.0), technical(×1.5), social(×2.0)
- **退出码**：0=pass, 2=fail, 3=error

---

## 5. 测试覆盖情况

### 6 类测试合同，共 36 条测试

| 测试类型 | 数量 | 覆盖内容 | 通过率 |
|---------|------|---------|--------|
| must-preserve | 10 | 数字、日期、URL、代码、千分位、百分比、protected spans | 10/10 ✅ |
| must-edit | 10 | 模板占位符、AI标识、知识截止、聊天残留、AI参数、pass/fail 退出码、advisory-only | 10/10 ✅ |
| fidelity-stress | 5 | 密集数字、数字变化、否定词、条件词、长度比例 | 5/5 ✅ |
| profile-boundaries | 6 | technical 步骤、essay 步骤、social 假互动、essay 假互动、technical 被动语态、social 短句 | 6/6 ✅ |
| long-form | 3 | strict 1.0、balanced 0.8、strict 不足 0.75 | 3/3 ✅ |
| unsupported-fiction | 2 | fiction 文本处理、fiction profile 拒绝 | 2/2 ✅ |
| **总计** | **36** | | **36/36 ✅** |

---

## 6. 实现过程中的 Bug 修复

### Bug 1: `tempfile.mkstemp` 参数错误

- **问题**：`run_tests.py` 中 `tempfile.mkstemp` 误用 `mode` 和 `encoding` 参数
- **修复**：移除不支持的参数，改用 `os.write(fd, text.encode('utf-8'))`

### Bug 2: 全角百分号 `％` 未处理

- **问题**：`fidelity_guard.py` 的 `extract_numbers` 正则未包含全角百分号 `％`
- **修复**：更新正则为 `r'\d[\d,]*\.?\d*[%‰％]?'`

### Bug 3: 数字前导零未规范化

- **问题**：`normalize_number` 未去除前导零，导致 "01" 和 "1" 被视为不同数字
- **修复**：增加 `re.sub(r'^0+(\d)', r'\1', n)` 去除前导零

### Bug 4: 日期独立年份重复提取

- **问题**：`extract_dates` 中 `\d{4}\s*年(?!度)` 从完整日期 "2024 年 1 月 15 日" 中额外提取了 "2024 年"，导致日期格式变化时误报
- **修复**：添加否定前瞻 `(?!\s*\d{1,2}\s*月)`，排除后跟月份的完整日期

---

## 7. 限制声明

- 编辑规则基于合成测试用例验证，未在真实大规模中文语料上独立验证
- 编辑结果应由作者人工审阅后再发布
- 本工具不判断文本是否 AI 生成
- v1 不支持 fiction 编辑
- v1 不实现 AI 概率、人味分、综合质量分

---

> 实现报告完毕。详细结构验证见 `structural-validation.md`，测试报告见 `unit-test-report.md`，偏差记录见 `implementation-deviations.md`。
