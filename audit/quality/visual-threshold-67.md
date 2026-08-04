# 档 67 第二段 — 视觉内容门槛分级 + OBS-89 同数据重复检测(路径 a)

- RUN_ID:`20260804T174355-vibe-coding-guide-v2-1-6-by4s00`
- 状态:**已到媒体批准点;新 readiness 下 3 张图表可批准(A-005/A-007/A-009)**
  ★停在批准点等审批准清单,未 continue(批准与续跑在下一段)。
- 本档副作用:零 uploadimg、零 add_material、零草稿、零发布、零微信调用。

---

## 第零步 归属判定:路径 a(Pipeline 侧,不动锁)

1. **两处协同(取证)**:`stages/media_enrichment.py content_validate` 读取
   `validation_config.json`(默认 `body_images_min=6`)→ 传参给
   `validators/validate_media_bindings.py`(`MIN_BODY_IMAGES=6` 仅是默认参数值,
   `body_images_min` 参数全覆盖,校验器自身无独立硬下限,最低允许 1);
   **媒体 skill(被锁)本身无任何 min 检查**(全仓 grep 为空)。
   即门槛协同 =「Pipeline 侧计算 → 作为参数传给 Pipeline 仓库的官方校验器」。
- **分级落 Pipeline 侧(路径 a)**:判据输入 = `zh_human_writing/final_article.md`
  (冻结产物),Pipeline 可算;校验器在 Pipeline 仓库(`validators/`),传参即可,
  无需改被锁 skill、无需 relock。lock 与台账不变(复核见第五步)。

## 第一步 分级判据定义(客观,无人工字段/开关/profile)

