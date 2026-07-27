# Media Enrichment — Architecture Reference

## 模块依赖关系

```
input_contract (入口)
  ├── page_fetcher (抓取)
  │     └── url_security (SSRF 防护)
  ├── image_extractor (解析)
  │     └── proxy_decoder (代理解码)
  ├── downloader (下载)
  │     └── url_security
  ├── image_inspector (检查)
  ├── image_deduplicator (去重)
  ├── image_classifier (分类)
  ├── chart_generator (数据图)
  ├── uploader (上传)
  │     └── secrets 扫描
  ├── placement_planner (位置建议)
  └── manifest_builder (汇总)
        └── uploader (secrets 扫描)
```

## 数据流

```
Request JSON
  → input_contract (校验)
  → for each material:
      → page_fetcher (抓取 AI HOT 页面)
      → image_extractor (解析图片候选)
      → for each candidate:
          → proxy_decoder (解码代理 URL)
          → url_security (SSRF 检查)
          → downloader (下载)
          → image_inspector (Hash/pHash/尺寸/MIME)
          → image_deduplicator (去重)
          → image_classifier (分类)
          → uploader (上传, dry_run 默认)
  → chart_generator (生成数据图)
  → placement_planner (位置建议)
  → manifest_builder (汇总)
  → media_manifest.json
```

## 安全边界

1. **URL 安全**: 只允许 http/https，阻止私网/云元数据/localhost
2. **下载安全**: 流式下载、大小限制、原子重命名、SHA256 命名
3. **图像安全**: 解压炸弹防护、最大像素限制
4. **凭证安全**: 只从环境变量读取、日志脱敏、manifest 禁止写入 Token/Secret
5. **发布安全**: PUBLISH_ALLOWED 永远为 false

## 测试策略

- **单元测试**: 114 个用例，覆盖所有模块
- **离线集成测试**: 使用固定 HTML/Image fixtures，不访问网络
- **真实网页测试**: 3 个 AI HOT permalink，保存 HTML 快照供回归
- **负向测试**: 不兼容数据拒绝出图、不合法输入 fail-closed
