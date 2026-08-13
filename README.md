# Media Enrichment Skill

> 为已写好的中文文章提供**可追溯、可审计**的媒体资产（配图 + 原创数据图）的 Agent Skill。
> An agent skill that supplies traceable, auditable media assets (images + original data charts) for finished articles.

**版本 / Version**: 0.1.0-dev19 · **许可证 / License**: MIT

## 概述

media-enrichment 是微信公众号内容创作工作区的第四个 Skill：读取上游写作产物中的 `material_id` / `claim_id`，从来源页面抓取并解析候选图片，做 Hash、感知 Hash、尺寸、质量检查与去重，排除头像 / Logo / 广告 / 社交分享卡，记录版权风险，按 canonical claim 中**已有的数字**生成原创数据图，上传合格图片，最终输出 `media_manifest.json` 与插图位置建议。

它**不**修改文章事实，**不**替代写作 / 去 AI 味 / 排版 Skill，**不**创建公众号草稿或正式发布。

## 流水线位置

```
super-writer → zh-human-writing → gzh-design → [media-enrichment] → 微信公众号
（写作）        （去 AI 味）       （排版）       （媒体富化）          （发布）
```

## 安装

```bash
git clone https://github.com/Amer-CN/media-enrichment.git
cd media-enrichment
pip install -r requirements.txt
```

## 使用

```bash
# 运行媒体富化（默认 dry_run，不真实上传）
python scripts/run_media_enrichment.py \
  --request examples/media_enrichment_request.example.json \
  --output-dir output/

# 校验产出的 manifest
python scripts/validate_media_manifest.py --manifest output/media_manifest.json
```

## 模块

| 模块 | 职责 |
|------|------|
| input_contract | 输入加载、Schema 校验、Claim/Material 交叉校验 |
| page_fetcher | 来源 permalink HTML 抓取（含禁止转载扫描） |
| image_extractor | HTML 图片候选解析 |
| proxy_decoder | img-proxy URL 解码 |
| url_security | SSRF 防护 |
| downloader | 图片下载（保留正确扩展名） |
| image_inspector | 图像质量检查 |
| image_deduplicator | 去重 |
| image_classifier | 分类（含社交分享卡 / 链接预览图拒绝规则） |
| chart_generator | 原创数据图（fail-closed） |
| uploader | 上传（dry_run / 图床） |
| placement_planner | 插图位置建议 |
| manifest_builder | Manifest 构建 |

## 测试

```bash
python -m pytest tests/ -q
```

> 说明：`tests/test_regression_visual_acceptance.py` 依赖真实的第三方回归图片，
> 这些图片**不随开源仓库分发**，因此在本仓库中该模块会被自动 `skip`；其余测试全部运行。

## 安全约束

- 默认 `dry_run` 模式，`PUBLISH_ALLOWED` 永不为 `true`
- SSRF 防护；凭证仅从环境读取，绝不写入日志 / manifest
- 拒绝头像 / Logo / 广告 / 社交分享卡（og:image、twitter:image、`/opengraph-image-*` 等链接预览图）
- 不修改文章事实；不创建公众号草稿或发布文章

## 仓库范围

本仓库为**纯源码版**：不包含运行 / 验证产物（`evidence/`）、打包清单（`MANIFEST.json`）以及抓取的第三方页面 / 图片。
这些均可由 `scripts/generate_evidence.py` 与 `scripts/build_zip.py` 在本地重新生成。

## 许可证

本项目基于 [MIT License](LICENSE) 开源，Copyright (c) 2026 佳木 (Jiamu), 摸鱼小李 (Moyu Xiaoli)。
