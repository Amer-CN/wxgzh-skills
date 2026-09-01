# zh-human-writing

简体中文写作编辑 Skill — 在不改变事实、意图、立场和任务边界的前提下减少模板化机器表达。

## 这是什么

一个给 AI Agent（Claude、Cursor 等）使用的写作编辑 Skill。它的作用是：

- **检测并移除**中文文本中常见的 AI 机器味模式（模板开场、无信息导航、聊天助手残留等）
- **保护**作者个人风格、事实陈述、技术参数等不可变内容
- **不判断**文本是否 AI 生成 — 它只处理已知的机器表达模式

适用于：公众号文章、技术博客、社论等非虚构文体编辑。

## 安装

将本目录放入你的 Skill 安装目录：

```
<skill-dir>/zh-human-writing/SKILL.md
```

以 Claude Desktop + reasonix 为例：

```
F:\AIXM\GZH\.reasonix\skills\zh-human-writing\SKILL.md
```

安装后 Agent 在收到"润色""编辑""去 AI 味""改自然"等请求时会自动加载本 Skill。

## 默认行为

| 参数 | 默认值 | 说明 |
|------|--------|------|
| source | unknown | 不自动判断来源 |
| strategy | preserve | 保守编辑，只做减法 |
| profile | essay | 默认散文文体 |
| length_retention | balanced | 保留 80%+ 原文长度 |
| output | clean | 直接输出最终文本 |

## 工具脚本

三个 Python 脚本提供确定性检查（不依赖 LLM）：

```bash
# 模式审计 — 检测文本中的 AI 模式
python scripts/pattern_audit.py --text article.txt --profile essay --check-level full

# 保真检查 — 验证编辑没有破坏不可变内容
python scripts/fidelity_guard.py --original original.txt --edited edited.txt --profile technical --source ai_draft

# 变化统计 — 量化编辑前后差异
python scripts/change_report.py --original original.txt --edited edited.txt --length-retention strict
```

## 模式分级

| 级别 | 数量 | 行为 |
|------|------|------|
| hard-residue | 5 组 | 单次出现即触发删除/替换 |
| strong-contextual | 6 组 | 聚集 ≥2 次时标记 |
| advisory-only | 12 条 | 只在 diff/audit 中提示，不自动修改 |

## 文体 Profile

profile 阈值真源在 `config/default.yaml` 的 pattern_thresholds（72C-2 起废除统一乘数；profiles/*.md 死文件已删除，OBS-232）。fiction 不被支持，拒绝处理。

## 运行测试

```bash
python tests/run_tests.py --verbose
```

36 条单元测试覆盖：模式检测、保真检查、Profile 边界、长文保护、fiction 拒绝。

## 文件结构

```
zh-human-writing/
├── SKILL.md                    # 核心入口
├── config/default.yaml         # 默认配置
├── core/                       # 核心约束和路由
│   ├── invariants.md           #   不可变硬约束
│   ├── input-contract.md       #   输入合同
│   ├── routing.md              #   路由与操作权限表
│   ├── execution-flow.md       #   固定 9 步执行流程
│   ├── output-contract.md      #   输出合同
│   ├── fidelity.md             #   保真机制规格
│   ├── workflow.md             #   工作流
│   └── constraints.md          #   核心约束
├── references/                 # 参考文件
│   ├── patterns/               #   模式包
│   │   ├── hard-residue.md
│   │   ├── strong-contextual.md
│   │   └── advisory-only.md
│   ├── protected-spans.md      #   Protected Spans 定义
│   ├── false-positive-protection.md
│   └── domain-lexicon.yaml     #   核心术语词典
├── author/                     # 作者 profile 模板
├── author-profile/             # 作者 profile schema
├── scripts/                    # 工具脚本
│   ├── pattern_audit.py
│   ├── fidelity_guard.py
│   └── change_report.py
└── tests/                      # 测试用例
    ├── run_tests.py
    └── */fixtures.yaml
```

## 限制声明

- 编辑规则基于合成测试用例验证，未在真实大规模中文语料上独立验证
- 编辑结果应由作者人工审阅后再发布
- 本工具不判断文本是否 AI 生成
- v1 不支持 fiction 编辑
- v1 不实现 AI 概率、人味分、综合质量分
- 聚集阈值（≥2）和长度比例阈值（0.90/0.80）为 heuristic，可在使用后校准
## 限制声明

- 六族规则来自上游 283 万字对照研究定点移植，并已接入自有冻结 RUN 校准；阈值仍应持续复核。
- `ai_tone` 是 review 信号，不判断文本是否 AI 生成，也不单独触发改写。
- 编辑结果应由作者人工审阅后再发布。
- v1 不支持 fiction 编辑。
- v1 不实现 AI 概率、人味分、综合质量分。
- 聚集阈值（≥2）和长度比例阈值（0.90/0.80）为 heuristic，可在使用后校准。

## 来源

本 Skill 基于对 11 个开源写作编辑工具的研究和重新实现，详见 `SOURCE-NOTES.md`。所有能力均以不同表述重新实现，未复制任何原始代码或规则文本。
