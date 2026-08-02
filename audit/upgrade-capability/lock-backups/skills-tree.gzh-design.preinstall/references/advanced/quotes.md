# 高级组件 —— 金句引用（Quotes）

> 三种层级：普通引用、重点金句、带来源引用。

## 输入语法

```markdown
<!-- 普通引用 -->
:::quote type="normal"
普通引用文本
:::

<!-- 重点金句 -->
:::quote type="highlight"
「核心金句」
:::

<!-- 带来源引用 -->
:::quote type="sourced" source="来源名称"
引文内容
:::
```

也可用标准 Markdown `> 引用`，排版引擎自动判断是否升级为金句。

## 最小输入

金句文本

## 选择条件

- 源稿有引号包裹的判断句
- 显式 `:::quote` 语法优先

## 禁止自动识别条件

- 无引号或非金句的普通段落不得自动升级

## 降级方式

回退为普通段落

## HTML 模板

见 `tests/advanced-components/expected/quote-{theme}.html`（6 份）。


---

## 生产 HTML 模板（moyu-green 主题示例）

> 其他主题使用相同结构，仅替换 `theme-adapters.md` 中的色值令牌。

```html
<section style="margin:0 0 24px;background:#ECFDF5;border-radius:0 12px 12px 0;border-left:4px solid #059669;padding:16px 20px;"><p style="margin:0;font-size:16px;font-weight:800;color:#047857;line-height:1.7;"><span leaf="">「排版的核心不是好看，而是可读。」</span></p></section>
```

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/quote-*.html`（验收产物，非生产依赖）。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。
