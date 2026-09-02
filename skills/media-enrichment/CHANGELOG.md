# Changelog

## 0.1.0-dev31 (2026-09-03) — 77W

- **OBS-357 审批车道名实修复**：request schema `approved_by` 改枚举 user/auto_rule/auto_approve（auto_approve=76R 遗留值，等同 auto_rule），新增同级 `basis` 依据字段（auto_* 车道必填）；`run_media_enrichment.py` 在 single_asset 批准搬运块前 fail-fast 校验车道——枚举外值拒、auto_* 缺 basis 拒、user 无用户动作证据拒（证据=user_images.json 既有通道含 material_id/source_url，或 approval 自带 approval_evidence_sha256 留痕）；SKILL.md 审批纪律节同步车道语义；既有测试夹具车道值 real-user/independent_reviewer 同步对齐枚举（16 测试语义不变）。
- **OBS-359 supplemental permalink 通道**：request schema materials[].aihot_permalink 类型改 `["string","null"]`（provenance=supplemental 允许 null，无站内页不猜不填）；`validate_media_manifest.py` 新增 REQUEST_MATERIAL_PERMALINK_LANE 按 provenance 分流——supplemental 非 null 须 `https://aihot.virxact.com/` 前缀（外站构造填充拒），normal/缺省维持既有口径。
- **测试 +5**：新增 tests/test_hf77w_approval_lane.py（车道 3 + permalink 2）。
- **版本字面量全站同步 dev30 → dev31**（77J 既定模式）：VERSION / README / WXGZH_PIPELINE_INTEGRATION / build_zip / generate_evidence / _verify_dev7 / __init__ / input_contract / url_security(User-Agent) / 两处测试版本钉子。

## 0.1.0-dev30 (2026-09-02) — 77U

- **测试字面量卫生清洗（77U）**：tests/test_hf77t_url_security_guard.py 内网/元数据 URL 改分段构造（77U 卫生新规：测试源码不携带完整地址字面量），断言语义零变化。
- **版本字面量全站同步 dev29 → dev30**（77J 既定模式）：VERSION / README / WXGZH_PIPELINE_INTEGRATION / build_zip / generate_evidence / _verify_dev7 / __init__ / input_contract / url_security(User-Agent) / 两处测试版本钉子。

## 0.1.0-dev29 (2026-09-02) — 77T

- **CVE 依赖收紧**：requirements.txt 下限 requests>=2.32.4,<4（CVE-2024-35195 / CVE-2024-47081）、Pillow>=10.3,<13（CVE-2023-50447 ARCE / CVE-2023-44271 / CVE-2024-28219）；本机实测 requests 2.34.2 / Pillow 12.2.0。
- **OBS-351 LP3**：SKILL.md frontmatter `permissions:` 块；声明节追加「自动决策边界」小节（EA2×56，76R/OBS-289 口径）。
- **SSRF1 回归钉子**：新增 tests/test_hf77t_url_security_guard.py（补云元数据直连 / IPv4-mapped IPv6 URL / require_dns=False 公网放行三缺口）；fixtures/html/malicious-ssrf.html 头注样本定性。

## 0.1.0-dev28 (2026-09-01) — 77S

- **LP3 权限声明**：SKILL.md 新增「权限与范围声明（最小权限）」节（文件读写/网络端点/凭据键名/子进程/明确不做）。

## 0.1.0-dev27 (2026-08-26) — 77J

- **OBS-325 源页声明图位置证据**：approval readiness 对 og:image/twitter:image/background-image 在源页 HTML 中可追溯的资产，将未知 DOM 位置提升为 `page-meta`；普通正文图语义不变。

## 0.1.0-dev26 (2026-08-24) — 77G

- **OBS-317 user_provided 供图通道开通**:`content_description_source=user_provided` 进入 OBS-87 可信描述白名单；用户供图以 caption/来源登记作为位置证据（`page_position.known=true`、`level=user-evidence`）；manifest schema 补 `asset_origin/page_region=user_provided` 与 `copyright_status=user_granted` 枚举；非供图车道语义不变。
- **OBS-316 配套**：零来源图时 chart 车道保持 discover 首选兜底；仍无可批准资产时由 pipeline 记录零图 shortfall，黑名单/restricted/证据断链不放宽。
- **OBS-316 官方 validator 对齐**：仅当 manifest 零候选、零错误且 bindings 为空时接受零图 shortfall；任一候选未绑定仍 FAIL。

