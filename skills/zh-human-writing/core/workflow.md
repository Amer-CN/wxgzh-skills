# core/workflow.md
# zh-human-writing v1 — 工作流（execution-flow 的别名文件）
# 内容与 core/execution-flow.md 一致，参见 core/execution-flow.md

参见 `core/execution-flow.md`。

固定 9 步执行流程：

1. 读取输入合同
2. 提取 protected spans
3. 识别 source、strategy 和 profile 对应权限
4. 诊断真实表达问题
5. 执行最小必要编辑
6. 独立做双向保真审计
7. 硬约束失败则局部回滚
8. 最多做一次高置信残留检查
9. 按 clean/diff/audit 输出

完整内容见 `core/execution-flow.md`。
