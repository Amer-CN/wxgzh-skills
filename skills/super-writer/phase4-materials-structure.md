# Phase 4 评测材料目录结构

> 本文件描述 Phase 4 评测所需材料的目录结构和文件格式。
> 按需准备，不必一次凑齐全部材料。

## 目录结构

```
phase4-materials/
├── human-articles/          # A. 人工定稿（5～10 篇）
│   ├── article-01.md
│   ├── article-01.meta.yaml
│   ├── article-02.md
│   ├── article-02.meta.yaml
│   └── ...
├── edit-pairs/              # B. AI 初稿→人工定稿（3～5 对）
│   ├── pair-01/
│   │   ├── draft.md
│   │   ├── final.md
│   │   └── notes.yaml
│   ├── pair-02/
│   │   └── ...
│   └── ...
├── tasks/                   # C. 24 个测试任务
│   ├── task-01/
│   │   ├── prompt.md
│   │   ├── materials/
│   │   ├── constraints.yaml
│   │   └── hidden-evaluation.yaml
│   ├── task-02/
│   │   └── ...
│   └── ...
├── scorer-calibration/      # D. 评分器校准集（24 篇，有人工标签）
│   ├── articles/
│   └── labels.json
├── scorer-blind/            # E. 评分器盲测集（12 篇，从未参与权重调整）
│   ├── articles/
│   └── labels.json
└── smoke-test/              # F. 冒烟测试（4 任务 × 4 版本 = 16 输出）
    ├── task-01/
    ├── task-02/
    ├── task-03/
    └── task-04/
```

---

## A. 人工定稿

每篇文章配一个同名 `.meta.yaml` 文件。

### article-XX.meta.yaml 格式

```yaml
title: ""
article_type: ""               # 产品体验 | 现象解读 | 工具分享 | 方法论 | 案例复盘 | 观点评论 | 个人经历型
written_by_user: true
satisfaction: 4                # 1-5
why_good:
  - ""
voice_notes:
  - ""
facts_verified: true
allow_for_voice_profile: true
```

### 选择原则

- 1～2 篇产品体验
- 1～2 篇现象解读
- 1～2 篇工具或教程
- 1～2 篇观点或方法论
- 1 篇你最满意的
- 1 篇你认为"很像自己，但数据一般"的

### 脱敏规则

如果包含隐私信息，用稳定占位符脱敏：
- `[公司A]`、`[朋友甲]`、`[产品B]`、`[城市C]`
- 同一个实体在所有文章里保持同一个占位符

---

## B. AI 初稿→人工定稿

### pair-XX/notes.yaml 格式

```yaml
article_type: ""
model_if_known: ""
user_confirmed_preferences:
  - ""
one_off_changes:
  - ""
facts_corrected:
  - ""
should_learn:
  - ""
should_not_learn:
  - ""
```

`should_not_learn` 很重要，防止系统把一次性的内容删除错误地学成永久文风规则。

---

## C. 24 个测试任务

每个任务包含 4 个部分：

### prompt.md

模拟真实使用时用户会说的话。

### materials/

放入真实素材：
- 笔记
- 网页摘录
- 产品资料
- 访谈
- 数据
- 个人经历
- 相互冲突的材料

### constraints.yaml（模型可见）

```yaml
target_reader: ""
desired_length: ""
article_type: ""
allowed_research: true
must_preserve: []
must_not_invent: []
expected_output_mode: full    # full | outline | exit
```

### hidden-evaluation.yaml（模型不可见，只用于评审）

```yaml
expected_behavior:
  - "识别素材不足"
  - "不得虚构用户体验"
known_facts: []
known_conflicts: []
hard_fail_conditions: []
acceptable_exit_statuses: []  # ready_to_write | needs_research | needs_author_input | research_limited | core_broken | evidence_conflict | unsuitable_topic | review_blocked
```

### 24 个任务分布

| 编号 | 类型 | 预期行为 |
|------|------|----------|
| T01-T03 | 产品体验 | 成功产出 |
| T04-T06 | 现象解读 | 成功产出 |
| T07-T09 | 工具分享 | 成功产出 |
| T10-T12 | 方法论 | 成功产出 |
| T13-T15 | 案例复盘 | 成功产出 |
| T16-T18 | 观点评论 | 成功产出 |
| T19-T20 | 个人经历型 | 成功产出 |
| T21-T22 | 素材不足 | 降级退出 |
| T23-T24 | 证据冲突/核心崩塌 | 失败退出 |

---

## F. 冒烟测试（先行）

先做 4 任务冒烟测试，只验证评测管线：

| 任务 | 类型 | 验证目标 |
|------|------|----------|
| S01 | 正常且素材充分 | 版本正确加载、输出匿名化 |
| S02 | 缺少个人经历 | 正确识别素材不足 |
| S03 | 证据互相冲突 | 正确识别冲突 |
| S04 | 核心观点应该崩塌 | 正确执行失败退出 |

4 个任务 × 4 个版本 = 16 个输出。

冒烟测试只检查：
- 版本是否正确加载
- 输出是否正确匿名化
- 日志是否记录版本
- 盲评文件是否泄露版本
- Hard Fail 是否能被正确记录
- 评分表是否可用

**冒烟测试只允许修复评测框架，不能修改 v0.2-rc1 的写作规则。**

确认评测管线没有问题后，再运行完整 24 任务。