## 0.1.0-dev24 (2026-08-22) — 77F

- **OBS-181 生成图表直出锚点**: `run_media_enrichment.py` 生成图表资产由 `ChartSpec.title` 直出 `placement.anchor` + `page_position known:true level:article-anchor`，规避 `find_anchors` 文本匹配落空导致的 `页面位置未知` OBS-87 闸门 FAIL_CLOSED（kmlb7t A-041 死锁；i2z69i A-087 对照过闸）；后续 `find_anchors` 回填不再覆盖已直出锚点。


## 0.1.0-dev23 (2026-08-21) — 77B

- **OBS-310 numbers schema 税(注释对齐)**:media_enrichment_request.schema.json 的 numbers 增加 description——元素仅 string 或 {value: number, unit},chart_group/metric_name/series_label/time_value 一律在 claim 级、禁止进 numbers 数组;形状语义与既有 oneOf/additionalProperties 一致,仅注释对齐。

## 0.1.0-dev10 (2026-08-09)

## 0.1.0-dev20 (2026-08-14) — 76R

- **OBS-291 pool-fetch ID 规范化**:池内资产登记映射回 canonical material_id(M-XX),
  禁止裸 iid 入库;映射不到才独立登记;continue 阶段不重抓 pool(只消费冻结清单)。
- **OBS-289 媒体审批自动放行**:config.auto_approve(默认关)开启且单图证据链齐全
  (可读描述+位置已知+sha256+去重通过+非黑名单)自动批准入账(approved_by=auto_approve
  + auto_approved 标记);缺证据/黑名单/restricted 仍硬停。

- OBS-275(76F):discover 快失败 + 有界并行——页面抓取 ThreadPoolExecutor(worker=4)
  并行、资产构建串行(asset_id 顺序稳定);x.com/twitter.com 原文页短超时(5s)
  失败即跳过并记 manifest.discovery_side_effects,不拖整段;站内页/官方源保持 15s;
  config.short_timeout_domains 可配置;pool 抓取同样短超时。测试 +3。

## 0.1.0-dev18 (2026-08-13)

- OBS-270(76J):站内页绑定一致性——continue 重分类的 source 一致性检查认可
  aihot_internal_url(站内页)与 source_page_url 相等,与 links.original
  (source_url)同等合法;无站内页字段的素材行为不变(xboc9w 形态回归:
  站内页图不再因 URL 不一致被挡在绑定层外,eligible 显著 >4 生产实证)。
  测试 +2。

## 0.1.0-dev17 (2026-08-12)

- OBS-269(76I):content_description 提质——抽取优先级 img alt/title → 父元素/
  兄弟节点可读文本(context_text,剥离 HTML 标签) → page_context(非裸片段) →
  素材标题兜底;以「<img」开头的裸 HTML 片段一律判不可读并触发回填(nryi0a
  实证:8 张绑定图 6 张裸片段)。测试 +2。

## 0.1.0-dev16 (2026-08-12)

- OBS-268(76H):materials 输入契约新增可选 provenance 枚举(normal/supplemental)
  ——supplemental=权威补充来源(官方博客/公告/releases,携带 source_url+抓取证据+
  登记理由),不要求 aihot dedup 池映射;媒体侧抓取按既有 source_url 兜底通道处理。

## 0.1.0-dev15 (2026-08-12)

- OBS-262(76G-R):站内页图源证据形态——站内页(aihot_internal)为单篇内容单元,
  页内 img 无章节上下文时位置即页面(page-meta,与 og:image 审核方裁定同源);
  三项证据=站内页 URL + 页内位置 + img-proxy 原始 URL 追溯,readiness 认可,
  不再因「位置未知/描述为空」拦站内页图。
- OBS-263(76G-R):站内页图相关性——站内页内容已筛选,图与素材同源即相关:
  分类器 internal_page 参数(站内页图不再加「source context unclear」review
  reason;站内页 og:image 是内容图/视频封面,不按 social share card 拒);
  素材/pool/continue 重分类三处调用接线;cross-section 站内页变体无需改
  (站内页单篇 h1 形态无跨节歧义,既有 h1 例外覆盖)。
