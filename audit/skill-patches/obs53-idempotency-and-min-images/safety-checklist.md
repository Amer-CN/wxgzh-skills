# Seven Safety Properties

- [x] 冻结本地文件SHA逐字校验，不一致拒绝。
- [x] 仅copyright_approval.json明确批准资产。
- [x] 数量不超过批准数。
- [x] URL安全检查未放宽。
- [x] 批准合同和稳定身份未放宽。
- [x] 无自动批准路径。
- [x] 已有success+合法URL不再调用uploadimg；复用前仍执行全部校验。

幂等回归、篡改失败、failed不复用、min默认/显式/非法值测试已加入。