2. **判据完整定义与计算**(每个量均从产物算出):
   - `code_blocks` = `final_article.md` 中成对 ``` 围栏、含 ≥1 行非空内容的
     代码块数量(`visual_threshold.count_code_blocks`;空围栏不计);
   - `code_dense` = `code_blocks >= 2`(独立理由:单个代码块可能是引用性片段,
     不足以定义文章形态;≥2 说明文章以代码/命令为主体,属技术文);
   - 非 `code_dense`(新闻综述)→ `body_images_min = 6`(默认,不降低);
   - `code_dense` → `body_images_min = 3`(最低可见性基线)
     且要求 `body_images + code_blocks >= 5`(视觉内容达标)。
3. **为何不能用作通用降门槛通道**:判据只看文章自身代码结构,与图片数量、批准
   记录、来源无关;新闻综述(0 代码块)恒为 6。★代入验证(本档核心验收):
   - RUN1 `20260731T135947`(fences=0)→ `code_dense=false` → **门槛 6 不降低**;
   - RUN2 `20260801T182628`(fences=0)→ **门槛 6 不降低**;
   - 电车 RUN `20260802T220853`(fences=0)→ **门槛 6 不降低**(分级未放松任何一项,
     档 60 的 6 张电车图仍需逐张过批准闸门)。
4. **代码块权重依据(独立,非为本篇反推)**:
   - 权重 1:1:微信正文中代码块与正文图同为「全宽、分隔文本流」的视觉组件;
     gzh-design 渲染体系中 `hammer_code_block` 与图片组件均 100% 宽度,10 行代码块
     渲染高约 250px,16:9 图在 375px 宽下高约 211px,高度比 ≈1.18 → 保守取整 1:1
     (不夸大代码视觉贡献;若取更高权重则高估代码,属主动放宽);
   - 视觉锚点下限 5:3000+ 字长文约每 600-800 字需要一个视觉锚点(图片或代码块,
     可读性基线),3950 字文章 → ≥5 锚点,5 为保守下界。两项依据均不依赖本篇文章
     的具体数字。
   - `effective_body_images_min(tier, config)`:无 config → 分级值;有 config →
     `max(分级值, config)`(分级值是文章类型的客观下限,人工 config 不得把新闻类
     压到 6 以下——旧 RUN1 的「reviewer 设 body_images_min=2」路径在新闻类被分级
     下限封死)。

## 第二步 OBS-89 同数据重复检测

5. **实现**(`visual_threshold.dedup_same_data_charts`,挂在
   `approval_evidence.build_approval_readiness`):生成图表按
   `chart_group` + 其 `claim_ids` 对应 claims 的 numbers 集合(排序后的
   (value, unit) 元组)分组;同组仅保留一张,其余标记 `duplicate_of=<保留者>`
   且 `approvable=false` + blocker「OBS-89: 同 chart_group 同 numbers,
   仅保留确定性形态(bar),同数据重复不得进入批准合同」。
6. **确定性规则(不由人工挑选)**:优先 bar 形态(从 `content_description`
   `生成图表(<type>)` 解析),解析失败回退最小 asset_id。依据:数据点为 2 个版本
   对比时,bar 是单指标多版本对比的基础形态,comparison 的并列增强在仅 2 个
   数据点时与 bar 视觉信息等价(无信息增量);保留 bar 确定性、可审计。
7. **测试**(`tests/test_obs67_visual_threshold.py`,12 项全过):同组重复识别/
   不同组不误判/duplicate 不可批准/单组收敛 1 张;★反向验证:本 RUN 6 张图表
   收敛为 3 张可批准(A-005/A-007/A-009,bar 形态)。

## 第三步 分级实施与验证

8. **实施**:
   - `stages/media_enrichment.py content_validate`:由 `final_article.md` 计算
     tier;无 config 时 `body_images_min` = 分级值,有 config 时取 max;code_dense
     时额外校验 `visual_units = body_image_count + code_blocks >= 5`,不满足即
     FAIL(通过理由=视觉内容达标,非图片数量豁免);
   - `approval_evidence.build_approval_readiness`:OBS-89 去重 + 输出
     `visual_tier` 块(code_blocks/code_dense/body_images_min/visual_units_min/
     criterion)。
9. **★反向验证三组**:
   a. 本 RUN(3 图表 + 2 代码块):`readiness` 重算 → `summary {total:10, approvable:3,
      blocked:7}`,tier `code_blocks=2 / code_dense=true / body_images_min=3 /
      visual_units_min=5`;3 图表 + 2 代码块 = 5 视觉单元 ≥5 → **通过,视觉内容达标**;
   b. RUN1/RUN2(零代码块):tier `code_dense=false / body_images_min=6` → **门槛不降低**;
   c. 电车 RUN(零代码块):tier `body_images_min=6` → **分级未放松任何一项**。
10. **留痕**:分级判据各项实际取值写入 `approval_readiness.json` 的 `visual_tier`
    块(批准点可见)+ 下一段 media 阶段 `stage_result.json` 的
    `validator_report.VISUAL_TIER`(receipt 绑定);本报告记录 by4s00 实测值。
11. **夹具冻结**:`tests/fixtures/obs67/`(registry 6 claims + 6 图表 manifest +
    code_dense/news 两种文章),不引用会被重跑覆盖的实时文件。

## 第四步 复核

12. 副作用:零 uploadimg、零 add_material、零草稿、零发布(本段仅重算 readiness,
    未触碰文章/批准合同/冻结清单)。
13. `upgrade_regression.py` **ALL PASS**(pytest 全量 PASS,仅 4 项预存环境失败
    排除清单外;排除清单仍 1 项;四锁 relock dry-run 全部「无变化」;doctor
    --require-wechat PASS;cross-side 仍 SKIP)。
14. 路径 a 复核项:lock 双侧 `81F9342A617893FBE3C51C4FCDCFFCB89E76D43EE4735F5FDB81B6422B951058`
    **未变**;台账仍 **7 条**;四锁 hash_ok 全 true;doctor PASS;安装侧经正式安装器
    同步后与 repo HEAD 逐字一致(OBS_68 MATCH)。

## 变更文件(wxgzh-pipeline 仓,`dev/0.1.0-dev2`)

- `wxgzh_pipeline/visual_threshold.py`(新增):分级判据 + OBS-89 去重
- `wxgzh_pipeline/approval_evidence.py`:readiness 挂 OBS-89 + visual_tier 块
- `wxgzh_pipeline/stages/media_enrichment.py`:分级门槛 + 视觉单元校验
- `tests/test_obs67_visual_threshold.py`(新增,12 项)+ `tests/fixtures/obs67/`
- `audit/quality/visual-threshold-67.md`(本报告)
