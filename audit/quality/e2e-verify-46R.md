# 档 46R — 端到端复跑:停机于 media_enrichment(aihot 交付数据缺陷,FAIL_CLOSED)

- 报告编号:e2e-verify-46R
- 执行日期:2026-08-02(Asia/Shanghai)
- 状态:**停机**。按档 46R 指令「任一阶段失败即停机,贴出 RUN_ID / STAGE / STATUS / 完整报错,不要自行重试」执行。失败发生在 media_enrichment 阶段,根因是本轮 agent 交付的 aihot 素材数据缺 `source_url` 字段(非流水线代码问题),由 producers 的 FAIL_CLOSED 校验按设计拦截。未自行重试任何阶段。
- RUN_ID:`20260802T220853-codex-sol-luna-max-m6pyv4`(run_dir:`F:\AIXM\wxgzh\.temp\wxgzh-pipeline\20260802T220853-codex-sol-luna-max-m6pyv4`)

## 第零步 连通性预检(通过)

- 微信 token:成功(errcode=None,access_token 存在);出口 IP:`185.217.5.28`(与档 46 停机的 183.221.4.191 不同,已在白名单)。
- 草稿箱 total_count = **3**(预期 3)✓。
- 基线:四锁 root(super-writer `46a00a1b…`/zh-human-writing `18491b36…`/media-enrichment `0d8aea21…`/gzh-design `f59d64bb…`)、两侧 lock sha 均 `8fb33d83…`、台账 2 条 ✓。

## 第一~三步 进度

- aihot 阶段:正常 API 抓取(aihot.virxact.com,3 组查询 42 条原始记录,去重后按主题挑选 12 条;`mode=aihot_api_normal`,非 override);ACK 完成,receipt ok。
- super_writer 阶段:13 个产物生成;官方 `validate_article_length.py`(full-mode)通过(`passed=true`,visible 2287);ACK 完成,receipt ok。
- zh_human_writing 阶段:final_article.md 生成(仅措辞微调,数字/URL/引号全保留);官方 `fidelity_guard.py` exit 0(13 检查 0 失败)、`pattern_audit` 全 0、`change_report` 无保护段变更;fidelity_report.json 六项零门禁;ACK 完成,receipt ok。

## 失败点(完整报错)

```
status: STAGE_FAILED
run_id: 20260802T220853-codex-sol-luna-max-m6pyv4
failed_stage: media_enrichment
error: media_enrichment: entrypoint subprocess failed (exit 2): FAIL_CLOSED: material M-01 source_url disagrees with dedup (FAIL_CLOSED)
fail_closed: true
```

- 根因(已定位,非猜测):`producers._dedup_index`(wxgzh_pipeline/producers.py L338-368)对每条 dedup 条目取 `source_url = it.get("source_url") or it.get("url")`(无 `links.original` 回退);本轮 aihot API 返回的条目普遍只有 `links.original` 而无 `source_url` 字段 → `di["source_url"]=None`;而 canonical_claim_registry 中我写的 material `source_url` 取了 `links.original` → 两者不一致 → FAIL_CLOSED(producers L484-487)。校验器按设计工作,责任在本轮 aihot 交付数据缺字段。

## 观察项(已产生数据的部分,据实)

- a. gzh_design intro 完整性:未到达该阶段(media 前置失败)。
- b. 内容保真守卫:未到达(在 gzh_design 阶段运行)。
- c. fenced code:本轮文章未含代码块(观察项为「若含」,不适用)。
- d. 档 42 两项 WARN:未到达(media 失败时未触发 doctor 输出;WARN 在 doctor 中)。
- e. 媒体批准点:未到达(discover 阶段在入参校验即失败,未进入批准等待)。
- f. 冒烟机制:未触及(relock 未执行),符合预期。

## 恢复方案(待裁决,不自行执行)

1. 修正 aihot 交付数据:给 `deduplicated_items.json`(与 `raw_items.json`)12 条统一补 `source_url = links.original`(fetch_log 保持正常抓取记录)。
2. 重新 ACK aihot 阶段(重算 produced hashes)。
3. `续发`:orchestrator 的 resume 会对已完成的 aihot receipt 做 FULL 校验,发现 produced hash 变更后自动 `invalidated_from=aihot`,重跑 aihot→super_writer→zh_human_writing(需重新交付并 ACK)→media→…→wechat_draft。这是 resume 的正常语义,不是手动阶段重试。
4. 或:裁决以新 RUN 重跑(修正后的 aihot 交付数据直接用于新 RUN)。

## 环境状态

- 无任何微信副作用(未到上传/草稿阶段);草稿箱仍 3 份;四锁/lock/台账未变;证据目录未触碰;未修改被锁 skill、未 relock、未手工编辑 lock;未删除任何文件。
- RUN 产物完整保留在 `.temp\wxgzh-pipeline\20260802T220853-codex-sol-luna-max-m6pyv4\`(aihot/super_writer/zh_human_writing 阶段产物与 receipts)。


## 归因更正(档 48,2026-08-03)

上文「根因…责任在本轮 aihot 交付数据缺字段,非流水线缺陷」表述**作废**。

- 更正:本次失败定性为**流水线缺陷,归入 OBS-31**(aihot URL 位于 `links.*`;`producers._load_dedup_index` 的 URL 提取为 `source_url → url`,缺少 `links.original` 回退,与 canonical_claim_registry 生成侧(source_url → links.original)口径不一致,导致 FAIL_CLOSED)。
- 追加登记 **OBS-81(高)**:比对逻辑对「两侧 source_url 均为 None」判为一致(放行),虽被 registry 前置空值检查兜底,仍是空值一致性缺陷;档 48 已修复为「任一侧取不到 URL 即 FAIL_CLOSED,两侧皆空不构成一致」。
- 修复见 `audit/quality/url-field-contract-48.md`(同源函数 `_material_source_url` + 显式 `_check_material_url_consistency`)。
