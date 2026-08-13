# CLAUDE.md — zh-human-writing Skill 使用说明

## 何时触发

当用户请求"润色""编辑""去 AI 味""改自然""去机器味"等中文写作编辑任务时，加载 `SKILL.md`。

## 默认参数

```
source: unknown
strategy: preserve
profile: essay
length_retention: balanced
output: clean
```

## 关键约束

- 不判断文本是否 AI 生成
- 不删除事实、数字、URL、代码、引用
- fiction 请求直接拒绝（v1 不支持）
- 编辑后长度不得低于原文的 80%（balanced 模式）

## 脚本工具

```bash
python scripts/pattern_audit.py --text input.txt --profile essay --check-level full
python scripts/fidelity_guard.py --original original.txt --edited edited.txt --profile technical
python scripts/change_report.py --original original.txt --edited edited.txt --length-retention strict
```
