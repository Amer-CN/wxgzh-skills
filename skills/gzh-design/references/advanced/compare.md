# 高级组件 —— 结构化对比（compare）

> 产品比较、版本差异、方案优缺点

## 输入语法

```markdown
:::compare title="标题"\n| 维度 | A | B |\n|---|---|---|\n| 体积 | 大 | 小 |\n:::
```

## 最小输入

至少 2 列方案 2 行对比

## 选择条件

- 源稿有明确的产品比较、版本差异、方案优缺点语义
- 显式 `:::compare` 语法优先

## 禁止自动识别条件

- 无明确产品比较、版本差异、方案优缺点语义的普通段落不得自动升级
- 不得自动补造数据、结果或行动建议

## 降级方式

回退为普通 Markdown 表格

## 发布限制

- 正式 release HTML 禁止 `../assets/`、`file://`、本地磁盘路径
- 所有图片 `src` 必须是作者提供的可访问 HTTPS URL

## 六主题适配规则

见 [theme-adapters.md](theme-adapters.md)。组件语义跨主题一致，只有视觉语言不同。

## 生产 HTML 模板（moyu-green 主题示例）

> 其他主题使用相同结构，仅替换 `theme-adapters.md` 中的色值令牌。

```html
<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:#111827;line-height:1.5;"><span leaf="">两种方案对比</span></p>
  <section style="margin:0 0 8px;padding:10px 14px;background:#ECFDF5;border-radius:12px;border-left:3px solid #059669;">
      <p style="margin:0 0 6px;font-size:14px;font-weight:700;color:#111827;"><span leaf="">镜像体积</span></p>
      <p style="margin:0 0 4px;font-size:13px;color:#374151;"><span style="font-weight:600;color:#9CA3AF;margin-right:4px;"><span leaf="">单阶段构建</span></span><span leaf="">大</span></p><p style="margin:0 0 4px;font-size:13px;color:#374151;"><span style="font-weight:600;color:#9CA3AF;margin-right:4px;"><span leaf="">多阶段构建</span></span><span leaf="">小</span></p>
    </section>
<section style="margin:0 0 8px;padding:10px 14px;background:#ECFDF5;border-radius:12px;border-left:3px solid #059669;">
      <p style="margin:0 0 6px;font-size:14px;font-weight:700;color:#111827;"><span leaf="">构建复杂度</span></p>
      <p style="margin:0 0 4px;font-size:13px;color:#374151;"><span style="font-weight:600;color:#9CA3AF;margin-right:4px;"><span leaf="">单阶段构建</span></span><span leaf="">低</span></p><p style="margin:0 0 4px;font-size:13px;color:#374151;"><span style="font-weight:600;color:#9CA3AF;margin-right:4px;"><span leaf="">多阶段构建</span></span><span leaf="">中</span></p>
    </section>
<section style="margin:0 0 8px;padding:10px 14px;background:#ECFDF5;border-radius:12px;border-left:3px solid #059669;">
      <p style="margin:0 0 6px;font-size:14px;font-weight:700;color:#111827;"><span leaf="">生产适用性</span></p>
      <p style="margin:0 0 4px;font-size:13px;color:#374151;"><span style="font-weight:600;color:#9CA3AF;margin-right:4px;"><span leaf="">单阶段构建</span></span><span leaf="">一般</span></p><p style="margin:0 0 4px;font-size:13px;color:#374151;"><span style="font-weight:600;color:#9CA3AF;margin-right:4px;"><span leaf="">多阶段构建</span></span><span leaf="">高</span></p>
    </section>
</section>
```

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/compare-*.html`（验收产物，非生产依赖）。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。
