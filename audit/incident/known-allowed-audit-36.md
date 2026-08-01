# 档 36 — known_allowed 影响面取证(2026-08-02)

- 全程只读;唯一写入本报告。沿用档 34/35 全部禁令:未恢复基线、未执行安装器、未 relock --apply、未触碰 .agents\skills 与 .temp RUN 目录、未改配置、未调微信接口。
- 证据基线:
  - 锁定版:`F:\AIXM\wxgzh\repos\media-enrichment` @ `cedf92ca45b0cdb7e010d489e9da67dd28ef6e59`(档 31 sibling,与 skills.lock.json 锁定一致)
  - 安装侧现场:证据副本 `F:\AIXM\wxgzh-incident-20260802\skills-asfound\media-enrichment`(档 34 已证与现场逐字一致,asfound 版 = 锁定版 + OBS-42/43 等历史热修 + 23:52:38 的 7 行补丁)
  - 归档 RUN:仓库 `audit\runs\20260731T135947-ai-bbg4al`、`audit\runs\20260801T182628-topic-ui5f7p`
  - 事件 RUN 证据副本:`F:\AIXM\wxgzh-incident-20260802\runs\20260801T231452-vibe-coding-guide-v2-1-1vg6jx`(原目录 `.temp\wxgzh-pipeline\20260801T231452-…` 未触碰)

## 第一 known_allowed 机制全貌

### 1. 锁定版 cedf92ca L405-447 原文(逐字)

`scripts/run_media_enrichment.py`:

```python
 405:     print(f"\n[media-enrichment] Generating charts...")
 406:     claims_with_numbers = [c for c in claims if c.get("numbers")]
 407:     if claims_with_numbers:
 408:         plan = build_chart_specs(claims_with_numbers, materials_by_id)
 409:         for w in plan.warnings:
 410:             builder.warnings.append(w)
 411:             print(f"  WARN: {w}")
 412:         for i, spec in enumerate(plan.specs):
 413:             chart_path = output_dir / "charts" / f"chart-{i+1:03d}.png"
 414:             chart_result = generate_chart(spec, chart_path)
 415:             if chart_result.success:
 416:                 asset_counter += 1
 417:                 asset_id = f"A-{asset_counter:03d}"
 418:                 chart_upload = {
 419:                     "mode": upload_mode, "status": "not_uploaded",
 420:                     "remote_url": None, "response_sha256": None,
 421:                 }
 422:                 # Discovery is strictly side-effect-free: do not even invoke a
 423:                 # dry-run uploader or emit an upload-attempt event. Generated
 424:                 # charts may be uploaded only in the explicit continue phase.
 425:                 if args.phase == "continue" and discovery_file_valid:
 426:                     chart_upload_result = timed_upload(
 427:                         uploader, upload_events, chart_result.chart_path, asset_id,
 428:                         copyright_status="known_allowed",
 429:                     )
 430:                     chart_upload = {
 431:                         "mode": upload_mode, "status": chart_upload_result.status,
 432:                         "remote_url": chart_upload_result.remote_url,
 433:                         "response_sha256": chart_upload_result.response_sha256,
 434:                     }
 435:                 asset = AssetRecord(
 436:                     asset_id=asset_id, asset_origin="generated",
 437:                     material_ids=list(set(dp.material_id for dp in spec.data_points)),
 438:                     claim_ids=[dp.claim_id for dp in spec.data_points],
 439:                     extraction_method="generated", decode_method="none",
 440:                     local_path=chart_result.chart_path, sha256=chart_result.sha256,
 441:                     perceptual_hash=chart_result.inspection.perceptual_hash if chart_result.inspection else None,
 442:                     mime_type="image/png",
 443:                     width=chart_result.inspection.width if chart_result.inspection else None,
 444:                     height=chart_result.inspection.height if chart_result.inspection else None,
 445:                     file_size=chart_result.inspection.file_size if chart_result.inspection else None,
 446:                     quality_status="pass", relevance_status="relevant",
 447:                     copyright_status="known_allowed", copyright_risk="low",
```

