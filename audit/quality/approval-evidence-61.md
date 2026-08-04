# 档 61 — OBS-87 批准信息链修复(只动 Pipeline 侧)

- 日期:2026-08-04
- 性质:修复档。改 Pipeline 侧代码 + 测试 + 报告;**未动任何被锁 skill、未 relock、未改 lock/台账、零微信调用**。
- 验收条件(第 8 项):六张电车图在新逻辑下必须显示「内容不明」+ 页面位置指向汽车新闻章节,且无法以档 50 那种理由被批准。

---

## 第一步 切断自证闭环

### 1.1 取证:claim 派生 alt_text 的下游消费链(逐处)

派生生产点 `placement_planner.py`:

```python
# placement_planner.py L67-68(同 L84-85/L94-95)
caption=f"图：{claim_text[:40]}",
alt_text=claim_text[:60],
```

下游消费(全链实测):

| # | 位置 | 用途 |
|---|---|---|
| 1 | `run_media_enrichment.py` L648 `asset.caption = placement.caption; asset.alt_text = placement.alt_text` | 非生成资产统一写入派生文本 |
| 2 | `manifest_builder.py` L96 | 写入 discover `media_manifest.json`(批准清单呈现物) |
| 3 | `article_bindings.py` L73 `"alt_text": asset.get("alt_text")` | 写入 `article_image_bindings.json` |
| 4 | `gzh-design/scripts/render_article.py` L184-196(`img.get("caption") or img.get("alt_text")`) | 渲染为 HTML **alt 属性 + 图注(figcaption)**,进入草稿正文 |
| 5 | 批准环节(档 49/50 实证) | 审核者直接读 manifest 的 alt_text 作为「内容适配性」依据——**自证闭环核心** |

结论:同一字段被批准环节与渲染环节共用;批准环节读到的「图片描述」实际是文章自己的 claim 文本。档 50 的 A-109 批准理由即由此产生(实为小米汽车图)。

### 1.2 字段分离方案(命名与改造)

- **图片内容描述**(新增,批准链专用):manifest asset 新字段 `content_description` + `content_description_source`。
  - 取值必须来自图片自身或其页面上下文;`content_description_source ∈ {page_alt, page_context, human, visual_analysis}`。
  - 产出侧在 media-enrichment(OBS-86/档 62)落实;Pipeline 侧(本档)先立字段级闸门:当前 manifest 无此字段 → 全部 FAIL_CLOSED。
- **渲染用 alt**(保留):`alt_text` 继续允许 claim 派生,仅用于 HTML alt/图注输出(第 2 条允许)。本档不改渲染路径。
- **「内容不明」**(readiness 呈现态,三值):`claim_derived` / `empty` / `unverifiable`。它不是放行理由也不是拒绝理由,是必须呈现给批准者的事实;「缺少可验证内容描述」使资产不得进入批准点(第 5 条)。

### 1.3 实现

新增 `wxgzh_pipeline/approval_evidence.py`:

- `assess_content()`:四态评估(verified / claim_derived / empty / unverifiable);派生检测保守化——文本是某条 claim 的前缀(≤60/40 窗口)即判派生,宁可多标「内容不明」。
- 口径说明(OBS-31 教训):本模块只做「检测派生痕迹」,不生产派生值;闸门阻断力来自字段级要求,即使检测漏判,字段缺失依然 FAIL_CLOSED。
- `extract_section_map()` / `fetch_html()`:DOM 文档序前置 h1/h2/h3 定位(与档 60 取证方法一致);抓取失败 → 位置未知 → 不得进入批准点,不允许降级。

## 第二步 批准清单增强

### 2.1 呈现物:`approval_readiness.json`

discover 完成后、等待人工批准前,管线写入 `media_enrichment/approval_readiness.json`(与 OBS-82 的 `approval_precheck.json` 并列)。逐张呈现:

```
asset_id / decision / content(kind+description+source) /
page_position(heading+level) / approvable / approvable_blockers
```

