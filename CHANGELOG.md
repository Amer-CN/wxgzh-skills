# Changelog

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
