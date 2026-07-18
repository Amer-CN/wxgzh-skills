# 高级组件 —— 行动引导（cta）

> 下一步操作、文章结尾行动建议

## 输入语法

```markdown
:::cta title="标题"\ntext="引导文本"\naction="行动描述"\nurl="https://..."\n:::
```

## 最小输入

明确行动文本 + HTTPS URL

## 选择条件

- 源稿有明确的下一步操作、文章结尾行动建议语义
- 显式 `:::cta` 语法优先

## 禁止自动识别条件

- 无明确下一步操作、文章结尾行动建议语义的普通段落不得自动升级
- 不得自动补造数据、结果或行动建议

## 降级方式

使用原有签名，不生成 CTA

## 发布限制

- 正式 release HTML 禁止 `../assets/`、`file://`、本地磁盘路径
- 所有图片 `src` 必须是作者提供的可访问 HTTPS URL

## 六主题适配规则

见 [theme-adapters.md](theme-adapters.md)。组件语义跨主题一致，只有视觉语言不同。

## 生产 HTML 模板（moyu-green 主题示例）

> 其他主题使用相同结构，仅替换 `theme-adapters.md` 中的色值令牌。

```html
<section style="margin:0 0 24px;background:#ECFDF5;border-radius:12px;padding:20px;text-align:center;box-shadow:0 4px 16px -4px rgba(0,0,0,0.08);">
  <p style="margin:0 0 10px;font-size:14px;color:#374151;line-height:1.8;"><span leaf="">先用本文的 Dockerfile 对照你的镜像构建流程。</span></p>
  <p style="margin:0;font-size:14px;font-weight:700;color:#059669;"><span leaf="">查看 Docker 官方构建指南 → https://docs.docker.com/build/</span></p>
</section>
```

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/cta-*.html`（验收产物，非生产依赖）。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。
