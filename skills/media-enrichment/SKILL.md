---
name: media-enrichment
description: >-
  媒体资产富化 Skill。读取 Super Writer 的 material_id 和 claim_id，从 AI HOT permalink
  页面抓取、解析、下载图片，做 Hash、感知 Hash、尺寸、质量检查和去重，排除头像/Logo/广告，
  记录版权风险，根据 canonical claim 中已有数字生成原创数据图，上传合格图片，输出
  media_manifest.json 和插图位置建议。不修改文章事实，不替代写作/去 AI 味/排版 Skill，
  不创建公众号草稿或正式发布。
permissions:
  file-scope: 项目 RUN 目录与调用方显式传入路径
  network:
    - 下载素材 claim source_url 页面图片
    - 上传微信图床 api.weixin.qq.com
  secrets: # 仅键名，值用 <env> 占位
    - WECHAT_APP_ID
    - WECHAT_APP_SECRET
    - WECHAT_API_ALLOWED
    - WECHAT_IMAGE_HOSTS
  subprocess: build_zip/generate_evidence 本技能内脚本
  prohibited: 安装依赖、正式发布、群发、删除文件
---

# Media Enrichment

## 权限与范围声明（最小权限）

- **文件读写**：仅限 RUN 目录内素材、图片缓存、审批与上传记录。
- **网络访问**：①下载素材 claim.source_url 指定页面的图片；②上传合格图片至微信图床（api.weixin.qq.com 素材接口，返回 mmbiz.qpic.cn URL）。无其他端点。
- **凭据**：仅从项目 .env 读取 WECHAT_APP_ID / WECHAT_APP_SECRET（及 WECHAT_API_ALLOWED / WECHAT_IMAGE_HOSTS 开关）；不硬编码、不回显。
- **子进程**：scripts/build_zip.py、generate_evidence.py 调用本技能内脚本做打包/取证；无外部命令。
- **明确不做**：不发布、不群发、不删除图床/草稿资源。

### 自动决策边界

- **自动批**：零图降级；auto_approve 开启（WXGZH_MEDIA_AUTO_APPROVE=1，默认关）且单图证据链齐全（76R/OBS-289 口径）。
- **必须人工**：图片审批（默认道）、restricted 资产、上传微信前终审。
- 来源：EA2×56，逐条对应 `scripts/run_media_enrichment.py` 决策点。

## 使命

为已写好的文章提供可追溯、可审计的媒体资产（图片、原创数据图），不修改文章事实，不猜测版权授权状态。

## 硬性优先级

来源可追溯 > 版权安全 > 事实不变 > 图片质量 > 数量 > 速度。

## 绝对约束（MUST）

1. 不得修改 claim_text、material_id、claim_id 或 source_url。
2. 不得搜索或补写新的文章事实。
3. 不得猜测图片版权已获授权。
4. 不得创建微信公众号草稿或正式发布文章。
5. 不得修改 Super Writer、zh-human-writing、gzh-design 或其他已有 Skill。
6. PUBLISH_ALLOWED 永远不能由本 Skill 设置为 true。
7. 原创数据图只能使用 canonical claim 中已有的数字，不得联网补充数据或推算未给出的数值。
8. 输入不合法时 fail-closed，不生成"看起来成功"的 manifest。
9. 日志和 manifest 中禁止出现 Token、Secret、Cookie 等敏感信息。

## 职责边界

### media-enrichment 负责

1. 读取 Super Writer 选中的 material_id 和 claim_id。
2. 根据 material_id 找到 AI HOT permalink 和原始 source_url。
3. **优先获取原始 source_url 页面**（dev7 起）；aihot_permalink 仅用于
   追溯与原始页不可访问时的兜底。明确禁止转载检查必须针对原始
   source_url 页面执行，命中（禁止转载/不得转载/禁止使用等）则该素材
   图片全部按 restricted 拒绝。
4. 解析页面中的图片候选（img/src/srcset/data-src/data-original/og:image/twitter:image/JSON-LD/background-image/img-proxy）。
5. 解码代理后的原始图片 URL。
6. 下载图片（按 检测MIME > Content-Type > URL后缀 保留/补齐扩展名）。
7. 做 Hash、感知 Hash、尺寸、MIME、文件头和质量检查。
8. 去重（SHA256 + URL 规范化 + 感知 Hash）。
9. 排除头像、Logo、图标、广告、追踪像素、社交分享卡/链接预览图和无关图片。
10. 记录来源、版权状态和风险。
11. 根据 canonical claim 中已有数字生成原创数据图。
12. 上传合格图片到可配置的稳定存储或公众号图床。
13. 输出 media_manifest.json。
14. 给出文章插图位置建议（不直接修改文章正文）。

### media-enrichment 不负责

1. 搜索或补写新的文章事实。
2. 修改 claim_text。
3. 修改 material_id、claim_id 或 source_url。
4. 重新组织文章论点。
5. 替代 Super Writer 的事实校验。
6. 替代 zh-human-writing。
7. 替代 gzh-design。
8. 创建微信公众号文章草稿。
9. 正式发布微信公众号文章。
10. 猜测图片版权已获授权。

## 输入合同

输入为 JSON 文件，符合 `schemas/media_enrichment_request.schema.json`。

