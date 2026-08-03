# 档 49 — resume 续跑 20260802T220853-codex-sol-luna-max-m6pyv4:停机于 media_enrichment(绑定 5 < min 6)

- 报告编号:e2e-verify-49
- 执行日期:2026-08-03(Asia/Shanghai)
- 状态:**停机**。按档 49 指令「任一阶段失败即停机,贴 RUN_ID / STAGE / STATUS / 完整报错,不自行重试」执行。media_enrichment 内容校验失败(绑定 5 张 < body_images_min=6);未自行重试、未手工补字段、未修改任何产物、未创建草稿。已发生 5 次真实 uploadimg(副作用已登账)。
- RUN_ID:`20260802T220853-codex-sol-luna-max-m6pyv4`

## 第零步 预检(通过)

- 微信 token 成功(出口 IP `185.217.5.28`);草稿箱 total_count=**3**;基线:四锁 root(`46a00a1b…/18491b36…/0d8aea21…/f59d64bb…`)、lock 双侧 `8fb33d83…`、台账 2 条。

## 第一步 resume 前置校验(实证,全过)

```
aihot:            ok=true, mismatches=[], skill_root_state=OK
super_writer:     ok=true, mismatches=[], skill_root_state=OK
zh_human_writing: ok=true, mismatches=[], skill_root_state=OK
```

档 48「前三阶段 receipts 仍有效、resume 可直接续跑」的判定**实证成立**。

## 第二步 执行(media 阶段失败点)

- media discover:成功,冻结 8 张候选(全部来自 M-06,ithome「OpenAI 下调 GPT-5.6 Luna 费用 80%」页),正常停在批准点(AWAITING_MEDIA_ASSET_APPROVAL)✓(观察项 e 前半:批准点正常停下)。
- 人工批准合同:6 张 single_asset(A-110..A-114、A-107),approval_id `AP-20260803T194207-INDEPENDENT-REVIEW-001`,approved_by=independent_reviewer,evidence `approval_evidence.md`(sha `510e23e1…`)。
- media continue:5 张成功上传(A-110..A-114,status=success,URL 均为 genuine mmbiz.qpic.cn);**A-107 被 continue 阶段判定 rejected**(`reasons=['dimensions 100x100 below minimum 640x360']`,批准记录已消费 asset_approval_consumed=True,但资产尺寸不达标)→ 绑定 5 张。
- **失败点(完整报错)**:`media_enrichment: content validator failed (exit 1): {'body_image_count': 5, 'min_required': 6, 'min_met': False, 'MEDIA_BINDINGS': 'FAIL', 'blocking_reason': 'fewer than 6 bound images — MUST NOT upload', ...}`,fail_closed=true。契约检查 `body_images_min: 5 < 6` 唯一问题。

## 观察项(已产生部分,据实)

- e. **档 48 URL 一致性校验在真实执行中通过**:discover 与 continue 均未出现 source_url 失配(修复生效的实跑验证);本阶段失败与 URL 无关。
- a/b/c/d(f)未到达(gzh_design 前置失败;无代码块;冒烟未触及)。
- OBS-60/OBS-70 观察:本 RUN 为跨 RUN 场景,5 张新素材与历史 RUN 无同 sha 资产(ithome 图,历史上传为 google cloud 图与图表),未出现重复上传/去重误判;同 RUN 内 5 张 asset_id 唯一,一次成功一次,无重复。
- 图表/OBS-71:无图表生成(`warnings=['No claims with numbers — no charts generated']`);上传的 known_allowed 均来自真实批准合同(single_asset),非 known_allowed 绕过。OBS-72 封面批准校验:未到达封面选择(wechat_draft 未执行)。

## 第三步 收尾(未完成部分)

- validate_draft_delta / 四锁复核 / doctor:未到草稿阶段;媒体失败后已确认前三阶段 receipts 仍 ok(见上)。
- **副作用已登账**(audit/side-effects/ledger.md):本 RUN 5 次 uploadimg(A-110..A-114,资产 sha 与返回 URL 逐条记录);无草稿、无封面、无发布/群发/定时/删除;草稿箱仍 3 份。
- 环境未变:四锁 root / lock `8fb33d83…` / 台账 2 条 / RUN 产物未修改。

## 需要裁决

1. **续跑路径**:已批准 6 张、实际合格 5 张。继续到草稿需要 ≥6 张绑定:候选方向——(a) 追加批准 A-109(1 张 review_required,1440x658,medium risk)使合格数达 6;(b) 批准剩余 A-108 之外的另一张?(A-108 为 1x1 tracking pixel,不可用);(c) 调整 validation_config body_images_min(需裁决授权,且属「改配置」)。建议 (a):追加批准 A-109 后续发,不触碰任何校验与配置。
2. 或裁决终止本 RUN(保留证据,副作用 5 次 uploadimg 已记录)。

## 证据文件

- `F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260802T220853-codex-sol-luna-max-m6pyv4\media_enrichment\{discover\asset_discovery_manifest.json, continue\media_manifest.json, continue\upload_events.json, article_image_bindings.json, copyright_approval.json, approval_evidence.md}`
