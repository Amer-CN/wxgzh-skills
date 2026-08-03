# 档 50 — 续跑 20260802T220853-codex-sol-luna-max-m6pyv4:停机于 wechat_draft(OBS-72 封面硬编码)

- 报告编号:e2e-verify-50
- 执行日期:2026-08-03(Asia/Shanghai)
- 状态:**停机**。media_enrichment(绑定 6 张)与 gzh_design 均通过;wechat_draft 阶段 entrypoint FAIL_CLOSED(`A-003 frozen cover sha256 mismatch`)——仓库版封面硬编码 A-003(历史资产 sha `418d841f…`)与本 RUN 无此文件,为 OBS-72 未修的表现。按指令不修 OBS-71/72/82、不自行重试、不调低任何阈值。
- RUN_ID:`20260802T220853-codex-sol-luna-max-m6pyv4`

## 第一步 追加批准前的说明(先答)

1. **A-109 适配性(非「差一张」)**:A-109 = ithome 新闻原图(1440×658),alt_text「OpenAI 于 7 月 31 日宣布下调 GPT-5.6 Terra 和 GPT-5.6 Luna 两款模型的调用费用」,来源与已批准 5 张同页(M-06, `ithome.com/0/983/917.htm`)。文章第三章「成本叙事的两面:降价与限额」直接论述 OpenAI 下调 GPT-5.6 系列价格,该图是该论点的新闻原图。批准理由为内容适配性。
2. **A-109 review_required 原因**:`['appears to be a photograph but source context unclear', 'copyright status unknown — cannot auto-approve for publishing']`。消除方式:人工审查 + single_asset 批准(批准即 known_allowed 的正式通道);审查确认来源(ithome 官方新闻页,与同页已批 5 张同源)与内容(alt_text 明确)。批准前状态未消除,批准动作即消除机制。
3. **批准合同状态与计数口径**:批准记录 7 条 = 原 6 条(5 条成功消费于 A-110..A-114,1 条 A-107 消费于 rejected 资产)+ 追加 A-109 1 条(新 approval_id `AP-…-INDEPENDENT-REVIEW-002`,未复用/未修改 `AP-20260803T194207`)。口径:已批准 6(实际可用 5)/ 追加 1 / 总批准 7 / 实际绑定 6;A-107 记录已绑定 rejected 判定不会复用,不产生计数冲突;「批准记录空耗于不达标资产」即 OBS-82,本档不修。
4. **validation_config 口径(据实)**:本 RUN 产物与当前代码中**不存在** `body_images_min=2` 或 `default_value=6` 字段;`validation_config.json` 不存在。实际生效值 = 默认 6(`stages/media_enrichment.py` L47-53,`body_images_min_source='default'`;`validate_media_bindings.py` L13 `MIN_BODY_IMAGES=6`)。无未生效配置,不登记新 OBS(若审核者所指为旧版配置,请给出路径)。

## 第二步 追加批准与续跑

- 追加批准 A-109(approval_id `AP-20260803T…-INDEPENDENT-REVIEW-002`,证据 `approval_evidence.md` 追加段,sha `1116d713…`)。
- media continue:绑定达 **6 张**;新增真实上传 1 次(A-109 success),前 5 张(A-110..A-114)追加 `skipped_already_uploaded`(幂等,OBS-53 生效,无重复上传)。**观察项 f:OBS-70 去重键(asset_id)正常命中,无误判**。
- gzh_design:通过(渲染 + 内容保真守卫 + 结构指纹校验)。
- **wechat_draft 失败(完整报错)**:
```
wechat_draft: entrypoint subprocess failed (exit 2): FAIL_CLOSED: A-003 frozen cover sha256 mismatch
stage_failure.json: {"entry": ".../publish_wechat_draft.py", "exit_code": 2, "stderr_tail": "FAIL_CLOSED: A-003 frozen cover sha256 mismatch", ...}
```
- 依据档 36 取证:仓库版 `producers._wechat()`(L822-859)封面路径与期望 sha 硬编码为历史 A-003(`418d841f…`),不读本 RUN media_manifest、不校验批准状态;本 RUN 无该文件 → FAIL_CLOSED。**观察项 e:OBS-72 封面选择 = 仓库版硬编码,未校验批准状态,首次在真实新 RUN 触发失败**。不修。

## 重点观察项

- **a. ★OBS-73 生产链路首次实证**:final_article.md 首个 `##` 前 2 段 —— para1(prefix40)OK、para2(full)OK,完整进入 final.html。**通过**。
- b. 内容保真守卫:gzh_design 阶段整体通过 → `_intro_content_fidelity` ok=True(2 段,无缺失)。
- c. 代码块:本轮文章无 fenced code(不适用)。
- d. 档 42 两项 WARN(跑后 doctor 实测):`OBS_69_LOCK_MATCH=MATCH`;`OBS_68_PIPELINE_MATCH=DIFF`(1 个文件 `audit/side-effects/ledger.md` 为本档新增未提交 → 报告提交并安装器同步后恢复 MATCH;如实记录,非环境异常)。
- e. OBS-72:见上(硬编码封面,失败点即其表现)。
- f. OBS-70:6 张 asset_id 唯一、1 次新上传 + 5 次幂等跳过,无误判。

## 收尾

- validate_draft_delta:未执行(未到草稿创建,`draft_before.json` 不存在;wechat_draft 在封面校验处失败,零草稿副作用)。
- 复核:四锁 root 未变(`46a00a1b…/18491b36…/0d8aea21…/f59d64bb…`);lock 双侧 `8fb33d83…`;台账仍 2 条;doctor `--require-wechat` PASS(exit 0,FAIL_CLOSED=false)。
- 副作用总账(已更新 `audit/side-effects/ledger.md`):本 RUN 累计真实 uploadimg **6 次**(A-110..A-114、A-109;第 6 次为本档新增),另有 5 条幂等跳过事件;草稿总数仍 3;无封面 add_material、无发布/群发/定时/删除。
- RUN 产物未修改(仅新增批准记录与证据,属批准点正常写入)。

## 需要裁决

1. **OBS-72 修复(档 47 预留)是续跑至草稿的唯一路径**:仓库版封面逻辑硬编码历史 A-003,任何不含该历史文件的新 RUN 都会在此 FAIL_CLOSED。建议授权档 47(修 `producers._wechat` 封面选择:从本 RUN 已批准资产的本地冻结文件选封面 + 校验批准状态)后,本 RUN 可继续走 wechat_draft 至草稿。
2. 或终止本 RUN(副作用 6 次 uploadimg 已登账,证据保留)。

## 证据文件

- RUN 产物:`…\media_enrichment\{copyright_approval.json(7 条), approval_evidence.md, continue\upload_events.json(11 事件), continue\media_manifest.json, article_image_bindings.json}`;`…\gzh_design\final.html`;`…\wechat_draft\stage_failure.json`