- 测试 +2(test_hf76g_video_poster:站内页 img page-meta 位置/og:image 不被
  social card 拒;四测试页案例回归语义:h84rqz A-013 类 img.src 站内页图由
  position unknown + unclear 双拦 → 现 page-meta + 无 unclear,可批候选)。
- 版本 0.1.0-dev15。

## 0.1.0-dev14 (2026-08-12)

- OBS-266(76G 增补):视频封面采集通道——视频型素材页(og:video / twitter:player /
  <video>)抽取封面为图片候选:<video poster>、twitter:player:image、og:image(视频页)、
  img-proxy thumb 链接全部纳入;资产标 video_poster=true,证据链走站内页形态
  (位置/描述/原始 URL 追溯同 76E);合规语义不变(no-repost 扫描照旧,封面按图片规则);
  视频本体不下载不上传(视频车道后置)。测试 +5(test_hf76g_video_poster:poster 抽取/
  twitter:player:image/img-proxy thumb 标记/非视频页不标/端到端进候选)。
  验收(源码树直跑 xvlvb4 副本冻结请求):6 个 video_poster 资产全部 review_required,
  来自 6 个真实视频素材页。

## 0.1.0-dev13 (2026-08-12)

- OBS-260(档76E):discovery 预算与最终入文数分离——max_total_images 只约束最终
  上传图数,discovery 用独立预算 discovery_budget(默认 max(24, 3×max_total),
  可配置),rejected/头像/重复图不再消耗中止条件;「skipping M-10」类截断场景
  回归修复(3 素材页 max_total=2 全抓)。
- OBS-260(档76E):图源优先级(用户确认业务规则)——AI HOT 站内页
  (materials[].aihot_internal_url,links.aihot 直出 HTML)优先;站内页无候选 →
  原始来源页兜底;原始页无论主用页为何都做 no-repost 扫描(命中→素材 restricted);
  页面抓到但无候选属正常(走图表/降级车道,不报 error)。
- OBS-260(档76E):img-proxy 下载 429 限流退避重试(429 实证,最多 3 次,1s/2s/4s)。
- 测试 +5(test_hf76e_source:预算回归/站内页优先/原始页兜底/no-repost 保留/
  429 重试);test_dev7_fixes 抓取优先级断言按新语义更新;test_obs71 图表上限
  断言改为「max_total 不截断 discovery 图表」(76E 语义)。

## 0.1.0-dev12 (2026-08-12)

- OBS-259(档76D):WebP→JPEG 自动转码——上传前检测 WebP magic(RIFF....WEBP),
  Pillow 打开(带 alpha 合成白底)转 JPEG 同目录 .jpg;转码成功用新路径上传并把
  {asset_id, from_format, to_format, original_bytes, converted_bytes} 记入
  manifest.transcodes(空列表=无转码);转码失败 fail-closed 不上传(微信 40005
  实证:WebP 直传被拒)。pipeline media post 将 transcodes 读入 side_effects 留痕。
  测试 +4(test_hf76d_webp:转码/非 WebP 不动/损坏 fail-closed/manifest 字段)。

## 0.1.0-dev11 (2026-08-11)

- OBS-254(档76C):discover 扩池——抓取范围从「已选素材」扩到「全池潜力源」,
  deduplicated_items 全池评估图源潜力补充抓取;每条素材除 source_url 外加抓
  links.aihot 站内页(直出 HTML 可绕 X 动态渲染);来源扩池的图仍按 OBS-86
  cross-section 语义做 claim 相关性绑定,只放行与文章相关者。pool_fetch_limit
  默认 30,pool_image_count 独立计数。
- OBS-248(档76C):来源域名黑名单——新增 config.domain_blacklist(可配置),
  首批 ithome.com / img.ithome.com(水印广告图);命中即拒,URL 尾段匹配。
- OBS-255(档76C):用户供图注入——runs/<RUN>/media_enrichment/user_images.json
  存在则纳入候选(user_provided 资产,copyright_status=user_granted 免版权
  审批,asset_origin=user_provided,登记来源链接);continue 阶段 user_granted_ids
  免守卫 + 免 source_url 比对。
- 76C 门禁降级链(用户裁决 2026-08-11,口径 43):图片数量不再是发文限制条件——
  body_images_min 保留为目标值,不足时降级(生图兜底 + 少图交付留痕),不再阻断。


