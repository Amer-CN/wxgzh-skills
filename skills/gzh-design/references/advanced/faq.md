# 高级组件 —— 问答组（faq）

> 读者常见问题、产品 FAQ

## 输入语法

```markdown
:::faq title="标题"\n@q: 问题\n@a: 回答\n:::
```

## 最小输入

至少 1 组问答

## 选择条件

- 源稿有明确的读者常见问题、产品 FAQ语义
- 显式 `:::faq` 语法优先

## 禁止自动识别条件

- 无明确读者常见问题、产品 FAQ语义的普通段落不得自动升级
- 不得自动补造数据、结果或行动建议

## 降级方式

回退为普通标题 + 段落

## 发布限制

- 正式 release HTML 禁止 `../assets/`、`file://`、本地磁盘路径
- 所有图片 `src` 必须是作者提供的可访问 HTTPS URL

## 六主题适配规则

见 [theme-adapters.md](theme-adapters.md)。组件语义跨主题一致，只有视觉语言不同。

## 生产 HTML 模板（moyu-green 主题示例）

> 其他主题使用相同结构，仅替换 `theme-adapters.md` 中的色值令牌。

```html
<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:#111827;line-height:1.5;"><span leaf="">常见问题</span></p>
  <section style="margin:0 0 14px;padding:12px 14px;border-radius:0 12px 12px 0;border-left:3px solid #059669;background:#ECFDF5;">
      <p style="margin:0 0 6px;font-size:14px;font-weight:700;color:#111827;line-height:1.6;"><span leaf="">Q: 多阶段构建会拖慢 CI 吗？</span></p>
      <p style="margin:0;font-size:13px;color:#374151;line-height:1.8;"><span leaf="">A: 构建阶段可能略长，但最终镜像更小，拉取与部署通常更快。</span></p>
    </section>
<section style="margin:0 0 14px;padding:12px 14px;border-radius:0 12px 12px 0;border-left:3px solid #059669;background:#ECFDF5;">
      <p style="margin:0 0 6px;font-size:14px;font-weight:700;color:#111827;line-height:1.6;"><span leaf="">Q: 是否适合所有项目？</span></p>
      <p style="margin:0;font-size:13px;color:#374151;line-height:1.8;"><span leaf="">A: 不适合极简脚本项目；当运行依赖明显少于构建依赖时更有价值。</span></p>
    </section>
</section>
```

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/faq-*.html`（验收产物，非生产依赖）。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。
