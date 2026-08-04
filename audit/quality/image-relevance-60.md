# 档 60 — 配图相关性取证 + OBS-86/87 登记

- 日期:2026-08-04
- 性质:**纯只读取证**。零代码改动、零微信调用、零产物修改、零 lock/台账改动。
- 取证对象:RUN `20260802T220853-codex-sol-luna-max-m6pyv4`(文章《Codex 用 Sol 指挥 Luna Max 省额度翻倍产出》)
- 证据目录:`.temp/wxgzh-pipeline/20260802T220853-codex-sol-luna-max-m6pyv4/media_enrichment/`(discover/continue 两阶段产物)
- 辅助取证:2026-08-04 现场抓取源页 `https://www.ithome.com/0/983/917.htm` DOM(指令允许);六图视觉拼接图存于 `.temp/obs60-grid.jpg`(临时取证件,不入库)

---

## 第一步 逐张取证(本档核心)

### 1.1 六张资产元数据

数据源:`discover/media_manifest.json` + `article_image_bindings.json`(continue 最终版,六张已上传微信图床)。

| asset_id | 原始 URL(ithome 图片直链) | 尺寸 | sha256(冻结清单) | 绑定章节 |
|---|---|---|---|---|
| A-109 | `img.ithome.com/newsuploadfiles/2026/7/73648c29-…jpg` | 1440×658 | `73b4e06d…` | 标题锚点 `# Codex 用 Sol 指挥 Luna Max 省额度翻倍产出`(confidence 0.5, after) |
| A-110 | `img.ithome.com/newsuploadfiles/2026/7/223135f7-…jpg` | 1080×1920 | `0b873fce…` | 同上 |
| A-111 | `img.ithome.com/newsuploadfiles/2026/7/22c6f53e-…jpg` | 1234×674 | `27460e24…` | 同上 |
| A-112 | `img.ithome.com/newsuploadfiles/2026/7/6555a03f-…jpg` | 1440×3120 | `81f3e427…` | 同上 |
| A-113 | `img.ithome.com/newsuploadfiles/2026/7/f8292a43-…png` | 1292×1272 | `6ba9dc54…` | 同上 |
| A-114 | `img.ithome.com/newsuploadfiles/2026/7/75ea2358-…jpg?x-bce-process=…` | 646×1148 | `8680b39c…` | 同上 |

- **alt_text 六张完全相同**,均为 C-06 claim 文本:「OpenAI 于 7 月 31 日宣布下调 GPT-5.6 Terra 和 GPT-5.6 Luna 两款模型的调用费用」。
- **绑定章节**:六张全部绑定到文章**标题锚点**(H1),不是任何正文章节——`placement_planner` 将 C-06(主题 claim)的 placement 套用到全部六张。
- 页面 img 自带 alt 属性:**A-109..A-113 为空,A-114 为「图片」**(2026-08-04 现场 DOM 实测)——即页内根本没有可用的图片内容描述;manifest 中的 alt_text 不是页面 alt,是 claim 派生文本(见 2.3)。

### 1.2 逐张内容主题判定(与文章主题「Codex 用 Sol 指挥 Luna Max 省额度」比对)

方法:现场抓取源页 DOM,按文档序取每张图**前最近 h2 章节**定位所属新闻条目;并六图视觉拼接确认。

| asset_id | 源页所属章节(前最近 h2) | 视觉确认 | 主题判定 |
|---|---|---|---|
| A-109 | #4「29.99 万元!小米澎程 N90 Max 增程 SUV 预售价格公布」 | 深色夜景汽车图 | **无关**(小米 SUV) |
| A-110 | #14「比亚迪大汉核心信息公布:四驱版 3.8 秒破百…」 | 金色汽车图 | **无关**(比亚迪电动车) |
| A-111 | #18「消息称比亚迪日本海獭 RACCO 微型车…」 | 车展长图 | **无关**(比亚迪微型车) |
| A-112 | #20「特斯拉全球第 1000 万辆电动车下线」 | 长图汽车 | **无关**(特斯拉电动车) |
| A-113 | #2「降价 80%!OpenAI 下调 GPT-5.6 Luna 模型费用…」 | 白底截图(价格/数据类) | **相关**(与文章主题直接对应) |
| A-114 | #3「携程回应“1.5 万元机票天价退票费全额退还”…」 | 灰调图 | **无关**(携程机票退票) |

- **结论:用户肉眼所见「配图全是电车」成立。** 6 张中 4 张(A-109/110/111/112)为汽车新闻配图,1 张(A-114)为机票新闻配图,仅 1 张(A-113)与文章主题相关。此前档 49/50 报告把 A-109 表述为「该论点的新闻原图」,与本次取证不符——据实更正,不再修饰。
- 注意:图与章节的对应关系是按 DOM 文档序的前置 h2 推定 + 视觉双重确认;A-109 的前置章节为小米 SUV,且视觉为汽车图,两项证据一致。