- OBS-247(档HF-4):meta 提取通道去冤——og:image/twitter:image 通道不再因通道
  本身被一票否决(x.com 等 SPA 源正文图只能经 meta 标签提取);仅 URL 命中动态
  伪卡片端点(/opengraph-image-xxxx 等)时拒绝。meta 通道资产 page_position
  记为 {"known": true, "heading": <页面 title>, "level": "page-meta"}。
- OBS-245(档HF-4):源图 content_description 直写——img alt/title(page_alt)>
  提取上下文(page_context,meta 通道用 og:title/og:description);严禁 claim 文本
  填充;都取不到则保持 null(readiness 判 empty 属诚实结果)。
- OBS-246(档HF-4):material 车道守卫语义修正——不再用「候选数 > 显式批准数」
  计数比较误杀纯 material 车道;改为每个上传候选必须有批准依据(single_asset 或
  material/source_url),存在无依据候选即 FAIL_CLOSED 并列明。material/source_url
  批准的资产在 continue 重跑分类,decision 可转 eligible;restricted/no-repost
  永不可被覆盖。


## 0.1.0-dev9 (2026-08-04)

- OBS-71(档63):生成图表纳入批准链——图表不再硬编码 known_allowed/eligible,
  决策改为 review_required、版权 unknown,必须经显式 single_asset 批准才上传;
  continue 阶段图表从冻结清单重建(与源资产同机制),绝不重复生成。
- 图表计入 max_total_images 数量上限;内容描述来自图表 spec/数据来源
  (content_description_source=generated),不使用 claim 派生文本填充。