L447 之后紧接 `decision="eligible", reasons=["Generated from canonical claim data"]`(L448)。核心:图表在**构造时**即被硬编码 `copyright_status="known_allowed"` / `decision="eligible"`,上传门只有两个:`args.phase == "continue"` 与 `discovery_file_valid`(L425),完全不查询 `asset_approvals` 与材料 `copyright_review`。

**同机制的源资产侧(L381-399,上下文)**:材料级 `copyright_review.status=known_allowed` 的源资产走另一条同样豁免逐资产合同比对的通道:

```python
 381:             # Material/source_url approval is represented by the material's
 382:             # copyright_review.status=known_allowed and needs no per-asset approval.
 383:             # All approval modes still require a valid frozen discovery manifest
 384:             # in continue, plus the normal quality/relevance/dedup gates.
 385:             if (discovery_file_valid
 386:                     and asset.copyright_status == "known_allowed"
 387:                     and asset.decision == "eligible"
 388:                     and asset.quality_status == "pass"
 389:                     and asset.relevance_status == "relevant"
 390:                     and asset.duplicate_of is None):
 391:                 upload_result = timed_upload(
 392:                     uploader, upload_events, local_path, asset.asset_id,
 393:                     copyright_status=asset.copyright_status,
 394:                 )
```

**上传器层强制(`src/media_enrichment/uploader.py` L195-200)**:任何上传都必须携带 `copyright_status="known_allowed"`,否则 `skipped`:

```python
195:     def upload(self, local_path: str, asset_id: str = "", copyright_status: str = "unknown") -> UploadResult:
196:         if copyright_status != "known_allowed":
197:             return UploadResult(
198:                 mode="wechat_image_host", status="skipped",
199:                 error=f"upload skipped: copyright_status={copyright_status}",
200:             )
```

安装侧 asfound 版同构(图表路径位于 L583-635,上传门 L604:`if args.phase == "continue" and discovery_file_valid:` + L607 `copyright_status="known_allowed"`)。

### 2. 什么条件落入这条路径

判定依据**不是**资产类型/来源域名/生成方式三者之一,而是资产对象的 `copyright_status == "known_allowed"` 字段值;该字段值由三个互不相同的来源产生:

1. **材料级版权审查**(来源域名相关):材料 `copyright_review.status="known_allowed"` 时,其源资产在发现期即获得该状态,cedf92ca L385-390 直接进上传(无需逐资产合同)。
2. **批准合同消费后改写**(L365):显式 `asset_approvals` 条目逐项通过 `approval_mismatches` + fresh 字段比对后,`copyright_status` 被改写为 `known_allowed` 再进上传。
3. **生成方式**(图表构造):L447 构造时硬编码,与任何批准/版权输入无关。

安装侧(OBS-42)将源资产候选收窄为 `upload_candidate_ids = set(asset_approvals) | material_approved_ids`(L171),且候选数超过显式批准数即 fail-closed(L172-176);材料级 known_allowed 仍可免逐资产合同上传,但需过冻结 sha 比对。**图表路径在两侧语义一致:硬编码豁免**。

### 3. 该路径上传前是否仍执行三项检查(逐项结论)

| 检查 | 源资产(材料级 known_allowed,cedf92ca) | 图表(两侧一致) | 批准合同路径(对照) |
|---|---|---|---|
| 本地 sha 与冻结清单逐资产比对 | **不执行**;仅 `discovery_file_valid`(冻结清单自洽校验) | **不执行**;图表**根本不在冻结清单内**(冻结 manifest 只含 source 资产,见事件 RUN 冻结清单仅 6 项实证) | 执行(L342-351 fresh 比对;安装侧 L226 对冻结文件实算比对) |
| URL 安全检查 | 发现期 `is_safe_url`(L196,cedf92ca;安装侧 L217-222 在 continue 再次执行);上传响应 URL 必须为微信图床(`normalize_wechat_url`,uploader L234-240,所有路径一致) | 本地生成无来源 URL;上传响应 URL 同样受微信图床检查 | 同左(源资产) |
| 数量上限 `max_total_images` | 发现循环内生效(L134/L182,cedf92ca;安装侧仅 discover 生效) | **不生效**——图表在发现循环之后生成,无任何数量上限 | 同左(源资产) |

