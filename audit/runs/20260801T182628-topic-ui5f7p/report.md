# RUN 20260801T182628-topic-ui5f7p · 端到端复验报告(第 6 阶段失败,停机上报)

## 最终状态

```text
RUN_ID=20260801T182628-topic-ui5f7p
TOPIC=智能体时代的数据库身份安全
STATUS=STAGE_FAILED
failed_stage=wechat_draft
RESUME_EXIT=1
completed_stages=[aihot, super_writer, zh_human_writing, media_enrichment, gzh_design]
uploaded_image_count=2
draft_created=true(真实副作用,BEFORE=1 AFTER=2 delta=1,未删除任何草稿)
formally_published=false
mass_send=false
scheduled=false
```

## 阶段总表

| 阶段 | 状态 | receipt SHA-256 | 备注 |
|---|---|---:|---|
| aihot | PASS | `275bd0f35831af28878fc918f78d6356d45fa8493780816b7974b7b6d285f5b2` | 真实抓取,raw=13→dedup=10 |
| super_writer | PASS | `cb82b06729d6ef00309d90373e124210a49eb1fe9d91d99311a3fec5842a3a7b` | Material-Heavy Full Mode,官方长度校验 passed=true |
| zh_human_writing | PASS | `140666c4152f00bab6c4f7c21cd572a1f46220f50f6bd01427aa5acf88e27d18` | 2 处轻量措辞,保真 13/13、0 警告;final_article.md SHA `736ff00f7858fe7018dfa84f69524ee6c0aa9720463d5ba0c75f254869169576` |
| media_enrichment | PASS | `5533a6283ddca0690bdade7d32fb496a7aa18b2cf94047c15a8bfeb0c1a7581f` | discover→人工批准→continue;真实上传 2 张(A-003/A-004) |
| gzh_design | PASS | `d7a6ed7a02539242d5f1647254885742051024843814de913edfce0ba5ed04ca` | smartisan 正式渲染,theme_identity PASS,无 fallback |
| wechat_draft | FAIL | `31e0cdc99442536cfe99a85c55f0faf19015f33331777a0ce6f7a935b0cc38bc` | 校验层误报,见下 |

## 媒体批准与上传(独立审核者裁决已执行)

- 冻结清单:`stages/media_enrichment/discover/asset_discovery_manifest.json`,`discovery_manifest_sha256=750f8a6eecba5008b6d7c04c64af2c0ec27008925b3f8fe31d822b2067532e90`
- 批准:A-003(sha `418d841fed238ad485cfc959555d518e5e1d6d005efd35080ce3a9035f2b87cf`)、A-004(sha `5346d55e5a7478a5e7f21a12060900a912c616664e11a2eb8ee1c8ebc09e5e9c`);不批准 A-001、A-010;其余维持拒绝;批准总数 2,未超出
- `validation_config.json`:`body_images_min=2`,`set_by=independent_reviewer`
- `approval_evidence.md` SHA `331c940af98f5aeb0bf9b63e7c5ad8087e309932cdd9c56a425e27be3f45c659`;`copyright_approval.json` SHA `961ab1a13b022aa594040ed8130dcd4ac7567c0823c62a8debe58d98fef7c49b`(含 3 项审计记录:6 个材料页 URL 与抓取时间戳、资产 ID 分配规则、A-003 第二份永久素材副本 OBS-60)
- 上传事件(真实,`mmbiz.qpic.cn`,均为本 RUN 内首次上传,无重复):
  - A-003:`https://mmbiz.qpic.cn/mmbiz_png/Rejn3syibRSY73DEibmyGCA6OcK4LXlmLp04g3ic1Tn42LTxn7IMDxDdluh30yCkP2icLD4OxHO4mxvmEo17TGm9Ajmk9MeNLvqBlzfdH8TT71c/0?from=appmsg`
  - A-004:`https://mmbiz.qpic.cn/sz_mmbiz_png/Rejn3syibRSZBJOyF383He5ibsMqLEvRzbWQXmot0Q0NibR9Q0ib77xZzodAbnvHq4UJw84mEe8gFVykgYcqfg6427CRZYxK80l6TfpqSdgpyac/0?from=appmsg`

## 失败详情(wechat_draft)

- `exit_code=1`,执行耗时 8.0s(见 `stage_receipt.json`),stdout/stderr/exit_code 已落盘 `stages/wechat_draft/stage_failure.log` 与 `stage_failure-stage6r-attempt1.json`
- validator 报告(见 `stage_result.json`):
  - `DRAFT_DELTA=FAIL`,`NEW_DRAFT_COUNT=0`,`NEW_DRAFT_UNIQUE=false`
  - `AFTER_eq_BEFORE_plus_1=true`,`OLD_DRAFTS_PRESERVED=true`,contract `CONTRACT=PASS`,无发布/群发/定时/删除端点
- 根因:gzh-design `publish_wechat_draft.py::_desensitize_item` 仅保留 media_id 前 8 字符并加 `[REDACTED]`,`draft_before.json` 与 `draft_after.json` 中两条草稿因此显示相同值 `Y3aIagws[REDACTED]`;`validate_draft_delta.py` 以 `set(media_id)` 判定新稿,脱敏碰撞导致误报 0 新稿。属校验层假阴性——草稿本身已真实创建(BEFORE=1→AFTER=2,delta=1,标题「智能体时代的数据库身份安全」),未删除任何草稿
- 封面校验已通过:创建前校验本地冻结文件 `discover/images/418d841fed238ad485cfc959555d518e5e1d6d005efd35080ce3a9035f2b87cf.png` SHA 逐字一致,未重新下载

## 安全属性核对(九条)

1. 上传前 sha256 与冻结清单逐字一致:PASS(A-003/A-004 上传前校验通过,不一致即拒绝)
2. 上传数量≤2:PASS(`uploaded_image_count=2`)
3. 封面来自本地冻结文件:PASS(sha 逐字一致,无网络重下载)
4. 本 RUN 内 success 资产不重复上传:PASS(每资产仅 1 次上传事件)
5. 显式批准、数量上限、URL 安全、批准合同、无自动批准路径:均 PASS(见 approval_evidence.md / copyright_approval.json)
6. 不发布/群发/定时/删除草稿:PASS(仅 draft/add + cover add_material)

## 归档与停止

- 失败后未重试(仅 1 次尝试),按指令停机上报
- 不续发、不修复、不删除任何已有草稿;PR #1 保持 OPEN 不合并
- 待用户裁决方向(另行处理):修复脱敏指纹唯一性(如前 8 字符 + SHA-256 摘要),并处置已创建的第二篇草稿
