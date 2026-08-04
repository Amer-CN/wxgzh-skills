# UNCONTROLLED — 本 RUN 未经人工批准,保留作回归样本

- RUN_ID:`20260801T231452-vibe-coding-guide-v2-1-1vg6jx`(主题「vibe-coding-guide v2.1 升级」,profile `fast_publish`,network_mode `live`)
- 归档时间:2026-08-02(档 37 第一步,自 `.temp\wxgzh-pipeline\` 原样复制,102 文件,树哈希与源逐字一致)
- 性质声明:
  - **零批准合同**:`asset_approvals=[]`、`copyright_approval.json` approvals 为空、材料 copyright_review 全部 unknown,未在媒体批准点停下交人工审批
  - **走 known_allowed 图表路径**:12 次上传全部为 continue 阶段重新生成的图表,`copyright_status="known_allowed"` 由构造硬编码,不查询任何批准/版权输入
  - **12 次重复上传**:6 张唯一图表(sha 46d83857…/d52b7b44…/2c441775…/3116603b…/62187244…/065258ed…)各上传 2 次(23:33 A-001..A-006 补丁前编号;00:05 A-032..A-037 补丁后编号),均 HTTP 200
  - **封面为未批准生成图表**:草稿 #3 封面取本地 continue\charts\chart-001.png(sha 46d83857…),该资产未经任何人工批准
  - **代码基线为热修态**:本 RUN 由含 7 行 asset_counter 热修的 media-enrichment 安装副本与含 `_wechat_cover_asset` 热修的 producers.py 执行;安装侧 skills.lock.json 于 23:52:56 被改写
- 保留用途:**OBS-71 修复后的回归样本**——修复生效后,此 RUN 的重放/复算必须 fail-closed(零上传、零草稿),不得再产生任何微信副作用
- 本目录内容为历史物证,禁止修改、删除或用于任何真实发布

## 档 63 补注(2026-08-04,OBS-71 修复验证)

- 修复生效后重放验证(离线,零网络零微信):以本 RUN 的 media_discovery_request.json
  (claims/numbers/chart_group 逐字)重放 discover → 6 张图表全部 decision=review_required、
  copyright=unknown;重放 continue 且 asset_approvals=[] → **fail-closed:零上传事件、
  零草稿、零微信副作用**。仅当对单张图表签发 single_asset 批准时才会上传该张。
- 上述 fail-closed 契约已由 tests/test_obs71_chart_approval.py 固化(夹具冻结,
  不引用本目录实时文件);本目录仍为历史物证,未做任何修改。
