# 档 51 — OBS-83 修复 + 守卫联动 + 第三次真实 relock

- 报告编号:obs83-intro-fidelity-51
- 执行日期:2026-08-03(Asia/Shanghai)
- 状态:**完成**。渲染器修复、守卫升级(双向反证)、回流升版 hammer.3、第三次真实 relock(含入口冒烟)全部落地;未发起新 RUN、未调微信接口、未续跑本 RUN、未修改本 RUN 任何产物、未手工编辑 lock。
- 工作副本:`F:\AIXM\wxgzh\repos\wxgzh-pipeline`;gzh 分支:`F:\AIXM\wxgzh\repos\gzh-design-skill-43r-build`

## 第一步 修法设计(先答)

1. **方案选 a(取消 oneliner,首段完整进正文)**。理由:① oneliner 的唯一内容就是 `intro[:40]`,首段正文化后它是纯重复卡片;② 取消后首段只有一个出口(正文),消除「封面/oneliner 截断 vs 正文全文」的语义歧义,守卫定义也随之干净(正文段落级校验);③ 视觉更简洁;④ 与审核者倾向一致。oneliner_card 从 usage 移除;gzh-design 测试无 oneliner 断言(仅 hammer-upgrade/structure-audit.md 文档提及,非断言)。
2. **封面 subtitle[:48] 保留,首段 >48 字封面截断可接受**:封面是设计元素;首段全文已进正文,封面截断不再造成内容缺失(档 43 亦明确封面截断长度不变)。
3. **校验影响**:章节数不变(`##` 驱动);结构指纹(FINGERPRINTS:cover/toc/chapter/signature/footer/img)不含 oneliner;首段与其余 intro 段落同一渲染路径(hammer_para),不触碰任何指纹;usage 仅 oneliner_card 消失、paragraph +1;component_usage_report 由 validator 按指纹重写,不受影响。

## 第二步 渲染器修复(commit `acc7745`,已 push)

- `parse_article`:首行在设 `intro` 的同时**也追加进 intro_paras**(同一路径,无单独分支——避免 OBS-31 式口径分裂)。
- `render`:删除 oneliner 卡片渲染与 `oneliner_card` 计数;封面 subtitle 不变。
- 测试 4 形态(首段 43 字 / 200 字 / 仅首段 / 无 intro):全部 PASS,断言首段全文出现在 hammer_para 正文段落中。

## 第三步 守卫联动升级(双向反证)

- `_intro_content_fidelity` 改为**正文区域**校验:`_body_plain_text` 仅提取 hammer_para 段落与 `<pre>` 代码块(封面/TOC/签名/页脚文本不再计入「存在」);**每个 intro 段落(含首段)同一标准:全文必须完整存在于正文**,prefix 40 容忍删除。
- 反证一(档 50 旧 HTML):**FAIL**(missing = 首段全文)—— 守卫成功拦下「首段只在封面」的假绿。
- 反证二(三篇历史 RUN 旧渲染):RUN1 / RUN2 / 事件 RUN **全部 FAIL**(首段缺失于正文)。
- 用新渲染器重渲染四篇(RUN1 / RUN2 / 事件 / 本 RUN):**全部 PASS**,首段完整进入正文(逐字对照:首段原文与正文段落文本一致)。
- Pipeline 测试重写(正文区域提取、封面-only 首段 FAIL、200 字首段、真实档 50 HTML FAIL 回归)。

## 第四步 回流与升版

- `RELEASE_NOTES.md` 首行 → **v2026.08.02-hammer.3**,写明 OBS-83(首段入正文、oneliner 取消);`WXGZH_PIPELINE_INTEGRATION.md` 版本行同步。
- push:`fix/obs73-codeblock-docs` HEAD = **`acc7745a152d0b2f09794227e1478730f6ffb9a9`**;新哈希:root `b517aec6…`(76)、manifest `ced84143…`(不变)、entrypoint `5356c480…`、version hammer.3、tree `725bd903…`。

## 第五步 第三次真实 relock(成功,exit 0)

- 远端见证 a/b/c PASS;dry-run 全字段核对(含 skill_version hammer.2→hammer.3)。
- `--apply` reason:`档51 gzh-design 升版:OBS-83 首段入正文 + oneliner 取消 + version hammer.3`。
- lock sha:**`8FB33D83… → CDC8F100C2A1D77F9FF87FF1D030C5871AB910B1ECB95376541F2BC713EF1186`**(双侧一致)。
- 台账第三条:`relock-gzh-design-20260803T121024Z-1afb45bd`(root f59d64bb→b517aec6,version hammer.2→hammer.3,commit 9596ecc→acc7745,source_commit_verified=true,doctor_result=PASS)。
- 安装器 PASS;**入口冒烟 PASS(CLI subprocess, production path)**;post-doctor PASS。
- 备份:仓库内 lock 备份 + 仓库外安装树备份(`F:\AIXM\wxgzh-relock-tree-backups\`)。

## 第六步 复核与本 RUN 影响评估

16. `upgrade_regression.py` ALL PASS(排除 1 项);双侧 doctor PASS(exit 0),`OBS_69=MATCH`、`OBS_68=MATCH`(586/586,安装侧与 repo HEAD 逐字一致);四锁 hash_ok 全 true(super-writer `46a00a1b…`/zh-human-writing `18491b36…`/media-enrichment `0d8aea21…`/gzh-design `b517aec6…`);lock 双侧 `CDC8F100…`;台账 3 条。observability 内嵌基线随 lock 同 commit 更新(CDC8F100)。
17. **本 RUN receipt 状态(实证)**:aihot / super_writer / zh_human_writing / **media_enrichment 全部 `ok=true, state=OK`(仍有效)**;gzh_design `ok=false, state=SKILL_UPGRADED`(entry_ids=[1afb45bd],mism=[entrypoint hash mismatch])。**档 52 续跑起点 = gzh_design 重跑**(新渲染器),前四阶段无需重跑;wechat_draft 仍需 OBS-72 修复方可过封面。
18. 本 RUN 前三阶段产物与 handshake hashes 逐字一致(未修改);本档未调微信 → 草稿箱仍 3 份,无新微信副作用。

## 需要裁决

- 档 52:续跑本 RUN(从 gzh_design 重跑)前,仍需 OBS-72(封面选择改自本 RUN 已批准资产)授权修复;OBS-82 保持观察。

## 双仓库 SHA

- Amer-CN/gzh-design-skill:`fix/obs73-codeblock-docs` HEAD = `acc7745a152d0b2f09794227e1478730f6ffb9a9`
- wxgzh-pipeline:本报告 commit = 见提交输出
