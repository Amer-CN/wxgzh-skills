# Safety Checklist

- [x] 本地文件SHA与冻结清单逐字一致；不一致即error/零上传/非零退出。
- [x] 只能上传copyright_approval.json显式single_asset批准资产；material/source_url不能扩大集合。
- [x] 上传候选数量不得超过asset_approvals数量；超出立即失败闭合。
- [x] URL安全检查保留且未放宽。
- [x] 批准合同、manifest SHA、approval_mismatches、稳定身份校验保留。
- [x] 没有新增自动批准路径；restricted仍最高优先。

Observability只增加事件字段，不改变接口、成功条件、上传判定或重试次数。测试：284 passed，6 skipped，0 failed。