**结论:known_allowed 路径绕过的仅是「批准合同 + 逐资产冻结比对」这一项(图表连冻结条目都不存在);其余护栏(冻结清单有效性、质量/相关性/去重门、上传器 known_allowed 强制、微信图床响应校验)仍在;图表额外豁免「冻结清单成员资格」与「数量上限」。** 安装侧源资产路径因 OBS-42 反而比锁定版更严(逐资产 sha 比对),但图表豁免在两侧相同。

## 第二 历史 RUN 复查(本档核心)

### 4. 两篇归档 RUN 逐次上传判定

**RUN 20260731T135947-ai-bbg4al**(2 次真实上传,均在 2026-07-31T18:18:03Z-18:18:07Z):

| 资产 | sha256 | 所走路径 | 依据 |
|---|---|---|---|
| A-003 | `418d841fed238ad485cfc959555d518e5e1d6d005efd35080ce3a9035f2b87cf` | **批准合同路径** | `continue/media_manifest.json`:`asset_approval_consumed=true`、`approval_id=AP-20260731T1449-INDEPENDENT-REVIEW-001`、`approval_identity_mismatch=[]`;`media_continuation_request.json` asset_approvals 含同 asset_id/同 sha(418d841f…);`approval_evidence.md` 批准清单含同 sha;材料 M-02 `copyright_review.status="unknown"`(非原生 known_allowed,上传完全依赖合同消费) |
| A-004 | `5346d55e5a7478a5e7f21a12060900a912c616664e11a2eb8ee1c8ebc09e5e9c` | **批准合同路径** | 同上(approval 条目 sha=5346d55e…,consumed=true) |

**RUN 20260801T182628-topic-ui5f7p**(2 次真实上传,2026-08-01T12:16:15Z-12:16:18Z):

| 资产 | sha256 | 所走路径 | 依据 |
|---|---|---|---|
| A-003 | 同上(418d841f…) | **批准合同路径** | `media_manifest.json`:consumed=true、`approval_id=AP-20260801T1830-INDEPENDENT-REVIEW-001`、mismatch=[];continuation request asset_approvals=2 条同 sha;approval_evidence.md 批准清单含同 sha |
| A-004 | 同上(5346d55e…) | **批准合同路径** | 同上 |

两 RUN 的 manifest 均**无 generated 资产**(RUN1 10 项、RUN2 13 项全部 `origin=source`),无图表参与。判定「批准合同路径」的关键证据是 `asset_approval_consumed=true` + `approval_id` + `approval_identity_mismatch=[]`——这些字段只在合同消费分支(L334-379)写入;且材料 copyright_review=unknown 排除了原生 known_allowed 通道,证明上传**依赖且只依赖**批准合同。

### 5. known_allowed 走查结论

- **两篇归档 RUN 共 4 次上传,全部走批准合同路径,无一张走 known_allowed 豁免路径。**
- 对「九条第 2、5 条全程有效」历史结论的影响:**无影响,结论维持**。九条#2(上传数量 ≤2 / ≤批准数):每 RUN 恰好 2 次上传 = 批准数 2;九条#5(显式批准,候选清单交人工审批):每 RUN 的 2 张均以 `independent_reviewer` 签发的合同逐资产消费,且上传前完成 sha/稳定身份与冻结清单逐项比对。
- 必须说明的两个限定(不影响判定,但避免误读):
  a. 上传器层要求 `copyright_status="known_allowed"` 是**所有**上传路径的公共前置——归档 RUN 的 known_allowed 来自合同消费后的字段改写(L365),「known_allowed 状态」≠「未批准」。
  b. 归档 RUN 实际运行在**安装侧**(含 dev2-hotfix2 去重与 OBS-42 门禁的版本,比锁定版更严),但「合同路径」的判定依据(consumed/approval_id/mismatch 字段)在两个版本中语义一致,不受版本影响。

