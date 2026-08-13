# 档 62 — OBS-86 正文边界判定(media-enrichment 升版 + 第六次真实 relock)

- 日期:2026-08-04
- 性质:修复档(路径 b——动被锁 media-enrichment + 升版 + 第六次真实 relock --apply)。
- 零微信调用;未动草稿;未改 RUN 产物;未动档 61 闸门语义(仅数据源增强)。

---

## 第零步 归属判定:正文边界判定落在 media-enrichment 侧(路径 b)

**结论:b(提取层)。** 理由:

1. **时序**:当前 discover 是 `extract → download → inspect → classify`。A-108(1×1
   tracking pixel)在 RUN 中被下载后才被分类器拒绝——已对 `img.ithome.com` 产生
   真实第三方请求(实测 RUN `downloads_succeeded=8` 含 A-108)。「下载前排除」
   只能发生在拥有 DOM 的提取层;Pipeline 侧过滤层看到的是已下载资产,无法挽回
   请求本身。
2. **章节归属字段**:第 6 条要求 manifest 记录跨章节图所属章节标题,供档 61
   `approval_readiness` 使用。manifest 由 skill 产出;Pipeline 侧重抓页面做位置
   解析是第二处页面抓取口径(页面漂移、重复请求),且无法写入 manifest。
3. **语义**:正文边界是提取语义,与分类器/下载器同层;Pipeline 侧候选过滤只能
   覆盖「已下载资产的二次判定」,是补充而非根治。

**两侧代价差异**:路径 a(仅 Pipeline)= 不动锁、无 relock,但保留下载浪费、
无法产出 manifest 章节字段,两档接不上;路径 b = 第六次 relock,但根治时序
问题且 manifest 直接携带位置字段(档 61 闸门直接消费,不再重抓页面)。

## 第一步 取证

### 2. 现有提取范围与过滤条件(完整)

- **提取范围**(`image_extractor.py`):全页 `<img>`/`<source>` 的 src/srcset/
  data-src/data-original/data-lazy-src + `og:image`/`twitter:image` meta +
  JSON-LD + CSS background-image。无正文容器选择、无页面位置记录。
- **过滤条件**(`image_classifier.py`,全部在下载**之后**):社交分享卡(og/twitter
  端点)/ 1×1 与 <5×5 / URL 命中 tracking/favicon/avatar/logo/ad/placeholder /
  上下文命中 avatar/logo/ad / 无法解码 / 解压炸弹 / 尺寸 <640×360 /
  copyright=restricted / SVG 与 unknown copyright → review_required。
  **没有任何一条与内容相关性有关**;`relevance_status` 仅是版权/来源代理。

### 3. A-108 时序代价

- 现状:提取(产候选)→ 下载(t.png 1×1,真实请求)→ inspect → classify 拒绝。
  **代价:对第三方产生了真实网络请求**(RUN 实测已发生)。
- 修复后:提取阶段凭「占位 src(t.png 类,存在真实 srcset/data-* 时)」与
  「HTML 尺寸属性 ≤5×5」直接排除——**下载前,零请求**。可做到,已实现并测试。

## 第二步 实施(media-enrichment 0.1.0-dev8)

### 4. 正文边界判定(提取层,`image_extractor.py`)

- **DOM 容器语义**:祖先标签(`aside/nav/header/footer` → peripheral;
  `article/main` → body)、ARIA role(`complementary/navigation/banner/contentinfo`
  → peripheral;`main` → body)、class/id 提示词(sidebar/recommend/related/ad/
  banner/footer/header/nav/menu/comment/avatar/hot/rank/info-list/advert/promo/
  sponsor → peripheral;post_content/article_content/news_content/content →
  body)。**peripheral 优先级高于 body**(正文容器内的广告仍是广告)。
- **尺寸属性**:width/height 属性 ≤5 → peripheral(tracking pixel,下载前)。
- **惰性占位 src**:img 同时带 src + srcset/data-* 且 src 为 data: URI 或
  占位文件名(t.png/blank/placeholder/1x1/pixel)时,占位 src 不产候选
  (A-108 的 t.png 场景,真实 URL 走 srcset)。
