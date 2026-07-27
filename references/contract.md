# Media Enrichment — Input/Output Contract

## 输入

### media_enrichment_request.json

```json
{
  "schema_version": "1.0",
  "run_id": "string",
  "article": {
    "path": "string",
    "sha256": "64-char hex"
  },
  "materials": [
    {
      "material_id": "string",
      "aihot_permalink": "URL",
      "source_url": "URL",
      "title": "string",
      "selected_claim_ids": ["string"]
    }
  ],
  "claims": [
    {
      "claim_id": "string",
      "claim_text": "string",
      "material_id": "string",
      "source_url": "URL",
      "source_excerpt": "string",
      "numbers": ["string"]
    }
  ],
  "config": {
    "network_mode": "live|offline_fixture",
    "upload_mode": "dry_run|wechat_image_host|stable_storage",
    "max_images_per_material": 3,
    "max_total_images": 12,
    "min_width": 640,
    "min_height": 360,
    "max_download_bytes": 15728640,
    "max_pixels": 40000000,
    "allow_unknown_license_for_publish": false
  }
}
```

### 输入门禁规则

1. claim_id 必须唯一
2. material_id 必须唯一
3. 每个 Claim 的 material_id 必须存在
4. Claim 的 source_url 必须与对应 Material 一致
5. article SHA256 必须匹配
6. allow_unknown_license_for_publish 必须为 false
7. 任何不合法输入 → fail-closed

## 输出

### media_manifest.json

完整资产清单，包含：
- 输入元数据（request_sha256, article_sha256）
- 汇总统计（pages_fetched, candidates_discovered, downloads_succeeded 等）
- 资产列表（每个资产的完整溯源信息）
- 错误和警告
- 门禁状态（publish_allowed 永远为 false）

### 其他产出

- 下载的图片文件（SHA256 命名）
- 生成的数据图（PNG）
- 插图位置建议
- Validator 验证报告

## 交接约束

- media-enrichment 不修改文章事实
- media-enrichment 不创建公众号草稿
- media-enrichment 不发布文章
- media-enrichment 的 PUBLISH_ALLOWED 永远为 false
- 只有 validator exit code = 0 才表示 manifest 有效
