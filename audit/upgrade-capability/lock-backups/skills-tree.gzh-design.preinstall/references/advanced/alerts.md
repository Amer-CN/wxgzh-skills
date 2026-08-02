# 高级组件 —— 提示框（Alerts）

> GFM 风格 NOTE / TIP / IMPORTANT / WARNING / CAUTION 五种类型。所有主题均可用，视觉适配各主题。

## 输入语法

```markdown
:::alert type="warning" title="风险提示"
正文内容
:::
```

### 类型映射

| type | 标签 | 用途 |
|------|------|------|
| note | NOTE | 补充说明 |
| tip | TIP | 小技巧 |
| important | IMPORTANT | 重点强调 |
| warning | WARNING | 风险提示 |
| caution | CAUTION | 严重警告 |

## 最小输入

type + 正文（title 可选）

## 选择条件

- 源稿有明确的风险提示/注意事项/补充说明语义
- 显式 `:::alert` 语法优先

## 禁止自动识别条件

- 无明确警示语义的普通段落不得自动升级为 alert

## 降级方式

回退为普通引用块 `>`

## 反例

```markdown
<!-- 错误：缺少 type -->
:::alert title="提示"
正文
:::

<!-- 错误：缺少正文 -->
:::alert type="warning" title="提示"
:::
```

## HTML 模板

见 `tests/advanced-components/expected/alert-{theme}.html`（6 份，每套主题一份）。


---

## 生产 HTML 模板（moyu-green 主题示例）

> 其他主题使用相同结构，仅替换 `theme-adapters.md` 中的色值令牌。

```html
<section style="margin:0 0 24px;background:#FFFBEB;border-radius:0 12px 12px 0;border-left:4px solid #FDE68A;padding:16px 20px;">
  <p style="margin:0 0 6px;"><span style="display:inline-block;background:#FDE68A;color:#F0FDF4;font-size:11px;font-weight:700;padding:2px 10px;border-radius:4px;letter-spacing:1px;"><span leaf="">WARNING</span></span></p>
  <p style="margin:0 0 8px;font-size:15px;font-weight:700;color:#92400E;line-height:1.5;"><span leaf="">风险提示</span></p>
  <p style="margin:0;font-size:14px;color:#374151;line-height:1.8;"><span leaf="">此版本在 PostgreSQL 16.2 上存在已知的连接池泄漏问题。</span></p>
</section>
```

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/alert-*.html`（验收产物，非生产依赖）。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。
