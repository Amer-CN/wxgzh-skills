# 高级组件 —— 事实数据卡（facts）

> 参数、版本、价格、状态等键值信息

## 输入语法

```markdown
:::facts title="标题"\n- 键: 值\n:::
```

## 最小输入

至少 2 条事实

## 选择条件

- 源稿有明确的参数、版本、价格、状态等键值信息语义
- 显式 `:::facts` 语法优先

## 禁止自动识别条件

- 无明确参数、版本、价格、状态等键值信息语义的普通段落不得自动升级
- 不得自动补造数据、结果或行动建议

## 降级方式

回退为普通列表

## 发布限制

- 正式 release HTML 禁止 `../assets/`、`file://`、本地磁盘路径
- 所有图片 `src` 必须是作者提供的可访问 HTTPS URL

## 六主题适配规则

见 [theme-adapters.md](theme-adapters.md)。组件语义跨主题一致，只有视觉语言不同。

## 生产 HTML 模板（moyu-green 主题示例）

> 其他主题使用相同结构，仅替换 `theme-adapters.md` 中的色值令牌。

```html
<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:#111827;line-height:1.5;"><span leaf="">核心数据</span></p>
  <section style="margin:0 0 8px;padding:10px 14px;background:#ECFDF5;border-radius:12px;border-left:3px solid #059669;">
      <p style="margin:0;font-size:13px;color:#9CA3AF;font-weight:600;"><span leaf="">月活用户</span></p>
      <p style="margin:2px 0 0;font-size:15px;color:#111827;font-weight:700;"><span leaf="">120 万</span></p>
    </section>
<section style="margin:0 0 8px;padding:10px 14px;background:#ECFDF5;border-radius:12px;border-left:3px solid #059669;">
      <p style="margin:0;font-size:13px;color:#9CA3AF;font-weight:600;"><span leaf="">同比增长</span></p>
      <p style="margin:2px 0 0;font-size:15px;color:#111827;font-weight:700;"><span leaf="">42%</span></p>
    </section>
<section style="margin:0 0 8px;padding:10px 14px;background:#ECFDF5;border-radius:12px;border-left:3px solid #059669;">
      <p style="margin:0;font-size:13px;color:#9CA3AF;font-weight:600;"><span leaf="">数据来源</span></p>
      <p style="margin:2px 0 0;font-size:15px;color:#111827;font-weight:700;"><span leaf="">2026 Q2 财报</span></p>
    </section>
</section>
```

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/facts-*.html`（验收产物，非生产依赖）。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。