### 6. 事件 RUN 12 次上传逐条(全部 known_allowed 图表路径)

冻结清单实证:事件 RUN `continue/asset_discovery_manifest.json` 仅含 **6 个 source 资产**(A-002/A-003/A-004/A-006/A-007/A-019,均为 vibe-coding-guide GitHub README 图,**无任何图表条目**);`media_continuation_request.json` 的 `asset_approvals=[]`;材料 copyright_review 全部 unknown。12 次上传全部为图表,走安装侧 L604-608 图表 known_allowed 路径:

**首轮(补丁前,编号从 0 重启,与冻结源资产 id 碰撞)2026-08-01T15:33:57Z-15:34:02Z(= 23:33:57-23:34:02 +08):**

| # | asset_id | 内容 | 本地 sha256 | 路径 |
|---|---|---|---|---|
| 1 | A-001 | chart-001.png | `46d83857d12e70fef795a0e883bbb89812e88302a9db5d5acc5b043d0656977b` | known_allowed 图表路径 |
| 2 | A-002 | chart-002.png | `d52b7b44e041cc207642f1bcaa4e247b1151cefb996fbef774cfb2ad79e184ec` | 同上 |
| 3 | A-003 | chart-003.png | `2c44177582309ead757c99bc7e68bd1e4601f918cf5d4d5e50c8aec09e1702d9` | 同上 |
| 4 | A-004 | chart-004.png | `3116603b65fde57120f4cc5e795d3ec04a82ab736095c6a0ea3eb133b8d75645` | 同上 |
| 5 | A-005 | chart-005.png | `62187244d84d1f0c9744aabf81fe2c7dbf9b1304a0cfa55ff808acb57e152fe7` | 同上 |
| 6 | A-006 | chart-006.png | `065258ed131231b093790a7cd074069b6b304e5132416157bf85f7b6752bb3b0` | 同上 |

**二轮(补丁后,编号续接 31 之后)2026-08-01T16:05:02Z-16:05:08Z(= 00:05:02-00:05:08 +08,08-02):**

