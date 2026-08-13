# 高级组件 —— 代码对照（Code Compare）

> 单代码块保持原版逻辑；新增 before/after 或 A/B 代码对照。

## 输入语法

```markdown
:::code-compare title="改前与改后"
@before lang="python"
旧代码
@end
@after lang="python"
新代码
@end
:::
```

## 最小输入

before + after 各一段代码

## 选择条件

- 源稿有明确的"改前/改后"或"A/B"对照语义
- 显式 `:::code-compare` 语法优先

## 禁止自动识别条件

- 单一代码块不使用此组件
- 无明确对照语义的两个代码块不自动升级

## 降级方式

回退为通用库 1a/1b 代码块

## HTML 模板

见 `tests/advanced-components/expected/code-compare-{theme}.html`（6 份）。


---

## 生产 HTML 模板（moyu-green 主题示例）

> 其他主题使用相同结构，仅替换 `theme-adapters.md` 中的色值令牌。

```html
<section style="margin:0 0 24px;">
  <p style="margin:0 0 12px;font-size:15px;font-weight:700;color:#111827;line-height:1.5;"><span leaf="">改前与改后</span></p>
  <section style="margin:0 0 12px;border-radius:12px;overflow:hidden;background:#1E293B;">
    <section style="padding:7px 14px;background:#0F172A;"><span style="font-size:11px;color:#64748B;letter-spacing:1px;"><span leaf="">改前</span></span></section>
    <section style="padding:11px 14px;"><p style="margin:0;font-family:'SF Mono',Consolas,Monaco,monospace;font-size:13px;line-height:1.6;color:#E2E8F0;"><span leaf="">pool = connect(maxconn=200)</span></p></section>
  </section>
  <section style="margin:0 0 12px;border-radius:12px;overflow:hidden;background:#1a3a2a;">
    <section style="padding:7px 14px;background:#0a2a1a;"><span style="font-size:11px;color:#6BCB77;letter-spacing:1px;"><span leaf="">改后</span></span></section>
    <section style="padding:11px 14px;"><p style="margin:0;font-family:'SF Mono',Consolas,Monaco,monospace;font-size:13px;line-height:1.6;color:#C8E6C9;"><span leaf="">pool = connect(maxconn=200, retry=True)</span></p></section>
  </section>
</section>
```

> 完整 6 主题 HTML 见 `tests/advanced-components/expected/code-compare-*.html`（验收产物，非生产依赖）。
> **生产排版时从本文件的 HTML 模板取代码**，按 `theme-adapters.md` 替换色值。
