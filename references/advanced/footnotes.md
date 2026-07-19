# 高级组件 —— 脚注（Footnotes）

> 正文引用标记与文末注释区。

## 输入语法

```markdown
正文中引用标记 [^1]

文末定义：
[^1]: 来源说明与 URL
```

## 最小输入

≥ 1 个脚注引用 + 定义

## 选择条件

- 源稿有 `[^N]` 脚注语法

## 禁止自动识别条件

- 无脚注语法时不生成脚注区
- 不得自动补造脚注

## 降级方式

不生成脚注区。脚注内容如果重要，融入正文。

## HTML 模板

见 `tests/advanced-components/expected/footnotes-{theme}.html`（6 份）。


---

## 生产 HTML 模板（moyu-green 主题示例）

> 其他主题使用相同结构，仅替换 `theme-adapters.md` 中的色值令牌。

```html
<section style="margin:24px 0 0;padding-top:16px;border-top:1px solid #D1D5DB;">
  <p style="margin:0 0 6px;font-size:12px;color:#9CA3AF;line-height:1.7;"><span style="font-weight:700;color:#059669;margin-right:4px;"><span leaf="">[1]</span></span><span leaf="">数据来源：example/benchmark v3.14.2 release notes</span></p>
<p style="margin:0 0 6px;font-size:12px;color:#9CA3AF;line-height:1.7;"><span style="font-weight:700;color:#059669;margin-right:4px;"><span leaf="">[2]</span></span><span leaf="">测试环境：8 核 CPU、32GB 内存</span></p>
</section>
```

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/footnotes-*.html`（验收产物，非生产依赖）。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。

> **⚠️ 微信兼容铁律（v5.2 修复）**：禁止在正文 HTML 中生成 `href="#..."` 内部片段链接。微信 `draft/add` API 不接受内部锚点链接，会返回 `errcode 45166 invalid content`。脚注引用标记和返回标记必须保留可见文字（`[1]`、`[2]`、`↩︎`）但不生成 `href` 属性。外部 HTTPS 链接（`href="https://..."`）不受此限制。