- 六张真实资产呈现示例(实测):`A-109 content.kind=claim_derived, description=内容不明(alt_text/caption 为文章 claim 派生文本,非图片内容描述), page_position.heading=「4、29.99 万元!小米澎程 N90 Max 增程 SUV 预售价格公布」, approvable=false`。
- 缺内容描述或页面位置的资产不得进入批准点:`approvable=false` + 具体 blocker;消费端 `enforce_approval_readiness()` 对合同逐条校验,任一不满足即 FAIL_CLOSED(而非降级呈现)。

### 2.2 rejected 资产不得写入批准合同(与 OBS-82 的分界)

- OBS-82(档55):物理门槛——尺寸 <640×360 挡在批准外(A-107 的 100×100 场景)。
- OBS-87(本档):批准语义门槛——`decision=rejected` 的资产在 readiness 中 `approvable=false`(blocker:`decision=rejected — 非可批准状态,不得写入批准合同`),即使尺寸达标(如 800×800 的 logo 类)也被拦;合同中出现即消费端 FAIL_CLOSED。
- 分界:OBS-82 管「物理达标」,OBS-87 管「语义可批准 + 信息完备」,两者独立叠加。

### 2.3 旧合同自动失效(第 11 条)

- 消费端要求每条 single_asset 批准记录携带 `approval_readiness_sha256` 且等于当前 `approval_readiness.json` 的 sha256。
- 档 49/50 的 `AP-20260803T194207-INDEPENDENT-REVIEW-001/002` **无此字段 → 自动失效**,任何后续 RUN 消费即 FAIL_CLOSED(`旧批准合同自动失效,不得复用`)。原记录文件未删除、未改写(零改动 RUN 产物),失效由消费端强制。

## 第三步 测试

`tests/test_obs87_approval_evidence.py` — **15 项全部 PASS**;夹具 `tests/fixtures/obs87/`(冻结,不引用实时文件):

- `manifest.json`:六张真实资产 + A-107/A-108 拒绝样本(自 RUN discover manifest 逐字复制,含 canonical `discovery_manifest_sha256`)
- `claims.json`:同 RUN 全部 claim_text(C-06 实测 120 字,alt == `ct[:60]` 成立)
- `page_sections.json`:六图页面位置(2026-08-04 现场 DOM 实测冻结)

关键用例:

1. **派生检测**:`alt == ct[:60]` / `caption == 图：ct[:40]` → 派生;无关文本 → 非派生。
2. **六张真实资产**:全部 `content.kind=claim_derived`、位置 known 且指向汽车/机票章节(A-109→小米澎程 N90 Max / A-110→比亚迪大汉 / A-111→比亚迪海獭 / A-112→特斯拉 1000 万辆 / A-113→OpenAI 降价 / A-114→携程退票),`approvable=false`,summary approvable=0。
3. **★反向验证(第 8 项)**:以档 50 式批准(A-109 + claim 派生理由)跑 `enforce_approval_readiness` → FAIL_CLOSED,报错含「缺少可验证内容描述(claim_derived)」——**修好的机制拦住了当初那次误批**。
4. **旧合同自动失效**:无 `approval_readiness_sha256` / sha 过期 → FAIL_CLOSED。
5. **rejected 拦截**:A-107/A-108 真实样本 approvable=false(blocker 含 `decision=rejected`),合同消费 FAIL_CLOSED。
6. **放行路径**:有 `content_description`(source=page_alt,非派生)+ 位置已知 → approvable=true,合同通过。
7. **渲染 alt 不受影响**:readiness 构建后 `media_manifest.json` 与 `article_image_bindings.json` 字节级未变(渲染路径未触碰)。
8. manifest/registry 缺失 → FAIL_CLOSED;OBS-82 预检函数与测试原样通过(全量回归见下)。

## 第四步 作废声明(追加式,不改原记录)

**自本档起,以下两份批准记录判定无效,不得被任何后续 RUN 复用或消费:**

- `AP-20260803T194207-INDEPENDENT-REVIEW-001`(A-110/A-111/A-112/A-113/A-114/A-107)
- `AP-20260803T195315-INDEPENDENT-REVIEW-002`(A-109)

