# 档 63 — OBS-71 图表路径纳入批准合同(media-enrichment 升版 + 第七次真实 relock)

- 日期:2026-08-04
- 性质:修复档(路径 b——改被锁 media-enrichment + 升版 dev9 + 第七次真实 relock)。
- ★零真实图片上传、零微信调用;事件 RUN 归档只读(重放离线);档 61/62 闸门语义未改(仅扩展可信来源枚举与位置回退,均不构成放宽)。

---

## 第零步 归属判定与批准语义

### 1. 归属:media-enrichment 侧(路径 b)

- known_allowed 硬编码与图表生成都在 **media-enrichment**:`run_media_enrichment.py`
  图表构造段 `copyright_status="known_allowed", decision="eligible"`,
  continue 阶段 `timed_upload(..., copyright_status="known_allowed")` 无条件上传,
  **完全不查询批准合同**(档 35 已实证)。Pipeline 侧无图表生成能力 → 必须改被锁侧。

### 2. 自生成资产的批准语义(先答清楚)

「无版权风险」≠「无需批准」。批准合同管三维,分工如下:

| 维度 | 约束 | 由谁校验 |
|---|---|---|
| 版权 | 图表是流水线基于 canonical claim 数据生成的原创可视化,无第三方版权——由 media 侧**声明**(source=generated)并经人工批准点确认;素材版权未知不传染给图表,但也不构成自动豁免 | media 侧声明 + 人工批准 |
| 数量 | 图表必须计入 `max_total_images` 上限;上传数 ≤ 批准数(每条上传都对应一条已消费的 single_asset 批准) | media 侧硬上限(本档新增)+ Pipeline 配置 |
| 内容适配性 | 图表指标/数据点/图表类型必须与文章相关、数量合理——批准清单必须呈现图表内容描述与数据来源,人工据此判断 | 人工批准(信息由 media 呈现,OBS-87 闸门强制) |

- **本档不是「给图表加一条版权白名单」**:known_allowed 硬编码被移除,图表与源图
  走同一条批准路径(决策 review_required → 单资产批准 → 消费后 known_allowed → 上传门)。

## 第一步 取证

### 3. 图表链路(修复前)

- 生成:`run_media_enrichment.py` 图表段(discover 与 continue 均执行;continue 重新
  生成且直接上传)。
- copyright_status:构造时硬编码 `known_allowed`;`decision="eligible"`。
- 上传前查不查批准合同:**不查**——`timed_upload(copyright_status="known_allowed")`
  绕过 `asset_approvals` 与材料 `copyright_review`;上传门仅 `phase==continue` +
  `discovery_file_valid`。
- 数量:图表循环无 `max_total_images`/`max_images_per_material` 检查(`asset_counter`
  无条件递增);冻结清单(asset_discovery_manifest)不含图表(discovery_records 未追加)。

### 4. 事件 RUN 12 次上传为何未被幂等拦住

- OBS-53 幂等键 = `asset_id`(continue 按 asset_id 查既有 success 事件)。
- 事件 RUN 两轮上传为 A-001..A-006(补丁前编号)与 A-032..A-037(补丁后编号),
  **asset_id 不同 → 幂等未命中**;内容 sha 完全一致(6 张唯一图表各 2 次)。
- 与 OBS-70 的关系:OBS-70 主张去重键应为 sha256 而非 asset_id——若按 sha 去重,
  两轮会命中同一键。修复后图表必须经批准才上传,「未批准零上传」已阻断该场景的
  第一轮;OBS-70 仍未修(本档不动,如实说明)。

### 5. known_allowed 其余使用点(逐处)

| 位置 | 用途 | 判定 |
|---|---|---|
| `run_media_enrichment.py` L170/L251 | 材料级 `copyright_review.status=known_allowed`(来自合同) | 合法(合同消费) |
| L515-551 | continue 单资产批准消费后置 known_allowed | 合法(显式批准) |
| L563-567 | 上传门条件(known_allowed + eligible + pass + relevant) | 合法(批准后的唯一上传通道) |
| 图表构造段(已删) | 硬编码 known_allowed/eligible | **同型破口,本档移除** |
| `generate_evidence.py`/tests | 测试证据/夹具 | 非运行路径 |

- 结论:常量 `known_allowed` 保留——它是「批准消费后的状态标记」与上传门条件,
  **不再是任何构造时豁免**;图表路径的硬编码豁免已彻底移除。

## 第二步 实施(media-enrichment 0.1.0-dev9)

1. **图表纳入批准链**:discover 生成图表决策 `review_required`、版权 `unknown`、
   `relevance_status="uncertain"`、reasons 注明 OBS-71;continue 阶段**不重新生成**
   图表,从冻结清单重建(与源资产同机制,`pending_uploads` 同一批准消费+上传门)。
   已批准图表才上传;未批准零上传。
2. **数量**:图表循环受 `max_total_images` 约束,超限跳过并告警;`total_assets_added`
   计入图表。
3. **内容描述与来源**:`content_description` 来自图表 spec(`生成图表({type})「{title}」,数据来源:{source_note}`),
   `content_description_source="generated"`——不使用 claim 派生文本填充(测试断言
   非 claim 前缀);渲染用 caption/alt 保留 spec 标题。
4. **稳定身份入冻结清单**:图表 discovery_record 含
   material_id(排序取首个,确定性)/source_page_url(数据源页面)/
   resolved_original_url(`{src}#chart-{sha[:12]}`,合成来源引用)/
   asset_sha256/asset_identity_sha256/asset_origin;`material_ids`/`claim_ids`
   排序保证跨进程确定性(修复 `set()` 顺序导致的 fresh_* 失配)。