关键字段：
- `schema_version`: "1.0"
- `run_id`: 本次运行唯一标识
- `article`: 文章路径和 SHA256
- `materials[]`: 素材列表，含 material_id、aihot_permalink、source_url、title、selected_claim_ids
- `claims[]`: Claim 列表，含 claim_id、claim_text、material_id、source_url、source_excerpt、numbers
- `config`: 运行配置

### 输入门禁

1. claim_id 必须唯一。
2. material_id 必须唯一映射到一个素材对象。
3. 每个 Claim 引用的 material_id 必须存在。
4. Claim 的 source_url 必须与对应 Material 一致。
5. article SHA256 必须匹配。
6. 输入不合法时 fail-closed，不继续抓图。
7. 不自动修复或猜测 Claim/material 映射。
8. 不可信输入只输出 validation error，不生成"看起来成功"的 manifest。

### 图表口径门禁（dev5 起，fail-closed）

1. Claim 的 numbers 想参与图表，必须显式声明 `chart_group`（基准/口径组）、
   `metric_name`（指标名）、`series_label`（数据点标签）；缺任一项则该 Claim
   不参与图表，并输出 `incompatible chart group` 警告。
2. bar/comparison 仅允许同 chart_group、同 metric_name、同 unit、且 ≥2 个
   数据点；不同基准的数值即使单位相同或同为空也绝不合并。
3. timeline 仅当每个数据点都有真实 `time_value` 时生成；禁止用输入序号冒充
   时间轴。
4. 图表标题、caption 和 alt_text 描述完整 chart_group 与全部数据点，禁止用
   单条 Claim 文本代表整张多数据点图。
5. 没有明确可比组时不生成图表（GENERATED_CHARTS=0 是合法结果）。

### 社交分享卡 / 链接预览图门禁（dev6 起，fail-closed）

1. 通过 `og:image` / `twitter:image` meta 标签发现的图片是链接预览图，
   **不在页面正文中渲染**，一律 `rejected`（category=social_share_card），
   与尺寸、清晰度、版权状态无关。
2. URL 命中动态分享卡端点模式（`opengraph-image` / `twitter-image` /
   `og-image` 等，例如 AI HOT 为每个条目动态生成的
   `/items/<id>/opengraph-image-xxxx` 卡片）时，即使经由其他抽取路径
   发现也一律 `rejected`。
3. 该规则在分类器最前置执行；被拒资产保留完整溯源与拒绝原因，便于审计。
4. 页面正文内的普通图片（img/src/srcset/JSON-LD 等）不受影响。

## 模块结构

```
src/media_enrichment/
  __init__.py          # 包初始化和版本号
  input_contract.py    # 输入加载、Schema 校验、Claim/Material 交叉校验
  page_fetcher.py      # AI HOT permalink HTML 抓取（live/offline_fixture）
  image_extractor.py   # HTML 图片候选解析
  proxy_decoder.py     # img-proxy URL 解码
  url_security.py      # SSRF 防护、URL 安全检查
  downloader.py        # 图片下载（流式、大小限制、原子重命名）
  image_inspector.py   # Hash/pHash/尺寸/MIME/EXIF/质量检查
  image_deduplicator.py # SHA256/URL/pHash 去重
  image_classifier.py  # 规则分类（reject/review_required/eligible）
  chart_generator.py   # 原创数据图生成
  uploader.py          # 可插拔上传（dry_run/wechat_image_host/stable_storage）
  placement_planner.py # 插图位置建议
  manifest_builder.py  # Manifest 汇总和确定性排序
```

## 运行模式

### network_mode
- `live`: 实际访问网络
- `offline_fixture`: 使用本地 HTML fixture

### upload_mode
- `dry_run`: 默认，只生成本地资产和计划
- `wechat_image_host`: 公众号图床
- `stable_storage`: 稳定存储

## CLI

```bash
python scripts/run_media_enrichment.py --request <request.json> --output-dir <dir>
```

## 安全要求

- 只允许 http/https 协议
- 拒绝 file/ftp/data/javascript 等协议
- 阻止 localhost、私网、链路本地、云元数据地址
- DNS 解析后再次检查 IP
- 每次重定向都重新检查
- 限制重定向次数
- 禁止将认证信息写入 URL
- 下载使用流式、大小限制、原子重命名
- 凭证只从环境变量或本地安全配置读取
- 日志和 manifest 禁止写入 Token/Secret/Cookie

## 产出

1. `media_manifest.json` — 完整的媒体资产清单
2. 下载的图片文件（SHA256 命名）
3. 生成的数据图（PNG）
4. `validator_report.json` — 验证报告
5. 插图位置建议

## Validator

`scripts/validate_media_manifest.py` 检查所有 P0 条件，退出码 0=PASS，非0=FAIL。


## 审批纪律（76V/OBS-296）

- **readiness_sha 口径**：`approval_readiness_sha256` 一律从最新的
  `approval_readiness_report.json` 原样照抄，禁止自算、禁止引用旧轮报告；
  readiness 报告重生成后旧 sha 一律作废（旧批准合同自动失效，不得复用）。
- **重复/镜像资产**：与其 canonical 孪生（同图，感知去重判定）共享审批依据——
  批准记录指向孪生资产 ID 并复用其 readiness，禁止裸批（无孪生依据不得独立批准）。