| # | asset_id | 内容 | 本地 sha256 | 路径 |
|---|---|---|---|---|
| 7 | A-032 | chart-001.png(与首轮 #1 同内容) | `46d83857…` | known_allowed 图表路径 |
| 8 | A-033 | chart-002.png(同 #2) | `d52b7b44…` | 同上 |
| 9 | A-034 | chart-003.png(同 #3) | `2c441775…` | 同上 |
| 10 | A-035 | chart-004.png(同 #4) | `3116603b…` | 同上 |
| 11 | A-036 | chart-005.png(同 #5) | `62187244…` | 同上 |
| 12 | A-037 | chart-006.png(同 #6) | `065258ed…` | 同上 |

依据:
- `upload_events.json` 12 条全部 `status=success`、`mode=wechat_image_host`、`http_status=200`,无任何 `skipped_already_uploaded`(去重键为 asset_id,两轮 id 不同,未命中);
- 最终 `continue/media_manifest.json` A-032..A-037:`asset_origin=generated`、`copyright_status=known_allowed`、`consumed=False`、无 approval_id——状态全部来自构造硬编码;
- 6 张图两轮内容逐字节相同:`continue\charts\chart-001..006.png` 实算 sha 与清单一致,且与 discover 阶段图表(A-026..A-031)sha 相同;
- 6 个冻结 source 资产从未出现在任何上传事件中(源资产 0 次上传)。

## 第三 封面批准状态核查

### 7. 仓库版封面选择是否检查批准状态

仓库 `wxgzh_pipeline/producers.py` `_wechat()` L822-859,**不检查批准状态**:

- L830-832:封面路径与期望 sha **硬编码**为 `418d841fed…png`(A-003 的 sha,取自历史 RUN 的已批准资产)——不读本 RUN 的 `media_manifest`、不读 `approval_evidence`、不查该资产是否在本 RUN 批准清单内;
- L833-845:唯一门禁 = 文件存在 + `sha256_file(cover) == expected_cover_sha`,不符即 FAIL_CLOSED;
- 结论:「已批准」的唯一隐含联系是硬编码 sha 恰好等于先前 RUN 被批准的 A-003 内容;批准状态本身从未被读取或校验。

安装侧热修 `_wechat_cover_asset`(仅安装树,仓库无此函数,`git log -S` 全历史为空):读本 RUN `continue/media_manifest.json`,取第一个 `asset_origin=generated` + `decision=eligible` + 本地文件 sha 与 manifest 一致的资产(L822-859 之前的插入段)。**同样不检查批准状态**(approval_id/approved_by 不参与判定),但消除了跨 RUN 硬编码依赖。

### 8. 九条第 3 条当前的实际保障强度

- 九条#3(封面来自本地冻结文件,不得重新下载):现状 = 封面必须是**本地存在的文件**且 sha 与(仓库版:硬编码常量;安装侧:本 RUN manifest)一致 → 「不重新下载」的字面要求满足,文件完整性有保证。
- 但「已批准资产」这一前提**未被封面选择代码验证**:批准状态只在 media 阶段上传门禁中生效,producers 封面选择不复核。若审批批准的是另一张封面,代码不会察觉;安装侧版本甚至可能选中一张**未批准**的 generated 图(事件 RUN 即如此:封面 = chart-001/A-032,从未经人工批准)。
- 事件实证:00:05:10 仓库版硬编码封面 FAIL(418d841f… 文件在本 RUN 不存在)→ 00:11:44 安装侧热修替换为 manifest 驱动 → 00:14 草稿成功,封面为本地 `continue\charts\chart-001.png`(sha 46d83857…,与 manifest 一致,无网络重下载)——#3 的「文件来源」部分生效,「批准」部分缺失。

## 第四 修复面评估(只评估,不实施)

### 9. 关闭 known_allowed 的影响

- 受影响功能:①**图表上传**——事件 RUN 中唯一实际触发 known_allowed 豁免的资产类,是「图表自动配图」能力的唯一上传通道;②材料级 known_allowed 直传(cedf92ca L385-390;安装侧已收窄为候选集并 fail-closed,实际影响小)。
- 图表如何取得批准:需把图表纳入批准对象。可行路径:在 continue 前先生成图表并**冻结**(图表 asset_id/sha256/material_ids/claim_ids 进入冻结清单或独立 chart manifest),人工在媒体批准点对图表清单逐张批准,批准条目随 `asset_approvals` 传入后上传。
- **需要引入新的批准类型**:现有 `asset_approvals` 语义面向 source 资产(含 `source_page_url`/`resolved_original_url` 等字段,`approval_mismatches` 依赖之);图表无来源 URL,需新增 `approved_scope="generated_chart"` 条目(字段:asset_id/sha256/material_ids/claim_ids/discovery_manifest_sha256)或独立 `chart_approvals` 契约,并让 `approval_mismatches` 支持无 URL 资产。

### 10. OBS-69 推荐方案落地点(基于档 35:推荐「仓库 lock sha 内嵌 + 启动强制 doctor」)

- **仓库 lock sha 内嵌**:落点在 `wxgzh_pipeline/contracts.py` **L130**(`lock = SD.load_lock(SKILL_ROOT)…`,运行期契约自行重读安装侧 lock 处)——将仓库权威 `skills.lock.json` 的 sha256 作为代码常量(或由 CI 校验的生成模块)内嵌,运行期比对安装侧 lock sha,不一致即 FAIL_CLOSED。安装侧 lock 在 23:52:56 被改写后其 sha 即可被此类比对检出。
- **启动强制 doctor**:入口 = `wxgzh_pipeline/cli.py` `main()`(L39)与 `orchestrator.py` 的 run 入口,在任一 stage 分发前执行 doctor(或等价 lock 校验),失败即停。对现有 RUN 流程的影响:每次启动增加一次秒级校验;doctor 不是 stage,不产生 receipts,不改产物;仅当环境漂移时行为从「带病续跑」变为 fail-closed。
- 二者组合可覆盖「安装侧 lock 可写」与「运行期不再单方面信任」两个缺陷面。

### 11. OBS-70 改为按 sha256 去重的改动点与风险

- 当前去重实现(安装侧):`run_media_enrichment.py` L95-107 加载既有 `upload_events.json`,以 **`event["asset_id"]`** 为键建 `existing_upload_events`;L539-564 命中即复用 URL 并追加 `skipped_already_uploaded`。cedf92ca **无**该跨次去重(仅有发现期感知哈希 `deduplicate_asset`)——即「success 不重复上传」是安装侧热修能力,不在锁定版内。事件字段(`uploader.py` L76-81)不记录本地文件 sha,只有 URL 与 `response_sha256`(=URL 的 sha)。
- 改为按 sha256 的改动点:
  1. `timed_upload` 调用点(L566-568 源资产、L605-608 图表)在事件中写入 `asset_sha256`;
  2. 加载器(L99-106)以 `event["asset_sha256"]` 为键;
  3. 上传前查找(L539)改为 `existing_upload_events.get(asset.sha256)`;
  4. 历史事件无 sha 字段 → 需显式迁移策略(视为无 prior 或 fail-closed),不得静默。
- 影响与风险:
  - 收益:事件 RUN 二轮 6 次同内容上传会被命中跳过(两轮 12 次 → 6 次);同一 manifest 内 A-026..A-031 与 A-032..A-037 的重复内容也不再产生第二次真实上传。
  - 风险 1:**跨 RUN 不覆盖**——`upload_events.json` 按 RUN 目录存放,无全局台账;OBS-60(A-003/A-004 在两 RUN 各产生第二份永久副本)仍会发生,除非引入全局去重台账。
  - 风险 2:**补丁前 id 碰撞历史事件不可靠映射**——首轮 A-001..A-006 事件当时指向图表,最终 manifest 中同 id 是 source 资产;按 sha 去重必须依据事件写入时刻的 manifest,否则误判。
  - 风险 3:内容 sha 相同的合法复用(不同 RUN/不同文章用同一张图)会被去重——「本 RUN 内不重复上传」是九条#4 的既定语义,跨 RUN 内容级去重是新语义,需产品裁决。

## 附:行号索引与证据文件

- `scripts/run_media_enrichment.py`(cedf92ca):L381-399 源 known_allowed 门;L404-457 图表生成+known_allowed 上传;L196 `is_safe_url`;L134/L182 数量上限;L322-379 批准合同消费分支(L365 改写 known_allowed)。
- `scripts/run_media_enrichment.py`(安装侧 asfound):L92-107 事件加载/asset_id 去重索引;L135-257 OBS-42 候选门禁(L166-176 候选集、L187-237 逐资产 frozen sha/身份/URL 比对);L263-269 **7 行补丁**(编号续接);L529-578 上传循环+去重;L583-635 图表 known_allowed 路径。
- `src/media_enrichment/uploader.py`(cedf92ca):L67-82 `timed_upload`;L173-260 `WechatImageHostUploader`(L196 known_allowed 强制、L234-240 微信图床 URL 校验)。
- `wxgzh_pipeline/producers.py`(仓库):L822-859 `_wechat`(L830-832 硬编码封面、L833-845 sha 门禁);安装侧 `_wechat_cover_asset` 为安装树独有。
- `wxgzh_pipeline/contracts.py` L130(运行期读安装侧 lock);`wxgzh_pipeline/cli.py` L39(启动入口)。
- 证据文件:两归档 RUN `stages/media_enrichment/{upload_events,media_manifest,media_continuation_request,approval_evidence,copyright_approval}.json`;事件 RUN 证据副本 `media_enrichment/{upload_events,media_manifest,continue/media_manifest,continue/asset_discovery_manifest,media_continuation_request,stage_receipt,stage_failure}.json` 与 `continue/charts/*.png`;`F:\AIXM\wxgzh-incident-20260802\diff\*`。
