# Eight Safety Properties

- [x] 冻结本地SHA校验未改。
- [x] 仅批准资产上传规则未改。
- [x] 批准数量硬上限未改。
- [x] URL安全检查未改。
- [x] 批准合同加载/验证未改。
- [x] 未新增自动批准路径。
- [x] uploadimg幂等护栏未改；本档不得新增uploadimg。
- [x] 尚未上传封面；若后续条件生效，必须先实现独立cover幂等事件。

失败观测仅在非零entry_run抛StageError前落盘；不改变成功判定、路由、输入、receipt或合同。