- **判定失败(unknown)**:保留为候选但标记位置未知——不默认收录,由档 61
  批准闸门拦下(第 5 条)。原因:无法证明是正文就不放行,宁缺毋滥。

### 5. 章节归属(第 6 条,两档接上)

- 每个候选记录文档序前最近 h1/h2/h3:`section_heading` / `section_level`。
- manifest 新增 `page_region`(body/peripheral/unknown)与 `page_position`
  ({known, heading, level});schema 同步。
- **档 61 联动**:`approval_evidence.build_approval_readiness` 优先消费 manifest
  的 `page_position`(不再重抓页面),缺字段的旧 manifest 回退原页面解析路径。
  **闸门语义未变**:位置必须 known 且内容描述可验证才可批准(测试覆盖)。

### 6. 跨章节对齐(`section_align.py`,仅 h2/h3 多章节结构)

- 背景:档 60 实测 ithome 聚合页全部图片(含四张汽车图)都在 `div.post_content`
  (页面正文容器)内——纯容器判定无法区分「本素材相关章节的图」与「同页其他
  新闻章节的图」。发现是 claim 驱动的,因此叠加章节对齐:
  图所属章节标题与素材 claim 文本词元交集 ≥3,或 claim 前 20 字在标题中,
  即对齐;否则判为跨章节图,下载前排除(位置仍记录)。
- 仅对 `h2/h3` 生效:h1 单篇页无跨章节歧义,不做该门(相关性归 OBS-87 批准
  闸门与素材层 OBS-29)。
- 阈值以六张真实图实测校准:C-06 与章节 #2 共享 OpenAI/GPT-5.6/Luna/模型/
  费用/下调(≥3);汽车/机票章节共享 0-1 个。

## 第三步 反向验证

### 7. ithome 聚合页回归(夹具冻结,不引用实时文件)

夹具 `fixtures/html/ithome-aggregate-obs86.html`(按 2026-08-04 真实 DOM 建模:
`div.bb > div.fl.content > div.post_content` + 六个真实 h2 标题与六张真实图
URL + 侧边栏/头像/推荐位/广告/页脚/1×1 像素),测试 `tests/test_body_boundary.py`
**7 项全过**:

- 四张汽车图 + 携程图:提取层判 body,章节归属正确(小米/比亚迪/特斯拉/携程);
  运行层判跨章节 → `decision=rejected, reason=cross-section image …, local_path=None`
  ——**下载前排除**;
- **A-108(t.png 占位)+ 头像(A-107 同款)+ 推荐位 + 广告 + 页脚 + 1×1 像素**:
  提取层直接排除(excluded 列表可见),不进 manifest、零下载;
- **A-113(OpenAI 章节图):保留并下载**,`page_position.heading` 含 OpenAI;
- run-level CLI 实测:`downloads_succeeded == 1`(仅 A-113);
- 旧 fixture(裸 body 页)回归:全量 **296 passed, 6 skipped**,零断言放宽。

### 8. 前瞻:GitHub 页面的「正文边界」

- 代码路径分析(未抓取 GitHub,基于提取逻辑):GitHub 仓库页是 HTML,README
  容器(`article.markdown-body`)无我方 body 提示词 → 判 unknown,README 内
  h1/h2 会被记录为章节;README 图片若与 claim 章节对齐可保留(需有图)。
  头像/og 卡片/仓库家具:og → 分类器社交卡拒绝;头像类按容器/URL 提示排除。
- **结论:vibe-coding-guide 类技术文的素材页(Ruby 代码库 README)大概率无
  可用网页配图**——README 无图则候选为空;该类文章的媒体形态本应是代码块
  为主(用户已单列档处理),流水线「每篇都从新闻页取图」的假设对技术文不成立,
  此为档 64(文章类型区分)的输入。

## 第四步 复核(路径 b)

### 9-10. 第六次真实 relock --apply 全链结果

- **远端见证 PASS (a/b/c)**:commit `08c7b22` 在远端真实存在;远端树与
  `--source-tree` 逐字一致;`source_tree_sha=a9b6b3e2…` 与实算一致。
