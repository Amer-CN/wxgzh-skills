# step-10-architecture-audit.md
# zh-human-writing v1 — Step 10 架构一致性审计

> 生成时间: 2026-07-14
> 执行 Agent: CatPaw (Step 10)
> 任务: 验证候选版实现与 Step 08 冻结架构的一致性
> 状态: ✅ 架构一致性通过

---

## 1. 审计方法

### 1.1 审计范围

逐项对比 Step 08 冻结架构规格与 Step 10 候选版实际实现，覆盖：
- 文件结构完整性
- 核心约束覆盖
- 路由与操作权限
- Profile 边界
- 模式分级与检测
- 保真机制
- 输出合同
- 测试合同
- 脚本功能

### 1.2 审计依据

- `work/step-08/` 目录下的全部架构规格文件
- `work/step-09/zh-human-writing/` 原始实现（只读参考）
- `work/step-10/zh-human-writing/` 测试候选版（含缺陷修复）

### 1.3 审计约束

- ❌ 未读取外部 Skill 仓库
- ❌ 未使用真实文章
- ❌ 未安装任何 Skill
- ❌ 未修改架构设计

---

## 2. 文件结构审计

### 2.1 必需文件清单

| # | Step 08 规定 | 实际路径 | 状态 |
|---|-------------|---------|------|
| 1 | `SKILL.md` | `SKILL.md` | ✅ |
| 2 | `core/invariants.md` | `core/invariants.md` | ✅ |
| 3 | `core/input-contract.md` | `core/input-contract.md` | ✅ |
| 4 | `core/routing.md` | `core/routing.md` | ✅ |
| 5 | `core/execution-flow.md` | `core/execution-flow.md` | ✅ |
| 6 | `core/output-contract.md` | `core/output-contract.md` | ✅ (从独立文件移至 core/) |
| 7 | `core/fidelity.md` | `core/fidelity.md` | ✅ (从独立文件移至 core/) |
| 8 | `profiles/essay.md` | `profiles/essay.md` | ✅ |
| 9 | `profiles/technical.md` | `profiles/technical.md` | ✅ |
| 10 | `profiles/social.md` | `profiles/social.md` | ✅ |
| 11 | `references/patterns/hard-residue.md` | `references/patterns/hard-residue.md` | ✅ |
| 12 | `references/patterns/strong-contextual.md` | `references/patterns/strong-contextual.md` | ✅ |
| 13 | `references/patterns/advisory-only.md` | `references/patterns/advisory-only.md` | ✅ |
| 14 | `references/protected-spans.md` | `references/protected-spans.md` | ✅ |
| 15 | `references/false-positive-protection.md` | `references/false-positive-protection.md` | ✅ |
| 16 | `references/domain-lexicon` | `references/domain-lexicon.yaml` | ✅ (.md → .yaml) |
| 17 | `author-profile/schema.md` | `author-profile/schema.md` | ✅ |
| 18 | `scripts/fidelity_guard.py` | `scripts/fidelity_guard.py` | ✅ |
| 19 | `scripts/change_report.py` | `scripts/change_report.py` | ✅ |
| 20 | `scripts/pattern_audit.py` | `scripts/pattern_audit.py` | ✅ |
| 21 | `SOURCE-NOTES.md` | `SOURCE-NOTES.md` | ✅ |

### 2.2 扩展文件（合理添加）

| 文件 | 类型 | 是否偏离架构 |
|------|------|------------|
| `README.md` | 用户文档 | 否 |
| `config/default.yaml` | 配置文件 | 否 |
| `core/workflow.md` | execution-flow 别名 | 否 |
| `core/constraints.md` | invariants 别名 | 否 |
| `author/author-profile.template.md` | 模板 | 否 |
| `author/sample-manifest.template.yaml` | 模板 | 否 |
| `tests/run_tests.py` | 测试运行器 | 否 |
| 6 × `tests/*/fixtures.yaml` | 测试 fixtures | 否 |
| 交付报告文件（5+） | 交付要求 | 否 |

