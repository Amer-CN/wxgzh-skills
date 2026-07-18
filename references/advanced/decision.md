# 高级组件 —— 决策说明卡（decision）

> 方案选择、选型结论

## 输入语法

```markdown
:::decision title="标题"\n@recommended: 推荐方案\n@option: 方案A | 说明\n@option: 方案B | 说明\n:::
```

## 最小输入

至少 2 个候选方案

## 选择条件

- 源稿有明确的方案选择、选型结论语义
- 显式 `:::decision` 语法优先

## 禁止自动识别条件

- 无明确方案选择、选型结论语义的普通段落不得自动升级
- 不得自动补造数据、结果或行动建议

## 降级方式

回退为普通对比段落

## 发布限制

- 正式 release HTML 禁止 `../assets/`、`file://`、本地磁盘路径
- 所有图片 `src` 必须是作者提供的可访问 HTTPS URL

## 六主题适配规则

见 [theme-adapters.md](theme-adapters.md)。组件语义跨主题一致，只有视觉语言不同。

## 生产 HTML 模板（moyu-green 主题示例）

> 其他主题使用相同结构，仅替换 `theme-adapters.md` 中的色值令牌。

```html
<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:#111827;line-height:1.5;"><span leaf="">技术选型</span></p>
  <p style="margin:0 0 12px;font-size:14px;color:#059669;font-weight:700;"><span leaf="">推荐方案：Docker 多阶段构建</span></p>
  <section style="margin:0 0 10px;padding:10px 14px;border-radius:0 12px 12px 0;border-left:3px solid #9CA3AF;background:#F0FDF4;">
      <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#9CA3AF;"><span leaf="">备选</span></p>
      <p style="margin:0 0 4px;font-size:14px;font-weight:600;color:#111827;"><span leaf="">单阶段构建</span></p>
      <p style="margin:0;font-size:13px;color:#374151;line-height:1.7;"><span leaf="">上手快，但镜像体积大</span></p>
    </section>
<section style="margin:0 0 10px;padding:10px 14px;border-radius:0 12px 12px 0;border-left:3px solid #059669;background:#ECFDF5;">
      <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#059669;"><span leaf="">推荐</span></p>
      <p style="margin:0 0 4px;font-size:14px;font-weight:600;color:#111827;"><span leaf="">多阶段构建</span></p>
      <p style="margin:0;font-size:13px;color:#374151;line-height:1.7;"><span leaf="">构建稍复杂，但运行镜像更小</span></p>
    </section>
</section>
```

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/decision-*.html`（验收产物，非生产依赖）。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。