### 1.3 alt_text 缺失问题

- 页内 alt 为空 → 批准链上唯一的「alt_text」是 claim 派生文本(`claim_text[:60]`,见 2.3),**不是图片内容描述**。
- 因此批准环节实际**无从判断图片内容**:A-109 被档 50 以「alt_text 与第三章论点对应」为由批准,而该图实为小米汽车图——alt_text 文本恰好来自同页 #2 的 claim,造成内容适配性误判。**alt_text 缺失/失真是 OBS-87 的直接证据。**

---

## 第二步 抓取范围取证

### 2.1 选取范围:全页 `<img>` 提取,无正文边界判定

`src/media_enrichment/image_extractor.py` `extract_images()` 核心:

```python
soup = BeautifulSoup(html, "html.parser")
# 1. img[src]
for img in soup.find_all("img", src=True):          # ← 全文档 img,无容器选择
    ...
# 2. img[srcset] 和 source[srcset]
for elem in soup.find_all(attrs={"srcset": True}):   # ← 全文档 srcset
    ...
# 3. img[data-src]/data-original/data-lazy-src
# 4. meta[og:image]  5. meta[twitter:image]  6. JSON-LD image  7. CSS background-image
```

- `page_fetcher.py` `fetch_page()` 仅做整页 HTML 获取(10 MB 上限)+ 重定向/SSRF 检查,**无任何 article/main 容器选择,无侧边栏/推荐位/信息流/页脚排除**。
- 唯一与「位置」沾边的数据是 `ImageCandidate.context = str(img)[:200]`(img 标签前后 200 字符),且只用于 avatar/logo/ad 字样识别,与正文区域判定无关。
- 实测:122 个候选 / 6 页 ≈ 每页 20 个,108 个被拒,大量为页面家具(头像、logo、广告、tracking pixel、小缩略图)——与全页抓取行为一致。A-109..A-114 正是**推荐位/信息流缩略图**级别的内容(A-110 甚至 1080×1920 竖图),全部进入候选。

**结论:抓取范围=整页,不区分正文内容图与页面周边图,无正文边界判定。** OBS-86 成立。

### 2.2 A-108(1×1 tracking pixel)为何能进入候选清单

- A-108(`img.ithome.com/images/v2/t.png`,1×1)在 discover 阶段**被分配 asset_id 并被下载**(本地文件 `discover/images/11b9c95a….png` 存在),随后被 `image_classifier.py` 拒绝:decision=`rejected`,reason=`1x1 or smaller — likely tracking pixel`(confidence 0.99)。
- 原因:全页提取对每个 img 都产候选并下载,过滤全部交给下游分类器。tracking pixel 恰好被「尺寸 <5×5」规则拦住;**与电车缩略图同一根因**(发现层对页面结构无感知),只是结局不同——pixel 被尺寸规则拦下,电车图(≥640×360、类照片、版权 unknown)全部通过自动过滤进入人工审批,而人工审批又无内容信息(OBS-87)。

### 2.3 现有过滤条件清单(完整)

`image_classifier.py` `classify_image()` 拒绝路径:社交分享卡(og:image/twitter:image/动态 OG 端点,dev6/dev7-hotfix1)/ 1×1 或 <5×5 tracking pixel / URL 命中 tracking、favicon、avatar、logo、ad、placeholder 模式 / 上下文含 avatar、headshot、logo、advertisement / 无法解码 / 解压炸弹 / 尺寸 < 640×360 / copyright=restricted / SVG、unknown copyright、photo 且来源语境不明 → review_required;eligible 仅当 copyright=known_allowed。

- **其中没有任何一条与「内容相关性」有关。** manifest 虽有 `relevance_status` 字段,但赋值逻辑是 `"relevant" if decision == "eligible" else "uncertain"`(run_media_enrichment.py L423)——它是版权/来源可发布性的代理,**从未对图片内容与文章主题做过比较**。六张批准图的 relevance_status 均为 `uncertain`,仍照常获批并绑定。

---

## 第三步 批准信息链取证

### 3.1 递交给人工批准的清单字段

批准点在管线中暂停,交付物为 `discover/media_manifest.json`(approval_evidence.md 明确「审核对象:media_enrichment/discover/asset_discovery_manifest.json」)。asset 字段全集(实测 A-109 对象)包括:

```
asset_id / decision / reasons / resolved_original_url / discovered_url / source_page_url /
width / height / mime_type / file_size / sha256 / perceptual_hash / local_path /
extraction_method / copyright_status / copyright_risk / quality_status / relevance_status /
alt_text / caption / claim_ids / material_ids / placement / approval_* / upload / ...
```