- 字段变化(dry-run 与台账逐字一致):

| 字段 | 旧值 | 新值 |
|---|---|---|
| skill_root_sha256 | `0d8aea21…` | `273314e0…` |
| runtime_manifest_sha256 | `172aa1b8…` | `5533c0c8…` |
| runtime_file_count | 57 | 59 |
| entrypoint_sha256 | `2d877a93…` | `a96554e4…` |
| full_commit_sha | `2595e014…` | `08c7b221…` |
| source_tree_sha | `6ba0ba41…` | `a9b6b3e2…` |
| skill_version | `0.1.0-dev7-hotfix4` | `0.1.0-dev8` |
| branch | restore/local-patches-obs42-53 | 不变 |

- 仓库外备份:lock 备份 `…/lock-backups/skills.lock.20260804T073354Z.json`
  (注意:档 45R2 已将备份改到仓库外,此路径为 relock 既定行为,档 52 判定
  可接受,未纳入 OBS-84);
- **台账第 6 条**:`relock-media-enrichment-20260804T073354Z-a9f86689`
  (old→new 全字段、source_commit_verified=true、remote_repo 记录完整);
- 安装器 PASS(source-tree install)→ post-doctor **PASS** →
  **入口冒烟 PASS(CLI subprocess,生产路径,media smoke 样本 discover 离线跑)**;
- 回归步骤首轮失败:仅 OBS-69 基线 3 项(`observability.py` 内嵌
  `REPO_LOCK_SHA256` 未随 lock 更新)——relock 按设计保留已写 lock,走
  档 57/54R 同款「relock 配套」:同步基线 `0FDF2ECE → EEE1A1E9` 后
  **upgrade_regression ALL PASS**(pytest 全量 PASS、排除清单仍 1 项、
  四锁 dry-run 全部无变化、doctor --require-wechat PASS、cross-side 仍 SKIP)。

### 11. 复核项(路径 b 清单)

- lock 双侧 sha:**`EEE1A1E94AC38FBBEF6A8CAE7D04EBF927BCAF66152D8F97A552A57C712927B2`**(一致,新值);
- 台账 **6 条**(末条 `a9f86689`,全文见上);
- media root `273314e0…` / version `0.1.0-dev8`;
- 四锁 hash_ok 全 true、doctor **PASS**、FAIL_CLOSED=false;
  OBS_69 lock MATCH(基线=双侧=EEE1A1E9);OBS_68 pipeline MATCH(见下);
- 安装侧与 repo HEAD 逐字一致:media 侧由 relock 安装器实装
  (root 273314e0,59 文件);Pipeline 侧经正式安装器(bundle-staging-61 重建)
  同步 observability 基线后 OBS_68 双侧一致;
- 副作用总账:与档 59 终稿完全一致——草稿箱 **2** 份、累计 uploadimg **22** 次、
  封面 add_material **4** 次、发布 **0**;本档零微信调用。

## 变更文件

- **media-enrichment 仓(`restore/local-patches-obs42-53`)**:
  `src/media_enrichment/image_extractor.py`(边界判定+章节归属+占位排除)、
  `src/media_enrichment/section_align.py`(新增,claim 章节对齐)、
  `src/media_enrichment/manifest_builder.py`(page_region/page_position)、
  `scripts/run_media_enrichment.py`(下载前跨章节闸门)、
  `schemas/media_manifest.schema.json`、`fixtures/html/ithome-aggregate-obs86.html`(新增)、
  `tests/test_body_boundary.py`(新增,7 项)、版本声明 11 处同步 + CHANGELOG。
  提交 `08c7b22185614f81888fcb42aae52ef0f5354c97`。
- **wxgzh-pipeline 仓(`dev/0.1.0-dev2`)**:
  `wxgzh_pipeline/approval_evidence.py`(manifest page_position 优先,语义不变)、
  `tests/test_obs87_approval_evidence.py`(+2 项联动测试)、
  `wxgzh_pipeline/observability.py`(OBS-69 基线同步 EEE1A1E9)、本报告。