- 图表稳定身份:material_id/source_page_url/resolved_original_url(#chart-{sha12})/
  asset_sha256/asset_identity_sha256 入冻结清单;material 级批准不再覆盖图表。
- 封面联动:未批准图表不可上传、不可作封面(事件 RUN 草稿 #3 场景不可再现)。


## 0.1.0-dev8 (2026-08-04)

- OBS-86(档62):正文边界判定——提取阶段按 DOM 容器语义(article/main/aside/nav/
  header/footer、ARIA role、class/id 提示词)与尺寸属性区分正文/周边/未知;
  侧边栏、推荐位、广告、页眉页脚、追踪像素(≤5×5 属性)与惰性占位 src
  (data: URI / t.png 类,存在真实 srcset/data-* 时)在下载前直接排除,零第三方请求。
- 章节归属:每个候选记录所属章节标题/层级(文档序前最近 h1/h2/h3),manifest 输出
  page_region 与 page_position,供 Pipeline 侧 OBS-87 approval_readiness 直接消费。
- 跨章节对齐(新增 section_align):聚合页正文容器内其他新闻章节的图与素材 claim
  词元不对齐时,下载前排除;未知结构保留候选但标记位置未知,由批准闸门拦下。


## 0.1.0-dev7-hotfix4 (2026-07-29)

- Restored material/source_url approval uploads in Continue while keeping stable single_asset approvals bound to the frozen discovery identity.
- Enforced precedence `restricted/no-repost > material/source_url > stable single_asset > unknown`; no ordinary approval can bypass an explicit no-repost statement.
- Added real offline CLI coverage for material, source_url, stable single_asset, no-repost, and unknown approval paths.
- Added structured canonical claim-number objects to the request schema and chart parser so Pipeline can preserve upstream values verbatim.

## 0.1.0-dev7-hotfix3 (2026-07-28)

- P0#3: replaced display-order-only single_asset approval with a two-phase discovery/continue contract bound to material, source page, resolved URL, content SHA256, stable asset identity, and the frozen discovery manifest SHA256.
- Discovery is upload-free and emits asset_discovery_manifest.json; continue fail-closes with approval_identity_mismatch on inserted images, changed bytes, changed material, or tampered discovery manifests.
- CI now installs runtime/test dependencies, runs full pytest plus non-skippable safety suites, preserves compileall, and uploads structured pytest/skip-reason artifacts.

## 0.1.0-dev7-hotfix2 (2026-07-29)

- P0#2 (wxgzh-pipeline dev2-hotfix4): consume `asset_approvals` (approved_scope=single_asset) AFTER the real asset_id is produced — only the matching asset becomes known_allowed; the material stays unknown; unmatched approvals are recorded as NOT consumed; the upload gate now judges the asset's final copyright status.
- Request schema: formal `asset_approvals` definition + `wechat_audit` upload_mode; input contract validates unique asset_id / single_asset scope / 64-hex evidence / no conflicting approvals.
- Manifest assets now record approval_id / approved_scope / approval_evidence / asset_approval_consumed.
- offline_fixture: image downloads read local fixtures (zero network); `is_safe_url(require_dns=False)` skips only DNS in offline runs.

## 0.1.0-dev7-hotfix1 (2026-07-27)

### 阻断问题修复（社交分享卡 URL 误杀，与 dev6-hotfix1 同源）

1. **社交分享卡 URL 检测改为按路径段匹配**：删除对完整 URL 的裸子串
   `r"og-image"` 匹配（会误杀文件名含该子串的正文图：blog-image-hero.jpg /
   catalog-image.png / dog-image.jpg）。改为 `is_social_preview_url(url)`：
   取 `urllib.parse.urlsplit(url).path`，按独立路径段判断——段以
   `opengraph-image` / `twitter-image` / `og-image` 开头（== 前缀 / 前缀+`-` /
   前缀+`.`），或为裸文件名 `og.{png,jpg,jpeg,webp}` 才判为分享卡。
   删除裸子串正则列表 `SOCIAL_PREVIEW_URL_PATTERNS`。
   `extraction_method` 判定前标准化 `strip().lower()`。
   - 必拒：AI HOT `/items/<id>/opengraph-image-*`、`/opengraph-image[-*]`、
     `/twitter-image[-*]`、`/og-image[-*]`、`/og.{png,jpg,jpeg,webp}`。
   - 不拒（img.src）：blog-image-hero.jpg / catalog-image.png / dog-image.jpg /
     my-og-image-example.jpg（除非抽取方法本身即 og:image/twitter:image）。
2. **新增正/负测试**（`tests/test_social_preview_rejection.py`）：段匹配
   正负例 + method 标准化 + HTML 抽取集成（同一 URL 同时在 `<img src>` 与
   `<meta og:image>` 时 img.src 先发现并保留）。
3. `_verify_dev7.py` 检查标签 `skill_version==dev5` 改为 `skill_version_correct`；
   `generate_evidence.py` 版本一致性 regex 支持 `-hotfix` 后缀。

### 版本

- 0.1.0-dev7 → 0.1.0-dev7-hotfix1（基于已审 dev7 zip 基线的最小 URL 修复；
  仅动 classify_image 的社交卡 URL 判定 + 测试 + 版本号，未改 dev7 的
  source_url 路由/上传扩展名逻辑）。`_verify_dev7.py` 文件名保留。

## 0.1.0-dev7 (2026-07-27)

### 修复（Qwen3.8 流水线最小修复指令）

1. **来源图上传修复**：
   - `downloader.py`：下载文件按 检测MIME > Content-Type > 原始URL后缀
     保留/补齐 `.png/.jpg/.webp/.gif` 扩展名（SHA256 命名 + 扩展名）；
   - `uploader.py`：wechat uploadimg 的 multipart filename 必带扩展名
     （文件无后缀时按 MIME 推导）——微信拒绝无扩展名文件名导致 dev5/dev6
     来源图全部 upload failed 的根因修复；编排器不再需要绕过 Skill 重传。
2. **图片发现路由**：`run_media_enrichment.py` 优先抓取
   `materials[].source_url` 原始来源页；`aihot_permalink` 仅用于追溯与
   原始页不可访问时的兜底（warning 记录回退原因）；`source_page_url`
   记录实际抓取页。AI HOT opengraph 资讯卡继续被 dev6 规则拒绝。
3. **明确禁止转载检查**：`page_fetcher.scan_no_repost()` 对**原始 source_url
   页面**扫描（禁止转载/不得转载/未经许可不得转载/严禁转载/禁止使用/
   不得使用/禁止复制/不得复制）；命中则该素材图片全部按 restricted 拒绝。
   不得只检查 AI HOT 详情页。
4. **Validator 逐一检查绑定资产**：`validate_media_manifest.py` 新增
   `--bindings`，对最终正文绑定的每一张资产检查 存在于 manifest、
   decision=eligible、upload.status=success、remote_url 为微信图床、
   sha256 一致——不再只统计生成图。
5. 新增 `tests/test_dev7_fixes.py`；REJECTION/路由/扩展名/扫描/绑定校验
   全覆盖。

## 0.1.0-dev6 (2026-07-27)

### 新增规则（用户要求）

1. **社交分享卡 / 链接预览图拒绝门禁**：`image_classifier.py` 新增最前置
   拒绝检查（category=`social_share_card`，decision=`rejected`）：
   - 经 `og:image` / `twitter:image` meta 标签发现的候选一律拒绝——它们是
     链接预览图，不在页面正文中渲染（如 AI HOT 为每个条目动态生成的
     OpenGraph 分享卡）；
   - URL 命中动态分享卡端点模式（`opengraph-image` / `twitter-image` /
     `og-image` 等）时，即使经其他抽取路径发现也一律拒绝；
   - `classify_image()` 新增可选参数 `extraction_method`（默认空串，旧调用
     行为不变）；`run_media_enrichment.py` 传入 `candidate.extraction_method`。
   来源：qwen38-pipeline 真实运行中 AI HOT og 卡（1200x630）被选为正文图，
   用户裁定此类图不得使用。
2. 拒绝路径回归 `REJECTION_CASES` 由 15 条扩至 18 条；新增
   `tests/test_social_preview_rejection.py`（含真实 AI HOT og 卡 URL 回归、
   正常正文图不受影响、runner 传参核验）。

### 版本

- 版本号 0.1.0-dev5 → 0.1.0-dev6（11 处一致性文件同步，`_verify_dev5.py`
  更名升级为 `_verify_dev6.py`，版本一致性测试残留门禁扩展 DEV5）。

## 0.1.0-dev5 (2026-07-27)

### P0 修复

1. **统一拒绝枚举**：`image_classifier.py` 全部 15 条拒绝路径（tracking pixel、
   extremely small、tracking URL、favicon、avatar URL、logo URL、ad/banner URL、
   placeholder URL、avatar context、logo context、advertisement context、
   undecodable、decompression bomb、below minimum dimensions、restricted
   copyright）由 `decision="reject"` 改为 canonical 的 `decision="rejected"`，
   与 `media_manifest.schema.json` 枚举一致。未把 "reject" 加入 Schema 兼容。
   来源：kimi-k3-visual-acceptance-v1 真实集成失败
   （INPUT_SCHEMA_VALID FAIL: 'reject' is not one of [...]）。
2. **图表口径门禁（fail-closed）**：`chart_generator.py` 不再按 unit 盲目分组。
   - 数据点必须携带显式 `chart_group` + `metric_name` + `series_label`；
   - bar/comparison 仅允许同 chart_group、同 metric_name、同 unit、≥2 点；
   - 跨基准同单位/空单位一律拒绝（"incompatible chart group" 警告）；
   - timeline 仅当每个数据点都有真实 `time_value` 时生成，禁止用输入序号
     冒充时间轴；
   - 图表标题/caption/alt 描述完整 chart_group 与全部数据点，禁止用单条
     Claim 文本代表多点图；runner 不再让 placement 覆盖图表 caption。
   - `build_chart_specs` 返回 `ChartBuildResult(specs, warnings)`。
   - 请求 Schema 的 claims 新增可选字段：chart_group/metric_name/
     series_label/unit/time_value。

### 文档修复

3. SKILL.md 与 README.md 的 CLI 入口统一为真实存在的
   `python scripts/run_media_enrichment.py --request <request.json> --output-dir <dir>`，
   移除不存在的 `scripts/media_enrichment.py` 引用；新增文档入口存在性测试。

### 测试

- 新增 `tests/test_rejected_enum.py`（15 条拒绝路径逐条断言 rejected +
  Schema/统计/不上传/最终选择/provenance 验证 + 运行时源码 reject 字面量=0）。
- 新增 `tests/test_regression_visual_acceptance.py`（A-001 logo / A-006
  banner-ad / A-010 1193x296 真实回归 Fixture）。
- 新增 `tests/test_chart_gating.py`（跨基准拒绝、空单位拒绝、同基准接受、
  无时间拒绝 timeline、真实日期接受 timeline、caption 覆盖全组、
  C-10-a/C-11-a/C-33-a/C-34-a 回归=0 图表）。
- 新增 `tests/test_documented_entry.py`（DOCUMENTED_ENTRY_EXISTS）。
- 更新 `tests/test_chart_generator.py` 至 dev5 API；更新既有断言至 rejected。

# CHANGELOG

## v0.1.0-dev4 — Review Fix Round 3 (2026-07-26)

### 修复

- **pytest 结构化门禁**：使用 --json-report 复算 returncode/total/passed/failed，四条件全满足才继续。
- **版权输入合同**：Material 增加 copyright_review 对象，known_allowed 必须非空字段。
- **来源图片上传路径**：从 Material.copyright_review.status 取状态，不再硬编码。
- **生成图上传路径**：在 add_asset 前调用 uploader，写入真实 upload 结果。
- **test_summary 去硬编码**：所有字段从结构化报告读取。
- **可移植核验脚本**：使用 Path(__file__) 而非硬编码 F 盘路径。
- **版本统一**：所有位置更新为 0.1.0-dev4。

## v0.1.0-dev3 — Review Fix Round 2 (2026-07-26)

### 修复

- **Validator 假 PASS 修复**：eligible/review_required 资产的 local_path 为 null/空字符串时立即 FAIL（不再跳过）；未提供 request 文件时 REQUEST_* 检查全部 FAIL；NO_ARTICLE_FACT_MUTATION 在文章不可用时 FAIL。
- **Request 校验**：提供 request 时复算 REQUEST_SHA256_MATCH、CLAIMS_TOTAL_MATCH、MATERIALS_TOTAL_MATCH。
- **ManifestBuilder 缓存修复**：删除 _cached_result，每次 build() 从当前状态重新计算；追加 error 后再次 build() 反映新 error 且 gate 变为 false。
- **构建门禁修复**：generate_evidence 生成包含 article fixture + request snapshot 的真实 sample；validator 使用 --request 参数；validator_exit_code != 0 时 build_zip 立即中止；test_summary 所有字段从真实报告读取。
- **版本一致性**：所有位置统一为 0.1.0-dev3。
- **三图证据**：实际生成 chart-bar.png、chart-comparison.png、chart-timeline.png 及逐图 traceability 报告。
- **版权和上传**：generated chart 为 known_allowed，eligible 时执行 uploader。

## v0.1.0-dev2 — Review Fix Round 1 (2026-07-26)

### 修复

- SSRF 手动重定向（allow_redirects=False 逐跳检查）
- IPv4-mapped IPv6 阻断、全量非公网 IP 阻断
- 文章缺失 = error 非 warning
- ManifestBuilder 幂等
- 3 种图表类型
- copyright 受控输入、未知 upload_mode 报错、access_token 脱敏
- MANIFEST.json 不自引用 Hash
- fixtures/images 包含 8 文件

## v0.1.0-dev1 — Initial Development (2026-07-25)

### 新增

- **Skill 骨架**：SKILL.md、VERSION、目录结构、CLI 入口。
- **输入合同**：JSON Schema（request + manifest）、示例文件、input_contract 模块（交叉校验、Hash 校验、fail-closed）。
- **页面抓取**：page_fetcher（live/offline_fixture 模式、脱敏元数据）。
- **图片解析**：image_extractor（img/src/srcset/data-src/data-original/og:image/twitter:image/JSON-LD/background-image）。
- **代理解码**：proxy_decoder（URL 编码、双重 URL 编码、Base64 URL、递归层数限制）。
- **SSRF 防护**：url_security（协议白名单、私网阻断、DNS 二次检查、重定向检查）。
- **下载器**：downloader（流式下载、大小限制、原子重命名、SHA256 命名、Content-Type 校验）。
- **图像检查**：image_inspector（SHA256、pHash、尺寸、MIME、EXIF、解压炸弹防护）。
- **去重**：image_deduplicator（SHA256 + URL 规范化 + pHash 近似去重）。
- **分类器**：image_classifier（reject/review_required/eligible 规则分类）。
- **原创数据图**：chart_generator（canonical claim 数字解析、可比性门禁、matplotlib PNG 生成、数据溯源）。
- **上传抽象**：uploader（dry_run 默认、mock uploader、可插拔接口）。
- **Manifest 构建**：manifest_builder（确定性排序、完整溯源）。
- **Validator**：validate_media_manifest.py（全部 P0 检查、退出码 0=PASS/非0=FAIL）。
- **测试**：单元测试（31+ 用例）、离线集成测试、固定 HTML/Image fixtures。
- **真实网页验证**：AI HOT permalink 抓取测试（3+ 页面、HTML 快照保存）。