- **alt_text 字段存在,但为 claim 派生值**:`placement_planner.py` 中 `alt_text = claim_text[:60]`、`caption = f"图：{claim_text[:40]}"`(L67-68/L84-85/L94-95),不是图片内容描述;**无页面位置(所属章节/前后文)字段**。
- 批准合同 `copyright_approval.json` 每条记录字段:approval_id / approved_scope / approved_by / approved_at / approval_evidence_sha256 / asset_id / asset_sha256 / asset_identity_sha256 / material_id / source_page_url / resolved_original_url / discovery_manifest_sha256——**合同本身不含 alt_text、不含内容描述、不含页面位置**。
- 档 49 的 approval_evidence.md 自述审核依据:「逐张核对 resolved_original_url 为 ithome 图片直链、asset_sha256 与冻结清单一致」——即**只审来源身份与版权,未审内容**。
- 额外实证:discover 中 decision=`rejected`(avatar,100×100,`mpimg/account/10233.jpg@s_2,w_100,h_100`)的 **A-107 出现在批准合同 AP-…-001 中并被批准、批准记录被消费**(档 50 记录)——批准候选未按 discover decision 过滤,OBS-82 的现场实据,同时佐证批准环节不看内容与规格。

### 3.2 档 49/50 报告中的 alt_text

- 档 49 报告:`e2e-verify-49.md` 未给出 A-110..A-114 的逐图内容描述(仅同源同页理由)。
- 档 50 报告:`e2e-verify-50.md` 对 A-109 引用「alt_text(OpenAI 下调 GPT-5.6 系列费用)」作为**内容适配性**依据——该 alt_text 是 C-06 claim 文本,而 A-109 实际是小米汽车图。**这是审核者在信息不足(且被 claim 派生文本误导)下批准的直接证据。**

---

## 第四步 登记

### OBS-86(高)— 资产发现不区分正文内容图与页面周边图

- 事实:抓图=整页 `<img>`/`srcset` 提取(`image_extractor.py`),无正文边界判定、无容器选择、无页面位置记录;tracking pixel(A-108)与推荐位缩略图(A-109..A-112)均可进入候选并下载。
- 影响:每篇新闻页 20+ 候选,108/122 被拒;真正相关内容混在页面家具中,发现层未产生任何「正文/周边」信号,下游只能靠尺寸/版权等代理过滤。

### OBS-87(高)— 批准清单不呈现内容描述,致人工批准无法履行内容适配性判断

- 事实:批准清单(manifest)唯一文本是 claim 派生 alt_text(与图片内容无关,页内 alt 为空);批准合同不含 alt_text/内容描述/页面位置;批准依据实际只剩 URL 身份与 sha256(OBS-86 之外的批准层缺陷)。
- 影响:六张批准图 4/6 与文章主题无关仍全部获批,批准通道形同只审版权与尺寸;档 50 的 A-109 批准理由被 claim 派生文本误导。

### 与 OBS-29 的关系

- 说明:指令所称 OBS-29(素材相关性无门禁)的登记文本**在当前 pipeline 仓库全仓检索不到**(含 git 历史、audit 全部报告),按指令给出的描述理解。
- 判定:**同一根因链上的两个层级**,不是独立缺陷:OBS-29 是「素材(claim/文章)层无相关性门禁」——素材与文章主题的匹配从未被校验;OBS-86 是「资产(图片)层发现无正文边界」,OBS-87 是「批准层无内容描述」。三者共同构成一条断裂的相关性链路:素材不相关 → 发现不区分 → 批准不审内容。修复 OBS-86/87 只是补资产层与批准层,素材层的相关性门禁(OBS-29)仍缺失。

---

## 第五步 方案(只设计,不实施)

### 5.1 OBS-86 正文图判定方案与代价

- 方案 A(推荐,落 media-enrichment 侧):发现阶段改为「正文容器优先」——优先选择 `<article>`/`main`/文章容器,或按 DOM 位置给候选打标记(所属章节 h2 文本、正文内/周边);无容器时回退整页但**保留位置元数据**供下游过滤。代价:动被锁 skill(media-enrichment,root 0d8aea21 将变)→ 升版 + 第五次 relock --apply + 全套 fixture/测试回归;收益:根因修复,位置信息一次到位。
- 方案 B(落 Pipeline 侧):在 media_enrichment 阶段之后对发现结果做「页面位置后处理」。代价:需先让 skill 输出位置元数据(否则无从判定),本质绕不开 skill 改动;可额外加「主题相关性二次门禁」(用图片所在章节标题 vs 文章主题做判定,LLM 或规则),作为 OBS-86 修复的补充闸门,属 Pipeline 侧独立改动、无需 relock。
- 方案 C(不做):维持现状 + 人工把关——已被本档证明无效(人工无信息可依)。