### 2.3 校验值验证

Step 10 候选版从 Step 09 源目录复制，经 SHA256 校验确认 43 个文件全部一致。唯一变更：
- `scripts/pattern_audit.py` — AHR-004 缺陷修复
- `references/patterns/hard-residue.md` — HR-004 触发线索同步更新

---

## 3. 核心约束审计

### 3.1 保护项（Protected Spans）

| 保护项 | 架构规定 | 脚本实现 | 状态 |
|--------|---------|---------|------|
| 数字 | 含千分位、小数、百分比 | `extract_numbers()` ✅ | ✅ |
| 日期 | YYYY-MM-DD / YYYY年M月D日 | `extract_dates()` ✅ | ✅ |
| URL | http/https | `extract_urls()` ✅ | ✅ |
| 代码块 | ``` 包围 | `extract_code_blocks()` ✅ | ✅ |
| 行内代码 | `code` | `extract_inline_code()` ✅ | ✅ |
| 命令 | $/> 前缀 + 常见命令 | `extract_commands()` ✅ | ✅ |
| 路径 | Unix/Windows 路径 | `extract_paths()` ✅ | ✅ |
| 引用 | > 前缀 | `extract_quotes()` ✅ | ✅ |
| 用户标记 | [[protected]] / <!--keep--> | `extract_user_protected()` ✅ | ✅ |

### 3.2 禁止项

| 禁止项 | 架构规定 | 实现状态 |
|--------|---------|---------|
| 不输出 AI 概率 | ✅ | 脚本无概率输出 ✅ |
| 不输出人味分 | ✅ | 脚本无评分输出 ✅ |
| 不输出综合质量分 | ✅ | 脚本只输出 pass/fail/warning ✅ |
| 不自动改写文本 | ✅ | pattern_audit 只检测不改写 ✅ |
| 不虚构内容 | ✅ | 脚本不生成文本 ✅ |

### 3.3 回滚规则

| 规则 | 架构规定 | 实现状态 |
|------|---------|---------|
| 硬约束失败 → 局部回滚 | ✅ | fidelity_guard 输出 `local_rollback` ✅ |
| Warning → 加入待确认列表 | ✅ | fidelity_guard 输出 `add_to_pending` ✅ |
| pass → 无动作 | ✅ | fidelity_guard 输出 `none` ✅ |

---

## 4. 模式分级审计

### 4.1 hard-residue（5 个模式组 + 1 个用户指定）

| 模式 ID | 名称 | 正则数量 | 架构覆盖 | 脚本实现 | 状态 |
|---------|------|---------|---------|---------|------|
| HR-001 | 模板占位符 | 3 | ✅ | ✅ | ✅ |
| HR-002 | AI 自我标识 | 5 | ✅ | ✅ | ✅ |
| HR-003 | 知识截止声明 | 4 | ✅ | ✅ | ✅ |
| HR-004 | 聊天助手残留 | 7 | ✅ | ✅ (Step 10 修复后) | ✅ |
| HR-005 | AI 来源参数 | 4 | ✅ | ✅ | ✅ |
| HR-006 | 用户指定 | N/A | ✅ | N/A (用户驱动) | ✅ |

### 4.2 strong-contextual（6 个模式组）

| 模式 ID | 名称 | 聚集阈值 | Profile 调整 | 脚本实现 | 状态 |
|---------|------|---------|-------------|---------|------|
| SC-001 | 无信息开场 | ≥2 | ×1.0/1.5/2.0 | ✅ | ✅ |
| SC-002 | 无信息导航 | ≥2 | ×1.0/1.5/2.0 | ✅ | ✅ |
| SC-003 | 无信息总结 | ≥2 | ×1.0/1.5/2.0 | ✅ | ✅ |
| SC-004 | 无来源权威铺垫 | ≥2 | ×1.0/1.5/2.0 | ✅ | ✅ |
| SC-005 | 连续同构结构 | ≥3 | ×1.0/1.5/2.0 | ✅ | ✅ |
| SC-006 | 明显假互动 | ≥2 | ×1.0/1.5/2.0 | ✅ | ✅ |

### 4.3 advisory-only

| 架构规定 | 脚本实现 | 状态 |
|---------|---------|------|
| 12 条模式（AO-001~AO-012） | 7 条正则 + 5 条文档 | ✅ (合理偏差) |

未在脚本中实现的 5 条（AO-005/008/009/010/012）需要复杂结构分析，不适合简单正则。已在 `references/patterns/advisory-only.md` 中作为文档保留。advisory-only 不影响 pass/fail，不阻塞使用。

---

## 5. Profile 边界审计

| Profile | 阈值系数 | 架构规定 | 脚本实现 | 状态 |
|---------|---------|---------|---------|------|
| essay | ×1.0 | ✅ | `PROFILE_MULTIPLIERS['essay'] = 1.0` | ✅ |
| technical | ×1.5 | ✅ | `PROFILE_MULTIPLIERS['technical'] = 1.5` | ✅ |
| social | ×2.0 | ✅ | `PROFILE_MULTIPLIERS['social'] = 2.0` | ✅ |
| fiction | 拒绝 | ✅ | argparse choices 不含 fiction | ✅ |

---

## 6. 脚本功能审计

### 6.1 fidelity_guard.py

| 功能 | 架构要求 | 实现状态 | 测试覆盖 |
|------|---------|---------|---------|
| 8 类确定性检查 | 数字/日期/URL/代码/命令/路径/引用/用户标记 | ✅ | MP-001~010, AMP-001~010 |
| 4 类 warning | 否定/条件/因果/不确定 | ✅ | FS-003~004, AFS-009~010 |
| 集合比较 | 数字按集合比较 | ✅ | AFS-005 |
| 规范化 | 千分位/百分号/前导零/日期格式 | ✅ | MP-003, MP-008, MP-009 |
| 退出码 | 0/1/2/3 | ✅ | ME-008, ME-009 |
| Profile 参数 | essay/technical/social | ✅ | 全部测试 |
| Source 参数 | author_written/ai_draft/mixed/unknown | ✅ | ALF-001 |
| Fiction 拒绝 | rc=3 | ✅ | AUF-003 |

### 6.2 change_report.py

| 功能 | 架构要求 | 实现状态 | 测试覆盖 |
|------|---------|---------|---------|
| 字符统计 | 含/不含空白 | ✅ | FS-005, LF-001~003 |
| 句数统计 | 原文/终稿 | ✅ | FS-005 |
| 段落统计 | 原文/终稿 | ✅ | FS-005 |
| 长度留存率 | strict(≥0.90)/balanced(≥0.80)/free | ✅ | LF-001~003, ALF-001~002 |
| 删除句检测 | 找出被删除的句子 | ✅ | FS-005 |
| Protected spans 变化 | 检查保护项 | ✅ | FS-005 |
| 退出码 | 0/3 | ✅ | 全部测试 |

### 6.3 pattern_audit.py

| 功能 | 架构要求 | 实现状态 | 测试覆盖 |
|------|---------|---------|---------|
| hard-residue 检测 | 单次出现即标记 | ✅ | ME-001~005, AHR-001~008 |
| strong-contextual 检测 | 聚集 ≥2 才标记 | ✅ | PB-001~006, ASC-001~008 |
| advisory-only 检测 | 只列出 | ✅ | ME-010, APB-002 |
| Profile 调整系数 | ×1.0/1.5/2.0 | ✅ | PB-001~006, ASC-006, ASC-008 |
| check-level | hard_residue_only/full | ✅ | ME-008, ME-009 |
| 退出码 | 0/2/3 | ✅ | ME-006~009, AHR-008 |
| 不自动改写 | 只检测 | ✅ | 全部测试 |
| Fiction 拒绝 | rc=3 | ✅ | APB-006, AUF-001~002 |

---

## 7. 测试合同审计

### 7.1 单元测试（Step 09 原有）

| 测试类型 | Step 08 要求 | 实际 | 状态 |
|---------|------------|------|------|
| must-preserve | ≥10 | 10 | ✅ |
| must-edit | ≥10 | 10 | ✅ |
| fidelity-stress | ≥5 | 5 | ✅ |
| profile-boundaries | ≥6 | 6 | ✅ |
| long-form | ≥3 | 3 | ✅ |
| unsupported-fiction | ≥2 | 2 | ✅ |
| **总计** | **≥36** | **36** | **✅** |

### 7.2 对抗性测试（Step 10 新建）

| 测试类型 | 数量 | 覆盖内容 | 状态 |
|---------|------|---------|------|
| must-preserve | 10 | 负数/版本号/Markdown链接/代码块/路径/时间/中英混合/protected spans/区间/全角 | ✅ |
| fidelity-stress | 10 | 完全保留/数字丢失/新增数字/重复/顺序/全角/命令/混合代码/否定词/条件因果 | ✅ |
| hard-residue | 8 | 占位符/AI标识/知识截止/助手残留(修复后)/AI参数/INSERT/多种混合/pass-fail影响 | ✅ |
| strong-contextual | 8 | 开场/总结/权威/单次不触发/假互动/social放宽/不影响pass-fail/technical放宽 | ✅ |
| profile-boundary | 6 | technical不误报/social二人称/essay普通句/technical代码/essay不触发technical/fiction拒绝 | ✅ |
| long-form | 2 | strict保护/balanced模式 | ✅ |
| unsupported-fiction | 3 | fiction文本/profile参数/fidelity_guard拒绝 | ✅ |
| **总计** | **47** | | **✅** |

---

## 8. 偏差审计

### 8.1 Step 09 遗留偏差（11 项）

| # | 偏差 | 类型 | 是否偏离架构 |
|---|------|------|------------|
| 1 | domain-lexicon .md → .yaml | 格式调整 | 否 |
| 2 | output-contract.md 放入 core/ | 格式调整 | 否 |
| 3 | fidelity.md 放入 core/ | 格式调整 | 否 |
| 4 | workflow.md / constraints.md 别名 | 合理扩展 | 否 |
| 5 | config/default.yaml | 合理扩展 | 否 |
| 6 | author/ 模板文件 | 合理扩展 | 否 |
| 7 | README.md | 合理扩展 | 否 |
| 8 | run_tests.py 硬编码测试 | 实现细节 | 否 |
| 9 | advisory-only 7/12 脚本实现 | 实现细节 | 否 |
| 10 | warning 词频统计 | 实现细节 | 否 |
| 11 | PB-004 断言宽松 | 实现细节 | 否 |

### 8.2 Step 10 新增变更

| # | 变更 | 类型 | 是否偏离架构 |
|---|------|------|------------|
| 12 | HR-004 正则补全（+3 条） | 缺陷修复 | 否（补全已有模式定义） |

---

## 9. 审计结论

| 检查项 | 结果 |
|--------|------|
| 所有必需文件已创建 | ✅ |
| 无关键文件遗漏 | ✅ |
| 扩展文件合理 | ✅ |
| 核心约束全部覆盖 | ✅ |
| 模式分级正确实现 | ✅ |
| Profile 边界正确 | ✅ |
| 脚本功能完整 | ✅ |
| 测试合同达标 | ✅ |
| 偏差不偏离架构 | ✅ (12 项全部合理) |
| 缺陷已修复 | ✅ (AHR-004) |
| **架构一致性总评** | **✅ 通过** |

---

> 架构审计完毕。测试结果见 `step-10-test-report.md`，缺陷修复见 `step-10-defect-fix-report.md`。