5. **material 级批准不再覆盖图表**:`material_approved_ids` 排除 generated 资产——
   图表必须显式 single_asset 批准(避免材料批准自动带出图表)。
6. **continue 重建细节**:generated 资产允许 `charts/` 目录本地文件、跳过
   `is_safe_url`(生成物从不被 fetch)。
7. **封面联动(第 8 条)**:OBS-72 封面三条件(单资产批准 + 上传成功 + 本地 sha 一致)
   对图表同样生效——未批准图表既不能上传也不能作封面;事件 RUN 的未批准
   chart-001 封面场景不可再现。
8. **Pipeline 配套**(不放宽闸门语义):`approval_evidence.py` 可信来源枚举
   + `generated`;generated 资产位置回退 `placement.anchor`(文章内拟绑定章节,
   `level="article-anchor"`);「位置必须已知 + 内容可验证才可批准」语义不变。

## 第三步 事件 RUN 重放回归(硬验收)

- UNCONTROLLED.md(审计归档副本)已含 fail-closed 契约声明(档 37 原载),本档追加
  档 63 补注记录验证结果;`.temp` 事件 RUN 目录零改动。
- 夹具冻结:`tests/fixtures/obs71/`(事件 RUN 的 media_discovery_request.json 逐字
  复制、final_article.md、14 个页面 fixture),不引用任何会被重跑覆盖的实时文件。
- 隔离手段:全部 CLI 子进程 `offline_fixture` + `dry_run`/`wechat_audit`(确定性
  URL,零网络零微信)。
- 验证结果(`tests/test_obs71_chart_approval.py`,4 项全过):
  - **重放 discover**:6 张图表全部 `review_required`/`unknown`/`content_description_source=generated`/
    身份字段齐全/冻结清单含图表;
  - **★重放 continue + asset_approvals=[]**:rc=0,`upload_events=[]`(零上传),
    全部资产 `not_uploaded`、`asset_approval_consumed=false`——**fail-closed,
    零上传、零草稿、零微信副作用**;
  - 重放 continue + 单张图表批准:仅该张上传(1 条事件)、批准消费、其余图表不上传;
  - 数量上限:max_total_images=1 时图表被拦截(告警可见)。

## 第四步 安全属性复核(九条,按本档口径编号)

| # | 属性 | 复核结果 |
|---|---|---|
| 2 | 上传数量上限 | **恢复**:图表计入 max_total_images;上传数 ≤ 批准数(每条上传对应已消费批准)。事件 RUN 12 次上传场景在重放中零上传。 |
| 3 | 封面来自本地冻结文件 | 保持:OBS-72 三条件对图表生效;未批准图表不可作封面(事件 RUN chart-001 封面不可再现)。 |
| 5 | 显式批准(候选清单交人工审批) | **恢复**:图表经批准点;approval_readiness 呈现图表内容描述与数据来源;重放无批准即零上传。 |
| 6 | 无自动批准路径 | **恢复**:known_allowed 硬编码移除,无新增自动批准路径(无新开关/新豁免);图表与源图同一批准+上传门。 |

- 「图表路径豁免」标注:**可撤销**。唯一残留豁免为操作层纪律(人工批准点必须
  实际停下等待),代码层已无任何图表自动放行路径;material 级批准合法存在(来自
  合同),且已显式排除对图表的覆盖。

## 第五步 复核(路径 b)

- **第七次真实 relock --apply 全链**:远端见证 PASS → 计算
  (root `273314e0→181752eb`、manifest/count 不变 `5533c0c8/59`、
  entrypoint `a96554e4→ab97f1ef`、commit `08c7b22→18414cc`、
  tree `a9b6b3e2→64755773`、version `dev8→dev9`)→ 仓库外备份 → lock+台账
  (第 7 条 `relock-media-enrichment-20260804T081330Z-86eefa4e`)→ 安装器 PASS →
  post-doctor PASS → **入口冒烟 PASS**。
- 回归首轮仅 OBS-69 基线 3 项失败(内嵌基线未随 lock 更新)→ 按档 57/62 既定
  配套同步 `REPO_LOCK_SHA256`(EEE1A1E9 → **81F9342A…**)→
  **upgrade_regression ALL PASS**(排除清单仍 1 项,cross-side 仍 SKIP)。
- lock 双侧 sha:`81F9342A617893FBE3C51C4FCDCFFCB89E76D43EE4735F5FDB81B6422B951058`。
- 台账 7 条(第 7 条 entry_id `86eefa4e`);四锁 hash_ok 全 true;doctor PASS;
  安装侧与 repo HEAD 逐字一致(OBS_68 MATCH)。
- 副作用总账:与档 59 终稿完全一致——草稿箱 2、uploadimg 22、add_material 4、
  发布 0;本档零微信调用。

## 变更文件

- **media-enrichment 仓(`restore/local-patches-obs42-53`,commit `18414cc`)**:
  `scripts/run_media_enrichment.py`(图表批准链/数量/确定性/重建)、
  `src/media_enrichment/manifest_builder.py`(content_description 字段)、
  `schemas/media_manifest.schema.json`、`tests/test_obs71_chart_approval.py`(新增,4 项)、
  `tests/fixtures/obs71/`(事件 RUN 冻结夹具)、版本声明 11 处 + CHANGELOG。
- **wxgzh-pipeline 仓(`dev/0.1.0-dev2`)**:
  `wxgzh_pipeline/approval_evidence.py`(generated 来源 + 图表位置回退,语义不变)、
  `tests/test_obs87_approval_evidence.py`(+3 项图表 readiness 测试)、
  `wxgzh_pipeline/observability.py`(OBS-69 基线同步)、
  `audit/runs/…/UNCONTROLLED.md`(档 63 补注)、本报告。