### 5.2 OBS-87 批准清单增强

- 强制要求:进入批准点的每张图必须携带——① 图片内容描述(页内 alt 有效时用页内 alt;为空时由视觉描述生成,明确标注来源);② 页面位置(所属章节标题/正文内 vs 周边);③ 源页章节与文章主题的相关性预判。**任一缺失即 FAIL_CLOSED,不得进入批准点。**
- 落点:批准清单由 skill 的 discover 输出 → 主体改动仍在 media-enrichment 侧(与 5.1 方案 A 同仓同次升版),Pipeline 侧批准点增加「字段完备性」校验(小改动,不需 relock)。

### 5.3 前瞻:vibe-coding-guide 素材(GitHub 仓库文件)是否走同一路径

- **会走同一条抓图路径。** Pipeline 侧 `producers.py` 以 `source_url -> links.original` 提取素材 URL(`_material_source_url`),写入 media 请求(missing source_url 直接 MediaRequestError),`run_media_enrichment.py` discover 阶段对该 URL 调 `fetch_page()`——GitHub 页面是 HTML,会被整页提取(头像、og:image、仓库卡片、README 图),同样踩 OBS-86。
- 实据:事件 RUN `20260801T225540-vibe-coding-guide-v2-1-9mi6fh` 的 `media_enrichment/stage_failure.json`——`exit_code=2, FAIL_CLOSED: dedup source_url https://github.com/Amer-CN/vibe-coding-guide is mapped by multiple different ids`。该 RUN 在入口预检即 FAIL_CLOSED,未进入 discover;但错误本身证明 GitHub 仓库 URL 已进入同一条 URL→fetch 链路。raw 文件直链(`raw.githubusercontent.com`)会被当作 HTML 抓取解析,通常 0 图片候选,同样无法产出正文图。

### 5.4 分档实施建议

- 档 A(media-enrichment 升版):OBS-86 正文容器/位置元数据 + OBS-87 批准清单字段完备;同仓同次 relock(第五次真实 apply);测试含 ithome 类聚合页 fixture 与 tracking pixel 反证。
- 档 B(Pipeline 侧):批准点「字段完备性」FAIL_CLOSED + 主题相关性二次闸门(可选);走安装器同步,不需 relock。
- 档 C(素材层,承接 OBS-29):aihot/素材选材阶段增加主题相关性门禁——独立立项。
- 优先级:OBS-87(批准信息)应先于或与 OBS-86 同批,因为它是人工把关唯一可依赖的环节,成本最低、见效最快。

---

## 第六步 复核

- **零代码改动**:本档未修改任何代码、被锁 skill、lock/台账、RUN 产物、批准记录;未重跑任何阶段、未新开 RUN;未删除任何文件。
- **零微信调用**:未调 token/上传/草稿任何接口;doctor 以离线方式复核(档 60 禁调微信接口,`--require-wechat` 未执行;最近一次真实双侧 doctor PASS 见档 59 终稿 overnight-summary-59.md)。
- 四锁 hash_ok:super-writer `46a00a1b…`(50)/ zh-human-writing `18491b36…`(53)/ media-enrichment `0d8aea21…`(57)/ gzh-design `c3dd056e…`(76,hammer.4)——doctor 实测全部 `hash_ok: true`,`FAIL_CLOSED: false`,`doctor: PASS`,OBS_69 lock MATCH、OBS_68 pipeline MATCH(608 文件 0 差异)。
- lock:双侧 `skills.lock.json` sha 均为 `0FDF2ECECD1FCD9A8A4957F004D7C2EDA8D99DF8C69C9AC3ED9D6730C559421E`(未变,doctor OBS_69 双侧实测一致)。
- 台账:仍 **5 条**(`59d63817`/`843f9372`/`1afb45bd`/`a0ec5388`/`29b8f728`),本档未写。
- 副作用总账:与档 59 终稿完全一致——草稿箱 **2** 份、累计 uploadimg **22** 次、封面 add_material **4** 次、发布 **0**。

## 附:证据文件索引

- RUN 产物:`.temp/wxgzh-pipeline/20260802T220853-codex-sol-luna-max-m6pyv4/media_enrichment/{discover,continue}/…`
- 批准合同:`…/copyright_approval.json`;批准证据:`…/approval_evidence.md`
- 六图视觉拼接(临时取证):`.temp/obs60-grid.jpg`(不入库)
- 现场 DOM 映射:2026-08-04 抓取 `ithome.com/0/983/917.htm`(11 个 img 标签,六目标图 srcset 定位,前置 h2 章节如上表)