**理由**:批准信息链缺陷——批准清单呈现的 alt_text 为文章 claim 派生文本(非图片内容描述),审核者被自证文本误导,无法履行内容适配性判断(假绿第六例)。原记录文件保持原样(禁止修改 RUN 产物),作废以本声明 + 消费端 `approval_readiness_sha256` 强制校验双重留档。草稿 #4 的配图自档 60 裁决起已冻结为物证,本档不触碰。

## 第五步 账目更正与复核

### 5.1 OBS-29 补登(第 12 条)

- 事实:OBS-29 在仓库(含 git 历史、全部 audit)检索不到登记文本——此前引用它属于「拿不存在的记录当依据」(缺陷第 37 处),据实更正。
- **补登 OBS-29(高)**:素材(claim/材料)层无主题相关性门禁——素材与文章主题的匹配从未被校验,是相关性缺陷链的最上游(素材层)。
- 与 OBS-86/87 的层级关系:**同一根因链的三个层级**:OBS-29(素材层:不相关素材进入)→ OBS-86(资产层:发现不区分正文/周边)→ OBS-87(批准层:人工无内容信息可依)。本档修复批准层;资产层(档 62)与素材层(单列)后续。

### 5.2 缺陷第 38 处记录

- 上一轮对「vibe-coding-guide 不会踩 OBS-86」的判断有误:素材 URL 经 `producers._material_source_url` 直入 fetch,GitHub 素材走同一条全页抓图路径;事件 RUN `stage_failure.json` 的 `FAIL_CLOSED: dedup source_url https://github.com/Amer-CN/vibe-coding-guide…` 即该 URL 进入同一链路的实证(此前凭 UNCONTROLLED.md 推断,未查 fetch 入口)。已在本档 `approval_evidence.py` 设计上对任意来源页统一要求「位置可验证」,不区分新闻页/GitHub。

### 5.3 复核(第 13-14 项)

- `upgrade_regression.py`:**ALL PASS**(pytest 全量 PASS,排除清单仍 1 项 `test_portable_installer_preserves_pipeline_release_include`;四锁 relock dry-run 全部「无变化」;doctor --require-wechat PASS;cross-side 仍 SKIP)。
- doctor:五技能(四锁 + aihot)`hash_ok` 全 true,`FAIL_CLOSED=false`,`doctor: PASS`;OBS_69 lock MATCH(双侧 `0fdf2ece…`);OBS_68 pipeline MATCH(614 文件,0 差异)。
- 双侧 `skills.lock.json` sha:`0FDF2ECECD1FCD9A8A4957F004D7C2EDA8D99DF8C69C9AC3ED9D6730C559421E`(未变)。
- 台账:仍 **5 条**(`59d63817`/`843f9372`/`1afb45bd`/`a0ec5388`/`29b8f728`);本档零写入。
- 安装侧同步:经正式安装器(bundle-staging-61/portable-bundle,locked-skills=安装侧四锁树、wxgzh-pipeline=repo HEAD、MANIFEST 逐文件 sha256 绑定、source-proofs 与 lock 一致)实装 `ok=true`,四锁 `runtime_root_match/runtime_manifest_match/receipt_written/verify_all_ok` 全 true;安装侧与 repo HEAD 逐字一致(614 文件 0 差异)。
- 副作用总账:与档 59 终稿完全一致——草稿箱 **2** 份、累计 uploadimg **22** 次、封面 add_material **4** 次、发布 **0**。本档零微信调用(doctor 的 wechat 检查仅验凭据存在性,零网络)。

## 变更文件

- `wxgzh_pipeline/approval_evidence.py`(新增):OBS-87 闸门(派生检测/内容评估/位置解析/readiness 构建/消费端强制)
- `wxgzh_pipeline/producers.py`(修改):discover 后写 `approval_readiness.json`;消费前 `enforce_approval_readiness`;`ApprovalEvidenceError` 纳入 FAIL_CLOSED
- `tests/test_obs87_approval_evidence.py`(新增):15 项测试(含六张真实资产反向验证)
- `tests/fixtures/obs87/`(新增):manifest.json / claims.json / page_sections.json(冻结回归夹具)
